# import logging
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import json
# from datetime import datetime, timedelta
# from models import Incident, db
# from sqlalchemy import func, extract
# import json
# from flask import current_app
# import os
# import json
# import numpy as np
# from collections import Counter

# # Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# def get_crime_data_by_area(days=30):
#     """Get crime data grouped by area for the last N days"""
#     cutoff_date = datetime.utcnow() - timedelta(days=days)
    
#     # Query incidents grouped by area
#     result = db.session.query(
#         Incident.area,
#         func.count(Incident.id).label('count')
#     ).filter(
#         Incident.incident_date >= cutoff_date
#     ).group_by(
#         Incident.area
#     ).all()
    
#     # Convert to dictionary
#     area_data = {area: count for area, count in result}
    
#     return area_data

# def get_crime_trend_by_month(area=None, months=6):
#     """Get monthly crime trends for the last N months"""
#     # Calculate the date N months ago
#     end_date = datetime.utcnow()
#     start_date = end_date - timedelta(days=30 * months)
    
#     # Base query
#     query = db.session.query(
#         extract('year', Incident.incident_date).label('year'),
#         extract('month', Incident.incident_date).label('month'),
#         func.count(Incident.id).label('count')
#     ).filter(
#         Incident.incident_date >= start_date,
#         Incident.incident_date <= end_date
#     )
    
#     # Add area filter if specified
#     if area:
#         query = query.filter(Incident.area == area)
    
#     # Group by year and month
#     result = query.group_by(
#         extract('year', Incident.incident_date),
#         extract('month', Incident.incident_date)
#     ).order_by(
#         extract('year', Incident.incident_date),
#         extract('month', Incident.incident_date)
#     ).all()
    
#     # Create a list of all months in the range
#     all_months = []
#     current_date = start_date
#     while current_date <= end_date:
#         all_months.append((current_date.year, current_date.month))
#         # Move to next month
#         if current_date.month == 12:
#             current_date = current_date.replace(year=current_date.year + 1, month=1)
#         else:
#             current_date = current_date.replace(month=current_date.month + 1)
    
#     # Convert query results to dictionary with all months
#     trend_data = {(year, month): 0 for year, month in all_months}
#     for year, month, count in result:
#         trend_data[(int(year), int(month))] = count
    
#     # Sort by date and format for display
#     sorted_data = sorted(trend_data.items())
#     labels = [f"{month_name[m][:3]} {y}" for (y, m), _ in sorted_data]
#     values = [count for _, count in sorted_data]
    
#     return labels, values

# def get_crime_types_distribution(area=None, days=30):
#     """Get distribution of crime types for the last N days"""
#     cutoff_date = datetime.utcnow() - timedelta(days=days)
    
#     # Base query
#     query = db.session.query(
#         Incident.incident_type,
#         func.count(Incident.id).label('count')
#     ).filter(
#         Incident.incident_date >= cutoff_date
#     )
    
#     # Add area filter if specified
#     if area:
#         query = query.filter(Incident.area == area)
    
#     # Group by incident type
#     result = query.group_by(
#         Incident.incident_type
#     ).order_by(
#         func.count(Incident.id).desc()
#     ).all()
    
#     # Convert to lists for plotting
#     types = [incident_type for incident_type, _ in result]
#     counts = [count for _, count in result]
    
#     return types, counts

# def get_kurla_areas():
#     """Get list of areas in Kurla from incidents"""
#     areas = db.session.query(Incident.area).distinct().all()
#     return [area[0] for area in areas if 'kurla' in area[0].lower()]

# def generate_crime_heatmap(days=30):
#     """Generate a heatmap of crime incidents"""
#     cutoff_date = datetime.utcnow() - timedelta(days=days)
    
#     # Query incidents with coordinates
#     incidents = Incident.query.filter(
#         Incident.incident_date >= cutoff_date,
#         Incident.latitude.isnot(None),
#         Incident.longitude.isnot(None)
#     ).all()
    
