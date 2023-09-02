from pydantic import BaseModel, constr, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from dependencies import CustomValidations



class BaseUser(BaseModel):
    pass


class RegisterUser(BaseModel):
    email : EmailStr
    username: constr(min_length=6, max_length=30)
    first_name : Optional[str] = None
    last_name : Optional[str] = None
    password : constr(min_length=8)
    language : Optional[str] = None
    timezone : Optional[str] = None
    profile_photo : Optional[str] = None

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return CustomValidations.validate_password(value)
