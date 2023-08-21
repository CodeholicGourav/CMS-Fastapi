from pydantic import BaseModel, UUID4, constr
import datetime
from typing import Optional


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
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=15,
        pattern='^[a-z]*$'
    )
    email: str
    password: str

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