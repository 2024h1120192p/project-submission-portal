#!/bin/bash

# Build script for all Docker images
# This script builds all service images from the project root

set -e

# Configuration
PROJECT_ID="paper-submission-portal"
REGION="us-central1"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/paper-submission-portal"
TAG="${TAG:-latest}"

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Docker images from: $PROJECT_ROOT"

# Array of services
SERVICES=(
    "users_service"
    "gateway"
    "analytics_service"
    "notification_service"
    "plagiarism_service"
    "submission_service"
)

# Build each service
for service in "${SERVICES[@]}"; do
    echo "========================================="
    echo "Building $service..."
    echo "========================================="
    
    # Build from project root with context of entire repo
    docker build \
        -f "./services/$service/Dockerfile" \
        -t "$REGISTRY/$service:$TAG" \
        .
    
    echo "✓ Built $REGISTRY/$service:$TAG"
    echo ""
done

echo "========================================="
echo "Pushing images to Artifact Registry..."
echo "========================================="

# Push each service
for service in "${SERVICES[@]}"; do
    echo "Pushing $service..."
    docker push "$REGISTRY/$service:$TAG"
    echo "✓ Pushed $REGISTRY/$service:$TAG"
done

echo "========================================="
echo "All images built and pushed successfully!"
echo "========================================="
