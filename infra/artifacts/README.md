# Artifact Build Automation

Automated build script for packaging Lambda and Flink deployment artifacts.

## Quick Start

```bash
# Build both artifacts
./scripts/build_artifacts.sh all

# Build Lambda only
./scripts/build_artifacts.sh lambda

# Build Flink only
./scripts/build_artifacts.sh flink

# Upload to S3 after building
./scripts/build_artifacts.sh upload-all \
  --lambda-bucket paper-portal-lambda-artifacts \
  --flink-bucket paper-portal-flink-artifacts
```

## Prerequisites

- **Python 3.x** with `pip` and `venv` (for Lambda)
- **Maven** (for Flink JAR)
- **AWS CLI** configured (for S3 uploads)

## Commands

| Command | Description |
|---------|-------------|
| `lambda` | Build Lambda ZIP only |
| `flink` | Build Flink JAR only |
| `all` | Build both artifacts (default) |
| `upload-lambda` | Upload Lambda ZIP to S3 |
| `upload-flink` | Upload Flink JAR to S3 |
| `upload-all` | Upload both to S3 |

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--lambda-bucket` | S3 bucket for Lambda | Required for upload |
| `--flink-bucket` | S3 bucket for Flink | Required for upload |
| `--lambda-key` | S3 key for Lambda ZIP | `lambda/submission_pdf_extract.zip` |
| `--flink-key` | S3 key for Flink JAR | `flink/analytics-flink-job-1.0.0.jar` |

## Output Artifacts

- **Lambda**: `infra/artifacts/lambda/submission_pdf_extract.zip`
- **Flink**: `infra/artifacts/flink/java/target/analytics-flink-job-1.0.0.jar`

## Typical Workflow

```bash
# 1. Build artifacts
./scripts/build_artifacts.sh all

# 2. Upload to S3
./scripts/build_artifacts.sh upload-all \
  --lambda-bucket my-lambda-bucket \
  --flink-bucket my-flink-bucket

# 3. Update terraform.tfvars with S3 paths
# 4. Run terraform apply
cd infra/terraform
terraform apply
```

## CI/CD Integration

```yaml
# Example GitHub Actions step
- name: Build and Upload Artifacts
  run: |
    ./scripts/build_artifacts.sh all
    ./scripts/build_artifacts.sh upload-all \
      --lambda-bucket ${{ secrets.LAMBDA_BUCKET }} \
      --flink-bucket ${{ secrets.FLINK_BUCKET }}
```

## Troubleshooting

**Maven not found:**
```bash
# Ubuntu/Debian
sudo apt-get install maven

# macOS
brew install maven
```

**Python venv issues:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# Verify Python
python3 --version
```

**AWS CLI not configured:**
```bash
aws configure
# Enter your credentials and default region
```