#     # Extract data for heatmap
#     locations = []
#     for incident in incidents:
#         locations.append({
#             'lat': incident.latitude,
#             'lon': incident.longitude,
#             'type': incident.incident_type,
#             'date': incident.incident_date.strftime('%Y-%m-%d')
#         })
    
#     return json.dumps(locations)

# # Helper for month names
# month_name = {
#     1: 'January', 2: 'February', 3: 'March', 4: 'April',
#     5: 'May', 6: 'June', 7: 'July', 8: 'August',
#     9: 'September', 10: 'October', 11: 'November', 12: 'December'
# }


# def generate_analytics_data(area=None, is_admin=False):
#     """Generate analytics data for the dashboard"""
#     try:
#         # Define Kurla areas
#         kurla_areas = [
#             "Kurla West", "Kurla East", "Kurla Station", "BKC", "Nehru Nagar", 
#             "Tilak Nagar", "Chunabhatti", "Chembur", "Saki Naka", "Asalpha", 
#             "Vinoba Bhave Nagar", "LBS Marg", "Kamani", "Premier Colony", 
#             "Kalina", "Santacruz East", "Vidyavihar", "Lokmanya Tilak Terminus", 
#             "Sion", "Jarimari", "Safed Pool"
#         ]
        
#         # Get data from map data file
#         map_data_path = os.path.join('static', 'data', 'map', 'crime_map_data.json')
#         area_data = {}
        
#         if os.path.exists(map_data_path):
#             with open(map_data_path, 'r') as f:
#                 map_data = json.load(f)
            
#             # Extract area data
#             for marker in map_data.get('markers', []):
#                 area_name = marker['title']
#                 area_data[area_name] = marker['incidents']
#         else:
#             # Generate dummy data if file doesn't exist
#             for area_name in kurla_areas:
#                 area_data[area_name] = np.random.randint(1, 10)
        
#         # Filter by selected area if specified
#         filtered_area_data = {}
#         if area:
#             for k, v in area_data.items():
#                 if area.lower() in k.lower() or k.lower() in area.lower():
#                     filtered_area_data[k] = v
            
#             if filtered_area_data:
#                 area_data = filtered_area_data
        
#         # Generate monthly trend data (last 6 months)
#         now = datetime.datetime.now()
#         trend_labels = []
#         for i in range(5, -1, -1):
#             month = now.month - i
#             year = now.year
#             if month <= 0:
#                 month += 12
#                 year -= 1
#             trend_labels.append(datetime.datetime(year, month, 1).strftime("%b %Y"))
        
#         # Generate trend values
#         trend_values = []
#         for _ in trend_labels:
#             # Generate random values with an upward trend
#             if not trend_values:
#                 trend_values.append(np.random.randint(5, 15))
#             else:
#                 # Add some randomness but maintain a general trend
#                 change = np.random.randint(-3, 5)  # More likely to increase
#                 new_value = max(1, trend_values[-1] + change)
#                 trend_values.append(new_value)
        
#         # Calculate percent change
#         if len(trend_values) >= 2 and trend_values[-2] > 0:
#             percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
#         else:
#             percent_change = 0
        
#         # Try to load crime data from reports
#         reports_data = []
#         reports_path = os.path.join('static', 'data', 'reports', 'reports.json')
        
#         if os.path.exists(reports_path):
#             try:
#                 with open(reports_path, 'r') as f:
#                     reports_data = json.load(f)
#             except Exception as e:
#                 logger.error(f"Error loading reports data: {str(e)}")
        
#         # Extract crime types from reports
#         crime_types_from_reports = {}
#         if reports_data:
#             crime_types_counter = Counter([report.get('crime_type', 'Other') for report in reports_data])
#             crime_types_from_reports = dict(crime_types_counter)
        
#         # If no reports data, generate dummy crime types data
#         if not crime_types_from_reports:
#             crime_types_from_reports = {
#                 "Theft": np.random.randint(10, 30),
#                 "Assault": np.random.randint(5, 15),
#                 "Robbery": np.random.randint(3, 12),
#                 "Vandalism": np.random.randint(2, 10),
#                 "Other": np.random.randint(5, 20)
#             }
        
