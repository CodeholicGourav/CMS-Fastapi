from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_organization_permissions


class Organization(Base):
    """
    The `Organization` class represents a table in a database called 'organization'.
    """
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True)
    orguid = Column(String(50), index=True, unique=True)
    org_name = Column(String(50), nullable=False)
    admin_id = Column(Integer, ForeignKey("frontendusers.id"))
    gtoken = Column(Text, nullable=True)
    registration_type = Column(String(20), default=1, comment="(e.g., 'open', 'approval_required', 'admin_only')")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = relationship("FrontendUser", foreign_keys=admin_id)
    allowed_registration = ['open', 'approval_required', 'admin_only']

    def __repr__(self):
        return f"<Organization(id={self.id}, organization_uid='{self.orguid}', organization_name='{self.org_name}')>"

    def __str__(self):
        return self.org_name


class OrganizationUser(Base):
    """
    The OrganizationUser class represents a table in a database called 'organization_users'.
    It is used to store information about users within an organization.
    """
    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(50), index=True, unique=True)
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

    def __repr__(self):
        return f"OrganizationUser(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, org_id={self.org_id}, role_id={self.role_id}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __str__(self):
        return f"OrganizationUser(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, org_id={self.org_id}, role_id={self.role_id}, created_at={self.created_at}, updated_at={self.updated_at})"


class OrganizationRole(Base):
    """
    The `OrganizationRole` class represents a table in a database called 'organization_roles'.
    It is used to store information about different roles within an organization.
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
        return f"<OrganizationRole(id={self.id}, role='{self.role}')>"

    def __str__(self):
        return f"Organization Role: {self.role}"


class OrganizationPermission(Base):
    __tablename__ = "organization_permissions"

    id = Column(Integer, primary_key=True, index=True)
    permission = Column(String(255), nullable=False)
    type = Column(Integer, nullable=False)
    codename = Column(String(50), index=True, unique=True, nullable=False)


def create_permissions():
    """
    Create predefined permissions in the database.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    try:
        print("Creating permissions data...")
        db = SessionLocal()
        permissions = [OrganizationPermission(**permission) for permission in predefined_organization_permissions]
        db.add_all(permissions)
        db.commit()
        return {"message": "Organization Permissions created successfully"}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


class OrganizationRolePermission(Base):
    """
    The `OrganizationRolePermission` class represents a table in a database called 'organization_rolepermissions'.
    It is used to store information about the permissions assigned to different roles within an organization.
    """
    __tablename__ = 'organization_rolepermissions'

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("organization_roles.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("organization_users.id"), nullable=True)
    permission_id = Column(Integer, ForeignKey("organization_permissions.id"), nullable=False)

    role = relationship("OrganizationRole", foreign_keys=role_id, back_populates="permissions")
    permission = relationship("OrganizationPermission", foreign_keys=permission_id)

    def __repr__(self):
        return f"<OrganizationRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})>"

    def __str__(self):
        return f"OrganizationRolePermission(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})"


