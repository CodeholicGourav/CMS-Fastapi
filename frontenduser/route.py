from fastapi import APIRouter, status, Query, Depends, UploadFile, File
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from . import controller, model, schema
from .middleware import authenticate_token
from dependencies import ALLOWED_EXTENSIONS

frontendUserRoutes = APIRouter()

@frontendUserRoutes.post("/register", response_model=schema.BaseUser, status_code=status.HTTP_201_CREATED) #Create user
def register(
    request: schema.RegisterUser, 
    db: Session = Depends(get_db),
): return controller.register_user(request, db)


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


@frontendUserRoutes.delete("/logout", status_code=status.HTTP_204_NO_CONTENT, description="Logout from all devices.") #Delete login token
def logout(
    db: Session = Depends(get_db),
    authToken: model.FrontendToken = Depends(authenticate_token)
): return controller.delete_token(authToken, db)


@frontendUserRoutes.delete("/logout-all", status_code=status.HTTP_204_NO_CONTENT, description="Logout from all devices.") #Delete login token
def logout_all(
    db: Session = Depends(get_db),
    authToken: model.FrontendToken = Depends(authenticate_token)
): return controller.delete_all_tokens(authToken, db)

@frontendUserRoutes.get("/send-token", status_code=status.HTTP_200_OK) #send forget password mail
def send_token(
    email: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.send_verification_mail(email, db)


@frontendUserRoutes.post('/create-password', response_model=schema.BaseUser, status_code=status.HTTP_201_CREATED) #Update password
def create_new_password(
    request: schema.ForgotPassword, 
    db: Session = Depends(get_db)
): return controller.create_new_password(request, db)


@frontendUserRoutes.post('/update-profile', response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Update profile
def update_profile(    
    data: schema.UpdateProfile,
    db : Session = Depends(get_db), 
    authToken: model.FrontendToken = Depends(authenticate_token),
): return controller.updateProfile(data, authToken, db)


@frontendUserRoutes.post('/update-profile-photo', response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Update profile
def update_profile_photo(    
    image: Annotated[UploadFile, File(description=f"A image file to use it as profile photo. Allowed extensions are {ALLOWED_EXTENSIONS}")],
    db : Session = Depends(get_db), 
    authToken: model.FrontendToken = Depends(authenticate_token),
): return controller.updateProfilePhoto(image, authToken, db)


@frontendUserRoutes.get('/subscriptions', response_model=List[schema.BaseSubscription], status_code=status.HTTP_200_OK) #Read all subscriptions
def all_subscriptions(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    # current_user: model.FrontendUser = Depends(authenticate_token),
): return controller.all_subscription_plans(limit, offset, db)


@frontendUserRoutes.get('/timezones', response_model=List[schema.TimeZones], status_code=status.HTTP_200_OK) #Read all subscriptions
def all_timezones( 
    db : Session = Depends(get_db), 
): return controller.timezonesList(db)

@frontendUserRoutes.post('/add-orders', response_model=schema.Orders,status_code=status.HTTP_201_CREATED)
def orders(
    request:schema.AddOrder,
    authToken:model.FrontendToken = Depends(authenticate_token),
    db: Session = Depends(get_db)
    
   
      
):
    return controller.add_orders(authToken,request,db)
            
    