#         # Sort crime types by count (descending)
#         sorted_types = sorted(crime_types_from_reports.items(), key=lambda x: x[1], reverse=True)
#         type_labels = [item[0] for item in sorted_types]
#         type_values = [item[1] for item in sorted_types]
        
#         # Generate heatmap data
#         heatmap_data = []
#         for area_name, count in area_data.items():
#             # Find coordinates for this area
#             for marker in map_data.get('markers', []) if 'markers' in map_data else []:
#                 if marker['title'] == area_name:
#                     heatmap_data.append({
#                         "lat": marker['position']['lat'],
#                         "lng": marker['position']['lng'],
#                         "weight": count
#                     })
#                     break
        
#         # Calculate total reports
#         total_reports = sum(area_data.values())
        
#         # Calculate high risk areas (areas with incident count > 7)
#         high_risk_areas = sum(1 for count in area_data.values() if count > 7)
        
#         # Calculate average daily reports (assuming data is for a month)
#         avg_daily_reports = round(total_reports / 30, 1)
        
#         # Find most common crime
#         most_common_crime = type_labels[0] if type_labels else "None"
#         most_common_percent = round((type_values[0] / sum(type_values) * 100) if type_values and sum(type_values) > 0 else 0)
        
#         # Return all the data
#         return {
#             "kurla_areas": kurla_areas,
#             "area_data": area_data,
#             "trend_labels": trend_labels,
#             "trend_values": trend_values,
#             "type_labels": type_labels,
#             "type_values": type_values,
#             "heatmap_data": heatmap_data,
#             "percent_change": percent_change,
#             "total_reports": total_reports,
#             "high_risk_areas": high_risk_areas,
#             "avg_daily_reports": avg_daily_reports,
#             "most_common_crime": most_common_crime,
#             "most_common_percent": most_common_percent
#         }
#     except Exception as e:
#         logger.error(f"Error generating analytics data: {str(e)}")
#         # Return empty data in case of error
#         return {
#             "kurla_areas": [],
#             "area_data": {},
#             "trend_labels": [],
#             "trend_values": [],
#             "type_labels": [],
#             "type_values": [],
#             "heatmap_data": [],
#             "percent_change": 0,
#             "total_reports": 0,
#             "high_risk_areas": 0,
#             "avg_daily_reports": 0,
#             "most_common_crime": "None",
#             "most_common_percent": 0
#         }

