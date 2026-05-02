from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from typing import Optional
from datetime import datetime
import cloudinary
import cloudinary.uploader

from core.database import get_db
from core.config import settings
from core.dependencies import get_current_active_user
from models import User, Incident, IncidentVote, IncidentType, IncidentStatus

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# Cloudinary config (only runs if keys are set)
# ─────────────────────────────────────────────

if settings.cloudinary_cloud_name:
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret
    )


# ─────────────────────────────────────────────
# Submit report — GET (show form)
# ─────────────────────────────────────────────

@router.get("/submit", response_class=HTMLResponse, name="reports.submit_get")
async def submit_get(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    return templates.TemplateResponse("submit_report.html", {
        "request": request,
        "user": current_user,
        "incident_types": [t.value for t in IncidentType]
    })


# ─────────────────────────────────────────────
# Submit report — POST
# ─────────────────────────────────────────────

@router.post("/submit", name="reports.submit_post")
async def submit_post(
    request: Request,
    incident_type: str         = Form(...),
    description: str           = Form(None),
    address: str               = Form(None),
    area: str                  = Form(...),
    city: str                  = Form("Mumbai"),
    state: str                 = Form("Maharashtra"),
    pincode: str               = Form(None),
    latitude: float            = Form(...),
    longitude: float           = Form(...),
    occurred_at: datetime      = Form(...),
    is_anonymous: bool         = Form(False),
    image: Optional[UploadFile] = File(None),
    db: AsyncSession           = Depends(get_db),
    current_user: User         = Depends(get_current_active_user)
):
    # validate incident type against enum
    try:
        i_type = IncidentType(incident_type)
    except ValueError:
        return templates.TemplateResponse("submit_report.html", {
            "request": request,
            "user": current_user,
            "incident_types": [t.value for t in IncidentType],
            "error": f"Invalid incident type: {incident_type}"
        })

    # upload image to Cloudinary if provided
    image_url = None
    if image and image.filename:
        if not settings.cloudinary_cloud_name:
            # Cloudinary not configured — skip silently in dev
            pass
        else:
            contents = await image.read()
            result = cloudinary.uploader.upload(
                contents,
                folder="safesteps/incidents",
                resource_type="image"
            )
            image_url = result.get("secure_url")

    # build PostGIS point from lat/lng
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)

    incident = Incident(
        reported_by=current_user.id,
        incident_type=i_type,
        description=description,
        image_url=image_url,
        address=address,
        area=area,
        city=city,
        state=state,
        pincode=pincode,
        latitude=latitude,
        longitude=longitude,
        location=point,
        occurred_at=occurred_at,
        is_anonymous=is_anonymous,
        status=IncidentStatus.pending
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    return RedirectResponse(url="/user/dashboard", status_code=status.HTTP_302_FOUND)


# ─────────────────────────────────────────────
# List incidents — JSON (used by Leaflet map)
# ─────────────────────────────────────────────

@router.get("/map-data", response_class=JSONResponse, name="reports.map_data")
async def map_data(
    db: AsyncSession = Depends(get_db),
    area: Optional[str] = None,
    incident_type: Optional[str] = None,
    status_filter: Optional[str] = "verified"     # map shows verified by default
):
    query = select(Incident)

    if status_filter:
        try:
            query = query.where(Incident.status == IncidentStatus(status_filter))
        except ValueError:
            pass

    if area:
        query = query.where(Incident.area.ilike(f"%{area}%"))

    if incident_type:
        try:
            query = query.where(Incident.incident_type == IncidentType(incident_type))
        except ValueError:
            pass

    result = await db.execute(query.order_by(Incident.occurred_at.desc()))
    incidents = result.scalars().all()

    return [
        {
            "id": str(i.id),
            "incident_type": i.incident_type.value,
            "description": i.description,
            "area": i.area,
            "city": i.city,
            "latitude": i.latitude,
            "longitude": i.longitude,
            "occurred_at": i.occurred_at.isoformat(),
            "status": i.status.value,
            "upvotes": i.upvotes,
            "image_url": i.image_url,
            "is_anonymous": i.is_anonymous,
            "reported_by": None if i.is_anonymous else str(i.reported_by)
        }
        for i in incidents
    ]


# ─────────────────────────────────────────────
# Get single incident
# ─────────────────────────────────────────────

@router.get("/{incident_id}", response_class=HTMLResponse, name="reports.detail")
async def incident_detail(
    request: Request,
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    return templates.TemplateResponse("incident_detail.html", {
        "request": request,
        "incident": incident,
        "user": current_user
    })


# ─────────────────────────────────────────────
# Upvote incident
# ─────────────────────────────────────────────

@router.post("/{incident_id}/upvote", response_class=JSONResponse, name="reports.upvote")
async def upvote_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # check incident exists
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # check if already voted — unique constraint handles DB level,
    # but we check first to return a clean error message
    existing = await db.execute(
        select(IncidentVote).where(
            IncidentVote.incident_id == incident_id,
            IncidentVote.user_id == current_user.id
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="You have already upvoted this incident")

    vote = IncidentVote(incident_id=incident_id, user_id=current_user.id)
    db.add(vote)

    # increment cached count
    incident.upvotes += 1

    await db.commit()

    return {"upvotes": incident.upvotes}


# ─────────────────────────────────────────────
# Nearby incidents — radius search via PostGIS
# ─────────────────────────────────────────────

@router.get("/nearby", response_class=JSONResponse, name="reports.nearby")
async def nearby_incidents(
    lat: float,
    lng: float,
    radius_meters: int = 2000,
    db: AsyncSession = Depends(get_db)
):
    point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)

    result = await db.execute(
        select(Incident).where(
            Incident.status == IncidentStatus.verified,
            ST_DWithin(Incident.location, point, radius_meters)
        ).order_by(Incident.occurred_at.desc()).limit(50)
    )
    incidents = result.scalars().all()

    return [
        {
            "id": str(i.id),
            "incident_type": i.incident_type.value,
            "area": i.area,
            "latitude": i.latitude,
            "longitude": i.longitude,
            "occurred_at": i.occurred_at.isoformat(),
            "upvotes": i.upvotes
        }
        for i in incidents
    ]