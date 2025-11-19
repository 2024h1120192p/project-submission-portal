"""Gateway Service - Main FastAPI Application.

Serves as the API gateway for the project submission portal.
Integrates all microservices and provides UI endpoints.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from services.users_service.app.client import UserServiceClient
from services.submission_service.app.client import SubmissionServiceClient
from services.plagiarism_service.app.client import PlagiarismServiceClient
from services.analytics_service.app.client import AnalyticsServiceClient
from services.notification_service.app.client import NotificationServiceClient

from .api.routes_public import router as public_router
from .api.routes_dashboard import router as dashboard_router


# Microservice URLs
USER_URL = "http://localhost:8001"
SUB_URL = "http://localhost:8002"
PLAG_URL = "http://localhost:8003"
ANALYTICS_URL = "http://localhost:8004"
NOTIFY_URL = "http://localhost:8005"


class ServiceClients:
    """Container for all microservice clients."""
    
    def __init__(self):
        self.user = UserServiceClient(USER_URL)
        self.submission = SubmissionServiceClient(SUB_URL)
        self.plagiarism = PlagiarismServiceClient(PLAG_URL)
        self.analytics = AnalyticsServiceClient(ANALYTICS_URL)
        self.notification = NotificationServiceClient(NOTIFY_URL)
    
    async def close_all(self):
        """Close all client connections."""
        await self.user.client.close()
        await self.submission.close()
        await self.plagiarism.close()
        await self.analytics.close()
        await self.notification.close()


# Global clients instance
clients: ServiceClients = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global clients
    
    # Startup: Initialize all service clients
    clients = ServiceClients()
    print("✓ Gateway service started - all clients initialized")
    
    yield
    
    # Shutdown: Close all client connections
    await clients.close_all()
    print("✓ Gateway service shutdown - all clients closed")


# Create FastAPI application
app = FastAPI(
    title="Project Submission Portal Gateway",
    description="API Gateway for the project submission system",
    version="1.0.0",
    lifespan=lifespan
)


# Configure templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Middleware to inject clients into request state
@app.middleware("http")
async def add_clients_to_request(request: Request, call_next):
    """Inject service clients into request.state for route handlers."""
    request.state.clients = clients
    request.state.templates = templates
    response = await call_next(request)
    return response


# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# Register routers
app.include_router(public_router, tags=["public"])
app.include_router(dashboard_router, tags=["dashboard"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
