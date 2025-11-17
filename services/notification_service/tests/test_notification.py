from fastapi.testclient import TestClient
from services.notification_service.app.main import app

client = TestClient(app)

def test_notify():
    payload = {"user_id": "u1", "message": "hello"}
    res = client.post("/notify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "u1"
    assert data["message"] == "hello"
    assert "id" in data
