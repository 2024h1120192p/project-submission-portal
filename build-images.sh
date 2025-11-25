#!/bin/bash

# Build script for all Docker images
# This script builds all service images from the project root

set -e

# Configuration
DOCKER_REGISTRY="h20240192/ss_g527.paper-submission-portal"
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
        -t "$DOCKER_REGISTRY:${service}-$TAG" \
        .
    
    echo "✓ Built $DOCKER_REGISTRY:${service}-$TAG"
    echo ""
done

echo "========================================="
echo "Pushing images to Docker Hub..."
echo "========================================="

# Push each service
for service in "${SERVICES[@]}"; do
    echo "Pushing $service..."
    docker push "$DOCKER_REGISTRY:${service}-$TAG"
    echo "✓ Pushed $DOCKER_REGISTRY:${service}-$TAG"
done

echo "========================================="
echo "All images built and pushed successfully!"
echo "========================================="
