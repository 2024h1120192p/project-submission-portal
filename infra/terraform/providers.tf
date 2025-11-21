#=============================================================================
# PROVIDER CONFIGURATION
#=============================================================================

# Prerequisites:
# - GCP: Set GOOGLE_APPLICATION_CREDENTIALS environment variable or use gcloud auth
# - AWS: Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, or use AWS CLI configuration
# - Kubernetes: Run `gcloud container clusters get-credentials <cluster-name>` after GKE creation

#-----------------------------------------------------------------------------
# Google Cloud Platform (GCP) Provider
#-----------------------------------------------------------------------------

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

#-----------------------------------------------------------------------------
# Kubernetes Provider
#-----------------------------------------------------------------------------

# Note: For initial deployment workflow:
# 1. First run: terraform apply -target=module.gke
# 2. Configure kubectl: gcloud container clusters get-credentials <cluster-name> --region <region>
# 3. Then run: terraform apply (to deploy k8s resources)

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.gke_context_name != "" ? var.gke_context_name : null
}

provider "helm" {
  # Helm 3.x provider configuration
  # Uses the same kubeconfig as kubectl
  kubernetes = {
    config_path    = "~/.kube/config"
    config_context = var.gke_context_name != "" ? var.gke_context_name : null
  }
}

#-----------------------------------------------------------------------------
# Amazon Web Services (AWS) Provider
#-----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.aws_tags
  }
}

