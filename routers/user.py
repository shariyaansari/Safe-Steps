from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from core.dependencies import get_current_active_user
from core.security import get_password_hash, verify_password
from core.config import settings
from models import User, Incident, IncidentVote, IncidentStatus, IncidentType

router = APIRouter(prefix="/user", tags=["user"])
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse, name="user.dashboard")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # user's own recent reports
    result = await db.execute(
        select(Incident)
        .where(Incident.reported_by == current_user.id)
        .order_by(Incident.reported_at.desc())
        .limit(10)
    )
    my_incidents = result.scalars().all()

    # counts for profile summary
    total_result    = await db.execute(
        select(func.count())
        .select_from(Incident)
        .where(Incident.reported_by == current_user.id)
    )
    verified_result = await db.execute(
        select(func.count())
        .select_from(Incident)
        .where(
            Incident.reported_by == current_user.id,
            Incident.status == IncidentStatus.verified
        )
    )

    return templates.TemplateResponse("user/dashboard.html", {
        "request": request,
        "user": current_user,
        "my_incidents": my_incidents,
        "stats": {
            "total_reported":    total_result.scalar(),
            "total_verified":    verified_result.scalar(),
        }
    })


# ─────────────────────────────────────────────
# Map view — main public page
# ─────────────────────────────────────────────

@router.get("/map", response_class=HTMLResponse, name="user.map")
async def map_view(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    return templates.TemplateResponse("user/map.html", {
        "request": request,
        "user": current_user,
        "incident_types": [t.value for t in IncidentType]
    })


# ─────────────────────────────────────────────
# My incidents — full list with pagination
# ─────────────────────────────────────────────

@router.get("/my-incidents", response_class=HTMLResponse, name="user.my_incidents")
async def my_incidents(
    request: Request,
    page: int = 1,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    page_size = 15
    offset = (page - 1) * page_size

    query = (
        select(Incident)
        .where(Incident.reported_by == current_user.id)
        .order_by(Incident.reported_at.desc())
    )

    if status_filter:
        try:
            query = query.where(Incident.status == IncidentStatus(status_filter))
        except ValueError:
            pass

    result = await db.execute(query.offset(offset).limit(page_size))
    incidents = result.scalars().all()

    total_result = await db.execute(
        select(func.count())
        .select_from(Incident)
        .where(Incident.reported_by == current_user.id)
    )
    total = total_result.scalar()

    return templates.TemplateResponse("user/my_incidents.html", {
        "request": request,
        "user": current_user,
        "incidents": incidents,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
        "status_filter": status_filter,
        "status_choices": [s.value for s in IncidentStatus]
    })


# ─────────────────────────────────────────────
# Delete own incident (only if still pending)
# ─────────────────────────────────────────────

@router.delete("/my-incidents/{incident_id}", response_class=JSONResponse, name="user.delete_incident")
async def delete_own_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # users can only delete their own incidents
    if str(incident.reported_by) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You can only delete your own reports")

    # once verified or rejected, it's in the system — only admin can delete it
    if incident.status != IncidentStatus.pending:
        raise HTTPException(
            status_code=400,
            detail="You can only delete pending reports. Contact admin to remove verified or rejected reports."
        )

    await db.delete(incident)
    await db.commit()

    return {"message": "Report deleted successfully"}


# ─────────────────────────────────────────────
# Profile page
# ─────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse, name="user.profile")
async def profile(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user": current_user
    })


# ─────────────────────────────────────────────
# Update profile
# ─────────────────────────────────────────────

@router.post("/profile", response_class=HTMLResponse, name="user.profile_post")
async def update_profile(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # check email not taken by someone else
    result = await db.execute(
        select(User).where(
            User.email == email,
            User.id != current_user.id
        )
    )
    if result.scalars().first():
        return templates.TemplateResponse("user/profile.html", {
            "request": request,
            "user": current_user,
            "error": "Email is already in use by another account"
        })

    current_user.email = email
    await db.commit()

    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user": current_user,
        "success": "Profile updated successfully"
    })


# ─────────────────────────────────────────────
# Change password
# ─────────────────────────────────────────────

@router.post("/change-password", response_class=HTMLResponse, name="user.change_password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if new_password != confirm_password:
        return templates.TemplateResponse("user/profile.html", {
            "request": request,
            "user": current_user,
            "error": "New passwords do not match"
        })

    if not verify_password(current_password[:72], current_user.password_hash):
        return templates.TemplateResponse("user/profile.html", {
            "request": request,
            "user": current_user,
            "error": "Current password is incorrect"
        })

    if len(new_password) < 8:
        return templates.TemplateResponse("user/profile.html", {
            "request": request,
            "user": current_user,
            "error": "New password must be at least 8 characters"
        })

    current_user.password_hash = get_password_hash(new_password[:72])
    await db.commit()

    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user": current_user,
        "success": "Password changed successfully"
    })


# ─────────────────────────────────────────────
# My votes — incidents this user has upvoted
# ─────────────────────────────────────────────

@router.get("/my-votes", response_class=JSONResponse, name="user.my_votes")
async def my_votes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(
        select(IncidentVote.incident_id)
        .where(IncidentVote.user_id == current_user.id)
    )
    voted_ids = [str(row.incident_id) for row in result.all()]

    return {"voted_incident_ids": voted_ids}