from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from core.dependencies import get_current_admin
from models import Users

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
async def dashboard(request: Request, current_user: Users = Depends(get_current_admin)):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": current_user})
