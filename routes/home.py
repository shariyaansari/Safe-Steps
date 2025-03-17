from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
@login_required
def home():
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))  # Ensure this route exists
    else:
        return redirect(url_for("parent.dashboard"))  # Ensure this route exists

