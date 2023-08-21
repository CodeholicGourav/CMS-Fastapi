from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class BackendUser(Base):
        __tablename__ = 'backendusers'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        uuid = Column(
                String, 
                unique=True, 
                index=True
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
                Integer, 
                ForeignKey("backendroles.id"),
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

        role = relationship("BackendRole", back_populates="users")


class BackendRole(Base):
        __tablename__ = 'backendroles'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        ruid = Column(
                String, 
                unique=True, 
                index=True
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
                String
            )


class BackendRolePermission(Base):
        __tablename__ = 'backendrolepermissions'

        id = Column(
                Integer, 
                primary_key=True, 
                index=True
            )
        role = Column(
                Integer,
                ForeignKey("backendroles.id")
        )
        permission = Column(
                Integer,
                ForeignKey("backendpermissions.id")
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
