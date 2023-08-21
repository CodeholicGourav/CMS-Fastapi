from .schema import RegisterUser
from sqlalchemy.orm import Session
from dependencies import Hash
from .model import BackendUser
import datetime
from fastapi import HTTPException,status
# from database import get_db


def all_backend_users( db: Session):
    return db.query(BackendUser).all()


def create_user(user: RegisterUser, db: Session):
    new_user = BackendUser(
        username=user.username,
        email=user.email,
        password=Hash.bcrypt(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def verify_email(token: str, db: Session):
    user = db.query(BackendUser).filter(BackendUser.verification_token == token).first()
    if user:
        user.email_verified_at = datetime.datetime.utcnow()
        user.verification_token = None 
        db.commit()
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token")