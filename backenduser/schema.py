from pydantic import BaseModel
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
    username: str
    email: str
    password: str

class showRole(BaseModel):
    role: str = ""
    class Config():
        orm_mode = True

class ShowUser(BaseModel):
    uuid : Optional[str]
    username : str
    email : str
    role: Optional[showRole]
    email_verified_at : Optional[datetime.datetime]
    is_active : bool
    is_deleted : bool
    created_at: datetime.datetime
    updated_at : datetime.datetime
    
