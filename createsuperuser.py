import getpass
from backenduser.model import BackendUser, BackendRole
from dependencies import Hash
from database import SessionLocal


def createsuperuser():
    db = SessionLocal()
    superuser = db.query(BackendUser).filter(BackendUser.role_id==0).first()

    if superuser:
        print("Superuser already created!")
        return

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = getpass.getpass("Enter password: ")

    superuserrole = BackendRole(
        id=0,
        ruid="0",
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
    )

    db = SessionLocal()
    db.add(superuser)
    db.commit()
    db.close()
    print("Superuser account created successfully.")

if __name__ == '__main__':
    createsuperuser()