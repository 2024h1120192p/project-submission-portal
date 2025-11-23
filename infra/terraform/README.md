# Multi-Cloud Terraform Infrastructure (GCP + AWS)

This directory provisions the core platform (GCP) and streaming + analytics (AWS) components for the assignment.

## Components
- **GCP**: GKE cluster, Cloud SQL (users + submissions), Firestore (analytics windows), ArgoCD (GitOps), Observability stack (Prometheus, Grafana, Loki), HPAs + Ingress.
- **AWS**: 
  - S3 bucket (PDF uploads with Lambda trigger)
  - Lambda function (PDF text extraction - serverless)
  - MSK (Kafka) cluster with automated topic creation
  - Managed Flink (Kinesis Data Analytics for Apache Flink) application consuming Kafka
  - S3 bucket (Flink checkpoints)

## Key Features
✅ **Multi-cloud architecture**: GCP for core services, AWS for analytics pipeline  
✅ **Serverless**: AWS Lambda for event-driven PDF processing  
✅ **Stream processing**: Managed Flink (Kinesis Data Analytics) consuming from MSK Kafka  
✅ **Kafka topics**: Automatically created via Terraform (Mongey/kafka provider)  
✅ **GitOps**: ArgoCD for Kubernetes deployments  
✅ **Autoscaling**: HPAs for 5 services (gateway, users, submissions, notification, plagiarism)  
✅ **Observability**: Full stack with Prometheus, Grafana, Loki

## Prerequisites
1. Terraform >= 1.6
2. Credentials:
   - **GCP**: `GOOGLE_APPLICATION_CREDENTIALS` pointing to service account with roles: `roles/container.admin`, `roles/cloudsql.admin`, `roles/datastore.owner`, `roles/iam.serviceAccountUser`.
   - **AWS**: Standard access keys with permissions for VPC, EC2, MSK, EMR, S3, Lambda, IAM.
3. **Lambda deployment package**: Upload `pdf-extract.zip` to S3 bucket specified in `lambda_deployment_bucket` variable
4. **Flink job JAR**: (Optional) Upload Flink job JAR to S3 and set `flink_job_jar` variable
5. Domain / DNS record (pending) for gateway ingress.

## Quick Start
```bash
cd infra/terraform
terraform init
terraform plan -var="gcp_project_id=YOUR_PROJECT" -var="environment=dev"
terraform apply -var="gcp_project_id=YOUR_PROJECT" -var="environment=dev"
```

## Post Apply Steps (Manual / To Automate Later)
1. Push application Kubernetes manifests to the Git repo ArgoCD watches.
2. Configure ArgoCD Application CRs for each microservice (gateway, users, submissions, notification, analytics, plagiarism).
3. Provide Helm values overrides for observability stack dashboards & scraping configs.
4. **Kafka topics are automatically created** by Terraform using the Mongey/kafka provider.
5. **Lambda function is automatically triggered** on PDF uploads to S3 bucket.
6. **Flink job deployment**: If `flink_job_jar` variable is set, the code is attached to the Managed Flink application.

## Kafka ↔ Managed Flink Networking
The Flink application must be deployed in the same VPC (or a peered one) as the MSK cluster to reach broker endpoints. The module now exposes:

### VPC Configuration Implementation
The `vpc_configuration` block is nested within `application_configuration` in `aws_kinesisanalyticsv2_application` (not a top-level resource).

**How it works:**
- When both `subnet_ids` and `security_group_ids` are provided, a `vpc_configuration` block is dynamically added
- Flink application ENIs are attached to the specified subnets
- Security groups control egress to MSK broker ports (9092 TLS)

**Configuration Flow:**
```
Root main.tf passes:
 - module.aws_msk.private_subnet_ids (subnets where MSK brokers are)
 - module.aws_msk.security_group_id (MSK security group)
    ↓
aws_managed_flink module receives as:
 - var.subnet_ids
 - var.security_group_ids
    ↓
aws_kinesisanalyticsv2_application resource creates:
 - dynamic vpc_configuration { subnet_ids, security_group_ids }
```

| Variable | Purpose |
|----------|---------|
| `subnet_ids` | Private subnet IDs for ENIs attached to the Flink app |
| `security_group_ids` | Security groups granting egress to MSK broker ports (TLS 9092) |

These are wired automatically from the MSK module outputs. Override only if you need a tighter security group.

**Security Group Requirements:**
Egress from Flink ENIs to MSK brokers:
```
Protocol: TCP
Port: 9092 (TLS brokers)
Destination: MSK broker subnets or security group ID
```

The MSK module's SG already allows ingress from `var.aws_vpc_cidr`, so reusing it works.

Flink runtime properties set via environment:
```
kafka.bootstrap.servers=<MSK TLS brokers>
```
Add more (in code/JAR) if needed:
```
security.protocol=SSL
group.id=flink-analytics-consumer
auto.offset.reset=latest
```

## MSK Topic Checklist
Ensure at least two topics for assignment compliance:
1. Input events (e.g. `submission_uploaded`)
2. Aggregated results (e.g. `analytics_results`)

The `plagiarism_checked` topic is available for additional flows.

## Troubleshooting Kafka ↔ Flink Integration

**Flink app fails to start with "Unable to connect to bootstrap brokers":**
- Verify subnets have route to MSK brokers (via NAT gateway or direct routing)
- Check security group egress rules allow port 9092 (TLS)
- Ensure Flink is in same VPC as MSK (or peered/routable)

**"Access Denied" in Flink logs:**
- Verify IAM role policy (`aws_iam_role_policy.kda_inline`) includes required Kafka permissions
- Check MSK security group allows ingress from Flink's VPC CIDR

**VPC configuration not applied:**
- Ensure both `subnet_ids` and `security_group_ids` are non-empty lists
- Verify `main.tf` passes MSK module outputs to `aws_managed_flink`

**Kafka topic not found by Flink:**
- Topics must be created before Flink application starts
- Terraform creates topics automatically (Mongey/kafka provider)
- Verify topic names in `terraform.tfvars` kafka_topics match Flink consumer config

## Module Overview
Each module isolates a logical infrastructure slice. Adjust variables or extend modules for production hardening (VPCs, security groups, secrets, etc.).

## Next TODOs
- Add VPC + subnet module for GCP instead of defaults.
- Add secret management (e.g., Google Secret Manager, AWS Secrets Manager) for DB creds.
- Add IAM least privilege refinements.
- Configure proper TLS certificates for Kafka (currently uses skip_tls_verify in MSK provider for dev).
- Set up VPC peering between AWS (MSK/Flink) and GCP (GKE) for cross-cloud connectivity.

## State Backend
Currently local state. Migrate to remote (e.g., GCS bucket + state lock) for team use.

## Destroy
```bash
terraform destroy -var="gcp_project_id=YOUR_PROJECT" -var="environment=dev"
```

