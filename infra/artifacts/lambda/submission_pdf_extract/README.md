# Lambda: PDF Extraction

Extracts lightweight metadata from uploaded PDF submissions in S3.

## Expected Event (S3 Put Notification Simplified)
```json
{
  "Records": [
    {"s3": {"bucket": {"name": "submission-bucket"}, "object": {"key": "papers/1234.pdf"}}}
  ]
}
```

## Output Body
```json
{
  "bucket": "submission-bucket",
  "key": "papers/1234.pdf",
  "page_count": 12,
  "sample_text_length": 1530
}
```

## Build & Package
```bash
cd infra/artifacts/lambda/submission_pdf_extract
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir build
pip install -r requirements.txt -t build
cp handler.py build/
cd build
zip -r ../submission_pdf_extract.zip .
aws s3 cp ../submission_pdf_extract.zip s3://$LAMBDA_DEPLOY_BUCKET/lambda/submission_pdf_extract.zip
```

Set Terraform variables:
```hcl
lambda_deployment_bucket = "your-bucket"
lambda_deployment_key    = "lambda/submission_pdf_extract.zip"
```
