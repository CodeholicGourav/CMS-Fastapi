from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import datetime
import uuid as uuid_lib

class BackendUser(Base):
        __tablename__ = 'backendusers'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        uuid = Column(
                UUID(as_uuid=True), 
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
                UUID(as_uuid=True), 
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
                default=datetime.datetime.utcnow
            )
        updated_at = Column(
                DateTime, 
                default=datetime.datetime.utcnow
            )

        role = relationship("BackendRole")


class BackendRole(Base):
        __tablename__ = 'backendroles'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        ruid = Column(
                UUID(as_uuid=True), 
                default=uuid_lib.uuid4, 
                unique=True, 
                nullable=False
            )
        created_by = Column(
                UUID(as_uuid=True),
                ForeignKey("backendusers.uuid")
        )
        role = Column(
                String
            )
        is_deleted = Column(
                Boolean,
                default=False
            )
        created_at = Column(
                DateTime, 
                default=datetime.datetime.utcnow
            )
        updated_at = Column(
                DateTime, 
                default=datetime.datetime.utcnow
            )

        users = relationship("BackendUser", back_populates="role")

        permissions = relationship("BackendPermission")


class BackendPermission(Base):
        __tablename__ = 'backendpermissions'

        id = Column(
                Integer, 
                primary_key=True, 
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
                unique=True,
                index=True
            )


class BackendRolePermission(Base):
        __tablename__ = 'backendrolepermissions'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        role = Column(
                UUID(as_uuid=True),
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
                Integer, 
                ForeignKey("backendusers.id")
            )
        created_at = Column(
                DateTime, 
                default=datetime.datetime.utcnow
            )
        expire_at = Column(
                DateTime, 
                default=datetime.datetime.utcnow
            )
        
        user = relationship("BackendUser")
