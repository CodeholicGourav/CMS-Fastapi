from pydantic import BaseModel, constr, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from dependencies import CustomValidations
from fastapi import UploadFile



class BaseUser(BaseModel):
    uuid : str
    email : str
    username: str
    first_name : Optional[str] = None
    last_name : Optional[str] = None
    language : Optional[str] = None
    timezone : Optional[str] = None
    profile_photo : Optional[str] = None
    email_verified_at : Optional[datetime] = None
    storage_token : Optional[str] = None
    storage_platform : Optional[str] = None
    active_plan : Optional[str] = None
    social_token : Optional[str] = None
    social_platform : Optional[str] = None
    is_active : bool
    is_deleted : bool
    created_at : datetime
    updated_at : datetime


class UpdateProfile(BaseModel):
    username: Optional[str] = None
    first_name : Optional[str] = None
    last_name : Optional[str] = None
    language : Optional[str] = None
    timezone : Optional[str] = None
    profile_photo : Optional[str] = None
    storage_token : Optional[str] = None
    storage_platform : Optional[str] = None
    social_token : Optional[str] = None
    social_platform : Optional[str] = None


class RegisterUser(BaseModel):
    email : EmailStr
    username: constr(min_length=6, max_length=30)
    first_name : Optional[str] = None
    last_name : Optional[str] = None
    password : constr(min_length=8)
    language : Optional[str] = None
    timezone : Optional[str] = None

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return CustomValidations.validate_password(value)


class UpdateUser(BaseModel):
    user_id: str
    is_active : Optional[bool] = None
    is_deleted : Optional[bool] = None


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    user: BaseUser


class LoginUser(BaseModel):
    username_or_email: str
    password: str


class ForgotPassword(BaseModel):
    token : str
    password: constr(min_length=8)

    @validator("password")
    def _password(cls, value):
        return CustomValidations.validate_password( value)


class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str


class BaseSubscription(BaseModel):
    suid : str
    name : str
    description : str
    price : float
    validity : int
    creator : ShowUser
    is_deleted : bool
    created_at : datetime


class TimeZones(BaseModel):
    timezone_name : str
    code : str
    time_difference : str


class AddOrder(BaseModel):
    ouid : str