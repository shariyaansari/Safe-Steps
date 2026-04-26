import secrets
import os

class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "process.env.JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "process.env.DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    OPENAPI_URL_PREFIX = "/api"
    REDOC_UI_URL = None