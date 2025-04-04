import os
from flask import Blueprint, json, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Users

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
    data = generate_analytics_data(area=selected_area, is_admin=True)
    
    # Load news analysis data if available
    news_data = {}
    news_analysis_path = os.path.join('static', 'data', 'news_analysis', 'crime_analysis.json')
    if os.path.exists(news_analysis_path):
        try:
            with open(news_analysis_path, 'r') as f:
                news_data = json.load(f)
        except Exception as e:
            print(f"Error loading news analysis data: {str(e)}")
    
    # Get last analysis timestamp
    last_analysis = news_data.get('timestamp', 'Never')
    
    return render_template(
        "parent_analytics.html",
        selected_area=selected_area,
        area_data=data['area_data'],
        trend_labels=data['trend_labels'],
        trend_values=data['trend_values'],
        type_labels=data['type_labels'],
        type_values=data['type_values'],
        kurla_areas=data['kurla_areas'],
        percent_change=data['percent_change'],
        total_reports=data['total_reports'],
        high_risk_areas=data['high_risk_areas'],
        avg_daily_reports=data['avg_daily_reports'],
        most_common_crime=data['most_common_crime'],
        most_common_percent=data['most_common_percent'],
        last_analysis=last_analysis,
        news_data=news_data
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

    user = Users.query.get(current_user.id)
    if user:
        user.username = username
        user.email = email
        user.phone = phone  # Ensure the phone column exists in the users table

        db.session.commit()
        flash("Profile updated successfully", "success")
    else:
        flash("User not found", "error")

    return redirect(url_for("parent.user_settings"))


@parent_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    user = Users.query.get(current_user.id)

    if not user or not check_password_hash(user.password, current_password):
        flash("Current password is incorrect", "error")
        return redirect(url_for("parent.user_settings"))

    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect(url_for("parent.user_settings"))

    user.password = generate_password_hash(new_password)
    db.session.commit()

    flash("Password changed successfully", "success")
    return redirect(url_for("parent.user_settings"))


@parent_bp.route("/update-notifications", methods=["POST"])
@login_required
def update_notifications():
    email_notifications = 1 if request.form.get("email_notifications") else 0
    sms_notifications = 1 if request.form.get("sms_notifications") else 0
    incident_alerts = 1 if request.form.get("incident_alerts") else 0

    user = Users.query.get(current_user.id)
    if user:
        user.email_notifications = email_notifications
        user.sms_notifications = sms_notifications
        user.incident_alerts = incident_alerts

        db.session.commit()
        flash("Notification preferences updated successfully", "success")
    else:
        flash("User not found", "error")

    return redirect(url_for("parent.user_settings"))


@parent_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    user = Users.query.get(current_user.id)

    if user:
        db.session.delete(user)
        db.session.commit()
        flash("Your account has been deleted", "info")
        return redirect(url_for("auth.login"))
    else:
        flash("User not found", "error")
        return redirect(url_for("parent.user_settings"))
