from typing import Annotated
from dotenv import load_dotenv
from pathlib import Path
import os
import secrets
from fastapi import Header, HTTPException, status
from passlib.context import CryptContext
from backenduser.model import BackendUser, BackendToken
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db



env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


async def authenticate_token(authtoken: Annotated[str, Header()], db : Session = Depends(get_db)):
    user_token = db.query(BackendToken).filter(BackendToken.token==authtoken).first()
    if not user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification token")
    
    return user_token.user


def generate_token(len:int):
    return secrets.token_urlsafe(len)  # Generates a URL-safe token of 32 characters


pwd_cxt = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Hash():
    def bcrypt(password: str):
        return pwd_cxt.hash(password)

    def verify(hashed_password,plain_password):
        return pwd_cxt.verify(plain_password,hashed_password)
    

import smtplib
from email.mime.text import MIMEText
class BackendEmail():
    def sendVerificationToken(user: BackendUser):
        # Email configuration
        sender_email = os.getenv('MAIL_USERNAME')
        sender_password = os.getenv('MAIL_PASSWORD')
        recipient_email = user.email
        subject = "Email Verification"
        verification_link = f"{os.getenv('EMAIL_VERIFY_URL')}?token={user.verification_token}"  # Include the verification token in the link

        # Create the email content
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
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
        except Exception as e:
            print(f"Failed to send email: {str(e)}")