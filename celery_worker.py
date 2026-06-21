"""
Celery task definitions for SafeSteps.

Each task gets its own sync DB session, runs its job, and closes
the session. Sessions are not shared across tasks or with FastAPI's
async engine.
"""

import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from celery_app import celery_app
from core.config import settings
from models import Incident, IncidentSource
from news_scraper import scrape_and_store

logger = logging.getLogger(__name__)

# sync engine + session factory, used only by Celery tasks.
# Celery workers are sync processes — mixing in async SQLAlchemy
# here would add complexity with no real benefit at this scale.
SYNC_DATABASE_URL = settings.database_url.replace("+asyncpg", "")
sync_engine = create_engine(SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(bind=sync_engine)


@celery_app.task(name="celery_worker.scrape_news_task")
def scrape_news_task():
    """
    Scheduled task — runs every hour via Celery Beat.
    Fetches RSS feeds, classifies + geocodes crime articles,
    inserts new ones as auto-verified incidents.
    """
    db = SyncSessionLocal()

    try:
        # load URLs of every article we've already scraped and stored,
        # so re-running the scraper doesn't insert duplicates
        existing_urls = db.execute(
            select(Incident.source_url).where(Incident.source == IncidentSource.news_scraper)
        ).scalars().all()
        seen_urls = set(url for url in existing_urls if url)

        summary = scrape_and_store(db, seen_urls)
        logger.info(f"[Celery] News scrape task finished: {summary}")
        return summary

    except Exception as e:
        logger.error(f"[Celery] News scrape task failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()