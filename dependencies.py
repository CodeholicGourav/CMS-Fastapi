from typing import Annotated
from fastapi import Header
from passlib.context import CryptContext



async def authenticate_token(authtoken: Annotated[str, Header()]):
    if authtoken != "123456789":
        return {'status': False, 'data': "User not authenticated"}


pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Hash():
    def bcrypt(password: str):
        return pwd_cxt.hash(password)

    def verify(hashed_password,plain_password):
        return pwd_cxt.verify(plain_password,hashed_password)