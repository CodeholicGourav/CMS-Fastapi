from .schema import RegisterUser, LoginUser
from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token
from .model import BackendUser, BackendToken
from datetime import datetime, timedelta
import secrets
from fastapi import HTTPException,status
# from database import get_db


def all_backend_users(db: Session):
    return db.query(BackendUser).all()


def create_user(user: RegisterUser, db: Session):
    existing_user = db.query(BackendUser).filter((BackendUser.email == user.email) | (BackendUser.username == user.username)).first()
    if existing_user:
        if user.username == existing_user.username :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username already in use")
        
        if user.email == existing_user.email :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already in use")
    
    new_user = BackendUser(
        username=user.username,
        email=user.email,
        password=Hash.bcrypt(user.password),
        verification_token = generate_token(32),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    BackendEmail.sendVerificationToken(new_user)
    return new_user

def verify_email(token: str, db: Session):
    user = db.query(BackendUser).filter(BackendUser.verification_token == token).first()
    if user:
        user.email_verified_at = datetime.utcnow()
        user.verification_token = None 
        db.commit()
        return {"message": "Email verified successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token")
    
def create_auth_token(request: LoginUser, db: Session):
    user = db.query(BackendUser).filter(
        (BackendUser.email == request.username_or_email) |
        ( BackendUser.username == request.username_or_email),
        BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your email first!")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    token = BackendToken(
        token = generate_token(16),
        user_id = user.id,
        expire_at = datetime.utcnow() + timedelta(hours=24)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token