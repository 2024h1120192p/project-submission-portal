#!/bin/bash
#=============================================================================
# Terraform Quality Assurance Script
#=============================================================================
# This script runs various checks to ensure Terraform code quality
#
# Usage: ./terraform-qa.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================================="
echo "Terraform Quality Assurance Checks"
echo "============================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print section
print_section() {
    echo ""
    echo "-----------------------------------------------------------------------------"
    echo "$1"
    echo "-----------------------------------------------------------------------------"
}

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}ERROR: terraform is not installed${NC}"
    exit 1
fi

# 1. Terraform Format Check
print_section "1. Checking Terraform Formatting"
if terraform fmt -check -recursive &> /dev/null; then
    print_status 0 "All files are properly formatted"
else
    print_status 1 "Some files need formatting"
    echo "   Run: terraform fmt -recursive"
    NEEDS_FMT=1
fi

# 2. Terraform Validation
print_section "2. Validating Terraform Configuration"
if terraform init -backend=false &> /dev/null; then
    if terraform validate &> /dev/null; then
        print_status 0 "Configuration is valid"
    else
        print_status 1 "Configuration validation failed"
        terraform validate
        exit 1
    fi
else
    print_status 1 "Terraform initialization failed"
    exit 1
fi

# 3. Check for required files
print_section "3. Checking Required Files"
REQUIRED_FILES=("main.tf" "variables.tf" "outputs.tf" "providers.tf" "versions.tf" "locals.tf")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "$file exists"
    else
        print_status 1 "$file is missing"
    fi
done

# 4. Check variable descriptions
print_section "4. Checking Variable Descriptions"
if grep -q 'variable.*{' variables.tf; then
    VARS_WITHOUT_DESC=$(grep -A 5 '^variable' variables.tf | grep -B 5 '{' | grep -v 'description' | grep '^variable' | wc -l || true)
    if [ "$VARS_WITHOUT_DESC" -eq 0 ]; then
        print_status 0 "All variables have descriptions"
    else
        print_warning "Some variables might be missing descriptions"
    fi
fi

# 5. Check output descriptions
print_section "5. Checking Output Descriptions"
if [ -f "outputs.tf" ]; then
    OUTPUTS_WITHOUT_DESC=$(grep -A 3 '^output' outputs.tf | grep -B 3 '{' | grep -v 'description' | grep '^output' | wc -l || true)
    if [ "$OUTPUTS_WITHOUT_DESC" -eq 0 ]; then
        print_status 0 "All outputs have descriptions"
    else
        print_warning "Some outputs might be missing descriptions"
    fi
fi

# 6. Check for hardcoded values
print_section "6. Checking for Common Hardcoded Values (Anti-patterns)"
HARDCODED_FOUND=0

# Check for hardcoded IPs
if grep -r -n --include="*.tf" --exclude="terraform.tfvars" --exclude="*.tfvars" '10\.\|192\.168\.\|172\.' . | grep -v '#' | grep -v 'default.*=' &> /dev/null; then
    print_warning "Potential hardcoded IP addresses found (check if in variables/tfvars)"
    HARDCODED_FOUND=1
fi

# Check for AWS account IDs
if grep -r -n --include="*.tf" --exclude="terraform.tfvars" --exclude="*.tfvars" 'arn:aws:' . | grep -v '#' | grep -v 'output' &> /dev/null; then
    print_warning "Potential hardcoded AWS ARNs found"
    HARDCODED_FOUND=1
fi

if [ $HARDCODED_FOUND -eq 0 ]; then
    print_status 0 "No obvious hardcoded values found"
fi

# 7. Check for sensitive outputs
print_section "7. Checking Sensitive Output Markers"
if [ -f "outputs.tf" ]; then
    if grep -q 'endpoint\|password\|key\|token\|secret' outputs.tf; then
        SENSITIVE_OUTPUTS=$(grep -B 5 'endpoint\|password\|key\|token\|secret' outputs.tf | grep 'output\|sensitive' || true)
        echo "Outputs with potentially sensitive data should be marked as sensitive = true"
        echo "$SENSITIVE_OUTPUTS" | grep 'output' | while read line; do
            OUTPUT_NAME=$(echo "$line" | cut -d'"' -f2)
            if grep -A 3 "output \"$OUTPUT_NAME\"" outputs.tf | grep -q 'sensitive.*true'; then
                echo -e "  ${GREEN}✓${NC} $OUTPUT_NAME is marked sensitive"
            else
                echo -e "  ${YELLOW}⚠${NC} $OUTPUT_NAME might need sensitive = true"
            fi
        done
    fi
fi

# 8. Check for TODO/FIXME comments
print_section "8. Checking for TODO/FIXME Comments"
TODO_COUNT=$(grep -r -n --include="*.tf" 'TODO\|FIXME' . | wc -l || true)
if [ "$TODO_COUNT" -gt 0 ]; then
    print_warning "Found $TODO_COUNT TODO/FIXME comments"
    grep -r -n --include="*.tf" 'TODO\|FIXME' . || true
else
    print_status 0 "No TODO/FIXME comments found"
fi

# 9. Check terraform.lock.hcl
print_section "9. Checking Dependency Lock File"
if [ -f ".terraform.lock.hcl" ]; then
    print_status 0 "Dependency lock file exists"
else
    print_warning "No .terraform.lock.hcl found - run 'terraform init' to create it"
fi

# 10. Check for terraform-docs
print_section "10. Checking Documentation"
if [ -f ".terraform-docs.yml" ]; then
    print_status 0 "terraform-docs configuration exists"
    if command -v terraform-docs &> /dev/null; then
        print_status 0 "terraform-docs is installed"
        echo "   Run: terraform-docs markdown table . > TERRAFORM.md"
    else
        print_warning "terraform-docs is not installed"
        echo "   Install: https://terraform-docs.io/user-guide/installation/"
    fi
else
    print_warning ".terraform-docs.yml not found"
fi

# Summary
echo ""
echo "============================================================================="
echo "Quality Assurance Check Complete"
echo "============================================================================="

if [ ${NEEDS_FMT:-0} -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run: terraform fmt -recursive"
    echo "  2. Commit the formatted files"
fi

echo ""
echo "For additional checks, consider installing:"
echo "  - tflint: https://github.com/terraform-linters/tflint"
echo "  - checkov: https://www.checkov.io/"
echo "  - terraform-docs: https://terraform-docs.io/"
