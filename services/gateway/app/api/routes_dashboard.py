"""Dashboard routes for the gateway service.

Provides student and faculty dashboards with real microservice integration.
"""
from fastapi import APIRouter, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
import jwt
from libs.events.schemas import User


router = APIRouter(prefix="/dashboard")


# Mock JWT configuration (same as routes_public)
SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"


def decode_token(token: str) -> dict:
    """Decode JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        return None


@router.get("/student", response_class=HTMLResponse)
async def dashboard_student(request: Request, access_token: Optional[str] = Cookie(None)):
    """Student dashboard with real data from microservices."""
    templates = request.state.templates
    clients = request.state.clients
    
    # Mock authentication - decode token
    user_id = "student_001"  # Default
    role = "student"
    if access_token:
        payload = decode_token(access_token)
        if payload:
            user_id = payload.get("sub", user_id)
            role = payload.get("role", role)
    
    # Fetch user data
    user = await clients.user.get_user(user_id)
    if not user:
        # Fallback to mock user so dev flow works without Users service data
        user = User(
            id=user_id,
            name="Demo Student",
            email=f"{user_id}@example.com",
            role=role,
        )
    
    # Fetch student's submissions
    submissions = await clients.submission.list_by_user(user_id)
    
    # Fetch plagiarism results for each submission (limited to recent ones)
    plagiarism_results = []
    for submission in submissions[:5]:  # Limit to 5 most recent
        # Note: PlagiarismServiceClient doesn't have a get_by_submission method
        # In a real app, we'd need to add that or store results differently
        # For now, we'll just show submission info
        pass
    
    # Fetch latest analytics
    analytics = await clients.analytics.get_latest()
    
    # Fetch user notifications
    notifications = await clients.notification.get_user_notifications(user_id)
    
    # Prepare context
    context = {
        "request": request,
        "user": user,
        "submissions": submissions,
        "submissions_count": len(submissions),
        "analytics": analytics,
        "notifications": notifications[:5],  # Show 5 most recent
        "has_notifications": len(notifications) > 0
    }
    
    return templates.TemplateResponse(
        name="dashboard_student.html",
        context=context
    )


@router.get("/faculty", response_class=HTMLResponse)
async def dashboard_faculty(request: Request, access_token: Optional[str] = Cookie(None)):
    """Faculty dashboard with real data from microservices."""
    templates = request.state.templates
    clients = request.state.clients
    
    # Mock authentication - decode token
    user_id = "faculty_001"  # Default
    role = "faculty"
    if access_token:
        payload = decode_token(access_token)
        if payload:
            user_id = payload.get("sub", user_id)
            role = payload.get("role", role)
    
    # Fetch user data
    user = await clients.user.get_user(user_id)
    if not user:
        # Fallback to mock user so dev flow works without Users service data
        user = User(
            id=user_id,
            name="Demo Faculty",
            email=f"{user_id}@example.com",
            role=role,
        )
    
    # Fetch analytics history
    analytics_history = await clients.analytics.get_history()
    
    # Get latest analytics
    latest_analytics = analytics_history[0] if analytics_history else None
    
    # Fetch all users to get recent submissions (faculty sees all)
    all_users = await clients.user.get_all()
    
    # Fetch recent submissions from all students
    recent_submissions = []
    for u in all_users[:10]:  # Limit to prevent too many API calls
        if u.role == "student":
            user_submissions = await clients.submission.list_by_user(u.id)
            recent_submissions.extend(user_submissions)
    
    # Sort by upload time and limit
    recent_submissions.sort(key=lambda s: s.uploaded_at, reverse=True)
    recent_submissions = recent_submissions[:10]
    
    # Calculate statistics
    total_submissions = len(recent_submissions)
    flagged_count = 0
    if latest_analytics and latest_analytics.avg_plagiarism > 0.5:
        # Mock: estimate flagged based on analytics
        flagged_count = int(total_submissions * latest_analytics.avg_plagiarism)
    
    # Prepare context
    context = {
        "request": request,
        "user": user,
        "analytics_history": analytics_history[:10],  # Last 10 windows
        "latest_analytics": latest_analytics,
        "recent_submissions": recent_submissions,
        "total_submissions": total_submissions,
        "flagged_count": flagged_count,
        "spike_detected": latest_analytics.spike_detected if latest_analytics else False
    }
    
    return templates.TemplateResponse(
        name="dashboard_faculty.html",
        context=context
    )