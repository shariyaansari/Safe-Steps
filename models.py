from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from database import db
from datetime import datetime

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="parent")  # "admin" or "parent"
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    incident_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    area = db.Column(db.String(100), nullable=False)  # Add area field (e.g., "Kurla West", "Kurla East")
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    incident_date = db.Column(db.DateTime, nullable=False)
    reported_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="reported")
    
    user = db.relationship('Users', backref=db.backref('incidents', lazy=True))



# class OTPVerification(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     otp = db.Column(db.String(10), nullable=False)
#     purpose = db.Column(db.String(50), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     expires_at = db.Column(db.DateTime, nullable=False)
    
#     def __repr__(self):
#         return f'<OTPVerification {self.id}>'