from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from database import db

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="parent")  # "admin" or "parent"
    created_at = db.Column(db.DateTime, server_default=db.func.now())