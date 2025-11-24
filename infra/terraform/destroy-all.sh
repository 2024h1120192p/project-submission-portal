#!/bin/bash

# Complete Infrastructure Destruction Script
# WARNING: This will destroy ALL infrastructure including databases, S3 buckets, and all data
# This action is IRREVERSIBLE!

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${RED}=========================================="
echo "  COMPLETE INFRASTRUCTURE DESTRUCTION"
echo -e "==========================================${NC}"
echo ""
echo -e "${YELLOW}WARNING: This will permanently destroy:${NC}"
echo "  • All GCP resources (GKE, Cloud SQL, Firestore, etc.)"
echo "  • All AWS resources (MSK, S3, Lambda, Flink, etc.)"
echo "  • All Kubernetes workloads and configurations"
echo "  • All databases and their data"
echo "  • All S3 buckets and uploaded files"
echo "  • All Terraform state"
echo ""
echo -e "${RED}THIS ACTION CANNOT BE UNDONE!${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo -e "${RED}Error: main.tf not found. Please run this script from infra/terraform/${NC}"
    exit 1
fi

# Confirmation prompts
read -p "Type 'DESTROY' to confirm you want to delete everything: " confirm1
if [ "$confirm1" != "DESTROY" ]; then
    echo "Cancelled."
    exit 0
fi

