
# import os
# import json
# import pandas as pd
# import numpy as np
# import datetime
# import logging
# from collections import Counter

# # Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

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







# import os
# import json
# import pandas as pd
# import numpy as np
# import datetime
# import logging
# import sqlite3
# from collections import Counter

# # Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

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
        
#         # Connect to the database
#         conn = sqlite3.connect('reports.db')
#         cursor = conn.cursor()
        
#         # Get all reports from the database
#         cursor.execute("SELECT * FROM reports")
#         db_reports = cursor.fetchall()
        
#         # Convert to list of dictionaries for easier processing
#         reports_data = []
#         for report in db_reports:
#             reports_data.append({
#                 'id': report[0],
#                 'date': report[1],
#                 'startTime': report[2],
#                 'endTime': report[3],
#                 'description': report[4],
#                 'lat': report[5],
#                 'lng': report[6],
#                 # Determine crime type from description (simple keyword matching)
#                 'crime_type': determine_crime_type(report[4])
#             })
        
#         # Get data from map data file for coordinates
#         map_data_path = os.path.join('static', 'data', 'map', 'crime_map_data.json')
#         area_data = {}
#         map_data = {}
        
#         if os.path.exists(map_data_path):
#             with open(map_data_path, 'r') as f:
#                 map_data = json.load(f)
        
#         # Count reports by area using coordinates
#         for report in reports_data:
#             # Find which area this report belongs to based on coordinates
#             area_name = find_area_by_coordinates(report['lat'], report['lng'], map_data, kurla_areas)
#             if area_name:
#                 area_data[area_name] = area_data.get(area_name, 0) + 1
        
#         # If no reports found, ensure all areas are represented with zero counts
#         for area_name in kurla_areas:
#             if area_name not in area_data:
#                 area_data[area_name] = 0
        
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
#         trend_values = []
        
#         for i in range(5, -1, -1):
#             month = now.month - i
#             year = now.year
#             if month <= 0:
#                 month += 12
#                 year -= 1
            
#             month_start = datetime.datetime(year, month, 1).strftime("%Y-%m-%d")
            
#             if month == 12:
#                 next_month = 1
#                 next_year = year + 1
#             else:
#                 next_month = month + 1
#                 next_year = year
            
#             month_end = datetime.datetime(next_year, next_month, 1).strftime("%Y-%m-%d")
            
#             # Count reports for this month
#             cursor.execute("SELECT COUNT(*) FROM reports WHERE date >= ? AND date < ?", 
#                           (month_start, month_end))
#             count = cursor.fetchone()[0]
            
#             trend_labels.append(datetime.datetime(year, month, 1).strftime("%b %Y"))
#             trend_values.append(count)
        
#         # Calculate percent change
#         if len(trend_values) >= 2 and trend_values[-2] > 0:
#             percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
#         else:
#             percent_change = 0
        
#         # Extract crime types from reports
#         crime_types_from_reports = {}
#         if reports_data:
#             crime_types_counter = Counter([report.get('crime_type', 'Other') for report in reports_data])
#             crime_types_from_reports = dict(crime_types_counter)
        
#         # If no reports data, ensure we have some default categories
#         if not crime_types_from_reports:
#             crime_types_from_reports = {
#                 "Theft": 0,
#                 "Assault": 0,
#                 "Robbery": 0,
#                 "Vandalism": 0,
#                 "Other": 0
#             }
        
#         # Sort crime types by count (descending)
#         sorted_types = sorted(crime_types_from_reports.items(), key=lambda x: x[1], reverse=True)
#         type_labels = [item[0] for item in sorted_types]
#         type_values = [item[1] for item in sorted_types]
        
#         # Generate heatmap data
#         heatmap_data = []
#         for report in reports_data:
#             heatmap_data.append({
#                 "lat": report['lat'],
#                 "lng": report['lng'],
#                 "weight": 1  # Each report has equal weight
#             })
        
#         # Calculate total reports
#         total_reports = len(reports_data)
        
#         # Calculate high risk areas (areas with incident count > 7)
#         high_risk_areas = sum(1 for count in area_data.values() if count > 7)
        
