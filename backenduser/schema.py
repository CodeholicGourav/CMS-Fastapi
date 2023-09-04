from pydantic import BaseModel, constr, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from dependencies import CustomValidations


class User(BaseModel):
    id : int
    uuid : str
    username : str
    email : str
    password : str
    role_id : Optional[int]=None
    verification_token : Optional[str]=None
    email_verified_at : Optional[datetime]=None
    is_active : bool
    is_deleted : bool
    created_at : datetime
    updated_at : datetime


class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str


class BasePermission(BaseModel):
    permission :str
    type :int
    codename : str

class permission(BaseModel):
    permission : str

class RolePermissions(BaseModel):
    permission : BasePermission


class ShowRole(BaseModel):
    ruid : str
    role : str
    is_deleted : bool
    creator : Optional[ShowUser]
    created_at : datetime
    updated_at : datetime
    permissions : Optional[List[RolePermissions]] = []


class ShowRoleName(BaseModel):
    role : str

class BaseUser(BaseModel):
    uuid : str
    username : str
    email : str
    role : ShowRoleName
    email_verified_at : Optional[datetime]=None
    is_active : bool
    is_deleted : bool
    created_at : datetime
    updated_at : datetime


class RegisterUser(BaseModel):
    username: constr(min_length=6, max_length=30,)
    email: EmailStr
    password: constr(min_length=8)
    role_id: str

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return CustomValidations.validate_password(value)


class LoginUser(BaseModel):
    username_or_email: str
    password: str
    

class UpdateUser(BaseModel):
    user_id: str
    role_id: Optional[str] = None
    is_deleted: Optional[bool] = None
    is_active: Optional[bool] = None


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    user: ShowUser


class ForgotPassword(BaseModel):
    token : str
    password: constr(min_length=8)

    @validator("password")
    def _password(cls, value):
        return CustomValidations.validate_password( value)



class CreateSubscription(BaseModel):
    name : str
    description : Optional[str]
    price : float
    validity : int


class BaseRolePermission(BaseModel):
    permission : BasePermission


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


class UpdateSubscription(BaseModel):
    suid : str
    is_deleted : bool

