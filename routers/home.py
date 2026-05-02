from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from core.dependencies import get_current_active_user
from models import Users

router = APIRouter()

@router.get("/")
async def home(current_user: Users = Depends(get_current_active_user)):
    return RedirectResponse(url=f"/{current_user.role}/dashboard")