"""
route.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from backenduser.middleware import authenticate_token, check_permission
from database import get_db

from . import controller, model, schema

backendUserRoutes = APIRouter()


@backendUserRoutes.post("/register",
    response_model=schema.BaseUser,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["create_user"]))],
    status_code=status.HTTP_201_CREATED,
    description="Create a new backend user.",
    name="Create user",
)
def register(
    data: schema.RegisterUser,
    sql: Session = Depends(get_db),
):
    """
    Creates a new backend user in the database.
    """
    return controller.create_user(data, sql)


@backendUserRoutes.get("/get-all",
    response_model=schema.ListUsers,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_user"]))],
    status_code=status.HTTP_200_OK,
    description="Fetch the list and total count of the backend users.",
    name="Users list"
)
async def get_users_list(
    limit : Optional[int]=10,
    offset : Optional[int]=0,
    sql : Session = Depends(get_db),
):
    """
    Retrieves:
        Specified number of backend users from the database.
        Total count of all backend users.
    """
    return controller.all_backend_users(limit, offset, sql)


@backendUserRoutes.get("/get/{user_id}",
    response_model=schema.User,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_user"]))],
    status_code=status.HTTP_200_OK,
    description="Fetch the details of a backend user.",
    name="User details"
)
async def get_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    sql : Session = Depends(get_db),
):
    """
    Retrieves all details of a user based on the provided user_id.
    """
    return controller.user_details(user_id, sql)


@backendUserRoutes.post("/update-user",
    response_model=schema.BaseUser,
    dependencies=[Depends(check_permission(["update_user"]))],
    status_code=status.HTTP_200_OK,
    description="Update the backend user's details.",
    name="Update user"
)
async def update_user_details(
    data: schema.UpdateUser,
    sql : Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token),
):
    """
    Updates the role and status of a user in the database based on the provided data.
    """
    return controller.update_user_role(data, auth_token, sql)



@backendUserRoutes.get("/verify-token",
    status_code=status.HTTP_202_ACCEPTED,
    description="Verify a email using token sent to that email address.",
    name="Verify Email"
)
def verify_email_token(
    token: str = Query(..., description="Email verification token"),
    sql: Session = Depends(get_db)
):
    """
    Verify email through token and enable user account login.
    """
    return controller.verify_email(token, sql)


@backendUserRoutes.post("/login",
    response_model= schema.ShowToken,
    status_code=status.HTTP_200_OK,
    description="Create and get authtoken for a user.",
    name="Login"
)
def login(
    request: schema.LoginUser,
    sql: Session = Depends(get_db),
):
    """
    Create a login token for backend user.
    """
    return controller.create_auth_token(request, sql)


@backendUserRoutes.delete(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete the authtoken from the database",
    name="Logout"
)
def logout(
    sql: Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token)
):
    """
    Deletes the login token associated with a specific user.
    """
    return controller.delete_token(auth_token, sql)


@backendUserRoutes.delete(
    path="/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete all the authtokens from the database for this user.",
    name="Logout all devices"
)
def logout_all(
    sql: Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token)
):
    """
    Deletes all the login token associated with a specific user.
    """
    return controller.delete_all_tokens(auth_token, sql)


@backendUserRoutes.get(
    path="/send-token",
    status_code=status.HTTP_200_OK,
    description="Send a token to the email to reset the password",
    name="Forgot password"
)
def send_token(
    email: str = Query(..., description="Email of the account"),
    sql: Session = Depends(get_db)
):
    """
    Sends a verification token in an email for the forget password feature.
    """
    return controller.send_verification_mail(email, sql)


@backendUserRoutes.post(
    path='/create-password',
    response_model=schema.ShowUser,
    status_code=status.HTTP_201_CREATED,
    description="Create a new password if you forgot the old one.",
    name="Reset password"
)
def create_new_password(
    request: schema.ForgotPassword,
    sql: Session = Depends(get_db)
):
    """
    Verify the token and change the password of the user.
    """
    return controller.create_new_password(request, sql)


@backendUserRoutes.post(
    path='/create-permission',
    response_model=schema.BasePermission,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["create_permission"]))],
    status_code=status.HTTP_201_CREATED,
    description="Create a new permission in the database",
    name="Create permission"
)
def create_permission(
    request : schema.BasePermission,
    sql: Session = Depends(get_db),
):
    """
    Creates a new permission in the database.
    """
    return controller.create_permission(request, sql)


@backendUserRoutes.get(
    path='/permissions',
    response_model=List[schema.BasePermission],
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_permission"]))],
    status_code=status.HTTP_200_OK,
    description="Fetch all the permissions from the database.",
    name="Permissions list"
)
def get_all_permissions(
    sql: Session = Depends(get_db),
):
    """
    Retrieves all the permissions from the database.
    """
    return sql.query(model.BackendPermission).all()


@backendUserRoutes.post(
    path='/add-role',
    response_model=schema.ShowRole,
    dependencies=[Depends(check_permission(["create_role"]))],
    status_code=status.HTTP_201_CREATED,
    description="Create a new role.",
    name="Create role"
)
def create_new_roles(
    request : schema.CreateRole,
    sql: Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token),
):
    """
    Create a new role.
    """
    return controller.add_role(request, auth_token.user, sql)


@backendUserRoutes.get(
    path='/roles',
    response_model=List[schema.ShowRole],
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_role"]))],
    status_code=status.HTTP_200_OK,
    description="Fetcch all the roles present in the database.",
    name="Roles list"
)
def get_all_roles(
    sql: Session = Depends(get_db),
):
    """
    Retrieves all Roles from the databsase.
    """
    return sql.query(model.BackendRole).filter(model.BackendRole.id!=0).all()


@backendUserRoutes.post(
    path='/assign-permission',
    response_model=schema.ShowRole,
    dependencies=[Depends(check_permission(["update_role"]))],
    status_code=status.HTTP_201_CREATED,
    description="Assign permissions to a role.",
    name="Assign permission"
)
def assign_permission(
    request : schema.AssignPermissions,
    sql: Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token),
):
    """
    Assigns permissions to a role in the database.
    """
    return controller.assign_permissions(request, auth_token, sql)


@backendUserRoutes.get(
    path='/features',
    response_model=List[schema.ListFeatures],
    status_code=status.HTTP_200_OK,
    description="Fetch all the features from the database.",
    name="Features List"
)
def get_all_features(
    sql: Session = Depends(get_db)
):
    """
    Retrieves all the features from the database.
    """
    return controller.get_all_features(sql)


@backendUserRoutes.post(
    path="/add-subscription",
    response_model=schema.BaseSubscription,
    dependencies=[Depends(check_permission(["create_subscription"]))],
    status_code=status.HTTP_201_CREATED,
    description="Create a new subscription plan.",
    name="Create subscription"
)
async def add_subscription(
    data: schema.CreateSubscription,
    sql : Session = Depends(get_db),
    auth_token: model.BackendToken = Depends(authenticate_token),
):
    """
    Creates a new subscription plan.
    """
    return controller.add_subscription(data, auth_token.user, sql)


@backendUserRoutes.get(
    path='/subscriptions',
    response_model=List[schema.BaseSubscription],
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_subscription"]))],
    status_code=status.HTTP_200_OK,
    description="Fetch all the subscriptions from the database.",
    name="Subscriptions list"
)
def all_subscriptions(
    limit : Optional[int]=10,
    offset : Optional[int]=0,
    sql : Session = Depends(get_db),
):
    """ Returns all subscription plans """
    return controller.all_subscription_plans(limit, offset, sql)


@backendUserRoutes.get(
    path='/subscriptions/{suid}',
    response_model=schema.BaseSubscription,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_subscription"]))],
    status_code=status.HTTP_200_OK,
    description="Get the details of a subscription.",
    name="Subscription details"
)
def subscription_details(
    suid: str = Path(
        title="Subscription ID",
        description="Pass the suid of the subscription to get"
    ),
    sql : Session = Depends(get_db),
):
    """
    Retrieves details of a subscription plan based on the provided suid.
    If the subscription does not exist, it raises a custom error .
    """
    return controller.subscription_plan_details(suid, sql)


@backendUserRoutes.put(
    path='/update-subscription',
    response_model=schema.BaseSubscription,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["update_subscription"]))],
    status_code=status.HTTP_200_OK,
    description="Update the fields of a suscription.",
    name="Update subscription"
)
def update_subscription(
    data: schema.UpdateSubscription,
    sql : Session = Depends(get_db),
):
    """
    Updates the details of a subscription plan in the database.
    """
    return controller.update_subscription_plan(data, sql)


@backendUserRoutes.delete(
    path='/delete-subscription/{suid}',
    response_model=schema.BaseSubscription,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["delete_subscription"]))],
    status_code=status.HTTP_200_OK,
    description="Delete a subscription (is_deleted).",
    name="Delete subscription"
)
def delete_subscription(
    suid: Annotated[str, Path(title="Subscription suid")],
    is_deleted: Annotated[bool, Query(
        title="delete subscription",
        description="Pass true to delete or false to restore the susbcription."
    )],
    sql : Session = Depends(get_db),
):
    """
    Deletes a subscription plan based on the provided `suid`.
    """
    return controller.delete_subscription_plan(suid, is_deleted, sql)


@backendUserRoutes.get(
    path="/get-all-frontend-users",
    response_model=schema.FrontenduserList,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_user"]))],
    status_code=status.HTTP_200_OK,
    description="Fetch all the frontend users from the database.",
    name="Frontend users list"
)
async def get_frontend_users_list(
    limit : Optional[int]=10,
    offset : Optional[int]=0,
    sql : Session = Depends(get_db),
):
    """
    Retrieves a list of frontend users from the database.
    """
    return controller.frontenduserlist(limit, offset, sql)


@backendUserRoutes.get(
    path="/get-frontend-user/{user_id}",
    response_model=schema.FrontendBaseUser,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["read_user"]))],
    status_code=status.HTTP_200_OK,
    description="Get the details of a frontend user.",
    name="Frontend user details"
)
async def get_frontend_user_details(
    user_id: Annotated[str, Path(title="The UUID of the user to get")],
    sql : Session = Depends(get_db),
):
    """
    Retrieves the details of a frontend user.
    """
    return controller.frontenduser_details(user_id, sql)


@backendUserRoutes.post(
    path="/update-frontend-user",
    response_model=schema.BaseUser,
    dependencies=[Depends(authenticate_token), Depends(check_permission(["update_user"]))],
    status_code=status.HTTP_200_OK,
    description="Update fields of a frontend user.",
    name="Update frontend user."
)
async def update_frontend_user_details(
    data: schema.UpdateUser,
    sql : Session = Depends(get_db),
):
    """
    Updates the attributes of a user in the database based on the provided data.
    """
    return controller.update_frontend_user(data, sql)
