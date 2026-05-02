from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.websockets import manager
from models import Users, Incident
import json
from fastapi.templating import Jinja2Templates
from core.dependencies import get_current_admin
from models import Users

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard")
async def dashboard(request: Request, current_user: Users = Depends(get_current_admin)):
    return templates.TemplateResponse(
        request, "adminhome.html", {"request": request, "user": current_user}
    )


# @router.get("/reports")
# async def reports(request: Request, current_user: Users = Depends(get_current_admin)):
#     return templates.TemplateResponse(request, "admin_report.html", {"request": request, "user": current_user})
@router.get("/reports", response_class=HTMLResponse, name="admin.reports")
async def admin_reports(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report))  # your model
    reports = result.scalars().all()

    return templates.TemplateResponse(
        "admin_reports.html", {"request": request, "reports": reports}
    )


@router.post("/incident/{incident_id}/status")
async def update_status(
    incident_id: int,
    request: Request,
    new_status: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_admin),
):
    result = await db.execute(select(Incident).filter(Incident.id == incident_id))
    incident = result.scalars().first()
    if not incident:
        return JSONResponse({"error": "Incident not found"}, status_code=404)

    incident.status = new_status
    await db.commit()

    # Broadcast status change
    await manager.broadcast(
        json.dumps({"id": incident.id, "status": new_status, "type": "status_update"})
    )

    return RedirectResponse(url="/admin/reports", status_code=status.HTTP_302_FOUND)

# @router.post("/users/{user_id}/edit", name="admin.edit_user")
# async def edit_user(...):
#     ...
#     return templates.TemplateResponse(
#         "admin_edit_user.html",
#         {
#             "request": request,
#             "user": user,
#             "error": "Something went wrong"  # optional
#         }
#     )