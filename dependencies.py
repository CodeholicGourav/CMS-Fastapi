from email.message import EmailMessage
import base64
import math
import random
import re
import secrets
import time

from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration class that defines various settings for the application.
    """
    SECRET_KEY: str
    APP_NAME: str = "Code-CMS"
    APP_URL: HttpUrl = "http://127.0.0.1:8000"
    ALLOWED_ORIGINS: list[str]
    DB_URL: str = "sqlite:///./sql_app.db"
    DEBUG: bool = True
    LANGUAGE_CODE: str = "en-us"
    USE_TZ: bool = True
    TIME_ZONE: str = "UTC"
    DEFAULT_CURRENCY: str = "USD"
    DEVELOPMENT: bool = True
    MAIL_HOST: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM_ADDRESS: EmailStr
    MAIL_FROM_NAME: str = APP_NAME
    FRONTEND_HOST: str = "127.0.0.1:3000"
    EMAIL_VERIFY_ENDPOINT_FRONTEND_USER: str = "frontend-user/verify-token"
    CREATE_PASSWORD_ENDPOINT_FRONTEND_USER: str = "frontend-user/create-password"
    EMAIL_VERIFY_ENDPOINT_BACKEND_USER: str = "backend-user/verify-token"
    CREATE_PASSWORD_ENDPOINT_BACKEND_USER: str = "backend-user/create-password"
    STRIPE_SECRET: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


SETTINGS = Settings()

def generate_token(length: int) -> str:
    """
    Generates a URL-safe token of a specified length.

    Args:
        length (int): The length of the token to be generated.

    Returns:
        str: A URL-safe token of the specified length.
    """
    return secrets.token_urlsafe(length)


def generate_uuid(unique_str: str) -> str:
    """
    Generates a unique identifier (UUID) by combining a base64-encoded string, a random number, and the current timestamp.

    Args:
        unique_str (str): The unique string to be encoded.

    Returns:
        str: The generated UUID.
    """
    encoded_str = base64.urlsafe_b64encode(unique_str.encode('utf-8')).decode('utf-8')
    random_num = random.randint(1111, 9999)
    timestamp = math.floor(time.time())
    uuid = f"{encoded_str}{random_num}{timestamp}"
    return uuid

class Hash:
    """
    The `Hash` class provides methods for hashing and verifying passwords using the bcrypt algorithm.
    """

    pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def bcrypt(password: str) -> str:
        """
        Hashes a password using the bcrypt algorithm and returns the hashed password.

        Args:
            password (str): The plain password to be hashed.

        Returns:
            str: The hashed password.
        """
        return Hash.pwd_cxt.hash(password)

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        """
        Verifies a plain password against a hashed password and returns a boolean indicating whether the password is valid.

        Args:
            hashed_password (str): The hashed password to be verified against.
            plain_password (str): The plain password to be verified.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        return Hash.pwd_cxt.verify(plain_password, hashed_password)
    

import smtplib
from email.mime.text import MIMEText

