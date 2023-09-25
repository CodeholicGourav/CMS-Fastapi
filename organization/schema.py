from datetime import datetime
from typing import List, Optional

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
    org_name: constr(min_length=5, max_length=50) = Field(title="organization's name")
    gtoken: dict = Field(title="google token json")
    registration_type: str = Field(title="Registration type", description="Use one of these value only(e.g., 'open', 'approval_required', 'admin_only')")

