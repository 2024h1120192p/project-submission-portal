variable "region" {}
variable "function_name" {}
variable "s3_bucket" {
  description = "S3 bucket containing Lambda deployment package"
  type        = string
}
variable "s3_key" {
  description = "S3 key for Lambda deployment package (e.g., lambda/pdf-extract.zip)"
  type        = string
  default     = "lambda/pdf-extract.zip"
}
variable "runtime" {
  type    = string
  default = "python3.11"
}
variable "handler" {
  type    = string
  default = "handler.lambda_handler"
}
variable "timeout" {
  type    = number
  default = 60
}
variable "memory_size" {
  type    = number
  default = 512
}
variable "source_bucket_arn" {
  description = "ARN of S3 bucket that triggers this Lambda"
  type        = string
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for S3 access
resource "aws_iam_role_policy" "lambda_s3" {
  name = "${var.function_name}-s3-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::*/*"
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "pdf_extract" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_role.arn
  runtime       = var.runtime
  handler       = var.handler
  timeout       = var.timeout
  memory_size   = var.memory_size

  s3_bucket = var.s3_bucket
  s3_key    = var.s3_key

  environment {
    variables = {
      ENVIRONMENT = "production"
    }
  }
}

# Lambda permission for S3 to invoke
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pdf_extract.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.source_bucket_arn
}

output "function_arn" { value = aws_lambda_function.pdf_extract.arn }
output "function_name" { value = aws_lambda_function.pdf_extract.function_name }
output "role_arn" { value = aws_iam_role.lambda_role.arn }
