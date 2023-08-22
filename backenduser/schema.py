from pydantic import BaseModel, UUID4, constr, EmailStr, validator
from typing import Optional
import datetime
import re


class User(BaseModel):
    id : int
    uuid : str
    username : str
    email : str
    password : str
    role_id : int
    verification_token : str
    email_verified_at : datetime.datetime
    is_active : bool
    is_deleted : bool
    created_at : datetime.datetime
    updated_at : datetime.datetime


class RegisterUser(BaseModel):
    username: constr(
        min_length=6, 
        max_length=30,
    )
    email: EmailStr
    password: str

    @validator("username")
    def validate_username(cls, value):
        pattern=r'^[a-zA-Z0-9_]+$'
        error_message = "Invalid username. It should contain only letters, numbers, and underscores."
        
        if not re.match(pattern, value):
            raise ValueError(error_message)
        
        return value


class showRole(BaseModel):
    role: str = ""
    class Config():
        from_attributes = True


class ShowUser(BaseModel):
    uuid : UUID4
    username : str
    email : str
    role: Optional[showRole]
    email_verified_at : Optional[datetime.datetime]
    is_active : bool
    is_deleted : bool
    created_at: datetime.datetime
    updated_at : datetime.datetime


class LoginUser(BaseModel):
    username_or_email: str
    password: str


class ShowToken(BaseModel):
    token: str
    expire_at: datetime.datetime
    user: ShowUser


class ForgotPassword(BaseModel):
    token : str
    password : str

class ShowBackendPermission(BaseModel):
    id : int
    permission : str
    type : str
    codename : str