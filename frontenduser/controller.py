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