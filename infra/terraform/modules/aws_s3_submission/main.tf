variable "region" {}
variable "name" {}
variable "lambda_function_arn" {
  description = "ARN of Lambda function to trigger on PDF upload"
  type        = string
}

resource "aws_s3_bucket" "submissions" {
  bucket        = var.name
  force_destroy = true
}

resource "aws_s3_bucket_notification" "lambda_trigger" {
  bucket = aws_s3_bucket.submissions.id

  lambda_function {
    lambda_function_arn = var.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".pdf"
  }
}

output "bucket_name" { value = aws_s3_bucket.submissions.bucket }
output "bucket_arn" { value = aws_s3_bucket.submissions.arn }
