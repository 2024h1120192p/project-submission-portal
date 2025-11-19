"""Public routes for the gateway service.

Handles authentication and public pages.
Gateway only orchestrates - business logic is in client.py and core modules.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from ..core.auth import create_access_token


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    templates = request.state.templates
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request, "message": "Welcome to Project Submission Portal"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render the login page."""
    templates = request.state.templates
    return templates.TemplateResponse(
        name="login.html",
        context={"request": request}
    )


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handle login - orchestrate authentication through client."""
    clients = request.state.clients
    
    # Orchestrate authentication through client
    user = await clients.authenticate_user(email, password)
    
    # Determine user details for token
    if user:
        user_id = user.id
        role = user.role
    else:
        # Fallback for demo: derive from email pattern
        if "student" in email.lower():
            user_id = "student_001"
            role = "student"
        elif "faculty" in email.lower():
            user_id = "faculty_001"
            role = "faculty"
        else:
            user_id = "user_001"
            role = "student"
    
    # Create JWT token using auth utility
    token = create_access_token(user_id, role)
    
    # Redirect to appropriate dashboard based on role
    if role == "faculty":
        response = RedirectResponse(url="/dashboard/faculty", status_code=303)
    else:
        response = RedirectResponse(url="/dashboard/student", status_code=303)
    
    # Set JWT cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax"
    )
    
    return response