from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr, validator

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