# -*- coding: utf-8 -*-
"""
dependencies.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import base64
import math
import os
import random
import re
import secrets
import smtplib
import time
import urllib.parse
from email.message import EmailMessage
from email.mime.text import MIMEText
from typing import Optional

import requests
from fastapi import HTTPException, UploadFile, status
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaInMemoryUpload
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, HttpUrl
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
    STRIPE_CLIENT: str
    STRIPE_SECRET: str
    PAYPAL_CLIENT: str
    PAYPAL_SECRET: str
    RAZORPAY_CLIENT: str
    RAZORPAY_SECRET: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ShowUser(BaseModel):
    """
    Represents a user with specific fields such as UUID, username, email, and verification token.
    """

    uuid: str
    username: str
    email: str
    profile_photo: Optional[str] = None
    verification_token: Optional[str] = None


class Hash:
    """
    The `Hash` class provides methods for hashing and verifying passwords using bcrypt algorithm.
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
        Verifies a plain password against a hashed password and returns a boolean.

        Args:
            hashed_password (str): The hashed password to be verified against.
            plain_password (str): The plain password to be verified.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        return Hash.pwd_cxt.verify(plain_password, hashed_password)


class FrontendEmail:
    """
    A class responsible for sending email verification tokens and forget password tokens to users.
    """

    @staticmethod
    def send_email_verification_token(user: ShowUser):
        """
        Sends an email verification token to the specified user's email address.
        """
        subject = "Email Verification"

        base_url = (
            f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.EMAIL_VERIFY_ENDPOINT_FRONTEND_USER}"
        )
        verification_token = urllib.parse.quote(user.verification_token)
        verification_link = f"{base_url}?token={verification_token}"
        message = MIMEText(
            f"Click the following link to verify your email: {verification_link}"
        )
        return send_mail(user.email, subject, message)

    @staticmethod
    def send_forget_password_token(user: ShowUser):
        """
        Sends a forget password token to the specified user's email address.
        """
        subject = "Reset password"
        base_url = f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.CREATE_PASSWORD_ENDPOINT_FRONTEND_USER}"
        verification_token = urllib.parse.quote(user.verification_token)
        verification_link = f"{base_url}?token={verification_token}"
        message = MIMEText(
            f"Click the following link to reset your password: {verification_link}"
        )
        return send_mail(user.email, subject, message)


class BackendEmail:
    """
    A class responsible for sending email verification tokens and forget password tokens to users.
    """

    @staticmethod
    def send_email_verification_token(user: ShowUser) -> bool:
        """
        Sends an email verification token to the specified user's email address.
        """
        subject = "Email Verification"
        base_url = (
            f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.EMAIL_VERIFY_ENDPOINT_BACKEND_USER}"
        )
        verification_token = urllib.parse.quote(user.verification_token)
        verification_link = f"{base_url}?token={verification_token}"
        message = MIMEText(
            f"Click the following link to verify your email: {verification_link}"
        )
        return send_mail(user.email, subject, message)

    @staticmethod
    def send_forget_password_token(user: ShowUser) -> bool:
        """
        Sends a forget password token to the specified user's email address.
        """
        subject = "Reset password"
        base_url = (
            f"{SETTINGS.FRONTEND_HOST}/{SETTINGS.CREATE_PASSWORD_ENDPOINT_BACKEND_USER}"
        )
        verification_token = urllib.parse.quote(user.verification_token)
        verification_link = f"{base_url}?token={verification_token}"
        message = MIMEText(
            f"Click the following link to reset your password: {verification_link}"
        )
        return send_mail(user.email, subject, message)


