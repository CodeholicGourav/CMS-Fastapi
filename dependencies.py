from dotenv import load_dotenv
from pathlib import Path
import os
import secrets
from passlib.context import CryptContext
from backenduser.model import BackendUser
from frontendurls import *


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

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


class FrontendEmail(BaseEmail):
    def sendEmailVerificationToken(self, user: BackendUser):
        subject = "Email Verification"
        verification_link = f"{SERVER_URL}/{EMAIL_VERIFY_URL}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)
    
    def sendForgetPasswordToken(self, user: BackendUser):
        subject = "Reset password"
        verification_link = f"{SERVER_URL}/{CREATE_PASSWORD_URL}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)

class BackendEmail(BaseEmail):
    def sendEmailVerificationToken(self, user: BackendUser):
        subject = "Email Verification"
        verification_link = f"{SERVER_URL}/{EMAIL_VERIFY_URL}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to verify your email: {verification_link}")
        return self.sendMail(user.email, subject, message)
    
    def sendForgetPasswordToken(self, user: BackendUser):
        subject = "Reset password"
        verification_link = f"{SERVER_URL}/{CREATE_PASSWORD_URL}?token={user.verification_token}"  # Include the verification token in the link
        message = MIMEText(f"Click the following link to reset your password: {verification_link}")
        return self.sendMail(user.email, subject, message)