#         # Calculate average daily reports (for the last 30 days)
#         thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
#         cursor.execute("SELECT COUNT(*) FROM reports WHERE date >= ?", (thirty_days_ago,))
#         recent_reports = cursor.fetchone()[0]
#         avg_daily_reports = round(recent_reports / 30, 1)
        
#         # Close database connection
#         conn.close()
        
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

# def determine_crime_type(description):
#     """Determine crime type from description using keyword matching"""
#     description = description.lower() if description else ""
    
#     if any(word in description for word in ['theft', 'steal', 'stole', 'stolen']):
#         return "Theft"
#     elif any(word in description for word in ['assault', 'attack', 'beat', 'hit']):
#         return "Assault"
#     elif any(word in description for word in ['robbery', 'robbed', 'mugging']):
#         return "Robbery"
#     elif any(word in description for word in ['vandalism', 'damage', 'graffiti', 'break']):
#         return "Vandalism"
#     elif any(word in description for word in ['harassment', 'stalking', 'following']):
#         return "Harassment"
#     elif any(word in description for word in ['drug', 'substance']):
#         return "Drug-related"
#     else:
#         return "Other"

# def find_area_by_coordinates(lat, lng, map_data, kurla_areas):
#     """Find which area a report belongs to based on coordinates"""
#     if not lat or not lng:
#         return None
    
#     # First try to match with map data markers
#     if 'markers' in map_data:
#         # Find the closest marker
#         closest_marker = None
#         min_distance = float('inf')
        
#         for marker in map_data['markers']:
#             if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
#                 marker_lat = marker['position']['lat']
#                 marker_lng = marker['position']['lng']
                
#                 # Calculate distance (simple Euclidean distance)
#                 distance = ((lat - marker_lat) ** 2 + (lng - marker_lng) ** 2) ** 0.5
                
#                 if distance < min_distance:
#                     min_distance = distance
#                     closest_marker = marker
        
#         # If we found a close marker and it's within a reasonable distance
#         if closest_marker and min_distance < 0.01:  # Approximately 1km
#             return closest_marker['title']
    
#     # If no match found, return a default area
#     return "Kurla"

# import os
# import json
# import pandas as pd
# import numpy as np
# import datetime
# import logging
# import sqlite3
# from collections import Counter

# # Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

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
        
#         # Connect to the database
#         conn = sqlite3.connect('reports.db')
#         conn.row_factory = sqlite3.Row  # This allows accessing columns by name
#         cursor = conn.cursor()
        
#         # Get all reports from the database
#         cursor.execute("SELECT * FROM reports")
#         db_reports = cursor.fetchall()
        
#         # Convert to list of dictionaries for easier processing
#         reports_data = []
#         for report in db_reports:
#             reports_data.append({
#                 'id': report['id'],
#                 'date': report['date'],
#                 'startTime': report['startTime'],
#                 'endTime': report['endTime'],
#                 'description': report['description'],
#                 'lat': report['lat'],
#                 'lng': report['lng'],
#                 # Determine crime type from description
#                 'crime_type': determine_crime_type(report['description']),
#                 'source': 'user_report'
#             })
        
#         # Load analyzed news articles data
#         news_analysis_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
#         news_incidents = []
        
#         if os.path.exists(news_analysis_path):
#             try:
#                 with open(news_analysis_path, 'r') as f:
#                     news_analysis = json.load(f)
                    
#                 # Extract incidents from news analysis
#                 if 'recent_incidents' in news_analysis:
#                     for incident in news_analysis['recent_incidents']:
#                         # Convert news incidents to a format similar to reports
#                         news_incidents.append({
#                             'id': 'news_' + str(len(news_incidents)),
#                             'date': incident.get('date', datetime.datetime.now().strftime("%Y-%m-%d")),
#                             'description': incident.get('title', ''),
#                             'location': incident.get('location', 'Kurla'),
#                             'crime_type': incident.get('category', 'Other'),
#                             'source': incident.get('source', 'News'),
#                             'url': incident.get('url', ''),
#                             'source_type': 'news'
#                         })
#             except Exception as e:
#                 logger.error(f"Error loading news analysis data: {str(e)}")
        
