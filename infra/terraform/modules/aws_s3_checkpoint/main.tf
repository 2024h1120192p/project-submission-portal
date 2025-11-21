variable "region" {}
variable "name" {}

resource "aws_s3_bucket" "checkpoint" {
  bucket        = var.name
  force_destroy = true
}

output "bucket_name" { value = aws_s3_bucket.checkpoint.bucket }
output "bucket_arn" { value = aws_s3_bucket.checkpoint.arn }
