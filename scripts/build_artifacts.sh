#!/usr/bin/env bash
#=============================================================================
# Artifact Build Script
# Packages Lambda ZIP and Flink JAR for Terraform deployment
#=============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACTS_DIR="$PROJECT_ROOT/infra/artifacts"

#=============================================================================
# Helper Functions
#=============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

#=============================================================================
# Build Lambda ZIP
#=============================================================================

build_lambda() {
    log_info "Building Lambda artifact..."
    
    local LAMBDA_DIR="$ARTIFACTS_DIR/lambda/submission_pdf_extract"
    local BUILD_DIR="$LAMBDA_DIR/build"
    local ZIP_FILE="$ARTIFACTS_DIR/lambda/submission_pdf_extract.zip"
    
    if [ ! -d "$LAMBDA_DIR" ]; then
        log_error "Lambda directory not found: $LAMBDA_DIR"
        exit 1
    fi
    
    cd "$LAMBDA_DIR"
    
    # Create / reuse virtual environment (for dependency resolution only)
    if [ ! -f .venv/bin/activate ]; then
        log_info "Creating Python virtual environment..."
        rm -rf .venv  # Clean up incomplete venv if exists
        python3 -m venv .venv
    else
        log_info "Reusing existing virtual environment..."
    fi
    # shellcheck disable=SC1091
    source .venv/bin/activate

    log_info "Upgrading pip & installing build-time deps..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    
    # Clean and create build directory
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
    
    # Package dependencies directly into build directory (fresh, no cached bytecode)
    log_info "Vendoring dependencies into build directory..."
    pip install --quiet -r requirements.txt -t "$BUILD_DIR"
    
    # Copy handler
    cp handler.py "$BUILD_DIR/"
    
    # Create ZIP
    log_info "Creating ZIP archive..."
    cd "$BUILD_DIR"
    rm -f "$ZIP_FILE"
    zip -r -q "$ZIP_FILE" .
    
    # Cleanup
    deactivate
    
    local ZIP_SIZE
    if command -v stat >/dev/null 2>&1; then
        # Portable size retrieval
        ZIP_SIZE=$(stat -c%s "$ZIP_FILE" 2>/dev/null || stat -f%z "$ZIP_FILE")
        log_info "Lambda ZIP created: $ZIP_FILE (${ZIP_SIZE} bytes)"
    else
        ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
        log_info "Lambda ZIP created: $ZIP_FILE ($ZIP_SIZE)"
    fi
}

#=============================================================================
# Build Flink JAR
#=============================================================================

build_flink() {
    log_info "Building Flink JAR..."
    
    local FLINK_DIR="$ARTIFACTS_DIR/flink/java"
    
    if [ ! -d "$FLINK_DIR" ]; then
        log_error "Flink directory not found: $FLINK_DIR"
        exit 1
    fi
    
    if [ ! -f "$FLINK_DIR/pom.xml" ]; then
        log_error "pom.xml not found in $FLINK_DIR"
        exit 1
    fi
    
    cd "$FLINK_DIR"
    
    # Build with Maven
    log_info "Running Maven package (this may take a few minutes)..."
    mvn --batch-mode clean package -DskipTests -q
    
    local JAR_FILE
    JAR_FILE=$(find target -maxdepth 1 -type f -name "*shaded*.jar" ! -name "*-sources.jar" ! -name "*-javadoc.jar" | head -n 1)
    if [ -z "$JAR_FILE" ]; then
        # Fall back to any jar
        JAR_FILE=$(find target -maxdepth 1 -type f -name "*.jar" ! -name "*-sources.jar" ! -name "*-javadoc.jar" | head -n 1)
    fi
    
    if [ -z "$JAR_FILE" ]; then
        log_error "Failed to find built JAR file in target/"
        exit 1
    fi
    
    local JAR_SIZE
    if command -v stat >/dev/null 2>&1; then
        JAR_SIZE=$(stat -c%s "$JAR_FILE" 2>/dev/null || stat -f%z "$JAR_FILE")
        log_info "Flink JAR created: $JAR_FILE (${JAR_SIZE} bytes)"
    else
        JAR_SIZE=$(du -h "$JAR_FILE" | cut -f1)
        log_info "Flink JAR created: $JAR_FILE ($JAR_SIZE)"
    fi

    # Provide deterministic copy path for Terraform consumers (optional)
    local CANONICAL_JAR="$ARTIFACTS_DIR/flink/java/target/analytics-flink-job-latest.jar"
    cp "$JAR_FILE" "$CANONICAL_JAR"
    log_info "Copied canonical JAR to: $CANONICAL_JAR"
}

#=============================================================================
# Upload to S3
#=============================================================================

