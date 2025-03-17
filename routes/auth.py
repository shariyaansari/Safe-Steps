from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Users

# Creating a blueprint
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "parent")  # Default to "parent" if empty

        # Check if username or email exists
        if Users.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "danger")
            return redirect(url_for("auth.register"))
        if Users.query.filter_by(email=email).first():
            flash("Email already exists. Please try logging in.", "warning")
            return redirect(url_for("auth.register"))

        # Hash password and create user
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        user = Users(username=username, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("sign_up.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()
        if not user:
            flash("User not found. Please register first.", "danger")
            return redirect(url_for("auth.login"))

        if check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful!", "success")

            # Redirect based on role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))  # Ensure this route exists
            else:
                return redirect(url_for("parent.dashboard"))  # Ensure this route exists

        else:
            flash("Invalid username or password. Try again.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out!", "info")
    return redirect(url_for("auth.login"))
