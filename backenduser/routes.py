from fastapi import APIRouter, status, Query, Depends, Path
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from . import controller, model, schema
from middleware import authenticate_token, check_permission

backendUserRoutes = APIRouter()


@backendUserRoutes.post("/register", response_model=schema.ShowUser, status_code=status.HTTP_201_CREATED) #Create user
def register(
    data: schema.RegisterUser, 
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_user"])),
): return controller.create_user(data, db)


@backendUserRoutes.get("/get", response_model=List[schema.ShowUser], status_code=status.HTTP_200_OK) #Read users
async def get_users_list(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_user"])),
): return controller.all_backend_users(limit, offset, db)


@backendUserRoutes.get("/get/{user_id}", response_model=schema.User, status_code=status.HTTP_200_OK) #Read user
async def get_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_user"])),
): return controller.userDetails(user_id, db)


@backendUserRoutes.post("/update-user", response_model=schema.User, status_code=status.HTTP_200_OK) #Update / delete user
async def update_user_details(
    data: schema.UpdateUser,
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_user"])),
): return controller.updateUserRole(data, db)



@backendUserRoutes.get("/verify-token", status_code=status.HTTP_200_OK, description="Verify the token sent to email to verify your email address.") #Update email verification
def verify_email_token(
    token: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.verify_email(token, db)


@backendUserRoutes.post("/login", response_model= schema.ShowToken, status_code=status.HTTP_200_OK) #Create login token
def login(
    request: schema.LoginUser, 
    db: Session = Depends(get_db),
): return controller.create_auth_token(request, db)


@backendUserRoutes.delete("/logout", status_code=status.HTTP_204_NO_CONTENT, description="Logout from all devices.") #Delete login token
def logout(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.delete_token(current_user, db)


@backendUserRoutes.get("/send-token", status_code=status.HTTP_200_OK) #send forget password mail
def send_token(
    email: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.send_verification_mail(email, db)


@backendUserRoutes.post('/create-password', response_model=schema.ShowUser, status_code=status.HTTP_201_CREATED) #Update password
def create_new_password(
    request: schema.ForgotPassword, 
    db: Session = Depends(get_db)
): return controller.create_new_password(request, db)


@backendUserRoutes.post('/create-permission', response_model=schema.BasePermission, status_code=status.HTTP_201_CREATED) #Create permissions
def create_permission(
    request : schema.BasePermission,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_permission"])),
): return controller.create_permission(request, db)


@backendUserRoutes.get('/permissions', response_model=List[schema.BasePermission], status_code=status.HTTP_200_OK) #Read permissions
def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_permission"])),
): return db.query(model.BackendPermission).all()


@backendUserRoutes.post('/add-role', response_model=schema.ShowRole, status_code=status.HTTP_201_CREATED) #Create role
def create_new_roles(
    request : schema.CreateRole,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_role"])),
): return controller.add_role(request, current_user, db)


@backendUserRoutes.get('/roles', response_model=List[schema.ShowRole], status_code=status.HTTP_200_OK) #Read all roles
def get_all_roles(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_role"])),
): return controller.get_roles_list(db)


@backendUserRoutes.post('/assign-permission', response_model=schema.ShowRole, status_code=status.HTTP_201_CREATED) #add rolepermission
def assign_permission(
    request : schema.AssignPermissions,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_role"])),
): return controller.assign_permissions(request, db)


@backendUserRoutes.post("/add-subscription", response_model=schema.BaseSubscription, status_code=status.HTTP_201_CREATED) #Create subscription
async def add_subscription(
    data: schema.CreateSubscription,
    db : Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_subscription"])),
): 
    return controller.add_subscription(data, current_user, db)


@backendUserRoutes.get('/subscriptions', response_model=List[schema.BaseSubscription], status_code=status.HTTP_200_OK) #Read all subscriptions
def all_subscriptions(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_subscription"])),
): return controller.all_subscription_plans(limit, offset, db)


@backendUserRoutes.put('/delete-subscription', response_model=schema.BaseSubscription, status_code=status.HTTP_200_OK) #Delete a subscriptions
def delete_subscription(
    data: schema.UpdateSubscription,
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_subscription"])),
): return controller.delete_subscription_plan(data, db)



@backendUserRoutes.get("/test", status_code=status.HTTP_200_OK) #Testing purpose
async def test(db : Session = Depends(get_db)): 
    return controller.test(db)
