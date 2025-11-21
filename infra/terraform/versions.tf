terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.11"
    }
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    kafka = {
      source  = "Mongey/kafka"
      version = "~> 0.7.0"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}
