variable "region" {}
variable "cluster_name" {}
variable "log_uri" {}
variable "subnet_ids" { type = list(string) }
variable "flink_job_jar" {
  description = "S3 path to Flink job JAR (e.g., s3://bucket/flink-job.jar)"
  type        = string
  default     = ""
}
variable "flink_job_class" {
  description = "Main class for Flink job"
  type        = string
  default     = "com.example.StreamProcessor"
}
variable "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers for Flink job"
  type        = string
  default     = ""
}

# Simplified EMR cluster with Flink application capability.
resource "aws_emr_cluster" "flink" {
  name          = var.cluster_name
  release_label = "emr-7.0.0" # Ensure Flink supported
  applications  = ["Hadoop", "Flink"]
  log_uri       = var.log_uri

  ec2_attributes {
    subnet_id        = element(var.subnet_ids, 0)
    instance_profile = "EMR_EC2_DefaultRole"
  }

  master_instance_group {
    instance_type = "m5.xlarge"
  }

  core_instance_group {
    instance_type  = "m5.xlarge"
    instance_count = 2
  }

  keep_job_flow_alive_when_no_steps = true

  configurations_json = <<EOF
[
  {
    "Classification": "flink-conf",
    "Properties": {
      "state.checkpoints.dir": "s3://${replace(var.log_uri, "arn:aws:s3:::", "")}/checkpoints",
      "execution.checkpointing.interval": "60000"
    }
  }
]
EOF

  bootstrap_action {
    path = "s3://elasticmapreduce/bootstrap-actions/run-if"
    name = "PlaceholderBootstrap"
    args = ["instance.isMaster=true", "echo bootstrap"]
  }

  service_role     = "EMR_DefaultRole"
  autoscaling_role = "EMR_AutoScaling_DefaultRole"

  termination_protection = false

  # Optional: Deploy Flink job as cluster step (only if JAR provided)
  dynamic "step" {
    for_each = var.flink_job_jar != "" ? [1] : []
    content {
      name              = "Flink Stream Processing Job"
      action_on_failure = "CONTINUE"

      hadoop_jar_step {
        jar = "command-runner.jar"
        args = [
          "flink",
          "run",
          "-m",
          "yarn-cluster",
          "-c",
          var.flink_job_class,
          var.flink_job_jar,
          "--kafka.bootstrap.servers",
          var.kafka_bootstrap_servers
        ]
      }
    }
  }
}

output "emr_cluster_id" { value = aws_emr_cluster.flink.id }
output "emr_master_dns" { value = aws_emr_cluster.flink.master_public_dns }
