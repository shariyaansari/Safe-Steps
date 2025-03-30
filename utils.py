import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from models import Incident, db
from sqlalchemy import func, extract
import json
import os
from datetime import datetime
from flask import current_app

def get_crime_data_by_area(days=30):
    """Get crime data grouped by area for the last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query incidents grouped by area
    result = db.session.query(
        Incident.area,
        func.count(Incident.id).label('count')
    ).filter(
        Incident.incident_date >= cutoff_date
    ).group_by(
        Incident.area
    ).all()
    
    # Convert to dictionary
    area_data = {area: count for area, count in result}
    
    return area_data

def get_crime_trend_by_month(area=None, months=6):
    """Get monthly crime trends for the last N months"""
    # Calculate the date N months ago
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months)
    
    # Base query
    query = db.session.query(
        extract('year', Incident.incident_date).label('year'),
        extract('month', Incident.incident_date).label('month'),
        func.count(Incident.id).label('count')
    ).filter(
        Incident.incident_date >= start_date,
        Incident.incident_date <= end_date
    )
    
    # Add area filter if specified
    if area:
        query = query.filter(Incident.area == area)
    
    # Group by year and month
    result = query.group_by(
        extract('year', Incident.incident_date),
        extract('month', Incident.incident_date)
    ).order_by(
        extract('year', Incident.incident_date),
        extract('month', Incident.incident_date)
    ).all()
    
    # Create a list of all months in the range
    all_months = []
    current_date = start_date
    while current_date <= end_date:
        all_months.append((current_date.year, current_date.month))
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Convert query results to dictionary with all months
    trend_data = {(year, month): 0 for year, month in all_months}
    for year, month, count in result:
        trend_data[(int(year), int(month))] = count
    
    # Sort by date and format for display
    sorted_data = sorted(trend_data.items())
    labels = [f"{month_name[m][:3]} {y}" for (y, m), _ in sorted_data]
    values = [count for _, count in sorted_data]
    
    return labels, values

def get_crime_types_distribution(area=None, days=30):
    """Get distribution of crime types for the last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Base query
    query = db.session.query(
        Incident.incident_type,
        func.count(Incident.id).label('count')
    ).filter(
        Incident.incident_date >= cutoff_date
    )
    
    # Add area filter if specified
    if area:
        query = query.filter(Incident.area == area)
    
    # Group by incident type
    result = query.group_by(
        Incident.incident_type
    ).order_by(
        func.count(Incident.id).desc()
    ).all()
    
    # Convert to lists for plotting
    types = [incident_type for incident_type, _ in result]
    counts = [count for _, count in result]
    
    return types, counts

def get_kurla_areas():
    """Get list of areas in Kurla from incidents"""
    areas = db.session.query(Incident.area).distinct().all()
    return [area[0] for area in areas if 'kurla' in area[0].lower()]

def generate_crime_heatmap(days=30):
    """Generate a heatmap of crime incidents"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Query incidents with coordinates
    incidents = Incident.query.filter(
        Incident.incident_date >= cutoff_date,
        Incident.latitude.isnot(None),
        Incident.longitude.isnot(None)
    ).all()
    
    # Extract data for heatmap
    locations = []
    for incident in incidents:
        locations.append({
            'lat': incident.latitude,
            'lon': incident.longitude,
            'type': incident.incident_type,
            'date': incident.incident_date.strftime('%Y-%m-%d')
        })
    
    return json.dumps(locations)

# Helper for month names
month_name = {
    1: 'January', 2: 'February', 3: 'March', 4: 'April',
    5: 'May', 6: 'June', 7: 'July', 8: 'August',
    9: 'September', 10: 'October', 11: 'November', 12: 'December'
}

def generate_analytics_data(area=None, is_admin=False):
    """Generate all analytics data needed for the dashboard"""
    # Get crime data by area
    area_data = get_crime_data_by_area(days=90)
    
    # Get crime trend data
    trend_labels, trend_values = get_crime_trend_by_month(area=area, months=6)
    
    # Get crime types distribution
    type_labels, type_values = get_crime_types_distribution(area=area, days=90)
    
    # Get list of Kurla areas
    kurla_areas = get_kurla_areas()
    
    # Generate heatmap data
    heatmap_data = generate_crime_heatmap(days=90)
    
    # Calculate month-over-month change
    if len(trend_values) >= 2:
        current_month = trend_values[-1]
        previous_month = trend_values[-2]
        if previous_month > 0:
            percent_change = ((current_month - previous_month) / previous_month) * 100
        else:
            percent_change = 100 if current_month > 0 else 0
    else:
        percent_change = 0
    
    # Additional data for admin
    admin_data = {}
    if is_admin:
        # Get total incidents
        total_incidents = sum(area_data.values())
        
        # Get recent incidents
        recent_incidents = Incident.query.order_by(
            Incident.reported_at.desc()
        ).limit(10).all()
        
        admin_data = {
            'total_incidents': total_incidents,
            'recent_incidents': recent_incidents
        }
    
    return {
        'area_data': area_data,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'type_labels': type_labels,
        'type_values': type_values,
        'kurla_areas': kurla_areas,
        'heatmap_data': heatmap_data,
        'percent_change': percent_change,
        'admin_data': admin_data
    }