#         # Get data from map data file for area coordinates
#         map_data_path = os.path.join('static', 'data', 'map', 'crime_map_data.json')
#         area_data = {area: 0 for area in kurla_areas}  # Initialize all areas with zero count
#         map_data = {}
        
#         if os.path.exists(map_data_path):
#             with open(map_data_path, 'r') as f:
#                 map_data = json.load(f)
        
#         # Count reports by area using coordinates
#         for report in reports_data:
#             # Find which area this report belongs to based on coordinates
#             area_name = find_area_by_coordinates(report['lat'], report['lng'], map_data, kurla_areas)
#             if area_name:
#                 area_data[area_name] = area_data.get(area_name, 0) + 1
        
#         # Add news incidents to area counts
#         for incident in news_incidents:
#             location = incident.get('location', '')
#             # Map location name to standardized area name
#             area_name = map_location_to_area(location, kurla_areas)
#             if area_name:
#                 area_data[area_name] = area_data.get(area_name, 0) + 1
        
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
#         trend_values = []
        
#         for i in range(5, -1, -1):
#             month = now.month - i
#             year = now.year
#             if month <= 0:
#                 month += 12
#                 year -= 1
            
#             month_start = datetime.datetime(year, month, 1).strftime("%Y-%m-%d")
            
#             if month == 12:
#                 next_month = 1
#                 next_year = year + 1
#             else:
#                 next_month = month + 1
#                 next_year = year
            
#             month_end = datetime.datetime(next_year, next_month, 1).strftime("%Y-%m-%d")
            
#             # Count reports for this month from database
#             cursor.execute("SELECT COUNT(*) FROM reports WHERE date >= ? AND date < ?", 
#                           (month_start, month_end))
#             db_count = cursor.fetchone()[0]
            
#             # Count news incidents for this month
#             news_count = sum(1 for incident in news_incidents 
#                             if month_start <= incident.get('date', '') < month_end)
            
#             # Total count for the month
#             total_count = db_count + news_count
            
#             trend_labels.append(datetime.datetime(year, month, 1).strftime("%b %Y"))
#             trend_values.append(total_count)
        
#         # Calculate percent change
#         if len(trend_values) >= 2 and trend_values[-2] > 0:
#             percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
#         else:
#             percent_change = 0
        
#         # Combine reports and news incidents for crime type analysis
#         all_incidents = reports_data + news_incidents
        
#         # Extract crime types from all incidents
#         crime_types = {}
#         if all_incidents:
#             crime_types_counter = Counter([incident.get('crime_type', 'Other') for incident in all_incidents])
#             crime_types = dict(crime_types_counter)
        
#         # If no incidents data, ensure we have some default categories
#         if not crime_types:
#             crime_types = {
#                 "Theft": 0,
#                 "Assault": 0,
#                 "Robbery": 0,
#                 "Vandalism": 0,
#                 "Other": 0
#             }
        
#         # Sort crime types by count (descending)
#         sorted_types = sorted(crime_types.items(), key=lambda x: x[1], reverse=True)
#         type_labels = [item[0] for item in sorted_types]
#         type_values = [item[1] for item in sorted_types]
        
#         # Generate heatmap data
#         heatmap_data = []
        
#         # Add database reports to heatmap
#         for report in reports_data:
#             if report['lat'] and report['lng']:
#                 heatmap_data.append({
#                     "lat": report['lat'],
#                     "lng": report['lng'],
#                     "weight": 1  # Each report has equal weight
#                 })
        
#         # Add news incidents to heatmap (if we can get coordinates)
#         for incident in news_incidents:
#             location = incident.get('location', '')
#             coords = get_coordinates_for_location(location, map_data)
#             if coords:
#                 heatmap_data.append({
#                     "lat": coords['lat'],
#                     "lng": coords['lng'],
#                     "weight": 1
#                 })
        
#         # Calculate total incidents
#         total_reports = len(all_incidents)
        
#         # Calculate high risk areas (areas with incident count > 7)
#         high_risk_areas = sum(1 for count in area_data.values() if count > 7)
        
#         # Calculate average daily reports (for the last 30 days)
#         thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
#         # Count database reports in last 30 days
#         cursor.execute("SELECT COUNT(*) FROM reports WHERE date >= ?", (thirty_days_ago,))
#         recent_db_reports = cursor.fetchone()[0]
        
