from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Users
import re

# Creating a blueprint
auth_bp = Blueprint("auth", __name__)

# Function to create admin user if it doesn't exist
def create_admin_if_not_exists():
    # Hardcoded admin credentials
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "admin123"  # You should use a stronger password in production
    
    # Check if admin already exists
    admin = Users.query.filter_by(username=admin_username).first()
    if not admin:
        # Create admin user
        hashed_password = generate_password_hash(admin_password, method="pbkdf2:sha256", salt_length=16)
        admin = Users(username=admin_username, email=admin_email, password=hashed_password, role="admin")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

@auth_bp.route('/')
def index():
    # If user is logged in, redirect based on role
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == "authorities":
            return redirect(url_for('authorities.dashboard'))
        else:  # parent role
            return redirect(url_for('parent.dashboard'))
    # If not logged in, redirect to login page
    else:
        return redirect(url_for('auth.login'))

# @auth_bp.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form.get("username")
#         email = request.form.get("email")
#         password = request.form.get("password")
#         role = request.form.get("role", "parent")  # Default to "parent" if empty

#         # Check if username or email exists
#         if Users.query.filter_by(username=username).first():
#             flash("Username already taken. Please choose another.", "danger")
#             return redirect(url_for("auth.register"))
#         if Users.query.filter_by(email=email).first():
#             flash("Email already exists. Please try logging in.", "warning")
#             return redirect(url_for("auth.register"))

#         # Prevent users from registering as admin through form manipulation
#         if role == "admin":
#             role = "parent"  # Default to parent if someone tries to register as admin

#         # Hash password and create user
#         hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
#         user = Users(username=username, email=email, password=hashed_password, role=role)
#         db.session.add(user)
#         db.session.commit()

#         flash("Account created successfully! Please log in.", "success")
#         return redirect(url_for("auth.login"))

#     return render_template("sign_up.html")

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
        
        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("auth.register"))
        
        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.", "danger")
            return redirect(url_for("auth.register"))
            
        if not re.search(r"[a-z]", password):
            flash("Password must contain at least one lowercase letter.", "danger")
            return redirect(url_for("auth.register"))
            
        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.", "danger")
            return redirect(url_for("auth.register"))
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            flash("Password must contain at least one special character.", "danger")
            return redirect(url_for("auth.register"))
        
        # Prevent users from registering as admin through form manipulation
        if role == "admin":
            role = "parent"  # Default to parent if someone tries to register as admin
        
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

        # Special case for admin login
        if username == "admin":
            user = Users.query.filter_by(username="admin").first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash("Admin Login Successful!", "success")
                return redirect(url_for("admin.dashboard"))
            else:
                flash("Invalid admin credentials. Try again.", "danger")
                return redirect(url_for("auth.login"))
        
        # Regular user login
        user = Users.query.filter_by(username=username).first()
        if not user:
            flash("User not found. Please register first.", "danger")
            return redirect(url_for("auth.login"))

        if check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful!", "success")

            # Redirect based on role
            if user.role == "authorities":
                return redirect(url_for("authorities.dashboard"))
            else:
                return redirect(url_for("parent.dashboard"))
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