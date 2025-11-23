#=============================================================================
# GCP OUTPUTS
#=============================================================================

output "gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = module.gke.name
}

output "gke_endpoint" {
  description = "Endpoint for GKE cluster API server"
  value       = module.gke.endpoint
  sensitive   = true
}

output "cloudsql_instance_connection_name" {
  description = "Cloud SQL instance connection name for connecting from GKE"
  value       = module.cloudsql.connection_name
}

output "firestore_database" {
  description = "Firestore database ID"
  value       = module.firestore.database_id
}

#=============================================================================
# AWS OUTPUTS
#=============================================================================

output "submission_bucket_name" {
  description = "S3 bucket name for PDF submissions"
  value       = module.submission_bucket.bucket_name
}

output "checkpoint_bucket" {
  description = "S3 bucket name for Flink checkpoints"
  value       = module.aws_checkpoint_bucket.bucket_name
}

output "pdf_lambda_function_name" {
  description = "AWS Lambda function name for PDF text extraction"
  value       = module.pdf_extract_lambda.function_name
}

output "msk_bootstrap_brokers" {
  description = "MSK Kafka cluster bootstrap brokers (TLS)"
  value       = module.aws_msk.bootstrap_brokers
  sensitive   = true
}

output "msk_topics" {
  description = "List of Kafka topics created in MSK cluster"
  value       = module.aws_msk.topic_names
}

output "managed_flink_application_name" {
  description = "Managed Flink application name"
  value       = module.aws_managed_flink.managed_flink_application_name
}

output "managed_flink_application_arn" {
  description = "Managed Flink application ARN"
  value       = module.aws_managed_flink.managed_flink_application_arn
}

output "managed_flink_application_version" {
  description = "Managed Flink application version ID"
  value       = module.aws_managed_flink.managed_flink_application_version
}

#=============================================================================
# CONNECTION INFORMATION
#=============================================================================

output "kafka_connection_info" {
  description = "Kafka connection details for application configuration"
  value = {
    bootstrap_brokers = module.aws_msk.bootstrap_brokers
    topics            = module.aws_msk.topic_names
  }
  sensitive = true
}

output "database_connection_info" {
  description = "Database connection details (without credentials)"
  value = {
    cloudsql_connection_name = module.cloudsql.connection_name
    firestore_database       = module.firestore.database_id
  }
}
