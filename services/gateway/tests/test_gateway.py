"""Tests for the gateway service."""
import pytest
from fastapi.testclient import TestClient
from services.gateway.app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


def test_home(client):
    """Test home page renders."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Project Submission Portal" in response.content


def test_login_page(client):
    """Test login page renders."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.content


def test_login_post_student(client):
    """Test login with student email redirects correctly."""
    response = client.post(
        "/login", 
        data={"email": "student@university.edu", "password": "test123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "/dashboard/student" in response.headers.get("location", "")


def test_login_post_faculty(client):
    """Test login with faculty email redirects correctly."""
    response = client.post(
        "/login", 
        data={"email": "faculty@university.edu", "password": "test123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "/dashboard/faculty" in response.headers.get("location", "")


def test_dashboard_student_renders(client):
    """Test student dashboard renders (may redirect if no auth)."""
    response = client.get("/dashboard/student")
    # Either renders (200) or redirects to login (303/307)
    assert response.status_code in (200, 303, 307)


def test_dashboard_faculty_renders(client):
    """Test faculty dashboard renders (may redirect if no auth)."""
    response = client.get("/dashboard/faculty")
    # Either renders (200) or redirects to login (303/307)
    assert response.status_code in (200, 303, 307)
