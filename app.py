from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import routers
from routes.auth import router as auth_router
from routes.home import router as home_router
from routes.admin import router as admin_router
from routes.parent import router as parent_router
from routes.news_analysis import router as news_analysis_router
from core.websockets import router as websocket_router

app = FastAPI(title="Safe-Steps API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        # Redirect unauthorized users to the login page
        return RedirectResponse(url="/auth/login")
    elif exc.status_code == 403:
        # Redirect forbidden users to the login page
        return RedirectResponse(url="/auth/login")
    
    # Check if request accepts html
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        templates = Jinja2Templates(directory="templates")
        # In a real app we might render an error template here
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(home_router, prefix="/home", tags=["home"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(parent_router, prefix="/parent", tags=["parent"])
app.include_router(news_analysis_router, tags=["news"])
app.include_router(websocket_router, tags=["websocket"])

@app.get("/")
async def root():
    # Redirect to home or auth
    return RedirectResponse(url="/home/")

# To run: uvicorn app:app --reload