from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import get_password_hash, verify_password, create_access_token
from models import Users

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})

@router.post("/register")
async def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("parent"),
    db: AsyncSession = Depends(get_db)
):
    if role == "admin":
        role = "parent"
        
    result = await db.execute(select(Users).filter((Users.username == username) | (Users.email == email)))
    if result.scalars().first():
        return templates.TemplateResponse("sign_up.html", {"request": request, "error": "Username or Email already taken"})
        
    password = password[:72]
    hashed_password = get_password_hash(password)
    user = Users(username=username, email=email, password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Users).filter(Users.username == username))
    user = result.scalars().first()
    
    password = password[:72]
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
        
    access_token = create_access_token(data={"sub": user.username})
    
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("access_token")
    return response