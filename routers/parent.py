from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.dependencies import get_current_active_user
from core.database import get_db
from core.websockets import manager
from models import Users, Incident, IncidentVote
import json
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
async def dashboard(request: Request, current_user: Users = Depends(get_current_active_user)):
    return templates.TemplateResponse(request, "parent_dashboard.html", {"request": request, "user": current_user})

@router.get("/report_incident", response_class=HTMLResponse)
async def report_incident_get(request: Request, current_user: Users = Depends(get_current_active_user)):
    return templates.TemplateResponse(request, "parent_report.html", {"request": request, "user": current_user})

@router.post("/report_incident")
async def report_incident_post(
    request: Request,
    incident_type: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    area: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_active_user)
):
    # Create geom point "POINT(lon lat)"
    geom_str = f"SRID=4326;POINT({longitude} {latitude})"
    new_incident = Incident(
        user_id=current_user.id,
        incident_type=incident_type,
        description=description,
        location=location,
        area=area,
        geom=geom_str,
        incident_date=datetime.utcnow()
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)
    
    # Broadcast to all connected WebSockets
    incident_data = {
        "id": new_incident.id,
        "type": incident_type,
        "description": description,
        "lat": latitude,
        "lng": longitude,
        "status": "reported",
        "timestamp": new_incident.incident_date.isoformat()
    }
    await manager.broadcast(json.dumps(incident_data))
    
    return RedirectResponse(url="/parent/dashboard", status_code=status.HTTP_302_FOUND)

@router.post("/incident/{incident_id}/vote")
async def vote_incident(
    incident_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_active_user)
):
    # Check if incident exists
    result = await db.execute(select(Incident).filter(Incident.id == incident_id))
    incident = result.scalars().first()
    if not incident:
        return JSONResponse({"error": "Incident not found"}, status_code=404)
        
    # Check if user already voted
    result = await db.execute(
        select(IncidentVote).filter(IncidentVote.incident_id == incident_id, IncidentVote.user_id == current_user.id)
    )
    existing_vote = result.scalars().first()
    if existing_vote:
        return JSONResponse({"error": "Already voted"}, status_code=400)
        
    # Add vote
    new_vote = IncidentVote(user_id=current_user.id, incident_id=incident_id, vote=1)
    db.add(new_vote)
    
    # Check total votes
    from sqlalchemy import func
    result = await db.execute(
        select(func.sum(IncidentVote.vote)).filter(IncidentVote.incident_id == incident_id)
    )
    total_votes = result.scalar() or 0
    total_votes += 1 # Add the current vote since it's not committed yet
    
    if total_votes >= 5 and incident.status == "reported":
        incident.status = "community_verified"
        await manager.broadcast(json.dumps({
            "id": incident.id,
            "status": incident.status,
            "type": "status_update"
        }))
        
    await db.commit()
    return JSONResponse({"message": "Vote recorded", "total_votes": total_votes, "status": incident.status})

@router.get("/get_reports")
async def get_reports(db: AsyncSession = Depends(get_db)):
    # Simple query to get all incidents
    # Note: For PostGIS geom parsing without ST_X/ST_Y, we need to extract coords, 
    # but since we need it fast, we can use func.ST_X and func.ST_Y
    from sqlalchemy import func
    result = await db.execute(
        select(
            Incident.id, 
            Incident.incident_type, 
            Incident.description, 
            Incident.status,
            Incident.incident_date,
            func.ST_Y(Incident.geom).label("lat"),
            func.ST_X(Incident.geom).label("lng")
        )
    )
    incidents = result.all()
    reports = []
    for inc in incidents:
        if inc.lat is not None and inc.lng is not None:
            reports.append({
                "id": inc.id,
                "type": inc.incident_type,
                "description": inc.description,
                "status": inc.status,
                "lat": inc.lat,
                "lng": inc.lng,
                "timestamp": inc.incident_date.isoformat() if inc.incident_date else None
            })
    return JSONResponse(content=reports)
