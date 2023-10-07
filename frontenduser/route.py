"""
frontenduser/route.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import ALLOWED_EXTENSIONS, TEMPLATES

from . import controller, model, schema
from .middleware import authenticate_token

frontendUserRoutes = APIRouter()

@frontendUserRoutes.post(
    path="/register",
    response_model=schema.BaseUser,
    status_code=status.HTTP_201_CREATED,
    description="Register a new user",
    name="Register user"
)
def register(
    request: schema.RegisterUser,
    background_tasks: BackgroundTasks,
    sql: Session = Depends(get_db)
):
    """
    Creates a new Frontend user
    """
    return controller.register_user(request, sql, background_tasks)


@frontendUserRoutes.get(
    path="/verify-token",
    status_code=status.HTTP_202_ACCEPTED,
    description="Verify a email using token sent to that email address.",
    name="Verify email"
)
def verify_email_token(
    token: str = Query(..., description="Email verification token"),
    sql: Session = Depends(get_db)
):
    """
    Verify email through token and enable user account login.
    """
    return controller.verify_email(token, sql)


@frontendUserRoutes.post(
    path="/login",
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


@frontendUserRoutes.get(
    path="/profile",
    response_model= schema.BaseUser,
    status_code=status.HTTP_200_OK,
    description="Returns the profile details of user.",
    name="Profile details"
)
def profile(
    auth_token: model.FrontendToken = Depends(authenticate_token),
):
    return auth_token.user


@frontendUserRoutes.delete(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete login token of this user.",
    name="Logout"
)
def logout(
    sql: Session = Depends(get_db),
    auth_token: model.FrontendToken = Depends(authenticate_token)
):
    """
    Deletes the login token for a user.
    """
    return controller.delete_token(auth_token, sql)


@frontendUserRoutes.delete(
    path="/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete all login tokens of this user.",
    name="Logout all devices"
)
def logout_all(
    sql: Session = Depends(get_db),
    auth_token: model.FrontendToken = Depends(authenticate_token)
):
    """
    Deletes all the login token for a user.
    """
    return controller.delete_all_tokens(auth_token, sql)

@frontendUserRoutes.get(
    path="/send-token",
    status_code=status.HTTP_200_OK,
    description="Send a token to the email to reset the password",
    name="Forgot password"
)
def send_token(
    email: str = Query(..., description="Email verification token"),
    sql: Session = Depends(get_db)
):
    """
    Sends a verification token in an email for the forget password feature.
    """
    return controller.send_verification_mail(email, sql)


@frontendUserRoutes.post(
    path='/create-password',
    response_model=schema.BaseUser,
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


@frontendUserRoutes.post(
    path='/update-profile',
    response_model=schema.BaseUser,
    status_code=status.HTTP_200_OK,
    description="Update details of your profile.",
    name="Update profile"
)
def update_profile(
    data: schema.UpdateProfile,
    sql : Session = Depends(get_db),
    auth_token: model.FrontendToken = Depends(authenticate_token)
):
    """
    Updates the profile of a user based on the provided data.
    """
    return controller.update_profile(data, auth_token, sql)


@frontendUserRoutes.post(
    path='/update-profile-photo',
    response_model=schema.BaseUser,
    status_code=status.HTTP_200_OK,
    description="Update the user's profile image.",
    name="Update profile photo"
)
def update_profile_photo(
    image: UploadFile = File(
        description=f"Allowed extensions are {ALLOWED_EXTENSIONS}"
    ),
    sql : Session = Depends(get_db),
    auth_token: model.FrontendToken = Depends(authenticate_token)
):
    """
    Updates the profile photo of a user.
    """
    return controller.update_profile_photo(image, auth_token, sql)


@frontendUserRoutes.get(
    path='/subscriptions',
    response_model=List[schema.BaseSubscription],
    status_code=status.HTTP_200_OK,
    description="Fetch all the subscriptions from database.",
    name="List subscriptions"
)
def all_subscriptions(
    limit : Optional[int]=10,
    offset : Optional[int]=0,
    sql : Session = Depends(get_db),
):
    """
    Retrieves details of a subscription plan based on the provided suid.
    If the subscription does not exist, it raises a custom error .
    """
    return controller.all_subscription_plans(limit, offset, sql)


@frontendUserRoutes.get(
    path='/subscriptions/{suid}',
    response_model=schema.BaseSubscription,
    status_code=status.HTTP_200_OK,
    description="Get the details of a subscription.",
    name="Subscription details"
)
def subscription_details(
    suid: str,
    sql : Session = Depends(get_db)
):
    """
    Get the details of a subscription based on the provided suid.
    """
    return controller.subscription_plan_detail(suid, sql)


@frontendUserRoutes.get(
    path='/timezones',
    response_model=List[schema.TimeZones],
    status_code=status.HTTP_200_OK,
    description="Fetch all the timezones available in database.",
    name="List timezones"
)
def all_timezones(
    sql : Session = Depends(get_db)
):
    """
    Retrieves a list of all timezones from the database.
    """
    return controller.timezones_list(sql)


@frontendUserRoutes.post(
    path='/stripe/create-order',
    response_model=schema.Orders,
    status_code=status.HTTP_201_CREATED,
    description="Create a new order in stripe.",
    name="Create stripe order"
)
def create_stripe_order(
    request:schema.AddOrder,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Adds a new order to the database and stripe.
    """
    return controller.stripe_add_orders(request, auth_token, sql)


