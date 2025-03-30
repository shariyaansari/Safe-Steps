from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from utils import generate_analytics_data
# Import your User model and db
# from models import db, User

parent_bp = Blueprint("parent", __name__)

@parent_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("parent_dashboard.html")

@parent_bp.route("/report-incident")
@login_required
def report_incident():
    return render_template("parent_report.html")

@parent_bp.route("/analytics")
@login_required
def analytics():
    # Get selected area from query parameters
    selected_area = request.args.get('area', None)
    
    # Generate analytics data
    data = generate_analytics_data(area=selected_area, is_admin=False)
    
    return render_template(
        "parent_analytics.html",
        selected_area=selected_area,
        area_data=data['area_data'],
        trend_labels=data['trend_labels'],
        trend_values=data['trend_values'],
        type_labels=data['type_labels'],
        type_values=data['type_values'],
        kurla_areas=data['kurla_areas'],
        heatmap_data=data['heatmap_data'],
        percent_change=data['percent_change']
    )

@parent_bp.route("/settings")
@login_required
def user_settings():
    return render_template("parent_settings.html")

@parent_bp.route("/news-analysis")
@login_required
def news_analysis():
    # Redirect to the admin's news analysis page
    return redirect(url_for('admin.news_analysis'))

# Add the settings-related routes
@parent_bp.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    username = request.form.get("username")
    email = request.form.get("email")
    phone = request.form.get("phone")
    
    # Update user information in your database
    # This is a placeholder - implement according to your database model
    
    flash("Profile updated successfully", "success")
    return redirect(url_for("parent.user_settings"))

@parent_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    
    # Implement password change logic
    # This is a placeholder - implement according to your authentication system
    
    flash("Password changed successfully", "success")
    return redirect(url_for("parent.user_settings"))

@parent_bp.route("/update-notifications", methods=["POST"])
@login_required
def update_notifications():
    # Get form data and update notification preferences
    # This is a placeholder - implement according to your database model
    
    flash("Notification preferences updated", "success")
    return redirect(url_for("parent.user_settings"))

@parent_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    # Delete the user account
    # This is a placeholder - implement according to your database model
    
    flash("Your account has been deleted", "info")
    return redirect(url_for("auth.login"))

