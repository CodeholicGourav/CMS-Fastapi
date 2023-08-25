from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backenduser.routes import backendUserRoutes 
from backenduser import model as backendModel
from database import engine
import sys
import uvicorn
import getpass
from dependencies import Hash
from database import SessionLocal
import secrets
from dotenv import load_dotenv
from pathlib import Path
import os
from dependencies import BackendEmail


env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()
allowed_origins = os.getenv('ALLOWED_ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict HTTP methods if needed
    allow_headers=["*"],  # You can restrict headers if needed
)

app.include_router(
    backendUserRoutes,
    prefix="/backend-user",
    tags=["backend-user"],
    responses={404: {"description": "User not authenticated"}},
)

def run():
    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")


def createsuperuser():
    db = SessionLocal()
    superuser = db.query(backendModel.BackendUser).filter(backendModel.BackendUser.id==0).first()
    db.close()

    if superuser:
        print("Superuser already exist!")
        return

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = "garbage"
    c_password = "garrbage2"
    while password!=c_password:
        password = getpass.getpass("Enter password: ")
        c_password = getpass.getpass("Enter password to confirm: ")
        if password!=c_password:
            print("Password did not match, please try again.")

    db = SessionLocal()
    superuserrole = db.query(backendModel.BackendRole).filter(backendModel.BackendRole.id==0).first()
    db.close()
    if not superuserrole:
        superuserrole = backendModel.BackendRole(id=0, role="superuser") 

        db = SessionLocal()
        db.add(superuserrole)
        db.commit()
        db.refresh(superuserrole)
        db.close()

    superuser = backendModel.BackendUser(
        id=0,
        username=username,
        email=email,
        password=Hash.bcrypt(password),
        role_id=superuserrole.ruid,
        verification_token = secrets.token_urlsafe(32)  # Generates a URL-safe token of 32 characters
    )

    db = SessionLocal()
    db.add(superuser)
    db.commit()
    db.refresh(superuser)
    backendEmail = BackendEmail()
    if not backendEmail.sendEmailVerificationToken(superuser):
        print("Can't send email.")

    print("Superuser account created successfully.")


def main():
    match sys.argv[1]:
        case 'migrate':
            print("Migrating all tables...")
            backendModel.Base.metadata.create_all(bind=engine)
        
        case 'drop':
            ans = input("Are you sure to delete all tables? (y/n) :")
            if ans=="y" or ans=="Y":
                print("Dropping all tables...")
                backendModel.Base.metadata.drop_all(bind=engine)
            print("exited.")

        case 'run':
            run()

        case 'createsuperuser':
            createsuperuser()
        
        case _:
            print("No command found. Try 'run', 'migrate', 'createsuperuser' instead.")


if __name__ == '__main__':
    main()

