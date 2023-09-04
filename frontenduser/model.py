from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
from datetime import datetime
import uuid as uuid_lib


class FrontendUser(Base):
    __tablename__ = 'frontendusers'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    uuid = Column(
        String(50), 
        default=str(uuid_lib.uuid4()), 
        unique=True, 
        nullable=False,
        index=True
    )
    first_name = Column(
        String(50),
        nullable=True
    )
    last_name = Column(
        String(50),
        nullable=True
    )
    username = Column(
        String(50), 
        unique=True, 
        index=True
    )
    email = Column(
        String(255), 
        unique=True, 
        index=True
    )
    password = Column(
        String, 
    )
    verification_token = Column(
        String, 
        nullable=True,
        unique=True
    )
    email_verified_at = Column(
        DateTime, 
        nullable=True
    )
    storage_token = Column(
        String,
        nullable=True
    )
    storage_platform = Column(
        String(10),
        nullable=True
    )
    language = Column(
        String(10),
        default="en"
    )
    timezone = Column(
        String(10),
        default="Asia/Kolkata"
    )
    active_plan = Column(
        String,
        nullable=True
    )
    profile_photo = Column(
        String,
        nullable=True
    )
    social_token = Column(
        String,
        nullable=True
    )
    social_platform = Column(
        String,
        nullable=True
    )
    is_active = Column(
        Boolean, 
        default=True
    )
    is_deleted = Column(
        Boolean, 
        default=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow
    )


class Timezone(Base):
    __tablename__ = 'timezones'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    timezone_name = Column(
        String(255)
    )
    code = Column(
        String(255),
        unique=True
    )
    time_difference = Column(
        String(50)
    )
