from pydantic import BaseModel
import datetime


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
    cretaed_at : datetime.datetime
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
    username:str
    email:str
    role_id: int