class CustomValidations:
    """
    Contains static methods for performing custom validations on user input.
    """

    @staticmethod
    # pylint: disable=R0913
    def raize_custom_error(
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type: str = "",
        loc: str = "",
        msg: str = "",
        inp: str = "",
        ctx: dict = None,
    ):
        """
        Raises an HTTPException with a custom error detail.
        """
        detail = {
            "detail": [
                {
                    "type": error_type,
                    "loc": ["body", loc],
                    "msg": msg,
                    "input": inp,
                    "ctx": ctx,
                }
            ]
        }
        raise HTTPException(status_code, detail)

    @staticmethod
    def validate_username(value: str):
        """
        Validates a given username value.

        Raises:
            HTTPException: If the value does not match the specified pattern.
        """
        pattern = r"^[a-zA-Z0-9_]+$"
        if not re.match(pattern, value):
            detail = {
                "detail": [
                    {
                        "type": "Invalid",
                        "loc": ["body", "username"],
                        "msg": "Invalid username",
                        "input": value,
                        "ctx": {
                            "username": "Should contain only letters, numbers, and underscores."
                        },
                    }
                ]
            }
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
            )

        return value

    @staticmethod
    def validate_password(value: str):
        """
        Validates a given password value.

        Raises:
            HTTPException: If the password does not meet the specified criteria.
        """
        pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@#$%^&+=!]).{8,}$"
        if not re.match(pattern, value):
            detail = {
                "detail": [
                    {
                        "type": "Invalid",
                        "loc": ["body", "password"],
                        "msg": "Invalid password",
                        "input": value,
                        "ctx": {
                            "password": (
                                "It should be: "
                                "At least 8 characters in length, "
                                "Contains at least one uppercase letter (A-Z), "
                                "Contains at least one lowercase letter (a-z), "
                                "Contains at least one digit (0-9), "
                                "Contains at least one special character "
                                "(e.g., !, @, #, $, %, etc.)."
                            )
                        },
                    }
                ]
            }
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
            )

        return value

    @staticmethod
    def validate_profile_photo(value: str):
        """
        Validates the file extension of a profile photo.

        Raises:
            HTTPException: If the file extension is not allowed.

        """
        allowed_extensions = ("jpg", "jpeg", "png")
        file_extension = value.split(".")[-1].lower()

        if file_extension not in allowed_extensions:
            detail = {
                "detail": [
                    {
                        "type": "Invalid",
                        "loc": ["body", "image"],
                        "msg": "Invalid image type",
                        "input": value,
                        "ctx": {"image": f"Use {allowed_extensions} files only"},
                    }
                ]
            }
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

        return value


def generate_token(length: int) -> str:
    """
    Generates a URL-safe token of a specified length.
    """
    return secrets.token_urlsafe(length)


def generate_uuid(unique_str: str) -> str:
    """
    Generates a unique identifier (UUID).
    """
    encoded_str = base64.urlsafe_b64encode(unique_str.encode("utf-8")).decode("utf-8")
    random_num = random.randint(1111, 9999)
    timestamp = math.floor(time.time())
    uuid = f"{encoded_str}{random_num}{timestamp}"
    return uuid


def send_mail(recipient_email: str, subject: str, message: str):
    """
    Sends an email to the specified recipient with the given subject and message.
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
    except smtplib.SMTPException as smtp_error:
        # Handle SMTP-related errors (e.g., authentication failure, connection issues)
        print(f"Failed to send email: {str(smtp_error)}")
        return False


def allowed_file(filename: str, allowed_extensions: set[str]):
    """
    Checks if a given filename has an allowed extension.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def generate_paypal_access_token():
    """
    This function generates an access token for PayPal API authentication.

    Returns:
        str: The access token for PayPal API authentication.
    """
    try:
        # Encode the PayPal client ID and secret using base64 encoding
        auth = base64.b64encode(
            f"{SETTINGS.PAYPAL_CLIENT}:{SETTINGS.PAYPAL_SECRET}".encode("utf-8")
        ).decode("utf-8")

        # Send a POST request to the PayPal API to obtain an access token
        response = requests.post(
            url=f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            data="grant_type=client_credentials",
            headers={"Authorization": f"Basic {auth}"},
            timeout=5,
        )

        # Check for HTTP errors
        response.raise_for_status()

        # Parse the response as JSON and extract the access token
        data = response.json()
        access_token = data["access_token"]

    except requests.exceptions.HTTPError as http_error:
        # Handle HTTP-related errors (e.g., 404, 500)
        CustomValidations.raize_custom_error(
            error_type="paypal_http_error",
            loc="paypal",
            msg=str(http_error),
            inp="paypal",
            ctx={"paypal": "http_error"},
        )

    except requests.exceptions.RequestException as req_error:
        # Handle network-related errors (e.g., connection timeout, DNS resolution error)
        CustomValidations.raize_custom_error(
            error_type="paypal_network_error",
            loc="paypal",
            msg=str(req_error),
            inp="paypal",
            ctx={"paypal": "network_error"},
        )

    # Return access token if successful, or handle the error cases above
    return access_token


def convert_currency(currency: str):
    """
    Convert the given currency to the default currency specified in the SETTINGS module.

    Raises:
        HTTPException: If the currency code is not valid or the API request fails.
    """
    conversion = requests.get(
        f"{CONVERSION_URL}/pair/{SETTINGS.DEFAULT_CURRENCY}/{currency}", timeout=5
    )
    conversion_json = conversion.json()
    if (
        conversion.status_code == status.HTTP_404_NOT_FOUND
        or conversion_json["result"] == "error"
    ):
        CustomValidations.raize_custom_error(
            error_type=conversion_json["error-type"],
            loc="currency",
            msg="Currency does not exist.",
            inp=currency,
            ctx={"currency": "exist"},
        )

    return conversion_json


