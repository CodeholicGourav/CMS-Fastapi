from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, constr, validator

from dependencies import CustomValidations


class BaseUser(BaseModel):
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


class UpdateProfile(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    storage_token: Optional[str] = None
    storage_platform: Optional[str] = None
    social_token: Optional[str] = None
    social_platform: Optional[str] = None

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)


class RegisterUser(BaseModel):
    email: EmailStr
    username: constr(min_length=6, max_length=30)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: constr(min_length=8)
    language: Optional[str] = None
    timezone: Optional[str] = None

    @validator("username")
    def username_valid(cls, value):
        return CustomValidations.validate_username(value)
    
    @validator("password")
    def password_validate(cls, value):
        return CustomValidations.validate_password(value)


class UpdateUser(BaseModel):
    user_id: str
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None


class ShowToken(BaseModel):
    token: str
    expire_at: datetime
    details: str
    user: BaseUser


class SystemDetails(BaseModel):
    ip_address: constr(max_length=30)
    browser: constr(max_length=30)
    system: constr(max_length=30)

    def to_string(self):
        return f"IP Address: {self.ip_address}, Browser: {self.browser}, System: {self.system}"

class LoginUser(BaseModel):
    username_or_email: str
    password: str
    details: SystemDetails


class ForgotPassword(BaseModel):
    token: str
    password: constr(min_length=8)

    @validator("password")
    def _password(cls, value):
        return CustomValidations.validate_password( value)


class ShowUser(BaseModel):
    uuid: str
    username: str
    email: str


class BaseSubscription(BaseModel):
    suid: str
    name: str
    description: str
    price: float
    validity: int
    creator: ShowUser
    is_deleted: bool
    created_at: datetime


class TimeZones(BaseModel):
    timezone_name: str
    code: str
    time_difference: str

class Orders(BaseModel):
    ouid: str
    total_amount: float
    final_amount: float
    currency: str
    conversion_rate: float
    coupon_amount: float
    cuoupon_code: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    user: ShowUser
    clientSecret: str



class AddOrder(BaseModel):
    suid : str
    currency: str        
    coupon_code:Optional[str] = None


class Createtransaction(BaseModel):
   transaction_id:str 
   order_id:str 


class AddTransaction(BaseModel):
    status: str
    payment_gateway: str


class StripeReturn(BaseModel):
  id: str
  amount: int
  canceled_at: int | None
  cancellation_reason: str | None
  capture_method: str
  client_secret: str
  confirmation_method: str
  created: int
  currency: str
  description: str
  livemode: bool
  payment_method: str
  payment_method_types: list
  receipt_email: EmailStr
  status: str


class RazorpayReturn(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    currency: str
    ouid: str
    status: str
