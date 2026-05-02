from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps

authorities_bp = Blueprint("authorities", __name__, url_prefix="/authorities")

# Custom decorator to check if user is an authority
def authorities_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "authorities":
            return "Access denied: Authorities only", 403
        return f(*args, **kwargs)
    return decorated_function

@authorities_bp.route("/dashboard")
@login_required
@authorities_required
def dashboard():
    return render_template("authorities_dashboard.html")