"""
Celery application instance for SafeSteps.

Celery needs its own SYNCHRONOUS database connection — separate from
the async SQLAlchemy engine used by FastAPI. Celery workers are
traditionally sync processes, and mixing async into them adds
complexity with no real benefit at this scale. So this file sets up
a plain psycopg2-based sync engine just for background tasks.

Run the worker with:
    celery -A celery_app worker --loglevel=info --pool=solo   (Windows)
    celery -A celery_app worker --loglevel=info                (Mac/Linux)

Run the scheduler (for periodic tasks like the news scraper) with:
    celery -A celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
from core.config import settings

# Celery needs a sync DB URL — convert the async one
# postgresql+asyncpg://...  →  postgresql://...
SYNC_DATABASE_URL = settings.database_url.replace("+asyncpg", "")

celery_app = Celery(
    "safesteps",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# ─────────────────────────────────────────────
# Scheduled tasks (Celery Beat)
# ─────────────────────────────────────────────

celery_app.conf.beat_schedule = {
    "scrape-news-every-hour": {
        "task": "celery_worker.scrape_news_task",
        "schedule": crontab(minute=0),     # runs at the top of every hour
    },
}

# import tasks so Celery registers them
import celery_worker  # noqa: E402, F401