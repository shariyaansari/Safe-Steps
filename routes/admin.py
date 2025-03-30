from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Users
from utils import generate_analytics_data
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("adminhome.html")

@admin_bp.route("/reports")
@login_required
def reports():
    return render_template("admin_report.html")

@admin_bp.route("/analytics")
@login_required
def analytics():
    # Get selected area from query parameters
    selected_area = request.args.get('area', None)
    
    # Generate analytics data
    data = generate_analytics_data(area=selected_area, is_admin=True)
    
    return render_template(
        "admin_analytics.html",
        selected_area=selected_area,
        area_data=data['area_data'],
        trend_labels=data['trend_labels'],
        trend_values=data['trend_values'],
        type_labels=data['type_labels'],
        type_values=data['type_values'],
        kurla_areas=data['kurla_areas'],
        heatmap_data=data['heatmap_data'],
        percent_change=data['percent_change'],
        total_incidents=data['admin_data']['total_incidents'],
        recent_incidents=data['admin_data']['recent_incidents']
    )


# @admin_bp.route('/analytics')
# @login_required
# def analytics():
#     # Load the map data
#     map_data_path = os.path.join(current_app.static_folder, 'map_data.geojson')
    
#     try:
#         with open(map_data_path, 'r') as f:
#             map_data = json.load(f)
#     except (FileNotFoundError, json.JSONDecodeError):
#         map_data = {"features": []}
    
#     # Extract areas from map data
#     kurla_areas = sorted(list(set([feature['properties']['name'] 
#                                    for feature in map_data['features']])))
    
#     # Get selected area from query parameters
#     selected_area = request.args.get('area', '')
    
#     # Filter data based on selected area
#     if selected_area:
#         filtered_features = [f for f in map_data['features'] 
#                             if f['properties']['name'] == selected_area]
#     else:
#         filtered_features = map_data['features']
    
#     # Process data for charts using incident data
#     # 1. Monthly trend
#     from datetime import datetime
    
#     # Get last 6 months
#     now = datetime.now()
#     months = []
#     for i in range(5, -1, -1):
#         month = now.month - i
#         year = now.year
#         if month <= 0:
#             month += 12
#             year -= 1
#         months.append(datetime(year, month, 1).strftime("%b %Y"))
    
#     trend_values = [0] * len(months)
    
#     # Count incidents by month
#     for feature in filtered_features:
#         if 'incidents' in feature['properties']:
#             for incident in feature['properties']['incidents']:
#                 incident_date = datetime.strptime(incident['date'], "%Y-%m-%d")
#                 incident_month = incident_date.strftime("%b %Y")
#                 if incident_month in months:
#                     trend_values[months.index(incident_month)] += 1
    
#     # Calculate percent change
#     if len(trend_values) >= 2 and trend_values[-2] > 0:
#         percent_change = ((trend_values[-1] - trend_values[-2]) / trend_values[-2]) * 100
#     else:
#         percent_change = 0
    
#     # 2. Crime types
#     crime_types = {
#         "Theft": 0,
#         "Assault": 0,
#         "Robbery": 0,
#         "Vandalism": 0,
#         "Other": 0
#     }
    
#     # Count incidents by type
#     for feature in filtered_features:
#         if 'incidents' in feature['properties']:
#             for incident in feature['properties']['incidents']:
#                 crime_type = incident['type']
#                 if crime_type in crime_types:
#                     crime_types[crime_type] += 1
#                 else:
#                     crime_types["Other"] += 1
    
#     # 3. Area data
#     area_data = {}
#     for feature in map_data['features']:
#         area_name = feature['properties']['name']
#         area_data[area_name] = feature['properties']['crime_count']
    
#     # Sort crime types for display
#     type_labels = list(crime_types.keys())
#     type_values = [crime_types[label] for label in type_labels]
    
#     return render_template('admin/analytics.html',
#                           kurla_areas=kurla_areas,
#                           selected_area=selected_area,
#                           trend_labels=months,
#                           trend_values=trend_values,
#                           percent_change=percent_change,
#                           type_labels=type_labels,
#                           type_values=type_values,
#                           area_data=area_data,
#                           map_data=map_data)


@admin_bp.route("/users")
@login_required
def users():
    users = Users.query.all()
    return render_template("admin_users.html", users=users)

@admin_bp.route('/edit_user/<int:user_id>', methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = Users.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))  # Redirect to users list

    return render_template('edit_user.html', user=user) 

@admin_bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = Users.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'danger')
    return redirect(url_for('admin.users'))  # Redirect to users list

@admin_bp.route("/news-analysis")
@login_required
def news_analysis():
    return redirect(url_for('news_analysis.news_analysis_page'))
