from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_feature, predefined_permissions


class BackendUser(Base):
    """
    The BackendUser class represents a table in the database that stores information about backend users.
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
    updated_at = Column(DateTime, default=datetime.utcnow)

    role = relationship('BackendRole', foreign_keys=role_id)
    subscriptions = relationship('Subscription', back_populates='creator')

    def __repr__(self):
        return f"BackendUser(id={self.id}, uuid={self.uuid}, username={self.username}, email={self.email}, password={self.password})"

    def __str__(self):
        return f"BackendUser: {self.username}"


class BackendRole(Base):
    """
    The BackendRole class represents a table in the database that stores information about backend roles.
    It defines the structure and relationships of the table.
    """
    __tablename__ = 'backendroles'

    id = Column(Integer, primary_key=True, index=True)
    ruid = Column(String(50), index=True, unique=True)
    role = Column(String(50), unique=True)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("backendusers.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship('BackendUser', foreign_keys=created_by)
    permissions = relationship('BackendRolePermission', back_populates='role')

    def __repr__(self):
        return f"<BackendRole(id={self.id}, ruid='{self.ruid}', role='{self.role}')>"

    def __str__(self):
        return f"BackendRole(id={self.id}, ruid='{self.ruid}', role='{self.role}')"


class BackendPermission(Base):
    """
    The `BackendPermission` class represents a table in the database called `backendpermissions`.
    It has fields for the permission ID, permission name, permission type, and permission codename.
    """
    __tablename__ = 'backendpermissions'

    id = Column(Integer, primary_key=True, index=True)
    permission = Column(String(255), nullable=False)
    type = Column(Integer, nullable=False)
    codename = Column(String(50), index=True, unique=True, nullable=False)

    def __repr__(self):
        return f"<BackendPermission(id={self.id}, permission={self.permission}, type={self.type}, codename={self.codename})>"

    def __str__(self):
        return f"BackendPermission(id={self.id}, permission={self.permission}, type={self.type}, codename={self.codename})"


def create_permissions():
    """
    Create predefined permissions in the database.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    try:
        print("Creating permissions data...")
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
    """
    The `BackendRolePermission` class represents a table in the database that stores information about the permissions associated with backend roles.
    It defines the structure and relationships of the table.
    """
    __tablename__ = 'backendrolepermissions'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("backendroles.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("backendpermissions.id"), nullable=False)

    role = relationship("BackendRole", foreign_keys=role_id)
    permission = relationship("BackendPermission", foreign_keys=permission_id)

    def __repr__(self):
        return f"<BackendRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"

    def __str__(self):
        return f"BackendRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})"


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
        return self.token


class Subscription(Base):
    """
    The `Subscription` class represents a table in the database that stores information about subscriptions.
    It defines the structure and relationships of the table.
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


class Feature(Base):
    """
    The `Feature` class represents a table in the database called `features`.
    It has fields for the feature's ID, type, and code.
    It also has a relationship with the `SubscriptionFeature` class.
    """
    __tablename__ = 'features'

    id = Column(Integer, primary_key=True)
    feature_type = Column(String(255))
    feature_code = Column(String(50))

    subscriptions = relationship("SubscriptionFeature", back_populates="feature")

    def __repr__(self):
        return f"Feature(id={self.id}, feature_type='{self.feature_type}', feature_code='{self.feature_code}')"

    def __str__(self):
        return f"Feature(id={self.id}, feature_type='{self.feature_type}', feature_code='{self.feature_code}')"


def create_features():
    """
    Creates feature objects in the database using predefined data.

    Returns:
        A dictionary with the message "features created successfully" if the features are created successfully.
        A dictionary with the error message if an exception occurs.
    """
    try:
        print("Creating features data...")
        db = SessionLocal()
        features = [Feature(**feature) for feature in predefined_feature]
        db.add_all(features)
        db.commit()
        return {"message": "features created successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()



class SubscriptionFeature(Base):
    """
    The `SubscriptionFeature` class represents a table in the database called `subscription_features`.
    It defines the structure and relationships of the table.
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
        return f"SubscriptionFeature(id={self.id}, subscription_id={self.subscription_id}, feature_id={self.feature_id}, quantity={self.quantity}, created_at={self.created_at})"

    def __str__(self):
        return f"SubscriptionFeature(id={self.id}, subscription_id={self.subscription_id}, feature_id={self.feature_id}, quantity={self.quantity}, created_at={self.created_at})"


class Coupon(Base):
    """
    The `Coupon` class is a SQLAlchemy model that represents a coupon in a database.
    It has fields for the coupon's ID, code, name, percentage, type, active status, creation timestamp, and update timestamp.
    """
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)
    coupon_code = Column(String(50), unique=True)
    name = Column(String(50))
    percentage = Column(Float)
    coupon_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"Coupon(id={self.id}, coupon_code='{self.coupon_code}', name='{self.name}', percentage={self.percentage}, coupon_type='{self.coupon_type}', is_active={self.is_active}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __str__(self):
        return f"Coupon: {self.name} ({self.coupon_code}) - {self.percentage}% off"