@frontendUserRoutes.post(
    path='/stripe/create-transaction',
    status_code=status.HTTP_201_CREATED,
    description="Create a transaction for stripe order.",
    name="Create stripe transaction"
)
def create_stripe_transaction(
    request: schema.StripeReturn,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Updates the status of an order in the database based on the Stripe payment status.
    Creates a new transaction record for the order if it doesn't already exist.
    Updates the active plan of the user associated with the authentication token 
    based on the product ID from the order.
    """
    return controller.stripe_add_transaction(request, auth_token, sql)


@frontendUserRoutes.post(
    path='/paypal/create-order',
    response_model=schema.Orders,
    status_code=status.HTTP_201_CREATED,
    description="Create a new order in paypal.",
    name="Create paypal order"
)
def create_paypal_order(
    request:schema.AddOrder,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Adds a new order to the database.
    """
    return controller.paypal_add_orders(request, auth_token, sql)


@frontendUserRoutes.post(
    path='/paypal/create-transaction',
    status_code=status.HTTP_201_CREATED,
    description="Create a transaction for paypal order.",
    name="Create paypal transaction"
)
def create_paypal_transaction(
    request: schema.StripeReturn,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Add a transaction to the database when a payment is made through PayPal.
    """
    return controller.paypal_add_transaction(request, auth_token, sql)


@frontendUserRoutes.post(
    path='/razorpay/create-order',
    response_model=schema.Orders,
    status_code=status.HTTP_201_CREATED,
    description="Create a new order in razorpay.",
    name="Create razorpays order"
)
def create_razorpay_order(
    request:schema.AddOrder,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Adds a new order to the database.
    """
    return controller.razorpay_add_orders(request, auth_token, sql)


@frontendUserRoutes.post(
    path='/razorpay/create-transaction',
    status_code=status.HTTP_201_CREATED,
    description="Create a transaction for paypal order.",
    name="Create paypal transaction"
)
def create_razorpay_transaction(
    request: schema.RazorpayReturn,
    auth_token:model.FrontendToken = Depends(authenticate_token),
    sql: Session = Depends(get_db)
):
    """
    Updates the status of an order in and creates a new transaction for the order.
    If a transaction record already exists for the order, returns the existing record.
    Also updates the active plan of the user associated with the order.
    """
    return controller.razorpay_add_transaction(request, auth_token, sql)


@frontendUserRoutes.get('/stripe/checkout')
def stripe_checkout():
    """
    Serve the stripe_checkout.html file for the Stripe checkout route.
    """
    return FileResponse(
        os.path.join(TEMPLATES, "stripe_checkout.html"),
        media_type="text/html"
    )


@frontendUserRoutes.get('/razorpay/checkout')
def razorpay_checkout():
    """
    Serve the razorpay_checkout.html file for the Razorpay checkout route.
    """
    return FileResponse(
        os.path.join(TEMPLATES, "razorpay_checkout.html"),
        media_type="text/html"
    )


@frontendUserRoutes.get('/paypal/checkout')
def paypal_checkout():
    """
    Serve the paypal_checkout.html file for the PayPal checkout route.
    """
    return FileResponse(
        os.path.join(TEMPLATES, "paypal_checkout.html"),
        media_type="text/html"
    )

