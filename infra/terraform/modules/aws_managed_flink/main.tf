variable "region" {}
variable "application_name" {}
variable "flink_job_jar" { # S3 path like s3://bucket/path/job.jar
  type        = string
  default     = ""
  description = "S3 URI to Flink job Uber/Fat JAR for Kinesis Data Analytics (empty to create app without code attachment)."
}
variable "kafka_bootstrap_servers" {
  type        = string
  default     = ""
  description = "Comma-separated MSK bootstrap servers for runtime properties."
}
variable "parallelism" {
  type        = number
  default     = 1
  description = "Initial Flink parallelism."
}
variable "checkpointing_enabled" {
  type        = bool
  default     = true
  description = "Enable application checkpointing & snapshots."
}

# Derive bucket/key from flink_job_jar if provided
locals {
  jar_parts  = var.flink_job_jar != "" ? split("/", replace(var.flink_job_jar, "s3://", "")) : []
  jar_bucket = length(local.jar_parts) > 0 ? local.jar_parts[0] : null
  jar_key    = length(local.jar_parts) > 1 ? join("/", slice(local.jar_parts, 1, length(local.jar_parts))) : null
}

resource "aws_iam_role" "kda_role" {
  name = "${var.application_name}-kda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "kinesisanalytics.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# Basic inline policy granting access to S3 (code + checkpoints), CloudWatch Logs, and MSK connectivity.
resource "aws_iam_role_policy" "kda_inline" {
  name = "${var.application_name}-kda-inline"
  role = aws_iam_role.kda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:ListBucket"]
        Resource = [
          local.jar_bucket != null ? "arn:aws:s3:::${local.jar_bucket}" : "*",
          local.jar_bucket != null ? "arn:aws:s3:::${local.jar_bucket}/${local.jar_key}" : "*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogGroups", "logs:DescribeLogStreams"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["kafka:DescribeCluster", "kafka:GetBootstrapBrokers", "kafka:ListClusters", "kafka:DescribeClusterV2"]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group (optional; created if not existing)
resource "aws_cloudwatch_log_group" "kda" {
  name              = "/aws/kinesis-analytics/${var.application_name}"
  retention_in_days = 14
}

resource "aws_kinesisanalyticsv2_application" "flink_app" {
  name                   = var.application_name
  runtime_environment    = "FLINK-1_18"
  service_execution_role = aws_iam_role.kda_role.arn

  application_configuration {
    environment_properties {
      property_group {
        property_group_id = "FlinkProperties"
        property_map = {
          "kafka.bootstrap.servers" = var.kafka_bootstrap_servers
        }
      }
    }

    flink_application_configuration {
      parallelism_configuration {
        configuration_type   = "CUSTOM"
        parallelism          = var.parallelism
        auto_scaling_enabled = true
      }
      checkpoint_configuration {
        configuration_type            = "CUSTOM"
        checkpointing_enabled         = var.checkpointing_enabled
        checkpoint_interval           = 60000
        min_pause_between_checkpoints = 5000
      }
      monitoring_configuration {
        configuration_type = "DEFAULT"
      }
    }

    dynamic "application_code_configuration" {
      for_each = var.flink_job_jar != "" ? [1] : []
      content {
        code_content_type = "ZIPFILE" # Fat JAR treated as binary; can also use PLAINTEXT for SQL
        code_content {
          s3_content_location {
            bucket_arn = local.jar_bucket != null ? "arn:aws:s3:::${local.jar_bucket}" : null
            file_key   = local.jar_key
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [application_configuration[0].flink_application_configuration[0].parallelism_configuration[0].parallelism]
  }

  depends_on = [aws_iam_role_policy.kda_inline, aws_cloudwatch_log_group.kda]
}

output "managed_flink_application_name" { value = aws_kinesisanalyticsv2_application.flink_app.name }
output "managed_flink_application_arn" { value = aws_kinesisanalyticsv2_application.flink_app.arn }
output "managed_flink_application_version" { value = aws_kinesisanalyticsv2_application.flink_app.version_id }
