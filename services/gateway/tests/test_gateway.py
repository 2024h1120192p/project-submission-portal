from fastapi.testclient import TestClient
from services.gateway.app.main import app

client = TestClient(app)

def test_home():
    r = client.get("/")
    assert r.status_code == 200

def test_login_post():
    r = client.post("/login", data={"email": "a@b.com", "password": "x"})
    assert r.status_code == 200

def test_dashboards():
    assert client.get("/dashboard/student").status_code == 200
    assert client.get("/dashboard/faculty").status_code == 200
