from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token
from .schema import RegisterUser, LoginUser, ForgotPassword, CreateRole, AssignPermissions
from .model import BackendUser, BackendToken, BackendRole, BackendPermission, BackendRolePermission
from datetime import datetime, timedelta
from fastapi import HTTPException,status
from typing import Optional
# from database import get_db


def all_backend_users(limit : int, offset : int, db: Session):
    return db.query(BackendUser).limit(limit).offset(offset).all()


def create_user(user: RegisterUser, db: Session):
    existing_user = db.query(BackendUser).filter(
        (BackendUser.email == user.email) 
        | 
        (BackendUser.username == user.username)
    ).first()

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
    backendEmail = BackendEmail()
    if backendEmail.sendVerificationToken(new_user):
        return new_user
    else:
        raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail="Cannot send email.")


def verify_email(token: str, db: Session):
    user = db.query(BackendUser).filter(
        BackendUser.verification_token == token,
        BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    
    user.email_verified_at = datetime.utcnow()
    user.verification_token = None 
    db.commit()
    return {"message": "Email verified successfully"}
    

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


def send_verification_mail(email: str, db: Session):
    user = db.query(BackendUser).filter(
        BackendUser.email == email,
        BackendUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No account found.")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    user.verification_token = generate_token(32)
    db.commit() 
    db.refresh(user)
    backendEmail = BackendEmail()
    if backendEmail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else :
        raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail="Cannot send email.")


def create_new_password(request: ForgotPassword, db: Session):
    user = db.query(BackendUser).filter(
        BackendUser.verification_token == request.token,
        BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token is expired!")
    
    if not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your email first!")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    user.password = Hash.bcrypt(request.password)
    user.verification_token = None 
    db.commit()
    db.refresh(user)
    return user

def add_role(request: CreateRole, user: BackendUser, db : Session):
    new_role = BackendRole(
        role = request.role,
        created_by = user.uuid
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


def assign_permissions(request : AssignPermissions, db : Session):
    role = db.query(BackendRole).filter(BackendRole.ruid==request.ruid, BackendRole.is_deleted==False).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found!")
    
    codenames = request.permissions
    permissions = db.query(BackendPermission).filter(BackendPermission.codename.in_(codenames)).all()
    # if len(permissions) != len(codenames):
    #     raise HTTPException(status_code=400, detail="Some permissions do not exist")

    # Associate permissions with the role
    for permission in permissions:
        role_permission = BackendRolePermission(role=role.id, permission=permission.codename)
        db.add(role_permission)
    
    db.commit()
    db.refresh(role)
    return role