from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, extract
from geoalchemy2.functions import ST_MakePoint, ST_SetSRID, ST_DWithin
from datetime import datetime, timezone
from typing import Optional

from core.database import get_db
from core.dependencies import require_admin
from models import Incident, IncidentStatus, IncidentType

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ─────────────────────────────────────────────
# Heatmap data
# Returns lat/lng of all verified incidents
# consumed directly by Leaflet.heat plugin
# ─────────────────────────────────────────────

@router.get("/heatmap", response_class=JSONResponse, name="analytics.heatmap")
async def heatmap(
    db: AsyncSession = Depends(get_db),
    area: Optional[str] = None,
    incident_type: Optional[str] = None
):
    query = (
        select(Incident.latitude, Incident.longitude, Incident.upvotes)
        .where(Incident.status == IncidentStatus.verified)
    )

    if area:
        query = query.where(Incident.area.ilike(f"%{area}%"))

    if incident_type:
        try:
            query = query.where(Incident.incident_type == IncidentType(incident_type))
        except ValueError:
            pass

    result = await db.execute(query)
    rows = result.all()

    # Leaflet.heat expects [lat, lng, intensity]
    # use upvotes + 1 as intensity so zero-vote incidents still appear
    return [[r.latitude, r.longitude, r.upvotes + 1] for r in rows]


# ─────────────────────────────────────────────
# Crime type breakdown
# Returns count per incident_type
# ─────────────────────────────────────────────

@router.get("/by-type", response_class=JSONResponse, name="analytics.by_type")
async def by_type(
    db: AsyncSession = Depends(get_db),
    area: Optional[str] = None
):
    query = (
        select(Incident.incident_type, func.count().label("count"))
        .where(Incident.status == IncidentStatus.verified)
        .group_by(Incident.incident_type)
        .order_by(func.count().desc())
    )

    if area:
        query = query.where(Incident.area.ilike(f"%{area}%"))

    result = await db.execute(query)
    rows = result.all()

    return [{"type": r.incident_type.value, "count": r.count} for r in rows]


# ─────────────────────────────────────────────
# Area breakdown
# Returns count per area — drives area ranking
# ─────────────────────────────────────────────

@router.get("/by-area", response_class=JSONResponse, name="analytics.by_area")
async def by_area(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, le=50)
):
    result = await db.execute(
        select(Incident.area, func.count().label("count"))
        .where(Incident.status == IncidentStatus.verified)
        .group_by(Incident.area)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = result.all()

    return [{"area": r.area, "count": r.count} for r in rows]


# ─────────────────────────────────────────────
# Monthly trend
# Returns count per month for the last 12 months
# ─────────────────────────────────────────────

@router.get("/monthly-trend", response_class=JSONResponse, name="analytics.monthly_trend")
async def monthly_trend(
    db: AsyncSession = Depends(get_db),
    area: Optional[str] = None
):
    query = (
        select(
            extract("year",  Incident.occurred_at).label("year"),
            extract("month", Incident.occurred_at).label("month"),
            func.count().label("count")
        )
        .where(Incident.status == IncidentStatus.verified)
        .group_by("year", "month")
        .order_by("year", "month")
    )

    if area:
        query = query.where(Incident.area.ilike(f"%{area}%"))

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "year":  int(r.year),
            "month": int(r.month),
            "count": r.count,
            "label": datetime(int(r.year), int(r.month), 1).strftime("%b %Y")
        }
        for r in rows
    ]


# ─────────────────────────────────────────────
# Safety score per area
# Simple weighted formula:
#   score = 100 - min(100, verified_count × recency_weight)
# Higher score = safer area
# ─────────────────────────────────────────────

@router.get("/safety-score", response_class=JSONResponse, name="analytics.safety_score")
async def safety_score(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, le=100)
):
    # weight recent incidents (last 30 days) heavier than older ones
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(
            Incident.area,
            func.count().label("total"),
            func.sum(
                case(
                    # incidents in last 30 days → weight 2.0
                    (func.now() - Incident.occurred_at < func.cast("30 days", type_=None), 2),
                    # incidents in last 90 days → weight 1.5
                    (func.now() - Incident.occurred_at < func.cast("90 days", type_=None), 1),
                    else_=1
                )
            ).label("weighted_count")
        )
        .where(Incident.status == IncidentStatus.verified)
        .group_by(Incident.area)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = result.all()

    scores = []
    for r in rows:
        # clamp between 0 and 100 — more weighted incidents = lower score
        raw = max(0, 100 - int(r.weighted_count * 3))
        scores.append({
            "area": r.area,
            "total_incidents": r.total,
            "safety_score": raw,
            "risk_level": (
                "high"   if raw < 40 else
                "medium" if raw < 70 else
                "low"
            )
        })

    # sort safest → most dangerous
    scores.sort(key=lambda x: x["safety_score"], ascending=False) if False else \
    scores.sort(key=lambda x: x["safety_score"])

    return scores


# ─────────────────────────────────────────────
# Summary stats — admin dashboard cards
# ─────────────────────────────────────────────

@router.get("/summary", response_class=JSONResponse, name="analytics.summary")
async def summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin)
):
    total     = await db.execute(select(func.count()).select_from(Incident))
    pending   = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.pending))
    verified  = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.verified))
    rejected  = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.rejected))

    # most reported area
    top_area_result = await db.execute(
        select(Incident.area, func.count().label("count"))
        .where(Incident.status == IncidentStatus.verified)
        .group_by(Incident.area)
        .order_by(func.count().desc())
        .limit(1)
    )
    top_area = top_area_result.first()

    return {
        "total":     total.scalar(),
        "pending":   pending.scalar(),
        "verified":  verified.scalar(),
        "rejected":  rejected.scalar(),
        "top_area":  top_area.area  if top_area else None,
        "top_area_count": top_area.count if top_area else 0
    }