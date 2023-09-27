from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from backenduser.middleware import authenticate_token, check_permission
from database import get_db

from . import controller, model, schema

backendUserRoutes = APIRouter()


@backendUserRoutes.post("/register", response_model=schema.BaseUser, status_code=status.HTTP_201_CREATED) #Create user
def register(
    data: schema.RegisterUser, 
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    have_permission: model.BackendUser = Depends(check_permission(["create_user"])),
): return controller.create_user(data, db)


@backendUserRoutes.get("/get-all", response_model=schema.ListUsers, status_code=status.HTTP_200_OK) #Read users
async def get_users_list(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_user"])),
): return controller.all_backend_users(limit, offset, db)


@backendUserRoutes.get("/get/{user_id}", response_model=schema.User, status_code=status.HTTP_200_OK) #Read user
async def get_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_user"])),
): return controller.userDetails(user_id, db)


@backendUserRoutes.post("/update-user", response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Update / delete user
async def update_user_details(
    data: schema.UpdateUser,
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_user"])),
): return controller.updateUserRole(data, authToken, db)



@backendUserRoutes.get("/verify-token", status_code=status.HTTP_202_ACCEPTED, description="Verify the token sent to email to verify your email address.") #Update email verification
def verify_email_token(
    token: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.verify_email(token, db)


@backendUserRoutes.post("/login", response_model= schema.ShowToken, status_code=status.HTTP_200_OK) #Create login token
def login(
    request: schema.LoginUser, 
    db: Session = Depends(get_db),
): return controller.create_auth_token(request, db)


@backendUserRoutes.delete("/logout", status_code=status.HTTP_204_NO_CONTENT) #Delete login token
def logout(
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token)
): return controller.delete_token(authToken, db)


@backendUserRoutes.delete("/logout-all", status_code=status.HTTP_204_NO_CONTENT, description="Logout from all devices.") #Delete all login token
def logout_all(
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token)
): return controller.delete_all_tokens(authToken, db)


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
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_permission"])),
): return controller.create_permission(request, db)


@backendUserRoutes.get('/permissions', response_model=List[schema.BasePermission], status_code=status.HTTP_200_OK) #Read permissions
def get_all_permissions(
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_permission"])),
): return db.query(model.BackendPermission).all()


@backendUserRoutes.post('/add-role', response_model=schema.ShowRole, status_code=status.HTTP_201_CREATED) #Create role
def create_new_roles(
    request : schema.CreateRole,
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_role"])),
): return controller.add_role(request, authToken.user, db)


@backendUserRoutes.get('/roles', response_model=List[schema.ShowRole], status_code=status.HTTP_200_OK) #Read all roles
def get_all_roles(
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_role"])),
): return db.query(model.BackendRole).filter(model.BackendRole.id!=0).all()


@backendUserRoutes.post('/assign-permission', response_model=schema.ShowRole, status_code=status.HTTP_201_CREATED) #add rolepermission
def assign_permission(
    request : schema.AssignPermissions,
    db: Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_role"])),
): return controller.assign_permissions(request, authToken, db)


@backendUserRoutes.get('/features', response_model=List[schema.ListFeatures], status_code=status.HTTP_200_OK)
def get_all_features(
    db: Session = Depends(get_db)
): return controller.get_all_features(db)


@backendUserRoutes.post("/add-subscription", response_model=schema.BaseSubscription, status_code=status.HTTP_201_CREATED) #Create subscription
async def add_subscription(
    data: schema.CreateSubscription,
    db : Session = Depends(get_db),
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["create_subscription"])),
): return controller.add_subscription(data, authToken.user, db)


@backendUserRoutes.get('/subscriptions', response_model=List[schema.BaseSubscription], status_code=status.HTTP_200_OK) #Read all subscriptions
def all_subscriptions(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_subscription"])),
): return controller.all_subscription_plans(limit, offset, db)


@backendUserRoutes.get('/subscriptions/{suid}', response_model=schema.BaseSubscription, status_code=status.HTTP_200_OK) #Read all subscriptions
def subscription_details(
    suid: str = Path(title="Subscription ID", description="Pass the suid of the subscription to get"),
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["read_subscription"])),
): return controller.subscription_plan_details(suid, db)


@backendUserRoutes.put('/update-subscription', response_model=schema.BaseSubscription, status_code=status.HTTP_200_OK) #Update/delet a subscriptions
def update_subscription(
    data: schema.UpdateSubscription,
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["update_subscription"])),
): return controller.update_subscription_plan(data, db)


@backendUserRoutes.delete('/delete-subscription/{suid}', response_model=schema.BaseSubscription, status_code=status.HTTP_200_OK) #Delete a subscriptions
def delete_subscription(
    suid: Annotated[str, Path(title="Subscription suid")],
    is_deleted: Annotated[bool, Query(title="delete subscription", description="Pass true to delete and false to restore the susbcription.")],
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions: model.BackendUser = Depends(check_permission(["delete_subscription"])),
): return controller.delete_subscription_plan(suid, is_deleted, db)


@backendUserRoutes.get("/get-all-frontend-users", response_model=schema.FrontenduserList, status_code=status.HTTP_200_OK) #Read users
async def get_frontend_users_list(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions = Depends(check_permission(["read_user"])),
): return controller.frontenduserlist(limit, offset, db)


@backendUserRoutes.get("/get-frontend-user/{user_id}", response_model=schema.FrontendBaseUser, status_code=status.HTTP_200_OK) #Read user
async def get_frontend_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions = Depends(check_permission(["read_user"])),
): return controller.frontenduserdetails(user_id, db)


@backendUserRoutes.post("/update-frontend-user", response_model=schema.BaseUser, status_code=status.HTTP_200_OK) #Update / delete user
async def update_frontend_user_details(
    data: schema.UpdateUser,
    db : Session = Depends(get_db), 
    authToken: model.BackendToken = Depends(authenticate_token),
    permissions = Depends(check_permission(["update_user"])),
): return controller.updateFrontendUser(data, db)

