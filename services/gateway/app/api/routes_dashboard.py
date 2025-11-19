"""Dashboard routes for the gateway service.

Provides student and faculty dashboards with real microservice integration.
Gateway only orchestrates - business logic is delegated to client.py.
"""
from fastapi import APIRouter, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

from ..core.auth import get_user_from_token


router = APIRouter(prefix="/dashboard")


@router.get("/researcher", response_class=HTMLResponse)
async def dashboard_student(request: Request, access_token: Optional[str] = Cookie(None)):
    """Researcher dashboard - orchestrate data fetching through client."""
    templates = request.state.templates
    clients = request.state.clients
    
    # Extract user info from token
    user_id, role = get_user_from_token(access_token, "student_001", "student")
    
    # Orchestrate data fetching through client
    context = await clients.get_student_dashboard_data(user_id)
    context["request"] = request
    
    return templates.TemplateResponse(
        name="dashboard_student.html",
        context=context
    )


@router.get("/reviewer", response_class=HTMLResponse)
async def dashboard_faculty(request: Request, access_token: Optional[str] = Cookie(None)):
    """Reviewer dashboard - orchestrate data fetching through client."""
    templates = request.state.templates
    clients = request.state.clients
    
    # Extract user info from token
    user_id, role = get_user_from_token(access_token, "faculty_001", "faculty")
    
    # Orchestrate data fetching through client
    context = await clients.get_faculty_dashboard_data(user_id)
    context["request"] = request
    
    return templates.TemplateResponse(
        name="dashboard_faculty.html",
        context=context
    )