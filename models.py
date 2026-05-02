import uuid
import enum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean,
    Integer, Float, ForeignKey, UniqueConstraint, Enum, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from core.database import Base 

# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    user  = "user"


class IncidentType(str, enum.Enum):
    theft      = "theft"
    assault    = "assault"
    harassment = "harassment"
    robbery    = "robbery"
    vandalism  = "vandalism"
    other      = "other"


class IncidentStatus(str, enum.Enum):
    pending  = "pending"
    verified = "verified"
    rejected = "rejected"


class AuditAction(str, enum.Enum):
    verified    = "verified"
    rejected    = "rejected"
    deleted     = "deleted"
    banned_user = "banned_user"


# ─────────────────────────────────────────────
# User
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username      = Column(String(100), unique=True, nullable=False, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login    = Column(DateTime(timezone=True), nullable=True)

    # relationships
    reported_incidents  = relationship("Incident", foreign_keys="Incident.reported_by",  back_populates="reporter")
    verified_incidents  = relationship("Incident", foreign_keys="Incident.verified_by",  back_populates="verifier")
    votes               = relationship("IncidentVote", back_populates="user")
    audit_actions       = relationship("AuditLog", foreign_keys="AuditLog.admin_id",     back_populates="admin")
    audit_targets       = relationship("AuditLog", foreign_keys="AuditLog.target_user",  back_populates="targeted_user")


# ─────────────────────────────────────────────
# Incident
# ─────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # who filed it
    reported_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # who actioned it (nullable — only set after admin review)
    verified_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_at   = Column(DateTime(timezone=True), nullable=True)

    # incident details
    incident_type = Column(Enum(IncidentType), nullable=False)
    description   = Column(Text, nullable=True)
    image_url     = Column(String(500), nullable=True)          # Cloudinary / S3 URL

    # location
    address       = Column(String(500), nullable=True)          # full readable address
    area          = Column(String(150), nullable=False, index=True)  # "Kurla West", "BKC"
    city          = Column(String(100), nullable=False, default="Mumbai")
    state         = Column(String(100), nullable=False, default="Maharashtra")
    pincode       = Column(String(10),  nullable=True)
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    location      = Column(                                     # PostGIS point for spatial queries
        Geometry(geometry_type="POINT", srid=4326),
        nullable=True
    )

    # timestamps — two intentional fields:
    # occurred_at  = when incident actually happened (user-entered)
    # reported_at  = when form was submitted (system-generated)
    occurred_at   = Column(DateTime(timezone=True), nullable=False)
    reported_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # moderation
    status        = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.pending)
    is_anonymous  = Column(Boolean, nullable=False, default=False)

    # community credibility — cached count, incremented by IncidentVote inserts
    upvotes       = Column(Integer, nullable=False, default=0)

    # relationships
    reporter      = relationship("User", foreign_keys=[reported_by], back_populates="reported_incidents")
    verifier      = relationship("User", foreign_keys=[verified_by], back_populates="verified_incidents")
    votes         = relationship("IncidentVote", back_populates="incident", cascade="all, delete-orphan")
    audit_logs    = relationship("AuditLog", back_populates="incident")


# ─────────────────────────────────────────────
# IncidentVote  (weak entity)
# ─────────────────────────────────────────────

class IncidentVote(Base):
    __tablename__ = "incident_votes"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"),     nullable=False, index=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # one vote per user per incident — enforced at DB level
    __table_args__ = (
        UniqueConstraint("incident_id", "user_id", name="uq_vote_incident_user"),
    )

    # relationships
    incident    = relationship("Incident", back_populates="votes")
    user        = relationship("User",     back_populates="votes")


# ─────────────────────────────────────────────
# AuditLog
# ─────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # which admin performed the action
    admin_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # what was actioned — either an incident OR a user, one can be null
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True, index=True)
    target_user = Column(UUID(as_uuid=True), ForeignKey("users.id"),     nullable=True)

    action      = Column(Enum(AuditAction), nullable=False)
    note        = Column(Text, nullable=True)                   # optional reason left by admin
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # relationships
    admin         = relationship("User", foreign_keys=[admin_id],    back_populates="audit_actions")
    targeted_user = relationship("User", foreign_keys=[target_user], back_populates="audit_targets")
    incident      = relationship("Incident", back_populates="audit_logs")