upload_lambda() {
    local BUCKET="${1:-}"
    local KEY="${2:-lambda/submission_pdf_extract.zip}"
    
    if [ -z "$BUCKET" ]; then
        log_error "S3 bucket not provided for Lambda upload"
        exit 1
    fi
    
    local ZIP_FILE="$ARTIFACTS_DIR/lambda/submission_pdf_extract.zip"
    
    if [ ! -f "$ZIP_FILE" ]; then
        log_error "Lambda ZIP not found. Run build first."
        exit 1
    fi
    
    log_info "Uploading Lambda ZIP to s3://$BUCKET/$KEY..."
    aws s3 cp "$ZIP_FILE" "s3://$BUCKET/$KEY"
    log_info "Lambda upload complete"
}

upload_flink() {
    local BUCKET="${1:-}"
    local KEY="${2:-flink/analytics-flink-job-1.0.0.jar}"
    
    if [ -z "$BUCKET" ]; then
        log_error "S3 bucket not provided for Flink upload"
        exit 1
    fi
    
    local FLINK_DIR="$ARTIFACTS_DIR/flink/java"
    local JAR_FILE
    JAR_FILE=$(find "$FLINK_DIR/target" -maxdepth 1 -type f -name "analytics-flink-job-latest.jar" 2>/dev/null)
    if [ -z "$JAR_FILE" ]; then
        JAR_FILE=$(find "$FLINK_DIR/target" -maxdepth 1 -type f -name "*.jar" ! -name "*-sources.jar" ! -name "*-javadoc.jar" 2>/dev/null | head -n 1)
    fi
    
    if [ -z "$JAR_FILE" ] || [ ! -f "$JAR_FILE" ]; then
        log_error "Flink JAR not found. Run build first."
        exit 1
    fi
    
    log_info "Uploading Flink JAR to s3://$BUCKET/$KEY..."
    aws s3 cp "$JAR_FILE" "s3://$BUCKET/$KEY"
    log_info "Flink upload complete"
}

#=============================================================================
# Main
#=============================================================================

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMMAND

Build and upload Lambda and Flink artifacts for Terraform deployment.

COMMANDS:
    lambda              Build Lambda ZIP only
    flink               Build Flink JAR only
    all                 Build both artifacts (default)
    upload-lambda       Upload Lambda ZIP to S3
    upload-flink        Upload Flink JAR to S3
    upload-all          Upload both artifacts to S3

OPTIONS:
    -h, --help          Show this help message
    --lambda-bucket     S3 bucket for Lambda artifacts
    --flink-bucket      S3 bucket for Flink artifacts
    --lambda-key        S3 key for Lambda ZIP (default: lambda/submission_pdf_extract.zip)
    --flink-key         S3 key for Flink JAR (default: flink/analytics-flink-job-1.0.0.jar)

EXAMPLES:
    # Build both artifacts
    $0 all

    # Build and upload Lambda
    $0 lambda
    $0 upload-lambda --lambda-bucket my-bucket

    # Build and upload Flink
    $0 flink
    $0 upload-flink --flink-bucket my-bucket

    # Build and upload everything
    $0 all
    $0 upload-all --lambda-bucket my-lambda-bucket --flink-bucket my-flink-bucket

PREREQUISITES:
    - Python 3.x with pip and venv
    - Maven (for Flink JAR)
    - AWS CLI (for S3 uploads)
EOF
}

main() {
    # Check prerequisites based on command
    case "${1:-all}" in
        lambda|all)
            check_command python3
            # check_command pip
            check_command zip
            ;;
        flink|all)
            check_command mvn
            ;;
        upload-*|all)
            check_command aws
            ;;
    esac
    
    # Parse arguments
    COMMAND="${1:-all}"
    shift || true
    
    LAMBDA_BUCKET=""
    FLINK_BUCKET=""
    LAMBDA_KEY="lambda/submission_pdf_extract.zip"
    FLINK_KEY="flink/analytics-flink-job-1.0.0.jar"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            --lambda-bucket)
                LAMBDA_BUCKET="$2"
                shift 2
                ;;
            --flink-bucket)
                FLINK_BUCKET="$2"
                shift 2
                ;;
            --lambda-key)
                LAMBDA_KEY="$2"
                shift 2
                ;;
            --flink-key)
                FLINK_KEY="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Execute command
    case "$COMMAND" in
        lambda)
            build_lambda
            ;;
        flink)
            build_flink
            ;;
        all)
            build_lambda
            build_flink
            ;;
        upload-lambda)
            upload_lambda "$LAMBDA_BUCKET" "$LAMBDA_KEY"
            ;;
        upload-flink)
            upload_flink "$FLINK_BUCKET" "$FLINK_KEY"
            ;;
        upload-all)
            upload_lambda "$LAMBDA_BUCKET" "$LAMBDA_KEY"
            upload_flink "$FLINK_BUCKET" "$FLINK_KEY"
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
    
    log_info "Done!"
}

main "$@"