class BaseEmail:
    """
    The `BaseEmail` class provides a method for sending emails using the SMTP protocol.
    """

    def sendMail(self, recipient_email: str, subject: str, message: str) -> bool:
        """
        Sends an email to the specified recipient with the given subject and message.

        Args:
            recipient_email (str): The email address of the recipient.
            subject (str): The subject of the email.
            message (str): The body of the email.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        sender_email = SETTINGS.MAIL_USERNAME
        sender_password = SETTINGS.MAIL_PASSWORD

        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(message)

        try:
            with smtplib.SMTP(SETTINGS.MAIL_HOST, SETTINGS.MAIL_PORT) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print("Email sent successfully.")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

class ShowUser(BaseModel):
    uuid : str
    username : str
    email : str
    verification_token: str

class FrontendEmail(BaseEmail):
    """
    The `FrontendEmail` class is responsible for sending email verification and password reset emails to frontend users.
    It extends the `BaseEmail` class and overrides two methods: `sendEmailVerificationToken` and `sendForgetPasswordToken`.
    """

    def sendEmailVerificationToken(self, user: ShowUser):
        """
        Sends an email verification token to the specified user's email address.
        It constructs the verification link using the user's verification token and the frontend endpoint for email verification.
        It then calls the `sendMail` method from the `BaseEmail` class to send the email.

        Args:
            user (ShowUser): The user object containing the necessary information.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "Email Verification"
        verification_link = f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.EMAIL_VERIFY_ENDPOINT_FRONTEND_USER}?token={user.verification_token}"
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)

    def sendForgetPasswordToken(self, user: ShowUser):
        """
        Sends a forget password token to the specified user's email address.
        It constructs the reset password link using the user's verification token and the frontend endpoint for creating a new password.
        It then calls the `sendMail` method from the `BaseEmail` class to send the email.

        Args:
            user (ShowUser): The user object containing the necessary information.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "Reset password"
        verification_link = f"{SETTINGS.FRONTEND_HOST}/{Settings.CREATE_PASSWORD_ENDPOINT_FRONTEND_USER}?token={user.verification_token}"
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)


class BackendEmail(BaseEmail):
    def sendEmailVerificationToken(self, user: ShowUser):
        """
        Sends an email verification token to the specified user's email address.

        Args:
            user (ShowUser): The user object containing the email and verification token.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "Email Verification"
        verification_link = f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.EMAIL_VERIFY_ENDPOINT_BACKEND_USER}?token={user.verification_token}"
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)
    
    def sendForgetPasswordToken(self, user: ShowUser):
        """
        Sends a forget password token to the specified user's email address.

        Args:
            user (ShowUser): The user object containing the email and verification token.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        subject = "Reset password"
        verification_link = f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.CREATE_PASSWORD_ENDPOINT_BACKEND_USER}?token={user.verification_token}"
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)
    

class CustomValidations():
    def customError(status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY, type: str = "", loc: str = "", msg: str = "", inp: str = "", ctx: dict = {}):
        """
        Raises an HTTPException with a custom error detail.

        Args:
            status_code (int, optional): The HTTP status code to be returned in the response. Default is 422 (Unprocessable Entity).
            type (str, optional): The type of the error.
            loc (str, optional): The location of the error.
            msg (str, optional): The error message.
            inp (str, optional): The input value that caused the error.
            ctx (dict, optional): Additional context information related to the error.
        """
        detail = {
            "detail": [
                {
                    "type": type,
                    "loc": ["body", loc],
                    "msg": msg,
                    "input": inp,
                    "ctx": ctx,
                }
            ]
        }
        raise HTTPException(status_code, detail)
    

    def validate_username(value: str) -> str:
        """
        Validates a given username value.

        Args:
            value (str): The username value to be validated.

        Returns:
            str: The validated username value.

        Raises:
            HTTPException: If the value does not match the specified pattern.
        """
        pattern = r'^[a-zA-Z0-9_]+$'
        if not re.match(pattern, value):
            detail = {
                "detail": [
                    {
                        "type": "Invalid",
                        "loc": ["body", "username"],
                        "msg": "Invalid username",
                        "input": value,
                        "ctx": {"username": "It should contain only letters, numbers, and underscores."},
                    }
                ]
            }
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

        return value
    

    def validate_password(value: str) -> str:
        """
        Validates a given password value.

        Args:
            value (str): The password value to be validated.

        Returns:
            str: The validated password value.

        Raises:
            HTTPException: If the password does not meet the specified criteria.
        """
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$'
        if not re.match(pattern, value):
            detail = {
                "detail": [
                    {
                        "type": "Invalid",
                        "loc": ["body", "password"],
                        "msg": "Invalid password",
                        "input": value,
                        "ctx": {
                            "password": "It should be: At least 8 characters in length, Contains at least one uppercase letter (A-Z), Contains at least one lowercase letter (a-z), Contains at least one digit (0-9), Contains at least one special character (e.g., !, @, #, $, %, etc.)."
                        },
                    }
                ]
            }
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

        return value


    def validate_profile_photo(value: str) -> str:
        """
        Validates the file extension of a profile photo.

        Args:
            value (str): The file name or path of the profile photo.

        Returns:
            str: The validated file name or path of the profile photo.

        Raises:
            HTTPException: If the file extension is not allowed.

        """
        allowed_extensions = ("jpg", "jpeg", "png")
        file_extension = value.split(".")[-1].lower()
    
        if file_extension not in allowed_extensions:
            detail = {
                "detail": [{
                    "type": "Invalid",
                    "loc": ["body", "image"],
                    "msg": "Invalid image type",
                    "input": value,
                    "ctx": {"image": f"Only {allowed_extensions} files are allowed for profile_photo"},
                }]
            }
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)
    
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