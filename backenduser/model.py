from typing import Dict, Union
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_permissions


class BackendUser(Base):
    """
    The BackendUser class represents a table in the database that stores information about backend users.
    """
    __tablename__ = 'backendusers'
    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    uuid = Column(
        String(50), 
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
        String(255), 
        nullable=False,
    )
    role_id = Column(
        Integer, 
        ForeignKey("backendroles.id"),
        nullable=True
    )
    verification_token = Column(
        String(255), 
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

    # Relationships
    role = relationship('BackendRole', foreign_keys=role_id)
    subscriptions = relationship('Subscription', back_populates='creator')


class BackendRole(Base):
    """
    Represents a table in the database that stores information about backend roles.
    """

    __tablename__ = 'backendroles'

    id = Column(
        Integer,
        primary_key=True, 
        index=True
    )
    ruid = Column(
        String(50), 
        index=True,
        unique=True, 
    )
    role = Column(
        String(50),
        unique=True
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_by = Column(
        Integer,
        ForeignKey("backendusers.id")
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    # Relationships
    creator = relationship('BackendUser', foreign_keys=created_by)
    permissions = relationship('BackendRolePermission', back_populates='role')


class BackendPermission(Base):
    __tablename__ = 'backendpermissions'

    id = Column(
        Integer, 
        primary_key=True, 
        index=True
    )
    permission = Column(
        String(255),
        nullable=False
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


def create_permissions() -> Union[Dict[str, str], Dict[str, str]]:
    """
    Create predefined permissions in the database.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    try:
        db = SessionLocal()
        permissions = [BackendPermission(**permission) for permission in predefined_permissions]
        db.add_all(permissions)
        db.commit()
        return {"message": "Permissions created successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


class BackendRolePermission(Base):
    __tablename__ = 'backendrolepermissions'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    role_id = Column(
        Integer,
        ForeignKey("backendroles.id"),
        nullable=False
    )
    permission_id = Column(
        Integer,
        ForeignKey("backendpermissions.id"),
        nullable=False
    )

    # Relationships
    role = relationship("BackendRole", foreign_keys=role_id)
    permission = relationship("BackendPermission", foreign_keys=permission_id)


class BackendToken(Base):
    __tablename__ = 'backendtokens'

    id = Column(
        Integer, 
        primary_key=True,
        index=True
    )
    token = Column(
        String(255), 
        unique=True, 
        index=True,
        nullable=False
    )
    user_id = Column(
        Integer, 
        ForeignKey("backendusers.id")
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )
    expire_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    # Relationships
    user = relationship('BackendUser', foreign_keys=user_id)


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
        unique=True, 
    )
    name = Column(
        String(50), 
    )
    description = Column(
        Text,
        nullable=True
    )
    price = Column(
        Float
    )
    sale_price = Column(
        Float
    )
    validity = Column(
        Integer, 
        comment="In days"
    )
    created_by = Column(
        Integer, 
        ForeignKey("backendusers.id")
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    # Relationships
    creator = relationship("BackendUser", back_populates="subscriptions")


class Feature(Base):
    __tablename__ = 'features'

    id = Column(
        Integer,
        primary_key=True
    )
    feature_type = Column(
        String(255)
    )
    feature_code = Column(
        String(50)
    )


class SubscriptionFeature(Base):
    __tablename__ = 'subscription_features'

    id = Column(
        Integer,
        primary_key=True
    )
    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id")
    )
    feature_id = Column(
        Integer,
        ForeignKey("features.id")
    )
    quantity = Column(
        Integer
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Coupon(Base):
    __tablename__ = 'coupons'

    id = Column(
        Integer,
        primary_key=True
    )
    coupon_code = Column(
        String(50),
        unique=True
    )
    name = Column(
        String(50)
    )
    percentage = Column(
        Float
    )
    coupon_type = Column(
        String(50)
    )
