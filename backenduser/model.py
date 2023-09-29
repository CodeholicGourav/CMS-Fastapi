"""
model.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_backend_permissions, predefined_feature


class BackendUser(Base):
    """
    Represents a table in the database that stores information about backend users.
    """
    __tablename__ = 'backendusers'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("backendroles.id"), nullable=True)
    verification_token = Column(String(255), nullable=True, unique=True)
    email_verified_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role = relationship('BackendRole', foreign_keys=role_id)
    subscriptions = relationship('Subscription', back_populates='creator')

    def __repr__(self):
        return (
            "BackendUser("
                f"id={self.id}, "
                f"uuid={self.uuid}, "
                f"username={self.username}, "
                f"email={self.email}, "
                f"password={self.password}"
            ")"
        )

    def __str__(self):
        return f"BackendUser: {self.username}"


class BackendRole(Base):
    """
    Represents a table in the database that stores information about backend roles.
    """
    __tablename__ = 'backendroles'

    id = Column(Integer, primary_key=True, index=True)
    ruid = Column(String(50), index=True, unique=True)
    role = Column(String(50), unique=True)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("backendusers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship('BackendUser', foreign_keys=created_by)
    permissions = relationship('BackendRolePermission', back_populates='role')

    def __repr__(self):
        return (
            "<BackendRole("
                f"id={self.id}, "
                f"ruid='{self.ruid}', "
                f"role='{self.role}')"
            ">"
        )

    def __str__(self):
        return f"BackendRole: '{self.role}')"


class BackendPermission(Base):
    """
    Represents a table in the database called `backendpermissions`.
    """
    __tablename__ = 'backendpermissions'

    id = Column(Integer, primary_key=True, index=True)
    permission = Column(String(255), nullable=False)
    type = Column(Integer, nullable=False)
    codename = Column(String(50), index=True, unique=True, nullable=False)

    def __repr__(self):
        return (
            "<BackendPermission("
                "id={self.id}, "
                "permission={self.permission}, "
                "type={self.type}, "
                "codename={self.codename})"
            ">"
        )

    def __str__(self):
        return f"BackendPermission: {self.codename})"


def create_permissions():
    """
    Create predefined permissions in the database.
    """
    print("Creating permissions data...")
    sql = SessionLocal()
    permissions = [
        BackendPermission(**permission) for permission in predefined_backend_permissions
    ]
    sql.add_all(permissions)
    sql.commit()
    sql.close()
    return {"message": "Backend permissions created successfully"}


class BackendRolePermission(Base):
    """
    Represents a table in the database that stores 
    information about the permissions associated with backend roles.
    """
    __tablename__ = 'backendrolepermissions'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("backendroles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("backendpermissions.id"), nullable=False)

    role = relationship("BackendRole", foreign_keys=role_id)
    permission = relationship("BackendPermission", foreign_keys=permission_id)

    def __repr__(self):
        return (
            "<BackendRolePermission("
                f"id={self.id}, "
                f"role_id={self.role_id}, "
                f"permission_id={self.permission_id})"
            ">")

    def __str__(self):
        return (
            "<BackendRolePermission("
                f"id={self.id}, "
                f"role_id={self.role_id}, "
                f"permission_id={self.permission_id})"
            ">")


class BackendToken(Base):
    """
    Represents a token for backend authentication.
    """
    __tablename__ = 'backendtokens'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("backendusers.id"))
    details = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expire_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('BackendUser', foreign_keys=user_id)

    def __repr__(self):
        return f"<BackendToken(id={self.id}, token={self.token}, user_id={self.user_id})>"

    def __str__(self):
        return f"BackendToken: {self.token}"


class Subscription(Base):
    """
    Represents a table in the database that stores information about subscriptions.
    """
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    suid = Column(String(50), index=True, unique=True)
    name = Column(String(50))
    description = Column(Text, nullable=True)
    price = Column(Float)
    sale_price = Column(Float)
    validity = Column(Integer, comment="In days")
    created_by = Column(Integer, ForeignKey("backendusers.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("BackendUser", back_populates="subscriptions")
    features = relationship("SubscriptionFeature", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, suid='{self.suid}', name='{self.name}')>"

    def __str__(self):
        return f"Subscription: {self.name}"


class SubscriptionUser(Base):
    """
    Represents a table in a database 
    that stores information about users who have subscribed to a service.
    """
    __tablename__ = 'subscription_users'

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    user_id = Column(Integer, ForeignKey("frontendusers.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("Subscription", foreign_keys=subscription_id)
    user = relationship("FrontendUser", foreign_keys=user_id)
    transaction = relationship("Transaction", foreign_keys=transaction_id)

    def __repr__(self):
        """
        Returns a string representation of the SubscriptionUser object.
        """
        return (
            "<SubscriptionUser("
                f"id={self.id}, "
                f"subscription_id={self.subscription_id}, "
                f"user_id={self.user_id}, "
                f"transaction_id={self.transaction_id})"
            ">")

    def __str__(self):
        """
        Returns a string representation of the SubscriptionUser object.
        """
        return (
            "<SubscriptionUser("
                f"id={self.id}, "
                f"subscription_id={self.subscription_id}, "
                f"user_id={self.user_id}, "
                f"transaction_id={self.transaction_id})"
            ">")


class Feature(Base):
    """
    The `Feature` class represents a table in the database called `features`.
    It has fields for the feature's ID, type, and code.
    It also has a relationship with the `SubscriptionFeature` class.
    """
    __tablename__ = 'features'

    id = Column(Integer, primary_key=True)
    feature_type = Column(String(255), unique=True)
    feature_code = Column(String(50), unique=True)

    subscriptions = relationship("SubscriptionFeature", back_populates="feature")

    def __repr__(self):
        return (
            "Feature("
                f"id={self.id}, "
                f"feature_type='{self.feature_type}', "
                f"feature_code='{self.feature_code}'"
            ")"
        )

    def __str__(self):
        return (
            "Feature("
                f"id={self.id}, "
                f"feature_type='{self.feature_type}', "
                f"feature_code='{self.feature_code}'"
            ")"
        )


def create_features():
    """
    Creates feature objects in the database using predefined data.
    """
    print("Creating features data...")
    sql = SessionLocal()
    features = [Feature(**feature) for feature in predefined_feature]
    sql.add_all(features)
    sql.commit()
    sql.close()
    return {"message": "features created successfully"}



class SubscriptionFeature(Base):
    """
    Represents a table in the database called `subscription_features`.
    """
    __tablename__ = 'subscription_features'

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    feature_id = Column(Integer, ForeignKey("features.id"))
    quantity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscription = relationship('Subscription', foreign_keys=subscription_id)
    feature = relationship('Feature', foreign_keys=feature_id)

    def __repr__(self):
        return (
            "SubscriptionFeature("
                f"id={self.id}, "
                f"subscription_id={self.subscription_id}, "
                f"feature_id={self.feature_id}, "
                f"quantity={self.quantity}, "
                f"created_at={self.created_at}"
            ")"
        )

    def __str__(self):
        return (
            "SubscriptionFeature("
                f"id={self.id}, "
                f"subscription_id={self.subscription_id}, "
                f"feature_id={self.feature_id}, "
                f"quantity={self.quantity}, "
                f"created_at={self.created_at}"
            ")"
        )


class Coupon(Base):
    """
    Represents a coupon in a database.
    """
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)
    coupon_code = Column(String(50), unique=True)
    name = Column(String(50))
    percentage = Column(Float)
    coupon_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            "Coupon("
                f"id={self.id}, "
                f"coupon_code='{self.coupon_code}', "
                f"name='{self.name}', "
                f"percentage={self.percentage}, "
                f"coupon_type='{self.coupon_type}', "
                f"is_active={self.is_active}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at}"
            ")"
        )
    def __str__(self):
        return f"Coupon: {self.name} ({self.coupon_code}) - {self.percentage}% off"
