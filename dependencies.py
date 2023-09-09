from dotenv import load_dotenv
from pathlib import Path
import os
import re
import secrets
from passlib.context import CryptContext
from fastapi import HTTPException,status
import base64
import random
import time
import math
from pydantic import BaseModel


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

def generate_token(len:int):
    return secrets.token_urlsafe(len)  # Generates a URL-safe token of 32 characters


def generate_uuid(unique_str : str):
    return f"{base64.urlsafe_b64encode(unique_str.encode('utf-8')).decode('utf-8')}{random.randint(1111, 9999)}{math.floor(time.time())}"

pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Hash():
    def bcrypt(password: str):
        return pwd_cxt.hash(password)

    def verify(hashed_password,plain_password):
        return pwd_cxt.verify(plain_password,hashed_password)
    

import smtplib
from email.mime.text import MIMEText

class BaseEmail():
    def sendMail(self, recipient_email, subject, message):
        sender_email = os.getenv('MAIL_USERNAME')
        sender_password = os.getenv('MAIL_PASSWORD')
        
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject

        # Send the email
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
            print("Email sent successfully.")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str

class FrontendEmail(BaseEmail):
    def sendEmailVerificationToken(self, user: ShowUser):
        subject = "Email Verification"
        verification_link = f"{os.getenv('SERVER_URL')}/{os.getenv('EMAIL_VERIFY_ENDPOINT')}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)
    
    def sendForgetPasswordToken(self, user: ShowUser):
        subject = "Reset password"
        verification_link = f"{os.getenv('SERVER_URL')}/{os.getenv('CREATE_PASSWORD_URL')}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)


class BackendEmail(BaseEmail):
    def sendEmailVerificationToken(self, user: ShowUser):
        subject = "Email Verification"
        verification_link = f"{os.getenv('SERVER_URL')}/{os.getenv('EMAIL_VERIFY_ENDPOINT')}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)
    
    def sendForgetPasswordToken(self, user: ShowUser):
        subject = "Reset password"
        verification_link = f"{os.getenv('SERVER_URL')}/{os.getenv('CREATE_PASSWORD_URL')}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)
    

class CustomValidations():
    def customError(status_code:int=status.HTTP_422_UNPROCESSABLE_ENTITY, type:str="", loc:str="", msg:str="", inp:str="", ctx: dict={}):
        detail = {
            "detail": [{
                "type": type,
                "loc": ["body", loc],
                "msg": msg,
                "input": inp,
                "ctx": ctx,
            }]
        }
        raise HTTPException(status_code, detail)
    

    def validate_username(value):
        pattern=r'^[a-zA-Z0-9_]+$'
        if not re.match(pattern, value):
            detail = [{
                "type": "Invalid",
                "loc": ["body", "username"],
                "msg": "Invalid username",
                "input": value,
                "ctx": {"username": "It should contain only letters, numbers, and underscores."},
            }]
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)
        
        return value
    

    def validate_password(value):
        pattern=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$'
        if not re.match(pattern, value):
            detail = [{
                "type": "Invalid",
                "loc": ["body", "password"],
                "msg": "Invalid passwpord",
                "input": value,
                "ctx": {"password": "It should be : At least 8 characters in length, Contains at least one uppercase letter (A-Z), Contains at least one lowercase letter (a-z), Contains at least one digit (0-9), Contains at least one special character (e.g., !, @, #, $, %, etc.)."},
            }]
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)
        
        return value


    def validate_profile_photo(value):
        allowed_extensions = ("jpg", "jpeg", "png")
        file_extension = value.filename.split(".")[-1]
        if file_extension.lower() not in allowed_extensions:
            raise ValueError("Only JPG, JPEG, and PNG files are allowed for profile_photo")
        return value
    

# Maximum hours for token validation
TOKEN_VALIDITY = 72 

# Maximum number of tokens for single user
TOKEN_LIMIT = 5

# Conversion api endpoint
CONVERSION_URL = "https://v6.exchangerate-api.com/v6/3a1bbc03599e950fa56cda33"
# Define allowed image file extensions and size limit
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


predefined_permissions = [
        {"permission": "Can create user", "type": 1, "codename": "create_user"},
        {"permission": "Can read user", "type": 1, "codename": "read_user"},
        {"permission": "Can update user", "type": 1, "codename": "update_user"},
        {"permission": "Can delete user", "type": 1, "codename": "delete_user"},
        {"permission": "Can create role", "type": 2, "codename": "create_role"},
        {"permission": "Can read role", "type": 2, "codename": "read_role"},
        {"permission": "Can update role", "type": 2, "codename": "update_role"},
        {"permission": "Can delete role", "type": 2, "codename": "delete_role"},
        {"permission": "Can create permission", "type": 3, "codename": "create_permission"},
        {"permission": "Can read permission", "type": 3, "codename": "read_permission"},
        {"permission": "Can update permission", "type": 3, "codename": "update_permission"},
        {"permission": "Can delete permission", "type": 3, "codename": "delete_permission"},
        {"permission": "Can create subscription", "type": 4, "codename": "create_subscription"},
        {"permission": "Can read subscription", "type": 4, "codename": "read_subscription"},
        {"permission": "Can delete subscription", "type": 4, "codename": "delete_subscription"}
    ]