#         # Count news incidents in last 30 days
#         recent_news_incidents = sum(1 for incident in news_incidents 
#                                   if incident.get('date', '') >= thirty_days_ago)
        
#         # Total recent incidents
#         recent_incidents_count = recent_db_reports + recent_news_incidents
#         avg_daily_reports = round(recent_incidents_count / 30, 1)
        
#         # Close database connection
#         conn.close()
        
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

# def determine_crime_type(description):
#     """Determine crime type from description using keyword matching"""
#     if not description:
#         return "Other"
        
#     description = description.lower()
    
#     if any(word in description for word in ['theft', 'steal', 'stole', 'stolen', 'pickpocket']):
#         if any(word in description for word in ['vehicle', 'car', 'bike', 'motorcycle', 'auto']):
#             return "Vehicle Theft"
#         return "Theft"
#     elif any(word in description for word in ['assault', 'attack', 'beat', 'hit', 'fight', 'violence']):
#         return "Assault"
#     elif any(word in description for word in ['robbery', 'robbed', 'mugging', 'snatching']):
#         return "Robbery"
#     elif any(word in description for word in ['vandalism', 'damage', 'graffiti', 'break', 'destroy']):
#         return "Vandalism"
#     elif any(word in description for word in ['harassment', 'stalking', 'following', 'eve teasing']):
#         return "Harassment"
#     elif any(word in description for word in ['drug', 'substance', 'alcohol', 'drunk']):
#         return "Drug-related"
#     elif any(word in description for word in ['fraud', 'scam', 'cheat', 'deceive']):
#         return "Fraud"
#     elif any(word in description for word in ['murder', 'kill', 'homicide', 'death']):
#         return "Murder"
#     elif any(word in description for word in ['kidnap', 'abduct', 'missing']):
#         return "Kidnapping"
#     else:
#         return "Other"

# def find_area_by_coordinates(lat, lng, map_data, kurla_areas):
#     """Find which area a report belongs to based on coordinates"""
#     if not lat or not lng:
#         return "Kurla"
    
#     # First try to match with map data markers
#     if 'markers' in map_data:
#         # Find the closest marker
#         closest_marker = None
#         min_distance = float('inf')
        
#         for marker in map_data['markers']:
#             if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
#                 marker_lat = marker['position']['lat']
#                 marker_lng = marker['position']['lng']
                
#                 # Calculate distance (simple Euclidean distance)
#                 distance = ((lat - marker_lat) ** 2 + (lng - marker_lng) ** 2) ** 0.5
                
#                 if distance < min_distance:
#                     min_distance = distance
#                     closest_marker = marker
        
#         # If we found a close marker and it's within a reasonable distance
#         if closest_marker and min_distance < 0.01:  # Approximately 1km
#             return closest_marker['title']
    
#     # If no match found, return a default area
#     return "Kurla"

# def map_location_to_area(location, kurla_areas):
#     """Map a location name to a standardized area name"""
#     if not location:
#         return "Kurla"
    
#     location = location.lower()
    
#     # Direct mapping for common locations
#     location_mapping = {
#         'kurla west': 'Kurla West',
#         'kurla east': 'Kurla East',
#         'kurla station': 'Kurla Station',
#         'bkc': 'BKC',
#         'nehru nagar': 'Nehru Nagar',
#         'tilak nagar': 'Tilak Nagar',
#         'chunabhatti': 'Chunabhatti',
#         'chembur': 'Chembur',
#         'saki naka': 'Saki Naka',
#         'asalpha': 'Asalpha',
#         'vinoba bhave nagar': 'Vinoba Bhave Nagar',
#         'lbs marg': 'LBS Marg',
#         'kamani': 'Kamani',
#         'premier colony': 'Premier Colony',
#         'kalina': 'Kalina',
#         'santacruz east': 'Santacruz East',
#         'vidyavihar': 'Vidyavihar',
#         'lokmanya tilak terminus': 'Lokmanya Tilak Terminus',
#         'sion': 'Sion',
#         'jarimari': 'Jarimari',
#         'safed pool': 'Safed Pool'
#     }
    
