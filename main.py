from fastapi import Depends, FastAPI
from backenduser.routes import backendUserRoutes 
from backenduser import model as backendModel
from database import engine
import sys
import uvicorn
import getpass
from dependencies import Hash
from database import SessionLocal
from dependencies import BackendEmail
import secrets

def run():
    app = FastAPI()

    app.include_router(
        backendUserRoutes,
        prefix="/backend-user",
        tags=["backend-user"],
        responses={404: {"description": "User not authenticated"}},
    )

    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")


def createsuperuser():
    db = SessionLocal()
    superuser = db.query(backendModel.BackendUser).filter(backendModel.BackendUser.role_id==0).first()
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
        db.close()

    superuser = backendModel.BackendUser(
        username=username,
        email=email,
        password=Hash.bcrypt(password),
        role_id=0,
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
    if sys.argv[1] == 'migrate':
        print("Migrating all tables...")
        backendModel.Base.metadata.create_all(bind=engine)

    elif sys.argv[1] == 'run':
        print("Running server")
        run()

    elif sys.argv[1] == 'createsuperuser':
        createsuperuser()
    
    else:
        print("No command found. Try 'run' or 'migrate' instead.")

if __name__ == '__main__':
    main()