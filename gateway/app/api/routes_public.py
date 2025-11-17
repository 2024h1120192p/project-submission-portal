from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="gateway/app/templates")
router = APIRouter()

@router.get("/")
def home(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(name="login.html", context={"request": request})
@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # stub auth
    return templates.TemplateResponse(name="index.html", context={"request": request, "message": "Logged in"})