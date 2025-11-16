from fastapi.testclient import TestClient
from submission_service.app.main import app
from datetime import datetime, timezone

client = TestClient(app)

def test_create_and_get():
    payload = {
        "id": "1",
        "user_id": "u1",
        "assignment_id": "a1",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "file_url": "gs://file.pdf",
        "text": "hello"
    }

    r = client.post("/submissions", json=payload)
    assert r.status_code == 200

    r = client.get("/submissions/1")
    assert r.status_code == 200
    assert r.json()["id"] == "1"
