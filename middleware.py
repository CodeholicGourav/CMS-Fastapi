from typing import Annotated
from fastapi import Header, HTTPException, status, Request
from backenduser.model import BackendToken, BackendUser, BackendRolePermission
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from datetime import datetime


async def authenticate_token(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    user = db.query(BackendUser).filter(BackendUser.uuid==user_token.user_id).first()
    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")

    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    return user

async def check_permission(authtoken: Annotated[str, Header()], codenames: list[str], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    user = db.query(BackendUser).filter(BackendUser.uuid==user_token.user_id, BackendUser.is_deleted==False, BackendUser.is_active==True).first()
    permissions = db.query(BackendRolePermission).filter(BackendRolePermission.role_id==user.role_id).all()
    return all(element in codenames for element in permissions)


def perm_req(codenames: list[str], db : Session):
    def wrapper(f):
        def wrapped(request: Request):
            authtoken = request.headers.get('authtoken')
            user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
            if not user_token:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
            
            user = db.query(BackendUser).filter(BackendUser.uuid==user_token.user_id).first()
            if not user or not user.is_active or user.is_deleted:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")

            if(datetime.now() > user_token.expire_at):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
            
            permissions = db.query(BackendRolePermission).filter(BackendRolePermission.role_id==user.role_id).all()
            if all(element in codenames for element in permissions):
                return f(request)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission denied.")

        return wrapped
    return wrapper