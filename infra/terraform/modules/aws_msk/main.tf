variable "region" {}
variable "vpc_cidr" {}
variable "private_subnets" { type = list(string) }
variable "cluster_name" {}
variable "kafka_version" {}
variable "topics" { type = list(string) }

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.cluster_name}-vpc" }
}

resource "aws_subnet" "private" {
  for_each                = toset(var.private_subnets)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.cluster_name}-subnet-${replace(each.value, ".0/24", "")}" }
}

resource "aws_security_group" "msk" {
  name        = "${var.cluster_name}-sg"
  description = "MSK security group"
  vpc_id      = aws_vpc.this.id
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_msk_cluster" "msk" {
  cluster_name           = var.cluster_name
  kafka_version          = var.kafka_version
  number_of_broker_nodes = length(var.private_subnets)

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = [for s in aws_subnet.private : s.id]
    security_groups = [aws_security_group.msk.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled = false
      }
      firehose {
        enabled = false
      }
      s3 {
        enabled = false
      }
    }
  }
}

# Kafka provider for topic creation
terraform {
  required_providers {
    kafka = {
      source  = "Mongey/kafka"
      version = "~> 0.7.0"
    }
  }
}

provider "kafka" {
  bootstrap_servers = [aws_msk_cluster.msk.bootstrap_brokers_tls]

  tls_enabled     = true
  skip_tls_verify = true # For dev/testing; use proper certs in production
}

# Create Kafka topics
resource "kafka_topic" "topics" {
  for_each = toset(var.topics)

  name               = each.key
  replication_factor = 2
  partitions         = 3

  config = {
    "retention.ms"   = "604800000" # 7 days
    "segment.ms"     = "86400000"  # 1 day
    "cleanup.policy" = "delete"
  }

  depends_on = [aws_msk_cluster.msk]
}

output "bootstrap_brokers" { value = aws_msk_cluster.msk.bootstrap_brokers_tls }
output "bootstrap_brokers_plaintext" { value = aws_msk_cluster.msk.bootstrap_brokers }
output "private_subnet_ids" { value = [for s in aws_subnet.private : s.id] }
output "vpc_id" { value = aws_vpc.this.id }
output "security_group_id" { value = aws_security_group.msk.id }
output "topic_names" { value = [for t in kafka_topic.topics : t.name] }
