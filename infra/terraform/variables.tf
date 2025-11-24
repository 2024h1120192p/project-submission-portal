#=============================================================================
# GENERAL CONFIGURATION
#=============================================================================

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

#=============================================================================
# GCP CONFIGURATION
#=============================================================================

variable "gcp_project_id" {
  description = "GCP project ID where resources will be deployed"
  type        = string

  validation {
    condition     = length(var.gcp_project_id) > 0
    error_message = "GCP project ID must not be empty."
  }
}

variable "gcp_region" {
  description = "GCP region for regional resources (e.g., GKE, Cloud SQL)"
  type        = string
  default     = "us-central1"
}

variable "gcp_zones" {
  description = "List of GCP zones for multi-zone deployments"
  type        = list(string)
  default     = ["us-central1-a", "us-central1-b"]

  validation {
    condition     = length(var.gcp_zones) >= 1
    error_message = "At least one zone must be specified."
  }
}

#=============================================================================
# AWS CONFIGURATION
#=============================================================================

variable "aws_region" {
  description = "AWS region for resources (MSK, EMR, Lambda, S3)"
  type        = string
  default     = "us-east-1"
}

variable "aws_vpc_cidr" {
  description = "CIDR block for AWS VPC (used by MSK cluster)"
  type        = string
  default     = "10.50.0.0/16"

  validation {
    condition     = can(cidrhost(var.aws_vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "aws_private_subnet_cidrs" {
  description = "List of CIDR blocks for private subnets in AWS VPC"
  type        = list(string)
  default     = ["10.50.1.0/24", "10.50.2.0/24"]

  validation {
    condition     = length(var.aws_private_subnet_cidrs) >= 2
    error_message = "At least two private subnets required for high availability."
  }
}

variable "aws_private_subnet_azs" {
  description = "List of AWS availability zones for private subnets (must match length and be distinct)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]

  validation {
    condition     = length(var.aws_private_subnet_azs) == length(var.aws_private_subnet_cidrs) && length(distinct(var.aws_private_subnet_azs)) == length(var.aws_private_subnet_azs)
    error_message = "aws_private_subnet_azs must match aws_private_subnet_cidrs length and all AZs must be distinct."
  }
}

#=============================================================================
# GKE CONFIGURATION
#=============================================================================

variable "gke_node_count" {
  description = "Number of nodes per zone in GKE default node pool"
  type        = number
  default     = 2

  validation {
    condition     = var.gke_node_count > 0
    error_message = "Node count must be at least 1."
  }
}

variable "gke_machine_type" {
  description = "Machine type for GKE nodes (e.g., e2-standard-4, n1-standard-2)"
  type        = string
  default     = "e2-standard-4"
}

variable "gke_disk_size_gb" {
  description = "Boot disk size (GB) for each GKE node"
  type        = number
  default     = 50

  validation {
    condition     = var.gke_disk_size_gb >= 10 && var.gke_disk_size_gb <= 2000
    error_message = "gke_disk_size_gb must be between 10 and 2000 GB."
  }
}

variable "gke_disk_type" {
  description = "Boot disk type for GKE nodes (pd-standard | pd-ssd)"
  type        = string
  default     = "pd-standard"

  validation {
    condition     = contains(["pd-standard", "pd-ssd"], var.gke_disk_type)
    error_message = "gke_disk_type must be one of: pd-standard, pd-ssd."
  }
}

#=============================================================================
# CLOUD SQL CONFIGURATION
#=============================================================================

variable "cloudsql_tier" {
  description = "Cloud SQL machine tier (e.g., db-f1-micro, db-custom-1-3840)"
  type        = string
  default     = "db-custom-1-3840"
}

variable "cloudsql_version" {
  description = "PostgreSQL version for Cloud SQL"
  type        = string
  default     = "POSTGRES_15"

  validation {
    condition     = can(regex("^POSTGRES_[0-9]+$", var.cloudsql_version))
    error_message = "Must be a valid PostgreSQL version (e.g., POSTGRES_15)."
  }
}

#=============================================================================
# S3 BUCKET CONFIGURATION
#=============================================================================

variable "submission_bucket_name" {
  description = "S3 bucket name for PDF submissions (auto-generated if null)"
  type        = string
  default     = null
}

variable "checkpoint_bucket_name" {
  description = "S3 bucket name for Flink checkpoints (auto-generated if null)"
  type        = string
  default     = null
}

#=============================================================================
# KUBERNETES & GITOPS CONFIGURATION
#=============================================================================

variable "argocd_version" {
  description = "Helm chart version for ArgoCD"
  type        = string
  default     = "5.51.3"
}

variable "gke_context_name" {
  description = "Kubernetes context name for GKE cluster (empty uses default)"
  type        = string
  default     = ""
}

variable "gateway_host" {
  description = "Domain name for gateway ingress (leave empty for IP-based access)"
  type        = string
  default     = ""
}

#=============================================================================
# AWS LAMBDA CONFIGURATION
#=============================================================================

variable "lambda_deployment_path" {
  description = "Local path to Lambda deployment ZIP file (relative to terraform directory)"
  type        = string
  default     = "../artifacts/lambda/submission_pdf_extract.zip"
}

variable "lambda_deployment_bucket" {
  description = "S3 bucket containing Lambda deployment package (optional, use lambda_deployment_path for local file)"
  type        = string
  default     = null
}

variable "lambda_deployment_key" {
  description = "S3 key (path) to Lambda deployment package ZIP file (optional, use lambda_deployment_path for local file)"
  type        = string
  default     = null
}

#=============================================================================
# APACHE FLINK CONFIGURATION
#=============================================================================

variable "flink_job_jar" {
  description = "S3 path to Flink job JAR file (e.g., s3://bucket/path/flink-job.jar)"
  type        = string
  # ISSUE #3: Made required (no default) with validation

  validation {
    condition     = can(regex("^s3://", var.flink_job_jar))
    error_message = "flink_job_jar must be an S3 path starting with 's3://'"
  }
}


#=============================================================================
# KAFKA CONFIGURATION
#=============================================================================

variable "kafka_topics" {
  description = "List of Kafka topic names to create in MSK cluster"
  type        = list(string)
  default     = ["submission_uploaded", "plagiarism_checked", "analytics_results"]

  validation {
    condition     = length(var.kafka_topics) > 0
    error_message = "At least one Kafka topic must be specified."
  }
}

#=============================================================================
# FEATURE FLAGS
#=============================================================================

variable "enable_firewall_rules" {
  description = "Enable creation of firewall rules for network security"
  type        = bool
  default     = true
}