#     # Check for direct match
#     if location in location_mapping:
#         return location_mapping[location]
    
#     # Check for partial match
#     for area_key, area_name in location_mapping.items():
#         if area_key in location or location in area_key:
#             return area_name
    
#     # Check against standard area list
#     for area in kurla_areas:
#         if area.lower() in location or location in area.lower():
#             return area
    
#     # Default to Kurla if no match found
#     return "Kurla"

# def get_coordinates_for_location(location, map_data):
#     """Get coordinates for a location based on map data"""
#     if not location or not map_data or 'markers' not in map_data:
#         return None
    
#     location = location.lower()
    
#     # Try to find exact match
#     for marker in map_data['markers']:
#         if 'title' in marker and marker['title'].lower() == location:
#             if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
#                 return {
#                     'lat': marker['position']['lat'],
#                     'lng': marker['position']['lng']
#                 }
    
#     # Try to find partial match
#     for marker in map_data['markers']:
#         if 'title' in marker and (marker['title'].lower() in location or location in marker['title'].lower()):
#             if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
#                 return {
#                     'lat': marker['position']['lat'],
#                     'lng': marker['position']['lng']
#                 }
    
#     # If no match found, return coordinates for Kurla (default)
#     for marker in map_data['markers']:
#         if 'title' in marker and marker['title'] == 'Kurla':
#             if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
#                 return {
#                     'lat': marker['position']['lat'],
#                     'lng': marker['position']['lng']
#                 }
    
#     # If still no match, return None
#     return None


import os
import json
import pandas as pd
import numpy as np
import datetime
import logging
import sqlite3
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
        
        # Initialize data structures
        area_data = {area: 0 for area in kurla_areas}
        crime_types = {
            "Theft": 0,
            "Vehicle Theft": 0,
            "Assault": 0,
            "Robbery": 0,
            "Vandalism": 0,
            "Harassment": 0,
            "Drug-related": 0,
            "Fraud": 0,
            "Murder": 0,
            "Kidnapping": 0,
            "Other": 0
        }
        
        # Get data from map data file for area coordinates
        map_data_path = os.path.join('static', 'data', 'map', 'crime_map_data.json')
        map_data = {}
        
        if os.path.exists(map_data_path):
            try:
                with open(map_data_path, 'r') as f:
                    map_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading map data: {str(e)}")
        
        # Initialize heatmap data and trend data
        heatmap_data = []
        now = datetime.datetime.now()
        trend_labels = []
        trend_values = [0, 0, 0, 0, 0, 0]  # Initialize with zeros
        
        # Generate trend labels (last 6 months)
        for i in range(5, -1, -1):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            trend_labels.append(datetime.datetime(year, month, 1).strftime("%b %Y"))
        
        # 1. Process database reports
        try:
            # Connect to the database
            conn = sqlite3.connect('reports.db')
            cursor = conn.cursor()
            
            # Get all reports from the database
            cursor.execute("SELECT id, date, description, lat, lng FROM reports")
            db_reports = cursor.fetchall()
            
            # Process each report
            for report in db_reports:
                report_id, date_str, description, lat, lng = report
                
                # Determine crime type
                crime_type = determine_crime_type(description)
                crime_types[crime_type] = crime_types.get(crime_type, 0) + 1
                
                # Add to area data
                if lat and lng:
                    area_name = find_area_by_coordinates(lat, lng, map_data, kurla_areas)
                    area_data[area_name] = area_data.get(area_name, 0) + 1
                    
                    # Add to heatmap
                    heatmap_data.append({
                        "lat": lat,
                        "lng": lng,
                        "weight": 1
                    })
                
                # Add to trend data
                if date_str:
                    try:
                        report_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        for i, label in enumerate(trend_labels):
                            label_date = datetime.datetime.strptime(label, "%b %Y")
                            if report_date.year == label_date.year and report_date.month == label_date.month:
                                trend_values[i] += 1
                                break
                    except Exception as e:
                        logger.error(f"Error parsing date {date_str}: {str(e)}")
            
            conn.close()
        except Exception as e:
            logger.error(f"Error processing database reports: {str(e)}")
        
        # 2. Process news article analysis
        try:
            news_analysis_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
            
            if os.path.exists(news_analysis_path):
                with open(news_analysis_path, 'r') as f:
                    news_analysis = json.load(f)
                
                # Add crime categories from news
                if 'crime_categories' in news_analysis:
                    for crime_type, count in news_analysis['crime_categories'].items():
                        # Map news crime types to our standardized types
                        mapped_type = map_crime_type(crime_type)
                        crime_types[mapped_type] = crime_types.get(mapped_type, 0) + count
                
                # Add crime locations from news
                if 'crime_locations' in news_analysis:
                    for location, count in news_analysis['crime_locations'].items():
                        # Map news locations to our standardized areas
                        area_name = map_location_to_area(location, kurla_areas)
                        area_data[area_name] = area_data.get(area_name, 0) + count
                
                # Process recent incidents for trend data
                if 'recent_incidents' in news_analysis:
                    for incident in news_analysis['recent_incidents']:
                        if 'date' in incident:
                            try:
                                # Try different date formats
                                incident_date = None
                                date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]
                                
                                for fmt in date_formats:
                                    try:
                                        incident_date = datetime.datetime.strptime(incident['date'], fmt)
                                        break
                                    except:
                                        continue
                                
                                if incident_date:
                                    for i, label in enumerate(trend_labels):
                                        label_date = datetime.datetime.strptime(label, "%b %Y")
                                        if incident_date.year == label_date.year and incident_date.month == label_date.month:
                                            trend_values[i] += 1
                                            break
                            except Exception as e:
                                logger.error(f"Error parsing incident date: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing news analysis: {str(e)}")
        
        # Filter by selected area if specified
        filtered_area_data = {}
        if area:
            for k, v in area_data.items():
                if area.lower() in k.lower() or k.lower() in area.lower():
                    filtered_area_data[k] = v
                    
            if filtered_area_data:
                area_data = filtered_area_data
        
        # Calculate percent change
        if len(trend_values) >= 2 and trend_values[-2] > 0:
            percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
        else:
            percent_change = 0
        
        # Sort crime types by count (descending)
        sorted_types = sorted(crime_types.items(), key=lambda x: x[1], reverse=True)
        type_labels = [item[0] for item in sorted_types]
        type_values = [item[1] for item in sorted_types]
        
        # Calculate total reports
        total_reports = sum(type_values)
        
        # Calculate high risk areas (areas with incident count > 7)
        high_risk_areas = sum(1 for count in area_data.values() if count > 7)
        
        # Calculate average daily reports (assuming data is for the last 30 days)
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

