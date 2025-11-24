variable "region" {}
variable "vpc_cidr" {}
variable "private_subnets" { type = list(string) }
variable "private_subnet_azs" { type = list(string) }
variable "cluster_name" {}
variable "kafka_version" {}
variable "topics" { 
  type        = list(string)
  description = "List of topic names for reference (topics will be auto-created by applications)"
}

locals {
  subnet_az_pairs = zipmap(var.private_subnets, var.private_subnet_azs)
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.cluster_name}-vpc" }
}

# Internet Gateway for NAT Gateway
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.cluster_name}-igw" }
}

# Public subnet for NAT Gateway
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 255) # Use last /24 in the VPC range
  availability_zone       = var.private_subnet_azs[0]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.cluster_name}-public-subnet" }
}

# Route table for public subnet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = { Name = "${var.cluster_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  tags   = { Name = "${var.cluster_name}-nat-eip" }
}

# NAT Gateway in public subnet
resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id
  tags          = { Name = "${var.cluster_name}-nat" }
  
  depends_on = [aws_internet_gateway.this]
}

resource "aws_subnet" "private" {
  for_each                = local.subnet_az_pairs
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.key
  availability_zone       = each.value
  map_public_ip_on_launch = false
  tags                    = { Name = "${var.cluster_name}-subnet-${replace(each.key, ".0/24", "")}" }
}

# Route table for private subnets (with NAT Gateway)
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }
  tags = { Name = "${var.cluster_name}-private-rt" }
}

# Associate private subnets with NAT Gateway route table
resource "aws_route_table_association" "private" {
  for_each       = aws_subnet.private
  subnet_id      = each.value.id
  route_table_id = aws_route_table.private.id
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

  configuration_info {
    arn      = aws_msk_configuration.msk_config.arn
    revision = aws_msk_configuration.msk_config.latest_revision
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

# MSK Configuration with auto-topic creation enabled
resource "aws_msk_configuration" "msk_config" {
  name              = "${var.cluster_name}-config"
  kafka_versions    = [var.kafka_version]
  server_properties = <<PROPERTIES
auto.create.topics.enable=true
default.replication.factor=2
min.insync.replicas=1
num.partitions=3
PROPERTIES
}

# NOTE: Kafka topics are NOT created by Terraform.
# Topics will be auto-created by applications on first use if auto.create.topics.enable=true
# on the MSK cluster, or can be created manually via kafka-topics CLI or MSK Console.

output "bootstrap_brokers" { value = aws_msk_cluster.msk.bootstrap_brokers_tls }
output "bootstrap_brokers_plaintext" { value = aws_msk_cluster.msk.bootstrap_brokers }
output "private_subnet_ids" { value = [for s in aws_subnet.private : s.id] }
output "vpc_id" { value = aws_vpc.this.id }
output "security_group_id" { value = aws_security_group.msk.id }
output "nat_gateway_id" { value = aws_nat_gateway.this.id }
output "nat_gateway_public_ip" { value = aws_eip.nat.public_ip }
output "topic_names" { 
  value       = var.topics
  description = "List of configured topic names (topics will be auto-created by applications)"
}
