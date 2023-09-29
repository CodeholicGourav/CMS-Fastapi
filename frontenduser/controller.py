"""
controller.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import math
import time
from datetime import datetime, timedelta

import razorpay
import requests
import stripe
from fastapi import UploadFile, status
from sqlalchemy.orm import Session

from backenduser import controller as backendusercontroller
from dependencies import (
    ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, PAYPAL_BASE_URL,
    SETTINGS, TOKEN_LIMIT, TOKEN_VALIDITY,
    CustomValidations, FrontendEmail, Hash,
    allowed_file, convert_currency, generate_paypal_access_token,
    generate_token, generate_uuid
)

from . import model, schema


def register_user(data: schema.RegisterUser, sql: Session):
    """
    Creates a new Frontend user
    """
    # Check if a user with the same email or username already exists
    existing_user = sql.query(model.FrontendUser).filter(
        (model.FrontendUser.email == data.email) |
        (model.FrontendUser.username == data.username)
    ).first()

    if existing_user:
        # raise a custom error indicating that the username is already in use
        if data.username == existing_user.username:
            CustomValidations.custom_error(
                type="exist",
                loc="username",
                msg="Username already in use",
                inp=data.username,
                ctx={"username": "unique"}
            )

        # raise a custom error indicating that the email is already in use
        if data.email == existing_user.email:
            CustomValidations.custom_error(
                type="exist",
                loc="email",
                msg="Email already in use",
                inp=data.email,
                ctx={"email": "unique"}
            )

    # Create a new FrontendUser object with the provided data
    new_user = model.FrontendUser(
        uuid=generate_uuid(data.username),
        username=data.username,
        email=data.email,
        password=Hash.bcrypt(data.password),
        verification_token=generate_token(32),
    )

    # Set optional fields if provided
    if data.first_name:
        new_user.first_name = data.first_name

    if data.last_name:
        new_user.last_name = data.last_name

    if data.language:
        new_user.language = data.language

    if data.timezone:
        # Check if the provided timezone exists in the database
        exist_timezone = sql.query(model.Timezone).filter_by(
            code=data.timezone
        ).first()
        if not exist_timezone:
            CustomValidations.custom_error(
                type="not_exist",
                loc="timezone",
                msg="Timezone does not exist.",
                inp=data.timezone,
                ctx={"timezone": "exist"}
            )
        new_user.timezone = data.timezone

    # Add the new user object to the database
    sql.add(new_user)
    sql.commit()
    sql.refresh(new_user)

    # Send an email verification token to the new user
    if not FrontendEmail.send_email_verification_token(new_user):
        # If the email fails to send, raise a error
        CustomValidations.custom_error(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="Internal",
            loc="email",
            msg="Cannot send email.",
            inp=data.email,
        )

    return new_user


def user_list(limit: int, offset: int, sql: Session) -> dict:
    """
    Retrieves a list of frontend users with pagination.
    """
    total = sql.query(model.FrontendUser.id).count()
    users = sql.query(model.FrontendUser).limit(limit).offset(offset).all()
    return {
        "users": users,
        "total": total
    }


def user_details(user_id: str, sql: Session):
    """
    Retrieves the details of a frontend user based on the provided user ID.
        
    Raises:
        custom_error: If the user does not exist.
    """
    user = sql.query(model.FrontendUser).filter_by(uuid=user_id).first()
    if not user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=user_id,
            ctx={"user": "exist"}
        )
    return user


def update_profile_photo(file: UploadFile, auth_token: model.FrontendToken, sql: Session):
    """
    Updates the profile photo of a user.
    """
    user = auth_token.user
    # Check if the file is an allowed image type
    if not allowed_file(file.filename):
        CustomValidations.custom_error(
            type="invalid",
            loc= "image",
            msg= f"Allowed extensions are {ALLOWED_EXTENSIONS}",
            inp= file.filename,
            ctx={"image": "invalid type"}
        )

    # Check file size
    if file.size > MAX_FILE_SIZE_BYTES:
        CustomValidations.custom_error(
            type="invalid",
            loc= "image",
            msg= f"Maximum image size should be {MAX_FILE_SIZE_BYTES} bytes" ,
            inp= f"{file.size} bytes",
            ctx={"image": "Big size"}
        )

    file_extension = file.filename.split(".")[-1]

    if user.profile_photo:
        unique_filename = user.profile_photo
    else:
        unique_filename = f"{math.floor(time.time())}_{user.username}.{file_extension}"

    with open(f"uploads/{unique_filename}", "wb") as image_file:
        image_file.write(file.file.read())

    user.profile_photo = unique_filename
    sql.commit()
    sql.refresh(user)
    return user


def update_user(data: schema.UpdateUser, sql: Session):
    """
    Updates the attributes of a user in the database based on the provided data.
    """
    user = sql.query(model.FrontendUser).filter_by(uuid=data.user_id).first()
    if not user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="user_id",
            msg="No user found.",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_deleted is not None:
        user.is_deleted = data.is_deleted
    sql.commit()
    sql.refresh(user)
    return user


def verify_email(token: str, sql: Session):
    """
    Verify email through token and enable user account login.
    """
    user = sql.query(model.FrontendUser).filter_by(
        verification_token=token,
        is_deleted=False
    ).first()

    if not user:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc= "token",
            msg= "Invalid verification token",
            inp= token,
            ctx={"token": "exist"}
        )

    if not user.is_active:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="deactive",
            loc= "account",
            msg= "Your account is deactivated!",
            inp= token,
            ctx={"account": "active"}
        )

    user.email_verified_at=datetime.utcnow()
    user.verification_token=None
    sql.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, sql: Session):
    """
    Create a login token for backend user.
    """
    user = sql.query(model.FrontendUser).filter(
        (model.FrontendUser.email == request.username_or_email) |
        (model.FrontendUser.username == request.username_or_email),
    ).filter_by(is_deleted=False).first()

    if not user:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="username_or_email",
            msg="Email/Username is wrong!",
            inp=request.username_or_email,
            ctx={"username_or_email": "exist"}
        )

    if not Hash.verify(user.password, request.password):
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="password",
            msg="Password is wrong!",
            inp=request.password,
            ctx={"password": "match"}
        )

    if not user.email_verified_at:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required",
            msg="Verify your email first!",
        )

    if not user.is_active:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!",
        )

    sql.query(model.FrontendToken).filter(
        model.FrontendToken.user_id == user.id,
        model.FrontendToken.expire_at < datetime.now()
    ).delete()
    sql.commit()
    # Count the number of active tokens for the user.
    tokens_count = sql.query(model.FrontendToken).filter_by(user_id=user.id).count()
    if tokens_count >= TOKEN_LIMIT:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="limit_exceed",
            msg=f"Login limit exceed (${TOKEN_LIMIT}).",
        )

    token = model.FrontendToken(
        token=generate_token(16),
        user_id=user.id,
        details=request.details.to_string(),
        expire_at=datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))
    )
    sql.add(token)
    sql.commit()
    sql.refresh(token)
    return token


def delete_token(auth_token: model.FrontendToken, sql: Session):
    """
    Deletes the login token for a user.
    """
    sql.query(model.FrontendToken).filter_by(
        token=auth_token.token
    ).delete()
    sql.commit()
    return True


def delete_all_tokens(auth_token: model.FrontendToken, sql: Session):
    """
    Deletes all the login token for a user.
    """
    sql.query(model.FrontendToken).filter_by(
        user_id=auth_token.user.id
    ).delete()
    sql.commit()
    return True


def send_verification_mail(email: str, sql: Session):
    """
    Sends a verification token in an email for the forget password feature.

    Raises:
        custom_error: If no account is found or the account is suspended.
        custom_error: If the email fails to send.
    """
    user = sql.query(model.FrontendUser).filter_by(
        email=email,
        is_deleted=False
    ).first()

    if not user:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc="email",
            msg="No account found.",
            inp=email,
            ctx={"email": "exist"}
        )

    if not user.is_active:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!"
        )

    user.verification_token = generate_token(32)
    sql.commit()
    sql.refresh(user)

    if not FrontendEmail.send_forget_password_token(user):
        CustomValidations.custom_error(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="mail_sent_error",
            msg="Cannot send email."
        )
    return {"message": "Email sent successfully"}


def create_new_password(request: schema.ForgotPassword, sql: Session):
    """
    Verify the token and change the password of the user
    """
    # Find the user with the given verification token
    user = sql.query(model.FrontendUser).filter_by(
        verification_token=request.token,
        is_deleted=False
    ).first()

    # If the user is not found, raise a custom error
    if not user:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="expired",
            loc="token",
            msg="Token is expired!",
            inp=request.token,
            ctx={"token": "valid"}
        )

    # If the user's email is not verified, raise a custom error
    if not user.email_verified_at:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required",
            msg="Verify your email first!",
        )

    # If the user's account is not active, raise a custom error
    if not user.is_active:
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!",
        )

    # Update the user's password with the new password
    user.password = Hash.bcrypt(request.password)

    # Set the verification token to None
    user.verification_token = None

    # Commit the changes to the database
    sql.commit()

    # Refresh the user object
    sql.refresh(user)

    # Return the updated user object
    return user


def update_profile(request: schema.UpdateProfile, auth_token: model.FrontendToken, sql: Session):
    """
    Updates the profile of a user based on the provided data.
    """
    user = auth_token.user
    if request.username:
        existing_user = sql.query(model.FrontendUser).filter_by(
            username=request.username
        ).first()
        if existing_user:
            CustomValidations.custom_error(
                type="exist",
                loc="username",
                msg="Username already in use",
                inp=request.username,
                ctx={"username": "unique"}
            )
        user.username = request.username

    if request.timezone:
        exist_timezone = sql.query(model.Timezone).filter_by(
            code=request.timezone
        ).first()
        if not exist_timezone:
            CustomValidations.custom_error(
                type="not_exist",
                loc="timezone",
                msg="Timezone does not exist.",
                inp=request.timezone,
                ctx={"timezone": "exist"}
            )
        user.timezone = request.timezone

    user.first_name = request.first_name or user.first_name
    user.last_name = request.last_name or user.last_name
    user.language = request.language or user.language
    user.storage_token = request.storage_token or user.storage_token
    user.storage_platform = request.storage_platform or user.storage_platform
    user.social_token = request.social_token or user.social_token
    user.social_platform = request.social_platform or user.social_platform

    sql.add(user)
    sql.commit()
    sql.refresh(user)
    return user


def all_subscription_plans(limit: int, offset: int, sql: Session):
    """
    Calls the `all_subscription_plans` function from the `backendusercontroller` .
    """
    return backendusercontroller.all_subscription_plans(limit, offset, sql)


def subscription_plan_detail(suid: str, sql: Session):
    """
    Calls the subscription_plan_details function from the `backendusercontroller`.
    """
    return backendusercontroller.subscription_plan_details(suid, sql)


def timezones_list(sql: Session):
    """
    Retrieves a list of all timezones from the database.
    """
    return sql.query(model.Timezone).all()


def stripe_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, sql: Session):
    """
    Adds a new order to the database.
    """

    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, sql)

    if not subscription or subscription.is_deleted:
        CustomValidations.custom_error(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convert_currency(request.currency)

    total_amount = subscription.sale_price * currency["conversion_rate"]
    final_amount = round(total_amount, 2)

    # Create a new order object
    order = model.Order(
        ouid=generate_uuid(authtoken.user.username),
        user_id=authtoken.user_id,
        total_amount=total_amount,
        final_amount=total_amount,
        currency=currency["target_code"],
        coupon_amount=0,
        conversion_rate=currency["conversion_rate"],
    )

    # Apply coupon discount if coupon ID is provided
    if request.coupon_code:
        coupon = backendusercontroller.coupon_details(
            request.coupon_code,
            sql
        )
        if not coupon or not coupon.is_active:
            CustomValidations.custom_error(
                type="not_exist",
                loc="coupon",
                msg="Coupon does not exist.",
                inp=request.coupon_code,
                ctx={"coupon": "exist"}
            )

        coupon_amount = (coupon.percentage / 100) * total_amount
        final_amount = total_amount - coupon_amount

        order.coupon_id = coupon.id
        order.cuoupon_code = coupon.coupon_code
        order.coupon_amount = coupon_amount
        order.final_amount = round(final_amount, 2)

    # Save the order to the database
    sql.add(order)
    sql.commit()
    sql.refresh(order)

    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=int(order.final_amount * 100),
            currency=order.currency,
            api_key=SETTINGS.STRIPE_SECRET,
            description=order.ouid,
            metadata={
                "order_id": order.ouid,
            }
        )
    except Exception as error:
        CustomValidations.custom_error(
            type="stripe_error",
            loc="currency",
            msg=str(error),
            inp=request.currency,
            ctx={"currency": "exist"}
        )

    order_product = model.OrderProduct(
        product_price = subscription.price,
        product_sale_price = subscription.sale_price,
        order_id = order.id,
        product_id = subscription.id,
        quantity = 1,
    )

    sql.add(order_product)
    sql.commit()
    order.clientSecret = intent['client_secret']
    return order


def stripe_add_transaction(
    request: schema.StripeReturn,
    auth_token: model.FrontendToken,
    sql: Session
):
    """
    Updates the status of an order in the database based on the Stripe payment status.
    Creates a new transaction record for the order if it doesn't already exist.
    Updates the active plan of the user associated with the authentication token 
    based on the product ID from the order.
    """
    # Retrieve the order based on the order unique ID provided in the request
    order = sql.query(model.Order).filter_by(ouid=request.description).first()

    # Update the status of the order with the status from the request
    order.status = request.status

    # Add the updated order to the database and commit the changes
    sql.add(order)
    sql.commit()

    # Retrieve the transaction record associated with the order
    transaction = sql.query(model.Transaction).filter_by(
        order_id=order.id
    ).first()

    # If the transaction record doesn't exist,
    # create a new transaction record
    if not transaction:
        transaction = model.Transaction(
            order_id=order.id,
            status=request.status,
            payment_gateway="stripe",
            payment_id=request.id,
        )

        # Add the new transaction record to the database
        sql.add(transaction)

        # commit the changes
        sql.commit()
        sql.refresh(transaction)

    # Retrieve the user associated with the authentication token
    user = auth_token.user

    # Retrieve the order product based on the order ID
    order_product = sql.query(model.OrderProduct).filter_by(
        order_id=order.id
    ).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database
    sql.add(user)
    # commit the changes
    sql.commit()

    sql.refresh(transaction)

    # Return the transaction record
    return transaction


def paypal_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, sql: Session):
    """
    Adds a new order to the database.
    """

    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, sql)

    if not subscription or subscription.is_deleted:
        CustomValidations.custom_error(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convert_currency(request.currency)

    total_amount = subscription.sale_price * currency["conversion_rate"]
    final_amount = round(total_amount, 2)

    # Create a new order object
    order = model.Order(
        ouid=generate_uuid(authtoken.user.username),
        user_id=authtoken.user_id,
        total_amount=total_amount,
        final_amount=total_amount,
        currency=currency["target_code"],
        coupon_amount=0,
        conversion_rate=currency["conversion_rate"],
    )

    # Apply coupon discount if coupon ID is provided
    if request.coupon_code:
        coupon = backendusercontroller.coupon_details(
            request.coupon_code,
            sql
        )
        if not coupon or not coupon.is_active:
            CustomValidations.custom_error(
                type="not_exist",
                loc="coupon",
                msg="Coupon does not exist.",
                inp=request.coupon_code,
                ctx={"coupon": "exist"}
            )

        coupon_amount = (coupon.percentage / 100) * total_amount
        final_amount = total_amount - coupon_amount

        order.coupon_id = coupon.id
        order.cuoupon_code = coupon.coupon_code
        order.coupon_amount = coupon_amount
        order.final_amount = round(final_amount, 2)

    # Save the order to the database
    sql.add(order)
    sql.commit()
    sql.refresh(order)

    try:
        # Create a PaymentIntent with the order amount and currency
        access_token = generate_paypal_access_token()

        response = requests.post(
            url=f'{PAYPAL_BASE_URL}/v2/checkout/orders',
            headers={"Authorization": f'Bearer {access_token}'},
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": order.currency,
                        "value": round(order.final_amount, 2),
                    },
                }],
            },
            timeout=5
        )
        paypal = response.json()

    except requests.exceptions.RequestException as error:
        CustomValidations.custom_error(
            type="paypal_error",
            loc="payment gateway",
            msg=str(error),
            inp="paypal",
            ctx={"paypal": "error"}
        )

    if 'id' not in paypal:
        CustomValidations.custom_error(
            type=paypal['name'],
            loc="paypal",
            msg=paypal['message'],
            inp='paypal',
            ctx={"paypal": paypal["links"]}
        )

    sql.add(
        model.OrderProduct(
            product_price = subscription.price,
            product_sale_price = subscription.sale_price,
            order_id = order.id,
            product_id = subscription.id,
            quantity = 1,
        )
    )
    sql.commit()
    order.clientSecret = paypal['id']
    return order


def paypal_add_transaction(
    request: schema.StripeReturn,
    auth_token: model.FrontendToken,
    sql: Session
):
    """
    Add a transaction to the database when a payment is made through PayPal.
    """
    # Retrieve the order from the database based on the provided order ID
    order = sql.query(model.Order).filter_by(ouid=request.description).first()

    # Update the status of the order with the status from the payment request
    order.status = request.status

    # Add the updated order to the database
    sql.add(order)
    sql.commit()

    # Check if a transaction already exists for the order
    transaction = sql.query(model.Transaction).filter_by(order_id=order.id).first()
    if transaction:
        return transaction

    # Create a new transaction record with the details of the payment
    transaction = model.Transaction(
        order_id=order.id,
        status=request.status,
        payment_gateway="stripe",
        payment_id=request.id,
    )

    # Add the transaction to the database
    sql.add(transaction)
    sql.commit()

    # Refresh the transaction object with the updated values
    sql.refresh(transaction)

    # Retrieve the user associated with the authentication token
    user = auth_token.user

    # Retrieve the order product from the database based on the order ID
    order_product = sql.query(model.OrderProduct).filter_by(order_id=order.id).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database
    sql.add(user)
    # commit the changes
    sql.commit()

    # Refresh the transaction record
    sql.refresh(transaction)

    # Return the transaction record
    return transaction


def razorpay_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, sql: Session):
    """
    Adds a new order to the database.
    """
    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, sql)

    if not subscription or subscription.is_deleted:
        CustomValidations.custom_error(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convert_currency(request.currency)
    total_amount = subscription.sale_price * currency["conversion_rate"]
    final_amount = round(total_amount, 2)

    # Create a new order object
    order = model.Order(
        ouid=generate_uuid(authtoken.user.username),
        user_id=authtoken.user_id,
        total_amount=total_amount,
        final_amount=total_amount,
        currency=currency["target_code"],
        coupon_amount=0,
        conversion_rate=currency["conversion_rate"],
    )

    # Apply coupon discount if coupon ID is provided
    if request.coupon_code:
        coupon = backendusercontroller.coupon_details(request.coupon_code, sql)
        if not coupon or not coupon.is_active:
            CustomValidations.custom_error(
                type="not_exist",
                loc="coupon",
                msg="Coupon does not exist.",
                inp=request.coupon_code,
                ctx={"coupon": "exist"}
            )

        coupon_amount = (coupon.percentage / 100) * total_amount
        final_amount = total_amount - coupon_amount

        order.coupon_id = coupon.id
        order.cuoupon_code = coupon.coupon_code
        order.coupon_amount = coupon_amount
        order.final_amount = round(final_amount, 2)

    # Save the order to the database
    sql.add(order)
    sql.commit()
    sql.refresh(order)

    amount_in_paise = int(order.final_amount * 100)

    try:
        client = razorpay.Client(auth=(SETTINGS.RAZORPAY_CLIENT, SETTINGS.RAZORPAY_SECRET))
        client.set_app_details({"title" : SETTINGS.APP_NAME})
        payment = razorpay.Order(client).create(
            data={
                "amount": amount_in_paise,
                "currency": order.currency,
                "receipt":  order.ouid
            }
        )
    except Exception as error:
        CustomValidations.custom_error(
            type="stripe_error",
            loc="currency",
            msg=str(error),
            inp=request.currency,
            ctx={"currency": "exist"}
        )

    order_product = model.OrderProduct(
        product_price = subscription.price,
        product_sale_price = subscription.sale_price,
        order_id = order.id,
        product_id = subscription.id,
        quantity = 1,
    )

    sql.add(order_product)
    sql.commit()
    order.clientSecret = payment['id']
    return order


def razorpay_add_transaction(
    request: schema.RazorpayReturn,
    auth_token: model.FrontendToken,
    sql: Session
):
    """
    Updates the status of an order in and creates a new transaction for the order.
    If a transaction record already exists for the order, returns the existing record.
    Also updates the active plan of the user associated with the order.
    """
    # Retrieve the order based on the provided order unique ID (ouid)
    order = sql.query(model.Order).filter_by(ouid=request.ouid).first()

    # Update the status of the order with the status provided in the request
    order.status = request.status

    # Add the updated order to the database and commit the changes
    sql.add(order)
    sql.commit()

    # Check if a transaction record already exists for the order
    transaction = sql.query(model.Transaction).filter_by(order_id=order.id).first()

    if transaction:
        # If a transaction record exists, return the existing record
        return transaction

    # create a new transaction record with the details from the request
    transaction = model.Transaction(
        order_id=order.id,
        status=request.status,
        payment_gateway="razorpay",
        payment_id=request.razorpay_payment_id,
    )

    # Add the new transaction record to the database
    sql.add(transaction)
    # commit the changes
    sql.commit()

    # Retrieve the user associated with the authentication token
    user = auth_token.user

    # Retrieve the order product from the database based on the order ID
    order_product = sql.query(model.OrderProduct).filter_by(
        order_id=order.id
    ).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database and commit the changes
    sql.add(user)
    sql.commit()

    # Create subscription-user mapping
    backendusercontroller.create_subscription_user(
        order_product.product_id,
        user.id, transaction.id, sql
    )

    # Refresh the transaction record
    sql.refresh(transaction)

    # Return the transaction record
    return transaction
