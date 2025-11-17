from fastapi.testclient import TestClient
from services.user_service.app.main import app

client = TestClient(app)

def test_create_get_user():
    payload = {"id": "1", "name": "A", "email": "a@test.com", "role": "student"}
    client.post("/users", json=payload)
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.json()["name"] == "A"
