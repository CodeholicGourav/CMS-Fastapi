from typing import Annotated
from fastapi import Header, HTTPException, status
from backenduser.model import BackendToken, BackendUser, BackendRolePermission
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from datetime import datetime


async def authenticate_token(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    user = db.query(BackendUser).filter(BackendUser.uuid==user_token.user_id).first()
    
    return user

async def check_permission(authtoken: Annotated[str, Header()], codenames: list[str], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    user = db.query(BackendUser).filter(BackendUser.uuid==user_token.user_id).first()
    permissions = db.query(BackendRolePermission).filter(BackendRolePermission.role_id==user.role_id).all()
    return all(element in codenames for element in permissions)