# Multi-Cloud Terraform Infrastructure (GCP + AWS)

This directory provisions the core platform (GCP) and streaming + analytics (AWS) components for the assignment.

## Components
- **GCP**: GKE cluster, Cloud SQL (users + submissions), Firestore (analytics windows), ArgoCD (GitOps), Observability stack (Prometheus, Grafana, Loki), HPAs + Ingress.
- **AWS**: 
  - S3 bucket (PDF uploads with Lambda trigger)
  - Lambda function (PDF text extraction - serverless)
  - MSK (Kafka) cluster with automated topic creation
  - EMR (Flink) cluster for stream processing
  - S3 bucket (Flink checkpoints)

## Key Features
✅ **Multi-cloud architecture**: GCP for core services, AWS for analytics pipeline  
✅ **Serverless**: AWS Lambda for event-driven PDF processing  
✅ **Stream processing**: Flink on EMR consuming from MSK Kafka  
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
6. **Flink job deployment**: If `flink_job_jar` variable is set, the job will be automatically deployed as an EMR step.

## Module Overview
Each module isolates a logical infrastructure slice. Adjust variables or extend modules for production hardening (VPCs, security groups, secrets, etc.).

## Next TODOs
- Add VPC + subnet module for GCP instead of defaults.
- Add secret management (e.g., Google Secret Manager, AWS Secrets Manager) for DB creds.
- Add IAM least privilege refinements.
- Configure proper TLS certificates for Kafka (currently uses skip_tls_verify for dev).
- Set up VPC peering between AWS (MSK/EMR) and GCP (GKE) for private connectivity.

## State Backend
Currently local state. Migrate to remote (e.g., GCS bucket + state lock) for team use.

## Destroy
```bash
terraform destroy -var="gcp_project_id=YOUR_PROJECT" -var="environment=dev"
```
