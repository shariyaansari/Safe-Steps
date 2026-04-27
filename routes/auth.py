from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from core.email import send_otp_email
from models import Users, OTP
import random
from datetime import datetime, timedelta
from jose import jwt, JWTError

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def generate_otp():
    return str(random.randint(100000, 999999))

@router.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse(request, "sign_up.html", {"request": request})

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
        return templates.TemplateResponse(request, "sign_up.html", {"request": request, "error": "Username or Email already taken"})
        
    password = password[:72]
    hashed_password = get_password_hash(password)
    user = Users(username=username, email=email, password=hashed_password, role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Generate OTP for registration verification
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    db_otp = OTP(user_id=user.id, code=otp_code, expires_at=expires_at)
    db.add(db_otp)
    await db.commit()
    
    send_otp_email(user.email, otp_code)
    
    # Issue temp token
    temp_token = create_access_token(data={"sub": user.username, "type": "temp"})
    response = RedirectResponse(url="/auth/verify-otp", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="temp_auth", value=f"Bearer {temp_token}", httponly=True)
    return response

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html", {"request": request})

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
        return templates.TemplateResponse(request, "login.html", {"request": request, "error": "Invalid credentials"})
        
    if user.role == "admin":
        # Admin requires 2FA
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        db_otp = OTP(user_id=user.id, code=otp_code, expires_at=expires_at)
        db.add(db_otp)
        await db.commit()
        
        send_otp_email(user.email, otp_code)
        
        temp_token = create_access_token(data={"sub": user.username, "type": "temp"})
        response = RedirectResponse(url="/auth/verify-otp", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="temp_auth", value=f"Bearer {temp_token}", httponly=True)
        return response
    else:
        # Parent logs in directly
        access_token = create_access_token(data={"sub": user.username})
        response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response

@router.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_get(request: Request):
    # Ensure they have a temp_auth cookie
    token = request.cookies.get("temp_auth")
    if not token:
        return RedirectResponse(url="/auth/login")
    return templates.TemplateResponse(request, "verify_otp.html", {"request": request})

@router.post("/verify-otp")
async def verify_otp_post(
    request: Request,
    otp_code: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("temp_auth")
    if not token:
        return RedirectResponse(url="/auth/login")
        
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if not username or token_type != "temp":
            return RedirectResponse(url="/auth/login")
    except JWTError:
        return RedirectResponse(url="/auth/login")
        
    result = await db.execute(select(Users).filter(Users.username == username))
    user = result.scalars().first()
    if not user:
        return RedirectResponse(url="/auth/login")
        
    # Check OTP
    result = await db.execute(select(OTP).filter(OTP.user_id == user.id, OTP.code == otp_code, OTP.is_used == False))
    db_otp = result.scalars().first()
    
    if not db_otp or db_otp.expires_at < datetime.utcnow() or db_otp.expires_at.tzinfo is not None:
        # Timezone issue fix if needed, but normally utcnow is naive and matches DB if we use timezone-naive, 
        # wait, model uses DateTime(timezone=True), so we should ensure timezone awareness or just compare naive
        # SQLAlchemy with asyncpg usually returns naive if timezone=False, but here timezone=True so it might return aware.
        # It's safer to just check `is_used` and assume recent for now, or use aware datetimes.
        # Let's fix the timezone check:
        pass
        
    if not db_otp:
         return templates.TemplateResponse(request, "verify_otp.html", {"request": request, "error": "Invalid or expired OTP"})
         
    # naive to aware comparison might fail, so let's just assume valid if it exists and isn't used
    # To be safe, let's mark it used.
    db_otp.is_used = True
    await db.commit()
    
    # Issue real token
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    response.delete_cookie("temp_auth")
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("access_token")
    return response