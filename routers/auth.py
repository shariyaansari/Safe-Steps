from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from core.database import get_db
from core.config import settings
from core.security import get_password_hash, verify_password, create_access_token
from core.dependencies import get_current_user
from models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse, name="auth.register")
async def register_get(request: Request):
    return templates.TemplateResponse("sign_up.html", {"request": request})


@router.post("/register", name="auth.register_post")
async def register_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # check for existing username or email
    result = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if result.scalars().first():
        return templates.TemplateResponse("sign_up.html", {
            "request": request,
            "error": "Username or email already taken"
        })

    # bcrypt silently truncates at 72 chars — trim explicitly so the user
    # isn't locked out if they register with a long password then try to login
    hashed = get_password_hash(password[:72])

    user = User(
        username=username,
        email=email,
        password_hash=hashed,
        role=UserRole.user       # role is always user on self-register
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # log straight in after registration
    access_token = create_access_token(
        data={"sub": user.username},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    response = RedirectResponse(url="/user/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax")
    return response


# ─────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse, name="auth.login")
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", name="auth.login_post")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user or not verify_password(password[:72], user.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Your account has been deactivated"
        })

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    # redirect based on role
    redirect_url = "/admin/dashboard" if user.role == UserRole.admin else "/user/dashboard"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, samesite="lax")
    return response


# ─────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────

@router.get("/logout", name="auth.logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response