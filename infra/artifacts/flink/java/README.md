# Flink Analytics Job (Java)

Simplified window aggregation job for submission/plagiarism processed events.

## Build
```bash
cd infra/artifacts/flink/java
mvn -q package
# Result: target/analytics-flink-job-1.0.0-shaded.jar
```

## Local Run (Kafka on localhost)
```bash
java -jar target/analytics-flink-job-1.0.0-shaded.jar \
  localhost:9092 \
  paper_uploaded_processed \
  plagiarism_checked_processed \
  analytics_window
```

Or use env vars:
```bash
export KAFKA_BOOTSTRAP=localhost:9092
export SUBMISSION_TOPIC=paper_uploaded_processed
export PLAGIARISM_TOPIC=plagiarism_checked_processed
export OUTPUT_TOPIC=analytics_window
java -jar target/analytics-flink-job-1.0.0-shaded.jar
```

## Deploy Artifact
```bash
aws s3 cp target/analytics-flink-job-1.0.0-shaded.jar s3://$FLINK_ARTIFACT_BUCKET/flink/analytics-flink-job-1.0.0.jar
```

Set Terraform variable:
```hcl
flink_job_jar = "s3://your-bucket/flink/analytics-flink-job-1.0.0.jar"
```
