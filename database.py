from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

# def init_db(app):
#     app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
#     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#     db.init_app(app)

#     with app.app_context():
#         db.create_all()
        
def init_db(app):
    app.config.from_object(Config)  # Load configurations from Config class
    db.init_app(app)

    with app.app_context():
        db.create_all()
