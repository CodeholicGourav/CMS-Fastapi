"""
schema.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import Annotated, List

from pydantic import BaseModel, Field


class BasicOrganization(BaseModel):
    """
    A pydantic model
    """
    orguid: str
    org_name: str
    admin_id: int
    gtoken: str
    registration_type: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ShowUser(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    username: str
    email: str


class ShowOrganization(BaseModel):
    """
    A pydantic model
    """
    orguid: str
    org_name: str
    admin: ShowUser
    registration_type: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class BasicOrganizationList(BaseModel):
    """
    A pydantic model
    """
    total: int
    organizations: List[ShowOrganization]


class CreateOrganization(BaseModel):
    """
    A pydantic model
    """
    org_name: str = Field(
        ...,
        ge=5,
        le=50,
        title="organization's name"
    )
    gtoken: dict = Field(
        ...,
        title="google token json"
    )
    registration_type: str = Field(
        ...,
        title="Registration type",
        description="Use one of these value only(e.g., 'open', 'approval_required', 'admin_only')"
    )


class OrgUserRegister(BaseModel):
    """
    A pydantic model
    """
    org_uid: str = Field(..., title="Organization's ouid")


class BasicRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: str


class BasicOrgPermission(BaseModel):
    """
    A pydantic model
    """
    type: int
    permission: str
    codename: str


class BasicOrgRolePermission(BaseModel):
    """
    A pydantic model
    """
    permission: BasicOrgPermission


class ShowOrgUser(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    user: ShowUser
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    role: BasicRole
    permissions: List[BasicOrgRolePermission]


class ShowOrgUserList(BaseModel):
    """
    A pydantic model
    """
    total: int
    users: List[ShowOrgUser]


class ShowOrgRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: str
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[BasicOrgRolePermission]


class ShowOrgRoleList(BaseModel):
    """
    A pydantic model
    """
    total: int
    roles: List[ShowOrgRole]


class CreateRole(BaseModel):
    """
    A pydantic model
    """
    role: str = Field(title="Name of the role")
    permissions: List[str] = Field(title="permission code")


class UpdateRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: Annotated[str, Field(None, title="Name of the role")]
    permissions: Annotated[List[str], Field(None, title="permission code")]


class UpdateUserPermission(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    permissions: Annotated[List[str], Field(None, title="permission code")]


class AssignRole(BaseModel):
    """
    A pydantic model
    """
    user_id: str
    role_id: str
