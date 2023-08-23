from pydantic import BaseModel, UUID4, constr, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re


class User(BaseModel):
    id : int
    uuid : str
    username : str
    email : str
    password : str
    role_id : int
    verification_token : str
    email_verified_at : datetime
    is_active : bool
    is_deleted : bool
    created_at : datetime
    updated_at : datetime

    class Config():
        from_attributes = True


class RegisterUser(BaseModel):
    username: constr(
        min_length=6, 
        max_length=30,
    )
    email: EmailStr
    password: str

    class Config():
        from_attributes = True

    @validator("username")
    def validate_username(cls, value):
        pattern=r'^[a-zA-Z0-9_]+$'
        error_message = "Invalid username. It should contain only letters, numbers, and underscores."
        
        if not re.match(pattern, value):
            raise ValueError(error_message)
        
        return value

class ShowRoleName(BaseModel):
    role : str

class ShowUser(BaseModel):
    uuid : UUID4
    username : str
    email : str
    role: Optional[ShowRoleName]
    email_verified_at : Optional[datetime]
    is_active : bool
    is_deleted : bool
    created_at: datetime
    updated_at : datetime
    
    class Config():
        from_attributes = True


class LoginUser(BaseModel):
    username_or_email: str
    password: str

    class Config():
        from_attributes = True


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    user: ShowUser
    
    class Config():
        from_attributes = True


class ForgotPassword(BaseModel):
    token : str
    password : str


class BasePermission(BaseModel):
    permission :str
    type :int
    codename : str

    class Config():
        from_attributes = True


class ShowRole(BaseModel):
    ruid : UUID4
    role : str
    is_deleted : bool
    creator : Optional[ShowUser]
    created_at : datetime
    updated_at : datetime
    permissions : List[BasePermission]

    class Config():
        from_attributes = True


class CreateRole(BaseModel):
    role : constr(
        min_length=3, 
        max_length=20,
    )

    class Config():
        from_attributes = True


class AssignPermissions(BaseModel):
    ruid : UUID4
    permissions : List[str]

    class Config():
        from_attributes = True
    