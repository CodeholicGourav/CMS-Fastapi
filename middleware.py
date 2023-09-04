from typing import Annotated
from fastapi import Header, HTTPException, status
from backenduser.model import BackendToken, BackendUser, BackendRolePermission
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db, SessionLocal
from datetime import datetime


async def authenticate_token(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
    """ Check token from header and return details of current user """
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
    
    if not user_token.user or not user_token.user.is_active or user_token.user.is_deleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token.")

    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    return user_token.user


def check_permission(codenames: list[str]):
    """ Return function to check if user has permissions """
    def has_permissions(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
        """ Check user permissions """
        user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
                
        if not user_token.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
        
        if user_token.user.role.id == 0:
            return True

        user_permissions = user_token.user.role.permissions
        if not user_permissions:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permisson not granted.")
        
        return all(element in codenames for element in user_permissions)
    
    return has_permissions
    