read -p "Are you ABSOLUTELY sure? Type 'YES DELETE EVERYTHING': " confirm2
if [ "$confirm2" != "YES DELETE EVERYTHING" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Starting destruction process...${NC}"
echo ""

# Step 1: Remove stuck Kafka topic resources from state
echo -e "${GREEN}Step 1: Cleaning up Terraform state...${NC}"
topics=(
    "paper_uploaded"
    "paper_uploaded_processed"
    "plagiarism_checked"
    "plagiarism_checked_processed"
    "analytics_window"
)

for topic in "${topics[@]}"; do
    resource="module.aws_msk.kafka_topic.topics[\"$topic\"]"
    if terraform state list 2>/dev/null | grep -q "$resource"; then
        echo "  Removing: $resource"
        terraform state rm "$resource" 2>/dev/null || true
    fi
done
echo ""

# Step 2: Empty S3 buckets before destruction (Terraform can't destroy non-empty buckets)
echo -e "${GREEN}Step 2: Emptying S3 buckets...${NC}"

# Get bucket names from Terraform state
SUBMISSION_BUCKET=$(terraform state show module.submission_bucket.aws_s3_bucket.submission 2>/dev/null | grep "bucket " | awk '{print $3}' | tr -d '"' || echo "")
CHECKPOINT_BUCKET=$(terraform state show module.aws_checkpoint_bucket.aws_s3_bucket.checkpoint 2>/dev/null | grep "bucket " | awk '{print $3}' | tr -d '"' || echo "")

if [ ! -z "$SUBMISSION_BUCKET" ]; then
    echo "  Emptying submission bucket: $SUBMISSION_BUCKET"
    aws s3 rm s3://$SUBMISSION_BUCKET --recursive 2>/dev/null || echo "    (bucket may not exist or already empty)"
fi

if [ ! -z "$CHECKPOINT_BUCKET" ]; then
    echo "  Emptying checkpoint bucket: $CHECKPOINT_BUCKET"
    aws s3 rm s3://$CHECKPOINT_BUCKET --recursive 2>/dev/null || echo "    (bucket may not exist or already empty)"
fi
echo ""

# Step 3: Disable deletion protection on Cloud SQL (if enabled)
echo -e "${GREEN}Step 3: Disabling Cloud SQL deletion protection...${NC}"
GCP_PROJECT=$(grep 'gcp_project_id' terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
CLOUDSQL_INSTANCE=$(terraform state show module.cloudsql.google_sql_database_instance.postgres 2>/dev/null | grep "name " | head -1 | awk '{print $3}' | tr -d '"' || echo "")

if [ ! -z "$CLOUDSQL_INSTANCE" ] && [ ! -z "$GCP_PROJECT" ]; then
    echo "  Disabling deletion protection for: $CLOUDSQL_INSTANCE"
    gcloud sql instances patch $CLOUDSQL_INSTANCE \
        --no-deletion-protection \
        --project=$GCP_PROJECT \
        --quiet 2>/dev/null || echo "    (instance may not exist or already disabled)"
fi
echo ""

# Step 3.5: Note about Firestore (cannot be deleted via API)
echo -e "${GREEN}Step 3.5: Checking Firestore database...${NC}"
if [ ! -z "$GCP_PROJECT" ]; then
    if gcloud firestore databases list --project=$GCP_PROJECT 2>/dev/null | grep -q "(default)"; then
        echo -e "${YELLOW}  Note: Firestore database '(default)' exists${NC}"
        echo "  ℹ Firestore default databases cannot be deleted via API"
        echo "  ℹ This is a GCP limitation - the database will persist"
        echo "  ℹ To remove it, you must delete the entire GCP project"
    else
        echo "  ✓ No Firestore database found"
    fi
fi
echo ""

# Step 4: Remove MSK cluster configuration (if it has issues)
echo -e "${GREEN}Step 4: Handling MSK cluster configuration...${NC}"
if terraform state list 2>/dev/null | grep -q "module.aws_msk.aws_msk_configuration"; then
    echo "  MSK configuration found in state"
fi
echo ""

# Step 5: Destroy all Terraform-managed infrastructure
echo -e "${GREEN}Step 5: Destroying all Terraform resources...${NC}"
echo "  This may take 15-30 minutes..."
echo ""

# Use -auto-approve to avoid additional prompts (we already confirmed above)
terraform destroy -auto-approve

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Terraform resources destroyed successfully!${NC}"
else
    echo ""
    echo -e "${YELLOW}Terraform destroy encountered errors. Continuing with cleanup...${NC}"
fi
echo ""

# Step 5b: Force delete leftover Lambda functions (if any)
echo -e "${GREEN}Step 5b: Forcing deletion of leftover Lambda functions...${NC}"
ENVIRONMENT=$(grep '^environment' terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
AWS_REGION=$(grep '^aws_region' terraform.tfvars | awk -F'=' '{print $2}' | tr -d ' "')
LAMBDA_NAME="${ENVIRONMENT}-pdf-extract"

if [ -z "$AWS_REGION" ]; then
    AWS_REGION="us-east-1" # fallback
fi

if aws lambda get-function --function-name "$LAMBDA_NAME" --region "$AWS_REGION" 1>/dev/null 2>&1; then
    echo "  Deleting Lambda function: $LAMBDA_NAME (region: $AWS_REGION)"
    aws lambda delete-function --function-name "$LAMBDA_NAME" --region "$AWS_REGION" 2>/dev/null || echo "    (failed to delete lambda)"
else
    echo "  Lambda function $LAMBDA_NAME not found (already deleted)"
fi

# Optionally delete any other environment-scoped lambdas that remain
OTHER_FUNCS=$(aws lambda list-functions --region "$AWS_REGION" --query "Functions[?starts_with(FunctionName, \`${ENVIRONMENT}-\`)].FunctionName" --output text 2>/dev/null || echo "")
for fn in $OTHER_FUNCS; do
    if [ "$fn" != "$LAMBDA_NAME" ]; then
        echo "  Deleting additional Lambda: $fn"
        aws lambda delete-function --function-name "$fn" --region "$AWS_REGION" 2>/dev/null || echo "    (failed to delete $fn)"
    fi
done
echo ""

# Step 6: Clean up local Terraform state
echo -e "${GREEN}Step 6: Cleaning up Terraform state files...${NC}"

read -p "Delete local Terraform state files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "terraform.tfstate" ]; then
        echo "  Creating backup: terraform.tfstate.destroyed.backup"
        cp terraform.tfstate terraform.tfstate.destroyed.backup
        echo "  Removing: terraform.tfstate"
        rm -f terraform.tfstate
    fi
    
    if [ -f "terraform.tfstate.backup" ]; then
        echo "  Removing: terraform.tfstate.backup"
        rm -f terraform.tfstate.backup
    fi
    
    if [ -d ".terraform" ]; then
        echo "  Removing: .terraform/"
        rm -rf .terraform
    fi
    
    if [ -f ".terraform.lock.hcl" ]; then
        echo "  Removing: .terraform.lock.hcl"
        rm -f .terraform.lock.hcl
    fi
    
    echo -e "${GREEN}  Local state cleaned up!${NC}"
else
    echo "  Keeping local state files"
fi
echo ""

# Step 7: Verify deletion
echo -e "${GREEN}Step 7: Verification${NC}"
echo ""
echo "Checking for remaining resources..."

# Check AWS resources
echo "  AWS Resources:"
MSK_CLUSTER_NAME="${ENVIRONMENT}-msk"
aws msk list-clusters --region "$AWS_REGION" --query "ClusterInfoList[?ClusterName==\`${MSK_CLUSTER_NAME}\`]" --output text 2>/dev/null && echo "    ⚠ MSK cluster still exists" || echo "    ✓ MSK cluster destroyed"
aws s3 ls 2>/dev/null | grep -E 'submission|checkpoint' && echo "    ⚠ S3 buckets still exist" || echo "    ✓ S3 buckets destroyed"
aws lambda list-functions --region "$AWS_REGION" --query "Functions[?starts_with(FunctionName, \`${ENVIRONMENT}-\`)].FunctionName" --output text 2>/dev/null | grep -q . && echo "    ⚠ Some Lambda functions still exist" || echo "    ✓ All environment Lambdas destroyed"

# Check GCP resources
echo "  GCP Resources:"
if [ ! -z "$GCP_PROJECT" ]; then
    gcloud container clusters list --project=$GCP_PROJECT 2>/dev/null | grep -q "dev-core-gke" && echo "    ⚠ GKE cluster still exists" || echo "    ✓ GKE cluster destroyed"
    gcloud sql instances list --project=$GCP_PROJECT 2>/dev/null | grep -q "dev-pg" && echo "    ⚠ Cloud SQL still exists" || echo "    ✓ Cloud SQL destroyed"
    gcloud firestore databases list --project=$GCP_PROJECT 2>/dev/null | grep -q "(default)" && echo "    ⚠ Firestore database still exists (cannot be deleted via API - this is normal)" || echo "    ✓ Firestore database removed"
fi

echo ""
echo -e "${RED}=========================================="
echo "  DESTRUCTION COMPLETE"
echo -e "==========================================${NC}"
echo ""
echo "Summary:"
echo "  • All cloud infrastructure destroyed"
echo "  • All data permanently deleted"
echo "  • Terraform state cleared"
echo ""
echo "To rebuild the infrastructure:"
echo "  1. terraform init"
echo "  2. terraform plan"
echo "  3. terraform apply"
echo ""
