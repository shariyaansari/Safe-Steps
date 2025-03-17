# from flask import Flask, render_template, request, redirect, url_for, flash
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# import secrets
# from werkzeug.security import generate_password_hash, check_password_hash

# # Generate secret key
# secret_key = secrets.token_hex(32)

# # Create Flask app
# app = Flask(__name__)

# # Database configuration
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
# app.config["SECRET_KEY"] = secret_key

# # Initialize Flask extensions
# db = SQLAlchemy(app)
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login"

# # User model
# class Users(UserMixin, db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(250), unique=True, nullable=False)
#     email = db.Column(db.String(250), unique=True, nullable=False)
#     password = db.Column(db.String(250), nullable=False)
#     role = db.Column(db.String(50), nullable=False, default="parent")  # "admin" or "parent"
#     created_at = db.Column(db.DateTime, server_default=db.func.now())

# # Initialize database
# with app.app_context():
#     db.create_all()

# @login_manager.user_loader
# def load_user(user_id):
#     return Users.query.get(int(user_id))

# @app.route('/register', methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         username = request.form.get("username")
#         email = request.form.get("email")
#         password = request.form.get("password")
#         role = request.form.get("role")  # Get role from form

#         # Check if username or email exists
#         if Users.query.filter_by(username=username).first():
#             flash("Username already taken. Please choose another.", "danger")
#             return redirect(url_for("register"))
#         if Users.query.filter_by(email=email).first():
#             flash("Email already exists. Please try logging in.", "warning")
#             return redirect(url_for("register"))

#         # Hash password and create user
#         hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
#         user = Users(username=username, email=email, password=hashed_password, role=role)
#         db.session.add(user)
#         db.session.commit()

#         flash("Account created successfully! Please log in.", "success")
#         return redirect(url_for("login"))

#     return render_template("sign_up.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")

#         user = Users.query.filter_by(username=username).first()
#         if not user:
#             flash("User not found. Please register first.", "danger")
#             return redirect(url_for("login"))

#         # Check password
#         if check_password_hash(user.password, password):
#             login_user(user)
#             flash("Login Successful!", "success")
#             return redirect(url_for("home"))
#         else:
#             flash("Invalid username or password. Try again.", "danger")
#             return redirect(url_for("login"))

#     return render_template("login.html")

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     flash("You have been logged out.", "info")
#     return redirect(url_for("login"))

# @app.route("/")
# @login_required
# def home():
#     return render_template("home.html", user=current_user)

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask
from flask_login import LoginManager
from models import db, Users
from database import init_db
from routes.auth import auth_bp
from routes.home import home_bp
from routes.admin import admin_bp
from routes.parent import parent_bp

app = Flask(__name__)
init_db(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(home_bp, url_prefix="/home")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(parent_bp, url_prefix="/parent")

if __name__ == '__main__':
    app.run(debug=True)
