from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, constr, validator

from dependencies import CustomValidations


class User(BaseModel):
    """ 
    The User class represents a user in the system.
    """
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


class BasePermission(BaseModel):
    permission :str
    type :int
    codename : str


class RolePermissions(BaseModel):
    permission : BasePermission

class BasicUser(BaseModel):
    username : str
    email : str

class ShowRole(BaseModel):
    ruid : Optional[str]
    role : str
    is_deleted : bool
    creator : Optional[BasicUser]
    created_at : datetime
    updated_at : datetime
    permissions : Optional[List[RolePermissions]] = []


class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str
    role:ShowRole

class permission(BaseModel):
    permission : str


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


class ListUsers(BaseModel):
    users: List[BaseUser]
    total: int

class RegisterUser(BaseModel):
    username: constr(min_length=6, max_length=30,)
    email: EmailStr
    password: constr(min_length=8)
    role_id: str = Field(..., description="ruid of a role.")

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return CustomValidations.validate_password(value)


class SystemDetails(BaseModel):
    ip_address: constr(max_length=30) = Field(..., description="IP address of you machine to link it with the login token")
    browser: constr(max_length=30) = Field(..., description="Name of the browser to link it with the login token")
    system: constr(max_length=30) = Field(..., description="Name of your machine to link it with the login token")

    def to_string(self):
        return f"IP Address: {self.ip_address}, Browser: {self.browser}, System: {self.system}"
    

class LoginUser(BaseModel):
    username_or_email: str
    password: str
    details: SystemDetails


class UpdateUser(BaseModel):
    user_id: str = Field(..., description="uuid of the user.")
    role_id: Optional[str] = Field(..., description="ruid of the role to assign.")
    is_deleted: Optional[bool] = Field(..., description="delete the user or not.")
    is_active: Optional[bool] = Field(..., description="activate the user or not.")


class RolePermission(BaseModel):
    role_id:str 
    role:Optional[str]
    permission:str 


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    details: str
    user: ShowUser
   


class ForgotPassword(BaseModel):
    token : str = Field(..., description="Token sent to user's email")
    password: constr(min_length=8)

    @validator("password")
    def _password(cls, value):
        return CustomValidations.validate_password( value)


class FeatureQuantity(BaseModel):
    feature_code: str = Field(..., description="feature_code from features list.")
    quantity: int = Field(..., description="Number of items allowed.")



class CreateSubscription(BaseModel):
    name : str
    description : Optional[str]
    price : float = Field(..., description="Price to show.")
    sale_price : float = Field(..., description="The actual price.")
    validity : int = Field(..., description="Validity for user in days.")
    features: list[FeatureQuantity]


class BaseRolePermission(BaseModel):
    permission : BasePermission


class CreateRole(BaseModel):
    role : constr(min_length=3, max_length=20) = Field(..., description="Name of the role.")


class AssignPermissions(BaseModel):
    ruid : str = Field(..., description="ruid of the role.")
    permissions : List[str] = Field(..., description="codename of permissions")


class ListFeatures(BaseModel):
    # id: int
    feature_type: str
    feature_code: str


class SubscriptionFeaturesMapping(BaseModel):
    quantity: int
    feature: ListFeatures


class BaseSubscription(BaseModel):
    suid : str
    name : str
    description : str
    price : float
    validity : int
    creator : Optional[BasicUser]
    is_deleted : bool
    created_at : datetime
    features: list[SubscriptionFeaturesMapping]


class UpdateSubscription(BaseModel):
    suid : str = Field(..., description="suid of the subscription")
    name : Optional[str] = None
    description : Optional[str] = None
    price : Optional[float] = None
    validity : Optional[int] = None
    is_deleted : Optional[bool] = None
    features: Optional[list[FeatureQuantity]] = None


class FrontendBaseUser(BaseModel):
    uuid: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    profile_photo: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    storage_token: Optional[str] = None
    storage_platform: Optional[str] = None
    active_plan: Optional[str] = None
    social_token: Optional[str] = None
    social_platform: Optional[str] = None
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    def __str__(self):
        return f"BaseUser(uuid={self.uuid}, email={self.email}, username={self.username}, is_active={self.is_active}, " \
               f"is_deleted={self.is_deleted}, created_at={self.created_at}, updated_at={self.updated_at})"


class FrontenduserList(BaseModel):
    users: List[FrontendBaseUser]
    total: int



