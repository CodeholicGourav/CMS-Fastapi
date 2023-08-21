import getpass
from backenduser.model import BackendUser, BackendRole
from dependencies import Hash
from database import SessionLocal
from dependencies import BackendEmail
import secrets


def createsuperuser():
    db = SessionLocal()
    superuser = db.query(BackendUser).filter(BackendUser.role_id==0).first()
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
    superuserrole = db.query(BackendRole).filter(BackendRole.id==0).first()
    db.close()
    if not superuserrole:
        superuserrole = BackendRole(
            id=0,
            role="superuser"
        )
        
        db = SessionLocal()
        db.add(superuserrole)
        db.commit()
        db.close()


    superuser = BackendUser(
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
    BackendEmail.sendVerificationToken(superuser)
    print("Superuser account created successfully.")

if __name__ == '__main__':
    createsuperuser()