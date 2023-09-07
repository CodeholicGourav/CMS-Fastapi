from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base, SessionLocal
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
        Integer, 
        ForeignKey("backendroles.id"),
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

    role = relationship('BackendRole', foreign_keys=role_id)
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


def create_permissions():
    predefined_permissions = [
        {"permission": "Can create user", "type": 1, "codename": "create_user"},
        {"permission": "Can read user", "type": 1, "codename": "read_user"},
        {"permission": "Can update user", "type": 1, "codename": "update_user"},
        {"permission": "Can delete user", "type": 1, "codename": "delete_user"},

        {"permission": "Can create role", "type": 2, "codename": "create_role"},
        {"permission": "Can read role", "type": 2, "codename": "read_role"},
        {"permission": "Can update role", "type": 2, "codename": "update_role"},
        {"permission": "Can delete role", "type": 2, "codename": "delete_role"},

        {"permission": "Can create permission", "type": 3, "codename": "create_permission"},
        {"permission": "Can read permission", "type": 3, "codename": "read_permission"},
        {"permission": "Can update permission", "type": 3, "codename": "update_permission"},
        {"permission": "Can delete permission", "type": 3, "codename": "delete_permission"},

        {"permission": "Can create subscription", "type": 4, "codename": "create_subscription"},
        {"permission": "Can read subscription", "type": 4, "codename": "read_subscription"},
        {"permission": "Can delete subscription", "type": 4, "codename": "delete_subscription"}
    ]

    try:
        db = SessionLocal()
        for permission in predefined_permissions:
            new_permission = BackendPermission(**permission)
            db.add(new_permission)

        db.commit()
        db.close()
        print("permissions created successfully")
        return {"message": "permissions created successfully"}
    
    except Exception as e:
        db.rollback()
        print(e)
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
        String, 
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

    creator = relationship("BackendUser", back_populates="subscriptions")
    

