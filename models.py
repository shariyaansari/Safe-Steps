from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from core.database import Base

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(250), unique=True, nullable=False, index=True)
    email = Column(String(250), unique=True, nullable=False, index=True)
    password = Column(String(250), nullable=False)
    role = Column(String(50), nullable=False, default="parent")  # "admin" or "parent"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    incidents = relationship("Incident", back_populates="user")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    incident_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    area = Column(String(100), nullable=False)
    
    # PostGIS Geometry column instead of separate float columns
    # SRID 4326 is standard GPS coordinates (WGS 84)
    geom = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    
    incident_date = Column(DateTime(timezone=True), nullable=False)
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="reported")
    
    user = relationship("Users", back_populates="incidents")