from typing import Annotated
from fastapi import Header, HTTPException, status
from backenduser.model import BackendToken
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from datetime import datetime


async def authenticate_token(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification token")
    
    if(datetime.now() > user_token.expire_at):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is expired, try login again.")
    
    return user_token.user