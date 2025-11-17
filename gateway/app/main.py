from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .api.routes_public import router as public_router
from .api.routes_dashboard import router as dashboard_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="gateway/app/static"), name="static")
templates = Jinja2Templates(directory="gateway/app/templates")

app.include_router(public_router)
app.include_router(dashboard_router)
