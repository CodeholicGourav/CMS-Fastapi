from fastapi import APIRouter
from typing import List
from .schema import RegisterUser, ShowUser
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from .controller import create_user, all_backend_users

backendUserRoutes = APIRouter()

@backendUserRoutes.get("/get", response_model=List[ShowUser])
async def get_users_list(db : Session = Depends(get_db)):
    return all_backend_users(db)


@backendUserRoutes.post("/register", response_model=ShowUser)
def register(request: RegisterUser, db: Session = Depends(get_db)):
    return create_user(request, db)