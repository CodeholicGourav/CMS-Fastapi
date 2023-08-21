from .schema import RegisterUser
from sqlalchemy.orm import Session
from dependencies import Hash
from .model import BackendUser
# from fastapi import Depends
# from database import get_db


def all_backend_users( db: Session):
    return db.query(BackendUser).all()


def create_user(user: RegisterUser, db: Session):
    new_user = BackendUser(
        username=user.username,
        email=user.email,
        password=Hash.bcrypt(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user