from sqlalchemy.orm import Session
from dependencies import Hash, FrontendEmail, generate_token, TOKEN_LIMIT, TOKEN_VALIDITY, CustomValidations
from . import schema, model
from datetime import datetime, timedelta
from fastapi import HTTPException,status
from dateutil.relativedelta import relativedelta
import getpass
import secrets


def register_user(data: schema.RegisterUser, db: Session):
    """ Creates a new Frontend user """
    existing_user = db.query(model.FrontendUser).filter(
        (model.FrontendUser.email == data.email) 
        | 
        (model.FrontendUser.username == data.username)
    ).first()

    if existing_user:
        if data.username == existing_user.username :
            CustomValidations.customError(
                type="exist", 
                loc= "username", 
                msg= "Username already in use", 
                inp= data.username,
                ctx={"username": "unique"}
            )
        
        if data.email == existing_user.email :
            CustomValidations.customError(
                type="exist", 
                loc= "email", 
                msg= "Email already in use", 
                inp= data.email,
                ctx={"email": "unique"}
            )
        
    new_user = model.FrontendUser(
        username=data.username,
        email=data.email,
        password=Hash.bcrypt(data.password),
        verification_token = generate_token(32),
    )

    if data.first_name: 
        new_user.first_name = data.first_name

    if data.last_name: 
        new_user.last_name = data.last_name

    if data.language: 
        new_user.language = data.language

    if data.timezone: 
        exist_timezone = db.query(model.Timezone).filter_by(code=data.timezone).first()
        if not exist_timezone:
            CustomValidations.customError(
                type="not_exist", 
                loc= "timezone", 
                msg= "Timezone does not exist.", 
                inp= data.timezone,
                ctx={"timezone": "exist"}
            )
        new_user.timezone = data.timezone
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    frontendEmail = FrontendEmail()
    if frontendEmail.sendEmailVerificationToken(new_user):
        return new_user
    else:
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="Internal", 
            loc= "email", 
            msg= "Cannot send email.", 
            inp= data.email,
        )


def userDetails(user_id: str, db: Session):
    """ Returns all details of the user """
    user =  db.query(model.FrontendUser).filter_by(uuid=user_id).first()
    if not user: 
        CustomValidations.customError(
            type="not_exist", 
            loc= "user_id", 
            msg= "User does not exist", 
            inp= user_id,
            ctx={"user": "exist"}
        )
    return user


def updateUser(data: schema.UpdateUser, db: Session):
    user = db.query(model.FrontendUser).filter_by(uuid=data.user_id).first()
    if not user:
        CustomValidations.customError(
            type="not_exist", 
            loc= "user_id", 
            msg= "No user found.", 
            inp= data.user_id,
            ctx={"user_id": "exist"}
        )
    
    if data.is_active is not None: user.is_active = data.is_active
    if data.is_deleted is not None: user.is_deleted = data.is_deleted
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def verify_email(token: str, db: Session):
    """ Verify email through token and enable user account login """
    user = db.query(model.FrontendUser).filter(
        model.FrontendUser.verification_token == token,
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist", 
            loc= "token", 
            msg= "Invalid verification token", 
            inp= token,
            ctx={"token": "exist"}
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="deactive", 
            loc= "account", 
            msg= "Your account is deactivated!", 
            inp= token,
            ctx={"account": "active"}
        )

    user.email_verified_at = datetime.utcnow()
    user.verification_token = None 
    db.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, db: Session):
    """ Create a login token for backend user """
    user = db.query(model.FrontendUser).filter(
        (model.FrontendUser.email == request.username_or_email) |
        (model.FrontendUser.username == request.username_or_email),
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed", 
            loc= "username_or_email", 
            msg= "Email/Userame is wrong!", 
            inp= request.username_or_email,
            ctx={"username_or_email": "exist"}
        )
    
    if not Hash.verify(user.password, request.password):
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed", 
            loc= "password", 
            msg= "Password is wrong!", 
            inp= request.password,
            ctx={"password": "match"}
        )
    
    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required", 
            msg= "Verify your email first!", 
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended", 
            msg= "Your account is suspended!", 
        )
    
    tokens_count = db.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id, 
        model.BackendToken.expire_at > datetime.now()
    ).count()
    if tokens_count>=TOKEN_LIMIT:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="limit_exceed", 
            msg= f"Login limit exceed (${TOKEN_LIMIT}).", 
        )
    
    token = model.BackendToken(
        token = generate_token(16),
        user_id = user.id,
        expire_at = datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