def determine_crime_type(description):
    """Determine crime type from description using keyword matching"""
    if not description:
        return "Other"
        
    description = str(description).lower()
    
    if any(word in description for word in ['theft', 'steal', 'stole', 'stolen', 'pickpocket']):
        if any(word in description for word in ['vehicle', 'car', 'bike', 'motorcycle', 'auto']):
            return "Vehicle Theft"
        return "Theft"
    elif any(word in description for word in ['assault', 'attack', 'beat', 'hit', 'fight', 'violence']):
        return "Assault"
    elif any(word in description for word in ['robbery', 'robbed', 'mugging', 'snatching']):
        return "Robbery"
    elif any(word in description for word in ['vandalism', 'damage', 'graffiti', 'break', 'destroy']):
        return "Vandalism"
    elif any(word in description for word in ['harassment', 'stalking', 'following', 'eve teasing']):
        return "Harassment"
    elif any(word in description for word in ['drug', 'substance', 'alcohol', 'drunk']):
        return "Drug-related"
    elif any(word in description for word in ['fraud', 'scam', 'cheat', 'deceive']):
        return "Fraud"
    elif any(word in description for word in ['murder', 'kill', 'homicide', 'death']):
        return "Murder"
    elif any(word in description for word in ['kidnap', 'abduct', 'missing']):
        return "Kidnapping"
    else:
        return "Other"

