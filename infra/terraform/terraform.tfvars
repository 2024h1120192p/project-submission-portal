environment    = "dev"
gcp_project_id = "paper-submission-portal"
gcp_region     = "us-central1"
gcp_zones      = ["us-central1-a", "us-central1-b"]

aws_region               = "us-east-1"
aws_vpc_cidr             = "10.50.0.0/16"
aws_private_subnet_cidrs = ["10.50.1.0/24", "10.50.2.0/24"]

cloudsql_tier    = "db-f1-micro"
cloudsql_version = "POSTGRES_15"

submission_bucket_name = "g527-submission-bucket"
checkpoint_bucket_name = "g527-checkpoint-bucket"

lambda_deployment_bucket = "lambda-deployment-artifacts"
lambda_deployment_key    = "lambda/pdf-extract.zip"

flink_job_jar   = "" # Set to S3 path when ready, e.g., "s3://bucket/flink-jobs/stream-processor.jar"
flink_job_class = "com.example.flink.SubmissionStreamProcessor"

argocd_version = "5.51.3"

gke_context_name = ""

enable_firewall_rules = true

kafka_topics = ["submission_uploaded", "plagiarism_checked", "analytics_results"]
