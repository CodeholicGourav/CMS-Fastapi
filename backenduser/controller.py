from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token
from . import schema, model
from datetime import datetime, timedelta
from fastapi import HTTPException,status


def all_backend_users(limit : int, offset : int, db: Session):
    return db.query(model.BackendUser).limit(limit).offset(offset).all()


def create_user(user: schema.RegisterUser, db: Session):
    existing_user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == user.email) 
        | 
        (model.BackendUser.username == user.username)
    ).first()

    if existing_user:
        if user.username == existing_user.username :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username already in use")
        
        if user.email == existing_user.email :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already in use")
    
    new_user = model.BackendUser(
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
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == token,
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    
    user.email_verified_at = datetime.utcnow()
    user.verification_token = None 
    db.commit()
    return {"message": "Email verified successfully"}
    

def create_auth_token(request: schema.LoginUser, db: Session):
    user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == request.username_or_email) 
        |
        (model.BackendUser.username == request.username_or_email),
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your email first!")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    token = model.BackendToken(
        token = generate_token(16),
        user_id = user.uuid,
        expire_at = datetime.utcnow() + timedelta(hours=24)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def send_verification_mail(email: str, db: Session):
    user = db.query(model.BackendUser).filter(
        model.BackendUser.email == email,
        model.BackendUser.is_deleted == False
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


def create_new_password(request: schema.ForgotPassword, db: Session):
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == request.token,
        model.BackendUser.is_deleted == False
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


def create_permission(request: schema.BasePermission, db: Session) :
    existingPermission = db.query(model.BackendPermission).filter(model.BackendPermission.codename==request.codename).first()
    if existingPermission:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exist!")
    
    newPermission = model.BackendPermission(
        permission = request.permission,
        type = request.type,
        codename = request.codename
    )

    db.add(newPermission)
    db.commit()
    db.refresh(newPermission)
    return newPermission


def add_role(request: schema.CreateRole, user: schema.CreateRole, db : Session):
    new_role = model.BackendRole(
        role = request.role,
        created_by = user.uuid
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


def assign_permissions(request : schema.AssignPermissions, db : Session):
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid==request.ruid, 
        model.BackendRole.is_deleted==False
    ).first()

    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found!")
    
    codenames = request.permissions
    permissions = db.query(model.BackendPermission).filter(model.BackendPermission.codename.in_(codenames)).all()
    # if len(permissions) != len(codenames):
    #     raise HTTPException(status_code=400, detail="Some permissions do not exist")

    # Associate permissions with the role
    for permission in permissions:
        role_permission = model.BackendRolePermission(role=role.id, permission=permission.codename)
        db.add(role_permission)
    
    db.commit()
    db.refresh(role)
    return role