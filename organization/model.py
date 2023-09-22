from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Organization(Base):
    """
    The `Organization` class represents a table in a database called 'organization'.
    """
    __tablename__ = 'organization'

    id = Column(Integer, primary_key=True, index=True)
    orguid = Column(String(50), index=True, unique=True)
    org_name = Column(String(50), nullable=False)
    admin_id = Column(Integer, ForeignKey("frontendusers.id"))
    gtoken = Column(String(255), nullable=True)
    registration_type = Column(Integer, default=1, comment="(e.g., 'open', 'approval_required', 'admin_only')")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"<Organization(id={self.id}, organization_uid='{self.orguid}', organization_name='{self.org_name}')>"

    def __str__(self):
        return self.org_name


class OrganizationRoles(Base):
    """
    The `OrganizationRoles` class represents a table in a database called 'organization_roles'.
    It is used to store information about different roles within an organization.
    """
    __tablename__ = "organization_roles"

    id = Column(Integer, primary_key=True, index=True)
    ruid = Column(String(50), index=True, unique=True)
    role = Column(String(50), unique=True)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("organization_users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OrganizationRoles(id={self.id}, role='{self.role}')>"

    def __str__(self):
        return f"Organization Role: {self.role}"


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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"OrganizationUser(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, org_id={self.org_id}, role_id={self.role_id}, created_at={self.created_at}, updated_at={self.updated_at})"

    def __str__(self):
        return f"OrganizationUser(id={self.id}, uuid={self.uuid}, user_id={self.user_id}, org_id={self.org_id}, role_id={self.role_id}, created_at={self.created_at}, updated_at={self.updated_at})"

