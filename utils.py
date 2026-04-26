import pandas as pd
import json
from datetime import datetime, timedelta
from models import Incident
from sqlalchemy import func, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_crime_data_by_area(db: AsyncSession, days=30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stmt = select(
        Incident.area,
        func.count(Incident.id).label('count')
    ).filter(Incident.incident_date >= cutoff_date).group_by(Incident.area)
    
    result = await db.execute(stmt)
    return {area: count for area, count in result.all()}

async def get_crime_trend_by_month(db: AsyncSession, area=None, months=6):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    stmt = select(
        extract('year', Incident.incident_date).label('year'),
        extract('month', Incident.incident_date).label('month'),
        func.count(Incident.id).label('count')
    ).filter(
        Incident.incident_date >= start_date,
        Incident.incident_date <= end_date
    )
    
    if area:
        stmt = stmt.filter(Incident.area == area)
        
    stmt = stmt.group_by(
        extract('year', Incident.incident_date),
        extract('month', Incident.incident_date)
    ).order_by(
        extract('year', Incident.incident_date),
        extract('month', Incident.incident_date)
    )
    
    result = await db.execute(stmt)
    # simplified return
    return {"labels": [], "values": []}

async def get_crime_types_distribution(db: AsyncSession, area=None, days=30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stmt = select(
        Incident.incident_type,
        func.count(Incident.id).label('count')
    ).filter(Incident.incident_date >= cutoff_date)
    
    if area:
        stmt = stmt.filter(Incident.area == area)
        
    stmt = stmt.group_by(Incident.incident_type).order_by(func.count(Incident.id).desc())
    result = await db.execute(stmt)
    types = []
    counts = []
    for inc_type, count in result.all():
        types.append(inc_type)
        counts.append(count)
    return types, counts

async def generate_crime_heatmap(db: AsyncSession, days=30):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    # With PostGIS, ST_Y and ST_X extract lat and lon
    stmt = select(
        func.ST_Y(Incident.geom).label('lat'),
        func.ST_X(Incident.geom).label('lon'),
        Incident.incident_type,
        Incident.incident_date
    ).filter(
        Incident.incident_date >= cutoff_date,
        Incident.geom.isnot(None)
    )
    
    result = await db.execute(stmt)
    locations = []
    for lat, lon, inc_type, inc_date in result.all():
        locations.append({
            'lat': lat,
            'lon': lon,
            'type': inc_type,
            'date': inc_date.strftime('%Y-%m-%d')
        })
    return json.dumps(locations)

async def generate_analytics_data(db: AsyncSession, area=None, is_admin=False):
    area_data = await get_crime_data_by_area(db, days=90)
    type_labels, type_values = await get_crime_types_distribution(db, area=area, days=90)
    heatmap_data = await generate_crime_heatmap(db, days=90)
    
    admin_data = {}
    if is_admin:
        total_incidents = sum(area_data.values())
        admin_data = {'total_incidents': total_incidents}
        
    return {
        'area_data': area_data,
        'type_labels': type_labels,
        'type_values': type_values,
        'heatmap_data': heatmap_data,
        'admin_data': admin_data
    }
