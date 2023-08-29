from pydantic import BaseModel, constr, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re


def validate_username(value):
    pattern=r'^[a-zA-Z0-9_]+$'
    error_message = "Invalid username. It should contain only letters, numbers, and underscores."
    
    if not re.match(pattern, value):
        raise ValueError(error_message)
    
    return value


def validate_password(value):
    pattern=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$'
    error_message = "Passwowrd should be : At least 8 characters in length, Contains at least one uppercase letter (A-Z), Contains at least one lowercase letter (a-z), Contains at least one digit (0-9), Contains at least one special character (e.g., !, @, #, $, %, etc.)."
    
    if not re.match(pattern, value):
        raise ValueError(error_message)
    
    return value


class CreateSubscription(BaseModel):
    name : str
    description : Optional[str]
    price : float
    validity : int


class User(BaseModel):
    id : int
    uuid : str
    username : str
    email : str
    password : str
    role_id : Optional[str]=None
    verification_token : Optional[str]=None
    email_verified_at : Optional[datetime]=None
    is_active : bool
    is_deleted : bool
    created_at : datetime
    updated_at : datetime

    class Config():
        from_attributes = True


class RegisterUser(BaseModel):
    username: constr(min_length=6, max_length=30,)
    email: EmailStr
    password: constr(min_length=8)
    role_id: str

    @validator("username")
    def username_valid(cls, value):
        return validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return validate_password(value)
    
    class Config():
        from_attributes = True


class ShowRoleName(BaseModel):
    role : str


class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str


class LoginUser(BaseModel):
    username_or_email: str
    password: str


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    user: ShowUser
    
    class Config():
        from_attributes = True


class ForgotPassword(BaseModel):
    token : str
    password: constr(min_length=8)

    @validator("password")
    def _password(cls, value):
        return validate_password( value)


class BasePermission(BaseModel):
    permission :str
    type :int
    codename : str


class BaseRolePermission(BaseModel):
    permission : BasePermission


class ShowRole(BaseModel):
    ruid : str
    role : str
    is_deleted : bool
    creator : Optional[ShowUser]
    created_at : datetime
    updated_at : datetime
    permissions : List[BasePermission]


class CreateRole(BaseModel):
    role : constr(
        min_length=3, 
        max_length=20,
    )


class AssignPermissions(BaseModel):
    ruid : str
    permissions : List[str]
    

class BaseSubscription(BaseModel):
    suid : str
    name : str
    description : str
    price : float
    validity : int
    creator : ShowUser
    is_deleted : bool
    created_at : datetime

