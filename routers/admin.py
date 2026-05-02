from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from typing import Optional
from core.database import get_db
from core.dependencies import get_current_active_user, require_admin
from models import User, Incident, IncidentStatus, AuditLog, AuditAction, UserRole
from ws.events import publish_incident

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# Admin dashboard
# ─────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse, name="admin.dashboard")
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # counts for dashboard stats
    total_result     = await db.execute(select(func.count()).select_from(Incident))
    pending_result   = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.pending))
    verified_result  = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.verified))
    rejected_result  = await db.execute(select(func.count()).select_from(Incident).where(Incident.status == IncidentStatus.rejected))

    # latest 20 pending incidents for the moderation queue
    pending_q = await db.execute(
        select(Incident)
        .where(Incident.status == IncidentStatus.pending)
        .order_by(Incident.reported_at.desc())
        .limit(20)
    )
    pending_incidents = pending_q.scalars().all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": current_user,
        "stats": {
            "total":    total_result.scalar(),
            "pending":  pending_result.scalar(),
            "verified": verified_result.scalar(),
            "rejected": rejected_result.scalar(),
        },
        "pending_incidents": pending_incidents
    })


# ─────────────────────────────────────────────
# Moderation queue — all pending (paginated)
# ─────────────────────────────────────────────

@router.get("/incidents", response_class=HTMLResponse, name="admin.incidents")
async def incident_queue(
    request: Request,
    page: int = 1,
    status_filter: Optional[str] = "pending",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    page_size = 20
    offset = (page - 1) * page_size

    query = select(Incident).order_by(Incident.reported_at.desc())
    if status_filter:
        try:
            query = query.where(Incident.status == IncidentStatus(status_filter))
        except ValueError:
            pass

    result = await db.execute(query.offset(offset).limit(page_size))
    incidents = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(Incident))
    total = total_result.scalar()

    return templates.TemplateResponse("admin/incidents.html", {
        "request": request,
        "user": current_user,
        "incidents": incidents,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
        "status_filter": status_filter
    })


# ─────────────────────────────────────────────
# Verify incident
# ─────────────────────────────────────────────

@router.post("/incidents/{incident_id}/verify", response_class=JSONResponse, name="admin.verify")
async def verify_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status == IncidentStatus.verified:
        raise HTTPException(status_code=400, detail="Incident is already verified")

    incident.status      = IncidentStatus.verified
    incident.verified_by = current_user.id
    incident.verified_at = datetime.now(timezone.utc)

    log = AuditLog(
        admin_id=current_user.id,
        incident_id=incident.id,
        action=AuditAction.verified
    )
    db.add(log)
    await db.commit()
    await publish_incident(incident)

    return {"message": "Incident verified", "incident_id": incident_id}


# ─────────────────────────────────────────────
# Reject incident
# ─────────────────────────────────────────────

@router.post("/incidents/{incident_id}/reject", response_class=JSONResponse, name="admin.reject")
async def reject_incident(
    request: Request,
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    body = await request.json()
    note = body.get("note", None)   # admin can optionally leave a rejection reason

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status == IncidentStatus.rejected:
        raise HTTPException(status_code=400, detail="Incident is already rejected")

    incident.status = IncidentStatus.rejected

    log = AuditLog(
        admin_id=current_user.id,
        incident_id=incident.id,
        action=AuditAction.rejected,
        note=note
    )
    db.add(log)
    await db.commit()

    return {"message": "Incident rejected", "incident_id": incident_id}


# ─────────────────────────────────────────────
# Delete incident
# ─────────────────────────────────────────────

@router.delete("/incidents/{incident_id}", response_class=JSONResponse, name="admin.delete_incident")
async def delete_incident(
    request: Request,
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    body = await request.json()
    note = body.get("note", None)

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalars().first()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    log = AuditLog(
        admin_id=current_user.id,
        incident_id=incident.id,
        action=AuditAction.deleted,
        note=note
    )
    db.add(log)

    await db.delete(incident)
    await db.commit()

    return {"message": "Incident deleted", "incident_id": incident_id}


# ─────────────────────────────────────────────
# Ban user
# ─────────────────────────────────────────────

@router.post("/users/{user_id}/ban", response_class=JSONResponse, name="admin.ban_user")
async def ban_user(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    body = await request.json()
    note = body.get("note", None)

    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.role == UserRole.admin:
        raise HTTPException(status_code=400, detail="Cannot ban another admin")

    if not target.is_active:
        raise HTTPException(status_code=400, detail="User is already banned")

    target.is_active = False

    log = AuditLog(
        admin_id=current_user.id,
        target_user=target.id,
        action=AuditAction.banned_user,
        note=note
    )
    db.add(log)
    await db.commit()

    return {"message": f"User {target.username} has been banned"}


# ─────────────────────────────────────────────
# Unban user
# ─────────────────────────────────────────────

@router.post("/users/{user_id}/unban", response_class=JSONResponse, name="admin.unban_user")
async def unban_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()

    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    if target.is_active:
        raise HTTPException(status_code=400, detail="User is not banned")

    target.is_active = True

    log = AuditLog(
        admin_id=current_user.id,
        target_user=target.id,
        action=AuditAction.banned_user,
        note="unbanned"
    )
    db.add(log)
    await db.commit()

    return {"message": f"User {target.username} has been unbanned"}


# ─────────────────────────────────────────────
# Audit log viewer
# ─────────────────────────────────────────────

@router.get("/audit-log", response_class=HTMLResponse, name="admin.audit_log")
async def audit_log(
    request: Request,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    page_size = 30
    offset = (page - 1) * page_size

    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = result.scalars().all()

    total_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = total_result.scalar()

    return templates.TemplateResponse("admin/audit_log.html", {
        "request": request,
        "user": current_user,
        "logs": logs,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size
    })


# ─────────────────────────────────────────────
# User list
# ─────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse, name="admin.users")
async def user_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": current_user,
        "users": users
    })