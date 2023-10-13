# -*- coding: utf-8 -*-
"""
organization/model.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, exc
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_organization_permissions


class Organization(Base):
    """
    Represents a table in a database called 'organizations'.
    """

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    orguid = Column(String(50), index=True, unique=True)
    org_name = Column(String(50), nullable=False)
    admin_id = Column(Integer, ForeignKey("frontendusers.id"))
    gtoken = Column(Text, nullable=True)
    registration_type = Column(
        String(20),
        default=1,
        comment="(e.g., 'open', 'approval_required', 'admin_only')",
    )
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = relationship("FrontendUser", foreign_keys=admin_id)
    allowed_registration = ["open", "approval_required", "admin_only"]

    def __repr__(self):
        return (
            "<Organization("
            f"id={self.id}, "
            f"organization_uid='{self.orguid}', "
            f"organization_name='{self.org_name}'"
            ")>"
        )

    def __str__(self):
        return self.org_name


class OrganizationUser(Base):
    """
    Represents a table in a database called 'organization_users'.
    """

    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("frontendusers.id"))
    org_id = Column(Integer, ForeignKey("organizations.id"))
    role_id = Column(Integer, ForeignKey("organization_roles.id"))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("FrontendUser", foreign_keys=user_id)
    Organization = relationship("Organization", foreign_keys=org_id)
    role = relationship("OrganizationRole", foreign_keys=role_id)
    permissions = relationship("OrganizationRolePermission", back_populates="org_user")

    def __repr__(self):
        return (
            "OrganizationUser("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"org_id={self.org_id}, "
            f"role_id={self.role_id}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at}"
            ")"
        )

    def __str__(self):
        return (
            "OrganizationUser("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"org_id={self.org_id}, "
            f"role_id={self.role_id}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at}"
            ")"
        )


class OrganizationRole(Base):
    """
    Represents a table in a database called 'organization_roles'.
    """

    __tablename__ = "organization_roles"

    id = Column(Integer, primary_key=True, index=True)
    ruid = Column(String(50), index=True, unique=True)
    role = Column(String(50))
    created_by = Column(Integer, ForeignKey("frontendusers.id"))
    org_id = Column(Integer, ForeignKey("organizations.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    permissions = relationship("OrganizationRolePermission", back_populates="role")

    def __repr__(self):
        return "<OrganizationRole(" f"id={self.id}, " f"role='{self.role}'" ")>"

    def __str__(self):
        return f"Organization Role: {self.role}"


class OrganizationPermission(Base):
    """
    Represents a table in a database called 'organization_permissions'.
    """

    __tablename__ = "organization_permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission = Column(String(255), nullable=False)
    type = Column(Integer, nullable=False)
    codename = Column(String(50), index=True, unique=True, nullable=False)

    def __repr__(self):
        return (
            "<OrganizationPermission("
            f"id={self.id}, "
            f"permission='{self.permission}'"
            f"type='{self.type}'"
            f"codename='{self.codename}'"
            ")>"
        )

    def __str__(self):
        return f"Organization Permission: {self.permission}"


def create_org_permissions():
    """
    Create predefined organization permissions in the database.
    """
    try:
        print("Creating organization permissions data...")
        sql = SessionLocal()
        permissions = [
            OrganizationPermission(**permission)
            for permission in predefined_organization_permissions
        ]
        sql.add_all(permissions)
        sql.commit()
        return {"message": "Organization Permissions created successfully"}
    except exc.IntegrityError as error:
        sql.rollback()
        return {"error": str(error)}
    except exc.SQLAlchemyError as error:
        sql.rollback()
        return {"error": str(error)}
    finally:
        sql.close()


class OrganizationRolePermission(Base):
    """
    Represents a table in a database called 'organization_rolepermissions'.
    """

    __tablename__ = "organization_rolepermissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("organization_roles.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("organization_users.id"), nullable=True)
    permission_id = Column(
        Integer, ForeignKey("organization_permissions.id"), nullable=False
    )

    role = relationship(
        "OrganizationRole", foreign_keys=role_id, back_populates="permissions"
    )
    org_user = relationship(
        "OrganizationUser", foreign_keys=user_id, back_populates="permissions"
    )
    permission = relationship("OrganizationPermission", foreign_keys=permission_id)

    def __repr__(self):
        return (
            "<OrganizationRolePermission("
            f"id={self.id}, "
            f"role_id={self.role_id}, "
            f"permission_id={self.permission_id}"
            ")>"
        )

    def __str__(self):
        return (
            "<OrganizationRolePermission("
            f"id={self.id}, "
            f"role_id={self.role_id}, "
            f"permission_id={self.permission_id}"
            ")>"
        )
