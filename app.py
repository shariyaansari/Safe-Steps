from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.database import engine, Base
from core.config import settings

from routers import auth, user, reports, admin, analytics
from ws.events import router as ws_router
from ws.events import redis_subscriber



# ─────────────────────────────────────────────
# Lifespan — runs on startup and shutdown
# creates all DB tables if they don't exist
# ─────────────────────────────────────────────

# redis_subscriber() - long running async function that subscribes to the Redis channel and waits for messages. When it gets one, it calls manager.broadcast().

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[SafeSteps] Database tables ready")
    asyncio.create_task(redis_subscriber())   # ← add this line
    yield
    await engine.dispose()
    print("[SafeSteps] Database connection closed")


# ─────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)


# ─────────────────────────────────────────────
# CORS
# Allows your HTML frontend (served from the
# same origin) to make fetch/XHR requests
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Static files
# ─────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(ws_router)


# ─────────────────────────────────────────────
# Root redirect
# ─────────────────────────────────────────────

from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login")