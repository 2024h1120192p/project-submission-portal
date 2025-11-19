#!/bin/bash
# Kafka Testing Script
# Tests the Kafka implementation with sample workflows

set -e

echo "=== Kafka Implementation Testing Guide ==="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. START KAFKA SERVICES${NC}"
echo "Run: docker-compose up -d"
echo ""

echo -e "${BLUE}2. VERIFY SERVICES ARE HEALTHY${NC}"
echo "Check Zookeeper:"
echo "  docker-compose ps | grep zookeeper"
echo ""
echo "Check Kafka:"
echo "  docker-compose ps | grep kafka"
echo ""
echo "Wait for both to show 'Up' status"
echo ""

echo -e "${BLUE}3. VERIFY KAFKA TOPICS ARE CREATED${NC}"
echo "Command:"
echo "  docker exec paper-submission-kafka kafka-topics --list --bootstrap-server kafka:29092"
echo ""
echo "Expected output:"
echo "  paper_uploaded"
echo "  plagiarism_checked"
echo "  __consumer_offsets"
echo ""

echo -e "${BLUE}4. TEST EVENT EMISSION (Submit a Paper)${NC}"
echo "Use this curl command to submit a paper:"
echo ""
cat <<'CURL'
curl -X POST http://localhost:8001/submissions/upload \
  -F "user_id=test-user-123" \
  -F "assignment_id=assignment-001" \
  -F "file=@sample.txt"
CURL
echo ""
echo "Replace sample.txt with an actual file"
echo ""

echo -e "${BLUE}5. MONITOR EVENTS IN REAL-TIME${NC}"
echo "Terminal 1 - Watch paper_uploaded events:"
echo "  docker exec -it paper-submission-kafka kafka-console-consumer \\"
echo "    --bootstrap-server kafka:29092 \\"
echo "    --topic paper_uploaded \\"
echo "    --from-beginning"
echo ""
echo "Terminal 2 - Watch plagiarism_checked events:"
echo "  docker exec -it paper-submission-kafka kafka-console-consumer \\"
echo "    --bootstrap-server kafka:29092 \\"
echo "    --topic plagiarism_checked \\"
echo "    --from-beginning"
echo ""

echo -e "${BLUE}6. CHECK SERVICE LOGS${NC}"
echo "Submission Service:"
echo "  docker-compose logs -f submission_service"
echo ""
echo "Analytics Service:"
echo "  docker-compose logs -f analytics_service"
echo ""
echo "Notification Service:"
echo "  docker-compose logs -f notification_service"
echo ""

echo -e "${BLUE}7. VERIFY EVENT FLOW${NC}"
echo "Expected flow:"
echo ""
echo "  User uploads paper"
echo "    ↓"
echo "  POST /submissions/upload"
echo "    ↓"
echo "  Submission Service emits 'paper_uploaded' event"
echo "    ↓"
echo "  ├─→ Analytics Service (increments counter)"
echo "  ├─→ Notification Service (creates notification)"
echo "    ↓"
echo "  Check notifications: GET /notifications/{user_id}"
echo ""

echo -e "${BLUE}8. TEST PLAGIARISM FLOW${NC}"
echo "Trigger plagiarism check:"
echo ""
cat <<'CURL'
curl -X POST http://localhost:8003/check \
  -H "Content-Type: application/json" \
  -d '{
    "id": "submission-id-from-step-4",
    "user_id": "test-user-123",
    "assignment_id": "assignment-001",
    "uploaded_at": "2024-11-19T10:30:00Z",
    "file_url": "/uploads/file.txt",
    "text": "Sample paper content"
  }'
CURL
echo ""
echo "This will emit 'plagiarism_checked' event"
echo ""

echo -e "${BLUE}9. VALIDATE EVENT DELIVERY${NC}"
echo "Check if events were received:"
echo ""
echo "Analytics Service:"
echo "  docker-compose logs analytics_service | grep 'Received event'"
echo ""
echo "Notification Service:"
echo "  docker-compose logs notification_service | grep 'Created notification'"
echo ""

echo -e "${BLUE}10. CONSUMER GROUP STATUS${NC}"
echo "View consumer groups:"
echo "  docker exec paper-submission-kafka kafka-consumer-groups \\"
echo "    --list --bootstrap-server kafka:29092"
echo ""
echo "Describe a consumer group:"
echo "  docker exec paper-submission-kafka kafka-consumer-groups \\"
echo "    --describe --group analytics-service \\"
echo "    --bootstrap-server kafka:29092"
echo ""

echo -e "${GREEN}✓ Testing Guide Complete${NC}"
echo ""
echo "For more details, see KAFKA_SETUP.md and KAFKA_QUICK_REFERENCE.md"
