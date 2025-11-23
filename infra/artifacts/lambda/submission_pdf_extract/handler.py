import json
import os
from typing import Any, Dict

try:
    from pypdf import PdfReader  # Lightweight PDF text extraction
except ImportError:
    PdfReader = None

import boto3

s3 = boto3.client("s3")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Extract text metadata from a newly uploaded PDF in the submissions bucket.

    Expected event shape (simplified S3 Put notification):
    {
        "Records": [
            {
                "s3": {"bucket": {"name": "bucket"}, "object": {"key": "path/file.pdf"}}
            }
        ]
    }

    Returns basic metadata JSON that downstream Kafka producers can enrich.
    """
    records = event.get("Records", [])
    if not records:
        return _response(400, {"error": "No Records in event"})

    record = records[0]
    bucket = record.get("s3", {}).get("bucket", {}).get("name")
    key = record.get("s3", {}).get("object", {}).get("key")
    if not bucket or not key:
        return _response(400, {"error": "Missing bucket/key"})

    # Download PDF to /tmp (Lambda ephemeral storage)
    local_path = f"/tmp/{os.path.basename(key)}"
    s3.download_file(bucket, key, local_path)

    text_length = None
    page_count = None
    if PdfReader is not None and local_path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(local_path)
            page_count = len(reader.pages)
            # Basic length metric (not full text to avoid large payloads)
            text_acc = []
            for page in reader.pages[: min(3, page_count)]:  # sample first 3 pages for speed
                try:
                    text_acc.append(page.extract_text() or "")
                except Exception:
                    pass
            text_length = sum(len(t) for t in text_acc)
        except Exception:
            pass

    metadata = {
        "bucket": bucket,
        "key": key,
        "page_count": page_count,
        "sample_text_length": text_length,
    }

    return _response(200, metadata)


def _response(status: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"},
    }
