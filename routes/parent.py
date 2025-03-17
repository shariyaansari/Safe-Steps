from flask import Blueprint, render_template
from flask_login import login_required

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
    return render_template("parent_analytics.html")

@parent_bp.route("/settings")
@login_required
def user_settings():
    return render_template("parent_settings.html")