import os
import json
import pandas as pd
import numpy as np
import datetime
import logging
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_analytics_data(area=None, is_admin=False):
    """Generate analytics data for the dashboard"""
    try:
        # Define Kurla areas
        kurla_areas = [
            "Kurla West", "Kurla East", "Kurla Station", "BKC", "Nehru Nagar", 
            "Tilak Nagar", "Chunabhatti", "Chembur", "Saki Naka", "Asalpha", 
            "Vinoba Bhave Nagar", "LBS Marg", "Kamani", "Premier Colony", 
            "Kalina", "Santacruz East", "Vidyavihar", "Lokmanya Tilak Terminus", 
            "Sion", "Jarimari", "Safed Pool"
        ]
        
        # Get data from map data file
        map_data_path = os.path.join('static', 'data', 'map', 'crime_map_data.json')
        area_data = {}
        
        if os.path.exists(map_data_path):
            with open(map_data_path, 'r') as f:
                map_data = json.load(f)
            
            # Extract area data
            for marker in map_data.get('markers', []):
                area_name = marker['title']
                area_data[area_name] = marker['incidents']
        else:
            # Generate dummy data if file doesn't exist
            for area_name in kurla_areas:
                area_data[area_name] = np.random.randint(1, 10)
        
        # Filter by selected area if specified
        filtered_area_data = {}
        if area:
            for k, v in area_data.items():
                if area.lower() in k.lower() or k.lower() in area.lower():
                    filtered_area_data[k] = v
            
            if filtered_area_data:
                area_data = filtered_area_data
        
        # Generate monthly trend data (last 6 months)
        now = datetime.datetime.now()
        trend_labels = []
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            trend_labels.append(datetime.datetime(year, month, 1).strftime("%b %Y"))
        
        # Generate trend values
        trend_values = []
        for _ in trend_labels:
            # Generate random values with an upward trend
            if not trend_values:
                trend_values.append(np.random.randint(5, 15))
            else:
                # Add some randomness but maintain a general trend
                change = np.random.randint(-3, 5)  # More likely to increase
                new_value = max(1, trend_values[-1] + change)
                trend_values.append(new_value)
        
        # Calculate percent change
        if len(trend_values) >= 2 and trend_values[-2] > 0:
            percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
        else:
            percent_change = 0
        
        # Try to load crime data from reports
        reports_data = []
        reports_path = os.path.join('static', 'data', 'reports', 'reports.json')
        
        if os.path.exists(reports_path):
            try:
                with open(reports_path, 'r') as f:
                    reports_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading reports data: {str(e)}")
        
        # Extract crime types from reports
        crime_types_from_reports = {}
        if reports_data:
            crime_types_counter = Counter([report.get('crime_type', 'Other') for report in reports_data])
            crime_types_from_reports = dict(crime_types_counter)
        
        # If no reports data, generate dummy crime types data
        if not crime_types_from_reports:
            crime_types_from_reports = {
                "Theft": np.random.randint(10, 30),
                "Assault": np.random.randint(5, 15),
                "Robbery": np.random.randint(3, 12),
                "Vandalism": np.random.randint(2, 10),
                "Other": np.random.randint(5, 20)
            }
        
        # Sort crime types by count (descending)
        sorted_types = sorted(crime_types_from_reports.items(), key=lambda x: x[1], reverse=True)
        type_labels = [item[0] for item in sorted_types]
        type_values = [item[1] for item in sorted_types]
        
        # Generate heatmap data
        heatmap_data = []
        for area_name, count in area_data.items():
            # Find coordinates for this area
            for marker in map_data.get('markers', []) if 'markers' in map_data else []:
                if marker['title'] == area_name:
                    heatmap_data.append({
                        "lat": marker['position']['lat'],
                        "lng": marker['position']['lng'],
                        "weight": count
                    })
                    break
        
        # Calculate total reports
        total_reports = sum(area_data.values())
        
        # Calculate high risk areas (areas with incident count > 7)
        high_risk_areas = sum(1 for count in area_data.values() if count > 7)
        
        # Calculate average daily reports (assuming data is for a month)
        avg_daily_reports = round(total_reports / 30, 1)
        
        # Find most common crime
        most_common_crime = type_labels[0] if type_labels else "None"
        most_common_percent = round((type_values[0] / sum(type_values) * 100) if type_values and sum(type_values) > 0 else 0)
        
        # Return all the data
        return {
            "kurla_areas": kurla_areas,
            "area_data": area_data,
            "trend_labels": trend_labels,
            "trend_values": trend_values,
            "type_labels": type_labels,
            "type_values": type_values,
            "heatmap_data": heatmap_data,
            "percent_change": percent_change,
            "total_reports": total_reports,
            "high_risk_areas": high_risk_areas,
            "avg_daily_reports": avg_daily_reports,
            "most_common_crime": most_common_crime,
            "most_common_percent": most_common_percent
        }
    except Exception as e:
        logger.error(f"Error generating analytics data: {str(e)}")
        # Return empty data in case of error
        return {
            "kurla_areas": [],
            "area_data": {},
            "trend_labels": [],
            "trend_values": [],
            "type_labels": [],
            "type_values": [],
            "heatmap_data": [],
            "percent_change": 0,
            "total_reports": 0,
            "high_risk_areas": 0,
            "avg_daily_reports": 0,
            "most_common_crime": "None",
            "most_common_percent": 0
        }
