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


@frontendUserRoutes.get("/verify-token", status_code=status.HTTP_202_ACCEPTED, description="Verify the token sent to email to verify your email address.") #Update email verification
def verify_email_token(
    token: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.verify_email(token, db)


@frontendUserRoutes.post("/login", response_model= schema.ShowToken, status_code=status.HTTP_200_OK) #Create login token
def login(
    request: schema.LoginUser, 
    db: Session = Depends(get_db),
): return controller.create_auth_token(request, db)


""" @backendUserRoutes.delete("/logout", status_code=status.HTTP_204_NO_CONTENT, description="Logout from all devices.") #Delete login token
def logout(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.delete_token(current_user, db) """


""" @backendUserRoutes.get("/send-token", status_code=status.HTTP_200_OK) #send forget password mail
def send_token(
    email: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.send_verification_mail(email, db) """


""" @backendUserRoutes.post('/create-password', response_model=schema.ShowUser, status_code=status.HTTP_201_CREATED) #Update password
def create_new_password(
    request: schema.ForgotPassword, 
    db: Session = Depends(get_db)
): return controller.create_new_password(request, db) """