from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from models import Users

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
    return render_template("admin_analytics.html")

@admin_bp.route("/users")
@login_required
def users():
    users = Users.query.all()
    return render_template("admin_users.html", users=users)

@admin_bp.route('/edit_user/<int:user_id>', methods=["GET", "POST"])
@login_required
def edit_users(user_id):
    user = Users.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))  # Redirect to users list

    return render_template('editUser.html', user=user)

@admin_bp.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = Users.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully!', 'danger')
    return redirect(url_for('admin.users'))  # Redirect to users list
