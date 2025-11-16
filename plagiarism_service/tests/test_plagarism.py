from fastapi.testclient import TestClient
from plagiarism_service.app.main import app
from datetime import datetime, timezone

client = TestClient(app)

def test_check():
    payload = {
        "id": "s1",
        "user_id": "u1",
        "assignment_id": "a1",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "file_url": "gs://x/y.pdf",
        "text": "hello world"
    }

    res = client.post("/check", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["submission_id"] == "s1"
    assert "internal_score" in data
    assert "external_score" in data
    assert "ai_generated_probability" in data
    assert isinstance(data["flagged_sections"], list)
