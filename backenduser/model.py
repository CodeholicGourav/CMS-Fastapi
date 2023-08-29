from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid as uuid_lib


class BackendUser(Base):
    __tablename__ = 'backendusers'

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
        nullable=False,
    )
    role_id = Column(
        String(50), 
        ForeignKey("backendroles.ruid"),
        nullable=True
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

    subscriptions = relationship('Subscription', back_populates='creator') # subscriptions created by the user


class BackendRole(Base):
    __tablename__ = 'backendroles'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    ruid = Column(
        String(50), 
        index=True,
        default=str(uuid_lib.uuid4()),
    )
    role = Column(
        String(50)
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_by = Column(
        String(50),
        ForeignKey("backendusers.uuid")
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow
    )


class BackendPermission(Base):
    __tablename__ = 'backendpermissions'

    id = Column(
        Integer, 
        primary_key=True, 
        index=True
    )
    permission = Column(
        String(255),
        nullable=False,
        unique=True
    )
    type = Column(
        Integer,
        nullable=False
    )
    codename = Column(
        String(50),
        index=True,
        unique=True,
        nullable=False
    )


class BackendRolePermission(Base):
    __tablename__ = 'backendrolepermissions'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    role_id = Column(
        String(50),
        ForeignKey("backendroles.ruid"),
        nullable=False
    )
    permission_id = Column(
        String,
        ForeignKey("backendpermissions.codename"),
        nullable=False
    )


class BackendToken(Base):
    __tablename__ = 'backendtokens'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    token = Column(
        String, 
        unique=True, 
        index=True,
        nullable=False
    )
    user_id = Column(
        String(50), 
        ForeignKey("backendusers.uuid")
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    expire_at = Column(
        DateTime, 
        default=datetime.utcnow
    )


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    suid = Column(
        String(50), 
        index=True,
        default=str(uuid_lib.uuid4()),
    )
    name = Column(
        String(50), 
        unique=True, 
        index=True,
        nullable=False
    )
    description = Column(
        String,
        nullable=True
    )
    price = Column(
        Float
    )
    validity = Column(
        Integer, 
        comment="In days"
    )
    created_by = Column(
        String(50), 
        ForeignKey("backendusers.uuid")
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    creator = relationship("BackendUser", back_populates="subscriptions")
    

