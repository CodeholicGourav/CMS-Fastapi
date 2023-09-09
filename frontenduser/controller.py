from sqlalchemy.orm import Session
from dependencies import Hash, FrontendEmail, generate_token, generate_uuid, TOKEN_LIMIT, TOKEN_VALIDITY, CustomValidations, allowed_file, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS
from . import schema, model
from datetime import datetime, timedelta
from fastapi import status, UploadFile
from backenduser import controller as backendusercontroller
import time
import math


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
        uuid=generate_uuid(data.username),
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


def userList(limit, offset, db: Session):
    return db.query(model.FrontendUser).limit(limit).offset(offset).all()


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


def updateProfilePhoto(file: UploadFile, user: model.FrontendUser, db: Session):

    # Check if the file is an allowed image type
    if not allowed_file(file.filename):
        CustomValidations.customError(
            type="invalid", 
            loc= "image", 
            msg= f"Allowed extensions are {ALLOWED_EXTENSIONS}", 
            inp= file.filename,
            ctx={"image": "invalid type"}
        )

    # Check file size
    if file.size > MAX_FILE_SIZE_BYTES:
        CustomValidations.customError(
            type="invalid", 
            loc= "image", 
            msg= f"Maximum image size should be {MAX_FILE_SIZE_BYTES} bytes" , 
            inp= f"{file.size} bytes",
            ctx={"image": "Big size"}
        )

    file_extension = file.filename.split(".")[-1]
    
    if user.profile_photo:
        unique_filename = user.profile_photo
    else:
        unique_filename = f"{math.floor(time.time())}_{user.username}.{file_extension}"

    with open(f"uploads/{unique_filename}", "wb") as image_file:
        image_file.write(file.file.read())

    user.profile_photo = unique_filename
    db.commit()
    db.refresh(user)
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
    user.updated_at = datetime.utcnow()
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
    
    tokens_count = db.query(model.FrontendToken).filter(
        model.FrontendToken.user_id == user.id, 
        model.FrontendToken.expire_at > datetime.now()
    ).count()
    if tokens_count>=TOKEN_LIMIT:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="limit_exceed", 
            msg= f"Login limit exceed (${TOKEN_LIMIT}).", 
        )
    
    token = model.FrontendToken(
        token = generate_token(16),
        user_id = user.id,
        expire_at = datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def delete_token(user: model.FrontendUser, db: Session):
    """ Deletes the login token """
    db.query(model.FrontendToken).filter_by(user_id=user.id).delete()
    db.commit()
    return True


def send_verification_mail(email: str, db: Session):
    """ sends a token in mail for forget password """
    user = db.query(model.FrontendUser).filter(
        model.FrontendToken.email == email,
        model.FrontendUser.is_deleted == False
    ).first()
    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist", 
            loc= "email", 
            msg= "No account found.", 
            inp= email,
            ctx={"email": "exist"}
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended", 
            msg= "Your account is suspended!", 
        )
    
    user.verification_token = generate_token(32)
    db.commit() 
    db.refresh(user)
    frontendemail = FrontendEmail()
    if frontendemail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else :
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="mail_sent_error", 
            msg= "Cannot send email.", 
        )


def create_new_password(request: schema.ForgotPassword, db: Session):
    """ Verify the token and change the password of the user """
    user = db.query(model.FrontendUser).filter(
        model.FrontendUser.verification_token == request.token,
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="expired", 
            loc= "token", 
            msg= "Token is expired!", 
            inp= request.token,
            ctx={"token": "valid"}
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
    
    user.password = Hash.bcrypt(request.password)
    user.verification_token = None 
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def updateProfile(request: schema.UpdateProfile, user: model.FrontendUser, db: Session):
    if request.username:
        existing_user = db.query(model.FrontendUser).filter_by(username = request.username).first()
        if existing_user:
            CustomValidations.customError(
                type="exist", 
                loc= "username", 
                msg= "Username already in use", 
                inp= request.username,
                ctx={"username": "unique"}
            )
        user.username = request.username

    if request.timezone :
        exist_timezone = db.query(model.Timezone).filter_by(code=request.timezone).first()
        if not exist_timezone:
            CustomValidations.customError(
                type="not_exist", 
                loc= "timezone", 
                msg= "Timezone does not exist.", 
                inp= request.timezone,
                ctx={"timezone": "exist"}
            )
        user.timezone = request.timezone

    if request.first_name :
        user.first_name = request.first_name

    if request.last_name :
        user.last_name = request.last_name

    if request.language :
        user.language = request.language

    if request.storage_token :
        user.storage_token = request.storage_token

    if request.storage_platform :
        user.storage_platform = request.storage_platform

    if request.social_token :
        user.social_token = request.social_token

    if request.social_platform :
        user.social_platform = request.social_platform

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def all_subscription_plans(limit: int, offset: int, db: Session):
    return backendusercontroller.all_subscription_plans(limit, offset, db)


def timezonesList(db: Session):
    return db.query(model.Timezone).all()