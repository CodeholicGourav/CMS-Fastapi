"""
schema.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr, validator

from dependencies import CustomValidations


class User(BaseModel):
    """
    A pydantic model
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
    """
    A pydantic model
    """
    permission :str
    type :int
    codename : str


class RolePermissions(BaseModel):
    """
    A pydantic model
    """
    permission : BasePermission


class BasicUser(BaseModel):
    """
    A pydantic model
    """
    username : str
    email : str


class ShowRole(BaseModel):
    """
    A pydantic model
    """
    ruid : Optional[str]
    role : str
    is_deleted : bool
    creator : Optional[BasicUser]
    created_at : datetime
    updated_at : datetime
    permissions : Optional[List[RolePermissions]] = []


class ShowUser(BaseModel):
    """
    A pydantic model
    """
    uuid : str
    username : str
    email : str
    role:ShowRole


class Permission(BaseModel):
    """
    A pydantic model
    """
    permission : str


class ShowRoleName(BaseModel):
    """
    A pydantic model
    """
    role : str


class BaseUser(BaseModel):
    """
    A pydantic model
    """
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
    """
    A pydantic model
    """
    users: List[BaseUser]
    total: int


class RegisterUser(BaseModel):
    """
    A pydantic model
    """
    username: constr(min_length=6, max_length=30,)
    email: EmailStr
    password: constr(min_length=8)
    role_id: str = Field(..., description="ruid of a role.")

    @validator("username")
    def username_valid(self, value):
        """
        Validates a given username value.
        """
        return CustomValidations.validate_username(value)

    @validator("password")
    def password_validate(self, value):
        """
        Validates a given password value.
        """
        return CustomValidations.validate_password(value)


class SystemDetails(BaseModel):
    """
    A pydantic model
    """
    ip_address: str = Field(
        ..., le=30,
        description="IP address of you machine to link it with the login token."
    )
    browser: str = Field(
        ...,
        le=30,
        description="Name of the browser to link it with the login token."
    )
    system: str = Field(
        ...,
        le=30,
        description="Name of your machine to link it with the login token."
    )

    def to_string(self):
        """
        Returns string representation of the object of this class.
        """
        return f"IP Address: {self.ip_address}, Browser: {self.browser}, System: {self.system}"


class LoginUser(BaseModel):
    """
    A pydantic model
    """
    username_or_email: str
    password: str
    details: SystemDetails


class UpdateUser(BaseModel):
    """
    A pydantic model
    """
    user_id: str = Field(..., description="uuid of the user.")
    role_id: Optional[str] = Field(..., description="ruid of the role to assign.")
    is_deleted: Optional[bool] = Field(..., description="delete the user or not.")
    is_active: Optional[bool] = Field(..., description="activate the user or not.")


class RolePermission(BaseModel):
    """
    A pydantic model
    """
    role_id:str
    role:Optional[str]
    permission:str


class ShowToken(BaseModel):
    """
    A pydantic model
    """
    token: str
    expire_at: datetime
    details: str
    user: ShowUser


class ForgotPassword(BaseModel):
    """
    A pydantic model
    """
    token : str = Field(..., description="Token sent to user's email")
    password: constr(min_length=8)

    @validator("password")
    def _password(self, value):
        return CustomValidations.validate_password( value)


class FeatureQuantity(BaseModel):
    """
    A pydantic model
    """
    feature_code: str = Field(..., description="feature_code from features list.")
    quantity: int = Field(..., description="Number of items allowed.")


class CreateSubscription(BaseModel):
    """
    A pydantic model
    """
    name : str
    description : Optional[str]
    price : float = Field(..., description="Price to show.")
    sale_price : float = Field(..., description="The actual price.")
    validity : int = Field(..., description="Validity for user in days.")
    features: list[FeatureQuantity]


class BaseRolePermission(BaseModel):
    """
    A pydantic model
    """
    permission : BasePermission


class CreateRole(BaseModel):
    """
    A pydantic model
    """
    role : str = Field(..., ge=3, le=20, description="Name of the role.")


class AssignPermissions(BaseModel):
    """
    A pydantic model
    """
    ruid : str = Field(..., description="ruid of the role.")
    permissions : List[str] = Field(..., description="codename of permissions")


class ListFeatures(BaseModel):
    """
    A pydantic model
    """
    feature_type: str
    feature_code: str


class SubscriptionFeaturesMapping(BaseModel):
    """
    A pydantic model
    """
    quantity: int
    feature: ListFeatures


class BaseSubscription(BaseModel):
    """
    A pydantic model
    """
    suid : str
    name : str
    description : str
    price : float
    sale_price: float
    validity : int
    creator : Optional[BasicUser]
    is_deleted : bool
    created_at : datetime
    features: list[SubscriptionFeaturesMapping]


class UpdateSubscription(BaseModel):
    """
    A pydantic model
    """
    suid : str = Field(..., description="suid of the subscription")
    name : Optional[str] = None
    description : Optional[str] = None
    price : Optional[float] = None
    validity : Optional[int] = None
    is_deleted : Optional[bool] = None
    features: Optional[list[FeatureQuantity]] = None


class FrontendBaseUser(BaseModel):
    """
    A pydantic model
    """
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
        return (
            "BaseUser("
                f"uuid={self.uuid}, "
                f"email={self.email}, "
                f"username={self.username}, "
                f"is_active={self.is_active}, "
                f"is_deleted={self.is_deleted}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at}"
            ")")


class FrontenduserList(BaseModel):
    """
    A pydantic model
    """
    users: List[FrontendBaseUser]
    total: int
