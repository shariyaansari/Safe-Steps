from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from core.dependencies import get_current_active_user
from models import Users

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
async def dashboard(request: Request, current_user: Users = Depends(get_current_active_user)):
    return templates.TemplateResponse("parent_dashboard.html", {"request": request, "user": current_user})
