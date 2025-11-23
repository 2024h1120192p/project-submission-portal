#=============================================================================
# DATA SOURCES
#=============================================================================

# Data source for GCP authentication (used by Kubernetes provider)
data "google_client_config" "current" {}

#=============================================================================
# RANDOM RESOURCES
#=============================================================================

resource "random_id" "bucket_suffix" {
  byte_length = 2
}

resource "random_id" "checkpoint_suffix" {
  byte_length = 2
}

#=============================================================================
# GCP API ENABLEMENT
#=============================================================================

locals {
  gcp_required_services = [
    "container.googleapis.com",      # GKE
    "sqladmin.googleapis.com",       # Cloud SQL
    "compute.googleapis.com",        # Compute Engine
    "cloudfunctions.googleapis.com", # Cloud Functions
    "run.googleapis.com",            # Cloud Run
    "firestore.googleapis.com",      # Firestore
    "iam.googleapis.com",            # IAM
  ]
}

resource "google_project_service" "enabled_services" {
  for_each = toset(local.gcp_required_services)

  project            = var.gcp_project_id
  service            = each.value
  disable_on_destroy = false
}

#=============================================================================
# GCP INFRASTRUCTURE
#=============================================================================

# Custom VPC & Subnet for cross-cloud connectivity (ISSUE #1 fix)
# NOTE: Actual AWS↔GCP routing requires VPN / Interconnect; simple
# VPC peering between GCP and AWS is NOT natively supported. This network
# establishes an isolated CIDR (10.0.0.0/20) reserved for GKE to later
# attach VPN tunnels. Security group rules on MSK allow this CIDR.
resource "google_compute_network" "gke_vpc" {
  name                    = "${var.environment}-gke-vpc"
  project                 = var.gcp_project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "gke_subnet" {
  name          = "${var.environment}-gke-subnet"
  project       = var.gcp_project_id
  region        = var.gcp_region
  network       = google_compute_network.gke_vpc.id
  ip_cidr_range = "10.0.0.0/20"
}

# GKE Cluster
module "gke" {
  source = "./modules/gcp_gke"

  project_id      = var.gcp_project_id
  region          = var.gcp_region
  zones           = var.gcp_zones
  cluster_name    = local.gke_cluster_name
  network_name    = google_compute_network.gke_vpc.name
  subnetwork_name = google_compute_subnetwork.gke_subnet.name

  depends_on = [google_project_service.enabled_services]
}

# Cloud SQL PostgreSQL Instance & Databases
module "cloudsql" {
  source = "./modules/gcp_cloudsql"

  project_id          = var.gcp_project_id
  region              = var.gcp_region
  tier                = var.cloudsql_tier
  engine_version      = var.cloudsql_version
  instance_name       = local.cloudsql_name
  users_db_name       = local.database_names.users
  submissions_db_name = local.database_names.submissions

  depends_on = [google_project_service.enabled_services]
}

# Firestore Database for Analytics
module "firestore" {
  source = "./modules/gcp_firestore"

  project_id  = var.gcp_project_id
  database_id = "(default)"

  depends_on = [google_project_service.enabled_services]
}

# Observability Stack (Prometheus, Grafana, Loki)
module "observability" {
  source = "./modules/gcp_observability"

  namespace = "observability"

  depends_on = [module.gke]
}

# ArgoCD for GitOps
# ArgoCD for GitOps
module "argocd" {
  source = "./modules/gcp_argo"

  namespace     = "argocd"
  chart_version = var.argocd_version

  depends_on = [module.gke]
}

# Kubernetes Application Layer (HPAs, Ingress)
module "k8s_apps" {
  source = "./modules/gcp_k8s_apps"

  namespace    = "default"
  gateway_host = var.gateway_host # Leave empty for IP-based access, or set domain

  depends_on = [module.gke]
}

#=============================================================================
# AWS INFRASTRUCTURE
#=============================================================================

# S3 Bucket for PDF Submissions
module "submission_bucket" {
  source = "./modules/aws_s3_submission"

  region              = var.aws_region
  name                = coalesce(var.submission_bucket_name, "${var.environment}-submission-pdfs-${random_id.bucket_suffix.hex}")
  lambda_function_arn = module.pdf_extract_lambda.function_arn
}

# Lambda Function for PDF Text Extraction
module "pdf_extract_lambda" {
  source = "./modules/aws_lambda"

  region            = var.aws_region
  function_name     = local.lambda_name
  s3_bucket         = var.lambda_deployment_bucket
  s3_key            = var.lambda_deployment_key
  runtime           = "python3.11"
  handler           = "handler.lambda_handler"
  timeout           = 60
  memory_size       = 512
  source_bucket_arn = module.submission_bucket.bucket_arn
}

# MSK Kafka Cluster
module "aws_msk" {
  source = "./modules/aws_msk"

  region          = var.aws_region
  vpc_cidr        = var.aws_vpc_cidr
  private_subnets = var.aws_private_subnet_cidrs
  cluster_name    = local.msk_cluster_name
  kafka_version   = "3.5.1"
  topics          = var.kafka_topics
}

# Allow GKE subnet CIDR (10.0.0.0/20) to reach Kafka brokers (port 9092 TLS)
# This is part of ISSUE #1 fix; assumes future VPN tunnel routes traffic.
resource "aws_security_group_rule" "msk_from_gke" {
  type              = "ingress"
  security_group_id = module.aws_msk.security_group_id
  from_port         = 9092
  to_port           = 9092
  protocol          = "tcp"
  cidr_blocks       = ["10.0.0.0/20"]
  description       = "Allow GKE (10.0.0.0/20) access to MSK brokers"
}

# S3 Bucket for Flink Checkpoints
module "aws_checkpoint_bucket" {
  source = "./modules/aws_s3_checkpoint"

  region = var.aws_region
  name   = coalesce(var.checkpoint_bucket_name, "${var.environment}-flink-checkpoints-${random_id.checkpoint_suffix.hex}")
}

# Managed Flink (Kinesis Data Analytics for Apache Flink) Application
module "aws_managed_flink" {
  source = "./modules/aws_managed_flink"

  region                  = var.aws_region
  application_name        = local.managed_flink_app_name
  flink_job_jar           = var.flink_job_jar
  kafka_bootstrap_servers = module.aws_msk.bootstrap_brokers_plaintext
  parallelism             = 1
  checkpointing_enabled   = true
  subnet_ids              = module.aws_msk.private_subnet_ids
  security_group_ids      = [module.aws_msk.security_group_id]
}
