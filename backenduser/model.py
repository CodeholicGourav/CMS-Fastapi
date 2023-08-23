from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid as uuid_lib
from typing import List

class BackendUser(Base):
        __tablename__ = 'backendusers'

        id = Column(
                Integer, 
                autoincrement=True, 
                index=True
            )
        uuid = Column(
                UUID(as_uuid=True), 
                primary_key=True,
                default=uuid_lib.uuid4, 
                unique=True, 
                nullable=False
            )
        username = Column(
                String, 
                unique=True, 
                index=True
            )
        email = Column(
                String, 
                unique=True, 
                index=True
            )
        password = Column(
                String
            )
        role_id = Column(
                UUID, 
                ForeignKey("backendroles.ruid"),
                nullable=True
            )
        verification_token = Column(
                String, 
                nullable=True
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

        role = relationship("BackendRole", foreign_keys=[role_id], back_populates="users")
        tokens = relationship("BackendToken", back_populates="user")


class BackendRole(Base):
        __tablename__ = 'backendroles'

        id = Column(
                Integer, 
                autoincrement=True, 
                index=True
            )
        ruid = Column(
                UUID(as_uuid=True), 
                primary_key=True, 
                index=True,
                default=uuid_lib.uuid4, 
                unique=True, 
                nullable=False
            )
        role = Column(
                String
            )
        is_deleted = Column(
                Boolean,
                default=False
            )
        created_by = Column(
                UUID,
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

        users = relationship("BackendUser", foreign_keys="[BackendUser.role_id]", back_populates="role", lazy="select")
        creator = relationship("BackendUser", foreign_keys="BackendRole.created_by")


        permissions = relationship("BackendRolePermission")


class BackendPermission(Base):
        __tablename__ = 'backendpermissions'

        id = Column(
                Integer, 
                autoincrement=True, 
                index=True
            )
        permission = Column(
                String
            )
        type = Column(
                String
            )
        codename = Column(
                String,
                primary_key=True, 
                index=True
            )


class BackendRolePermission(Base):
        __tablename__ = 'backendrolepermissions'

        id = Column(
                Integer, 
                autoincrement=True,
                primary_key=True, 
                index=True
            )
        role = Column(
                UUID,
                ForeignKey("backendroles.ruid")
        )
        permission = Column(
                String,
                ForeignKey("backendpermissions.codename")
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
                index=True
            )
        user_id = Column(
                UUID, 
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
        
        user = relationship("BackendUser", back_populates="tokens")


