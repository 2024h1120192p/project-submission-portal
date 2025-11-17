"""Public routes for the gateway service.

Handles authentication and public pages.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import jwt
from datetime import datetime, timedelta


router = APIRouter()


# Mock JWT configuration
SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"


def create_access_token(user_id: str, role: str) -> str:
    """Create a mock JWT token for development."""
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


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
    """Handle login - mock authentication with real user service call."""
    clients = request.state.clients
    templates = request.state.templates
    
    # Mock user lookup - in real app would validate password
    # For demo: student emails contain "student", faculty contain "faculty"
    if "student" in email.lower():
        user_id = "student_001"
        role = "student"
    elif "faculty" in email.lower():
        user_id = "faculty_001"
        role = "faculty"
    else:
        # Default to student
        user_id = "user_001"
        role = "student"
    
    # Attempt to fetch user from user service
    user = await clients.user.get_user(user_id)
    
    if user:
        # User exists - use real data
        role = user.role
        user_id = user.id
    
    # Create JWT token
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