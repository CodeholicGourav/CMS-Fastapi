from datetime import datetime
from typing import List, Optional, Annotated

from pydantic import BaseModel, constr, validator, Field

from dependencies import CustomValidations


class BasicOrganization(BaseModel):
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
    uuid: str
    username: str
    email: str


class ShowOrganization(BaseModel):
    orguid: str
    org_name: str
    admin: ShowUser
    registration_type: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime



class BasicOrganizationList(BaseModel):
    total: int
    organizations: List[ShowOrganization]


class CreateOrganization(BaseModel):
    org_name: constr(min_length=5, max_length=50) = Field(..., title="organization's name")
    gtoken: dict = Field(..., title="google token json")
    registration_type: str = Field(..., title="Registration type", description="Use one of these value only(e.g., 'open', 'approval_required', 'admin_only')")


class OrgUserRegister(BaseModel):
    org_uid: str = Field(..., title="Organization's ouid")


class BasicRole(BaseModel):
    ruid: str
    role: str


class ShowOrgUser(BaseModel):
    uuid: str
    user: ShowUser
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    role: BasicRole

class ShowOrgUserList(BaseModel):
    total: int
    users: List[ShowOrgUser]


class BasicOrgPermission(BaseModel):
    type: int
    permission: str
    codename: str


class BasicOrgRolePermission(BaseModel):
    permission: BasicOrgPermission


class ShowOrgRole(BaseModel):
    ruid: str
    role: str
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[BasicOrgRolePermission]


class ShowOrgRoleList(BaseModel):
    total: int
    roles: List[ShowOrgRole]


class CreateRole(BaseModel):
    role: str = Field(title="Name of the role")
    permissions: List[str] = Field(title="permission code")


class UpdateRole(BaseModel):
    ruid: str
    role: Annotated[str, Field(None, title="Name of the role")]
    permissions: Annotated[List[str], Field(None, title="permission code")]