def find_area_by_coordinates(lat, lng, map_data, kurla_areas):
    """Find which area a report belongs to based on coordinates"""
    if not lat or not lng:
        return "Kurla"
    
    # First try to match with map data markers
    if 'markers' in map_data:
        # Find the closest marker
        closest_marker = None
        min_distance = float('inf')
        
        for marker in map_data['markers']:
            if 'position' in marker and 'lat' in marker['position'] and 'lng' in marker['position']:
                marker_lat = marker['position']['lat']
                marker_lng = marker['position']['lng']
                
                # Calculate distance (simple Euclidean distance)
                distance = ((float(lat) - float(marker_lat)) ** 2 + (float(lng) - float(marker_lng)) ** 2) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    closest_marker = marker
        
        # If we found a close marker and it's within a reasonable distance
        if closest_marker and min_distance < 0.01:  # Approximately 1km
            return closest_marker['title']
    
    # If no match found, return a default area
    return "Kurla"

def map_location_to_area(location, kurla_areas):
    """Map a location name to a standardized area name"""
    if not location:
        return "Kurla"
    
    location = str(location).lower()
    
    # Direct mapping for common locations
    location_mapping = {
        'kurla west': 'Kurla West',
        'kurla east': 'Kurla East',
        'kurla station': 'Kurla Station',
        'bkc': 'BKC',
        'nehru nagar': 'Nehru Nagar',
        'tilak nagar': 'Tilak Nagar',
        'chunabhatti': 'Chunabhatti',
        'chembur': 'Chembur',
        'saki naka': 'Saki Naka',
        'asalpha': 'Asalpha',
        'vinoba bhave nagar': 'Vinoba Bhave Nagar',
        'lbs marg': 'LBS Marg',
        'kamani': 'Kamani',
        'premier colony': 'Premier Colony',
        'kalina': 'Kalina',
        'santacruz east': 'Santacruz East',
        'vidyavihar': 'Vidyavihar',
        'lokmanya tilak terminus': 'Lokmanya Tilak Terminus',
        'sion': 'Sion',
        'jarimari': 'Jarimari',
        'safed pool': 'Safed Pool'
    }
    
    # Check for direct match
    if location in location_mapping:
        return location_mapping[location]
    
    # Check for partial match
    for area_key, area_name in location_mapping.items():
        if area_key in location or location in area_key:
            return area_name
    
    # Check against standard area list
    for area in kurla_areas:
        if area.lower() in location or location in area.lower():
            return area
    
    # Default to Kurla if no match found
    return "Kurla"

def map_crime_type(crime_type):
    """Map crime types from news analysis to standardized types"""
    if not crime_type:
        return "Other"
    
    crime_type = str(crime_type).lower()
    
    # Direct mapping
    type_mapping = {
        'theft': 'Theft',
        'stealing': 'Theft',
        'larceny': 'Theft',
        'pickpocket': 'Theft',
        'shoplifting': 'Theft',
        
        'vehicle theft': 'Vehicle Theft',
        'car theft': 'Vehicle Theft',
        'bike theft': 'Vehicle Theft',
        'auto theft': 'Vehicle Theft',
        'motor vehicle theft': 'Vehicle Theft',
        
        'assault': 'Assault',
        'attack': 'Assault',
        'battery': 'Assault',
        'violence': 'Assault',
        'fight': 'Assault',
        
        'robbery': 'Robbery',
        'mugging': 'Robbery',
        'snatching': 'Robbery',
        'armed robbery': 'Robbery',
        
        'vandalism': 'Vandalism',
        'property damage': 'Vandalism',
        'graffiti': 'Vandalism',
        'destruction': 'Vandalism',
        
        'harassment': 'Harassment',
        'stalking': 'Harassment',
        'eve teasing': 'Harassment',
        'bullying': 'Harassment',
        
        'drug': 'Drug-related',
        'narcotics': 'Drug-related',
        'substance abuse': 'Drug-related',
        'alcohol': 'Drug-related',
        
        'fraud': 'Fraud',
        'scam': 'Fraud',
        'cheating': 'Fraud',
        'forgery': 'Fraud',
        
        'murder': 'Murder',
        'homicide': 'Murder',
        'killing': 'Murder',
        
        'kidnapping': 'Kidnapping',
        'abduction': 'Kidnapping',
        'missing person': 'Kidnapping'
    }
    
    # Check for direct match
    for key, value in type_mapping.items():
        if key in crime_type:
            return value
    
    # Default to Other if no match found
    return "Other"