def create_folder_if_not_exists(folder_path: str, creds: Credentials):
    """
    Creates a folder in Google Drive if it does not already exist.

    Args:
        folder_path (str): The path of the folder to be created.
        It should be in the format "Folder1/Folder2/Folder3".
        creds (Credentials): The Google Drive credentials object.
    """
    parts = folder_path.split("/")
    current_folder_id = "root"

    # Build the Google Drive service using the provided credentials
    service = build("drive", "v3", credentials=creds)
    try:
        for part in parts:
            # Check if the folder already exists in the current folder using the Drive v3 API
            folder_query = (
                f"'{current_folder_id}' in parents "
                "and mimeType='application/vnd.google-apps.folder' "
                "and name='{part}'"
            )
            # pylint: disable=E1101
            folder = service.files().list(q=folder_query).execute()

            if folder.get("files"):
                # If the folder exists, update current_folder_id with the folder's ID
                current_folder_id = folder["files"][0]["id"]
            else:
                # If the folder does not exist,
                # create the folder with the given name and parent folder ID (if available)
                folder_metadata = {
                    "name": part,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [current_folder_id] if current_folder_id else [],
                }
                # pylint: disable=E1101
                folder = (
                    service.files().create(body=folder_metadata, fields="id").execute()
                )
                current_folder_id = folder["id"]
    except HttpError as error:
        CustomValidations.raize_custom_error(
            error_type="drive",
            loc="google_drive",
            msg=str(error),
            inp="",
            ctx={"drive": "unexpected error"},
        )

    return folder


async def upload_to_drive(file: UploadFile, creds: Credentials, folder_id):
    """
    Uploads a file to Google Drive using the Google Drive API.
    """
    try:
        # Read the file content and create a MediaInMemoryUpload object
        content = await file.read()
        media = MediaInMemoryUpload(content, mimetype=file.content_type)

        # Call the Drive v3 API
        service = build("drive", "v3", credentials=creds)

        # pylint: disable=E1101
        created_file = (
            service.files()
            .create(
                body={
                    "name": f"{math.floor(time.time())}_{file.filename}",
                    "parents": [folder_id],
                },
                media_body=media,
            )
            .execute()
        )

    except HttpError as error:
        CustomValidations.raize_custom_error(
            error_type="drive",
            loc="google_drive",
            msg=str(error),
            inp="",
            ctx={"drive": "unexpected error"},
        )

    return created_file


SETTINGS = Settings()

TEMPLATES = os.path.join(os.path.dirname(__file__), "templates")

STATIC_FOLDER = "static"

UPLOAD_FOLDER = STATIC_FOLDER + "/uploads"

PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"

# Maximum hours for token validation
TOKEN_VALIDITY = 72

# Maximum number of tokens for single user
TOKEN_LIMIT = 5

# Conversion api endpoint
CONVERSION_URL = "https://v6.exchangerate-api.com/v6/3a1bbc03599e950fa56cda33"

# Define allowed image file extensions
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}

# Define allowed file extensions
ALLOWED_FILE_EXTENSIONS = {
    "csv",
    "xlsx",
    "pdf",
    "jpg",
    "png",
    "page",
    "word",
    "ppt",
    "txt",
    "webp",
}

# Define maximu file size
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

predefined_backend_permissions = [
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
    {
        "permission": "Can create subscription",
        "type": 4,
        "codename": "create_subscription",
    },
    {"permission": "Can read subscription", "type": 4, "codename": "read_subscription"},
    {
        "permission": "Can Update subscription",
        "type": 4,
        "codename": "update_subscription",
    },
    {
        "permission": "Can delete subscription",
        "type": 4,
        "codename": "delete_subscription",
    },
]

predefined_organization_permissions = [
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
    {"permission": "Can create project", "type": 4, "codename": "create_project"},
    {"permission": "Can read project", "type": 4, "codename": "read_project"},
    {"permission": "Can update project", "type": 4, "codename": "update_project"},
    {"permission": "Can delete project", "type": 4, "codename": "delete_project"},
]

predefined_project_permissions = [
    {"permission": "Can create task", "type": 1, "codename": "create_task"},
    {"permission": "Can update task", "type": 1, "codename": "update_task"},
    {"permission": "Can assign task", "type": 2, "codename": "assign_task"},
    {"permission": "Can create column", "type": 3, "codename": "create_column"},
]

predefined_feature = [
    {"feature_type": "Can create organization", "feature_code": "create_organization"},
    {"feature_type": "Can add member", "feature_code": "add_member"},
    {"feature_type": "Can add task", "feature_code": "add_task"},
    {"feature_type": "Can create chat", "feature_code": "add_chat"},
]
