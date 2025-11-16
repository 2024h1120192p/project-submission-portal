from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/dashboard")

@router.get("/student")
def dashboard_student(request: Request):
    return templates.TemplateResponse(name="dashboard_student.html", context={"request": request})

@router.get("/faculty")
def dashboard_faculty(request: Request):
    return templates.TemplateResponse(name="dashboard_faculty.html", context={"request": request})