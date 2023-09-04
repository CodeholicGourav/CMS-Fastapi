from fastapi import APIRouter, status, Query, Depends, Path, UploadFile, File
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from . import controller, model, schema
from middleware import authenticate_token, check_permission

frontendUserRoutes = APIRouter()

@frontendUserRoutes.post("/register", response_model=schema.BaseUser, status_code=status.HTTP_201_CREATED) #Create user
def register(
    request: schema.RegisterUser, 
    db: Session = Depends(get_db),
): return controller.register_user(request, db)


@frontendUserRoutes.get("/get", response_model=List[schema.BaseUser], status_code=status.HTTP_200_OK) #Read users
async def get_users_list(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    current_user = Depends(authenticate_token),
    permissions = Depends(check_permission(["read_user"])),
): return db.query(model.FrontendUser).limit(limit).offset(offset).all()


@frontendUserRoutes.get("/get/{user_id}", response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Read user
async def get_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    db : Session = Depends(get_db), 
    current_user = Depends(authenticate_token),
    permissions = Depends(check_permission(["read_user"])),
): return controller.userDetails(user_id, db)


@frontendUserRoutes.post("/update-user", response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Update / delete user
async def update_user_details(
    data: schema.UpdateUser,
    db : Session = Depends(get_db), 
    current_user = Depends(authenticate_token),
    permissions = Depends(check_permission(["update_user"])),
): return controller.updateUser(data, db)


