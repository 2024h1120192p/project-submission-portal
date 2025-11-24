#!/bin/bash

# Script to clean up stuck Kafka topic resources from Terraform state
# Run this from the infra/terraform directory

set -e

echo "=========================================="
echo "Terraform State Cleanup for Kafka Topics"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo "Error: main.tf not found. Please run this script from infra/terraform/"
    exit 1
fi

# List of topics to remove
topics=(
    "paper_uploaded"
    "paper_uploaded_processed"
    "plagiarism_checked"
    "plagiarism_checked_processed"
    "analytics_window"
)

echo "This will remove the following Kafka topic resources from Terraform state:"
for topic in "${topics[@]}"; do
    echo "  - module.aws_msk.kafka_topic.topics[\"$topic\"]"
done
echo ""
echo "Note: This does NOT delete the actual topics if they were created."
echo "It only removes them from Terraform's state tracking."
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Removing resources from state..."
echo ""

for topic in "${topics[@]}"; do
    resource="module.aws_msk.kafka_topic.topics[\"$topic\"]"
    echo "Removing: $resource"
    
    # Check if resource exists in state first
    if terraform state list | grep -q "$resource"; then
        terraform state rm "$resource" || true
        echo "  ✓ Removed"
    else
        echo "  ⊘ Not found in state (already removed or never created)"
    fi
done

echo ""
echo "=========================================="
echo "Cleanup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run: terraform refresh"
echo "2. Run: terraform plan (to verify changes)"
echo "3. Run: terraform apply"
echo ""
echo "After successful apply, create Kafka topics manually or via application."
echo "See FIX_INSTRUCTIONS.md for details."
