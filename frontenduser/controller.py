from typing import Optional
import math
import time
import requests
from datetime import datetime, timedelta

from fastapi import UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backenduser import controller as backendusercontroller
from dependencies import (
    ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, TOKEN_LIMIT,TOKEN_VALIDITY, 
    CustomValidations, FrontendEmail,Hash, 
    allowed_file, generate_token, generate_uuid
)

from dependencies import (
    SETTINGS, PAYPAL_BASE_URL, 
    generatePaypalAccessToken, convertCurrency
)

from . import model, schema
import stripe
import razorpay

def register_user(data: schema.RegisterUser, db: Session) -> Optional[model.FrontendUser]:
    """
    Creates a new Frontend user

    Args:
        data (schema.RegisterUser): The data of the user to be registered.
        db (Session): The SQLAlchemy database session.

    Returns:
        Optional[model.FrontendUser]: The newly registered user object.
    """
    # Check if a user with the same email or username already exists in the database
    existing_user = db.query(model.FrontendUser).filter(
        (model.FrontendUser.email == data.email) |
        (model.FrontendUser.username == data.username)
    ).first()

    if existing_user:
        # If a user with the same username exists, raise a custom error indicating that the username is already in use
        if data.username == existing_user.username:
            CustomValidations.customError(
                type="exist",
                loc="username",
                msg="Username already in use",
                inp=data.username,
                ctx={"username": "unique"}
            )

        # If a user with the same email exists, raise a custom error indicating that the email is already in use
        if data.email == existing_user.email:
            CustomValidations.customError(
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
        exist_timezone = db.query(model.Timezone).filter_by(code=data.timezone).first()
        if not exist_timezone:
            CustomValidations.customError(
                type="not_exist",
                loc="timezone",
                msg="Timezone does not exist.",
                inp=data.timezone,
                ctx={"timezone": "exist"}
            )
        new_user.timezone = data.timezone

    # Add the new user object to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send an email verification token to the new user
    frontendEmail = FrontendEmail()
    if frontendEmail.sendEmailVerificationToken(new_user):
        return new_user
    else:
        # If the email fails to send, raise a custom error indicating that the email cannot be sent
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="Internal",
            loc="email",
            msg="Cannot send email.",
            inp=data.email,
        )


def userList(limit: int, offset: int, db: Session) -> dict:
    """
    Retrieves a list of frontend users from the database with pagination.

    Args:
        limit (int): The maximum number of users to retrieve.
        offset (int): The number of users to skip before starting to retrieve.
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary with the following keys:
            - "users": A list of frontend user objects.
            - "total": The total number of frontend users in the database.
    """
    total = db.query(func.count(model.FrontendUser.id)).scalar()
    users = db.query(model.FrontendUser).limit(limit).offset(offset).all()
    return {
        "users": users,
        "total": total
    }


def userDetails(user_id: str, db: Session):
    """
    Retrieves the details of a frontend user based on the provided user ID.

    Args:
        user_id (str): The ID of the user for whom the details are being retrieved.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.FrontendUser: The frontend user object containing the details of the user.
        
    Raises:
        CustomError: If the user does not exist.
    """
    user = db.query(model.FrontendUser).filter_by(uuid=user_id).first()
    if not user:
        CustomValidations.customError(
            type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=user_id,
            ctx={"user": "exist"}
        )
    return user


def updateProfilePhoto(file: UploadFile, authToken: model.FrontendToken, db: Session):
    """
    Updates the profile photo of a user.

    Args:
        file (UploadFile): The uploaded file containing the new profile photo.
        user (model.FrontendUser): The user object for whom the profile photo is being updated.
        db (Session): The database session object.

    Raises:
        CustomError: If the file is not an allowed image type or if its size exceeds the maximum allowed size.

    Returns:
        None. The function updates the user's profile photo in the database if all validations pass.
    """
    user = authToken.user
    # Check if the file is an allowed image type
    if not allowed_file(file.filename):
        CustomValidations.customError(
            type="invalid", 
            loc= "image", 
            msg= f"Allowed extensions are {ALLOWED_EXTENSIONS}", 
            inp= file.filename,
            ctx={"image": "invalid type"}
        )

    # Check file size
    if file.size > MAX_FILE_SIZE_BYTES:
        CustomValidations.customError(
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
    db.commit()
    db.refresh(user)
    return user


def updateUser(data: schema.UpdateUser, db: Session):
    """
    Updates the attributes of a user in the database based on the provided data.

    Args:
        data (schema.UpdateUser): The data containing the user ID and the attributes to be updated.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.FrontendUser: The updated user object.
    """
    user = db.query(model.FrontendUser).filter_by(uuid=data.user_id).first()
    if not user:
        CustomValidations.customError(
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
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def verify_email(token: str, db: Session):
    """
    Verify email through token and enable user account login
    
    Args:
    - token (str): The verification token provided by the user.
    - db (Session): The SQLAlchemy database session.
    
    Returns:
    - dict: A dictionary with the message "Email verified successfully".
    """
    user = db.query(model.FrontendUser).filter(
        model.FrontendUser.verification_token == token,
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist", 
            loc= "token", 
            msg= "Invalid verification token", 
            inp= token,
            ctx={"token": "exist"}
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="deactive", 
            loc= "account", 
            msg= "Your account is deactivated!", 
            inp= token,
            ctx={"account": "active"}
        )

    user.email_verified_at = datetime.utcnow()
    user.verification_token = None 
    user.updated_at = datetime.utcnow()
    db.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, db: Session) -> model.FrontendToken:
    """
    Create a login token for backend user

    Args:
        request (schema.LoginUser): An object containing the username/email and password provided by the user.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.FrontendToken: The newly created login token for the user.
    """
    user = db.query(model.FrontendUser).filter(
        (model.FrontendUser.email == request.username_or_email) |
        (model.FrontendUser.username == request.username_or_email),
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="username_or_email",
            msg="Email/Username is wrong!",
            inp=request.username_or_email,
            ctx={"username_or_email": "exist"}
        )

    if not Hash.verify(user.password, request.password):
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="password",
            msg="Password is wrong!",
            inp=request.password,
            ctx={"password": "match"}
        )

    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required",
            msg="Verify your email first!",
        )

    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!",
        )

    db.query(model.FrontendToken).filter(
        model.FrontendToken.user_id == user.id,
        model.FrontendToken.expire_at < datetime.now()
    ).delete()
    db.commit()
    # Count the number of active tokens for the user. If it exceeds the token limit, raise an HTTPException with a 403 status code and an error message
    tokens_count = db.query(model.FrontendToken).filter(
        model.FrontendToken.user_id == user.id,
    ).count()
    if tokens_count >= TOKEN_LIMIT:
        CustomValidations.customError(
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
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def delete_token(authToken: model.FrontendToken, db: Session):
    """
    Deletes the login token for a user.

    Args:
        user (model.FrontendUser): The user object for whom the login token is being deleted.
        db (Session): The SQLAlchemy database session.

    Returns:
        bool: True if the token has been successfully deleted.
    """
    db.query(model.FrontendToken).filter_by(token=authToken.token).delete()
    db.commit()
    return True


def delete_all_tokens(authToken: model.FrontendToken, db: Session):
    """
    Deletes the login token for a user.

    Args:
        user (model.FrontendUser): The user object for whom the login token is being deleted.
        db (Session): The SQLAlchemy database session.

    Returns:
        bool: True if the token has been successfully deleted.
    """
    db.query(model.FrontendToken).filter_by(user_id=authToken.user.id).delete()
    db.commit()
    return True


def send_verification_mail(email: str, db: Session):
    """
    Sends a verification token in an email for the forget password feature.

    Args:
        email (str): The email address of the user requesting the forget password feature.
        db (Session): The SQLAlchemy database session.

    Returns:
        dict: A dictionary with the message "Email sent successfully" if the email is sent successfully.

    Raises:
        CustomError: If no account is found or the account is suspended.
        CustomError: If the email fails to send.
    """
    user = db.query(model.FrontendUser).filter(
        model.FrontendUser.email == email,
        model.FrontendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc="email",
            msg="No account found.",
            inp=email,
            ctx={"email": "exist"}
        )

    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!"
        )

    user.verification_token = generate_token(32)
    db.commit()
    db.refresh(user)

    frontendemail = FrontendEmail()
    if frontendemail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else:
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="mail_sent_error",
            msg="Cannot send email."
        )


def create_new_password(request: schema.ForgotPassword, db: Session):
    """
    Verify the token and change the password of the user

    Args:
        request (schema.ForgotPassword): An object containing the token provided by the user.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.FrontendUser: The updated user object with the new password.
    """
    # Query the database to find the user with the given verification token
    user = db.query(model.FrontendUser).filter(
        model.FrontendUser.verification_token == request.token,
        model.FrontendUser.is_deleted == False
    ).first()

    # If the user is not found, raise a custom error indicating that the token is expired
    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="expired",
            loc="token",
            msg="Token is expired!",
            inp=request.token,
            ctx={"token": "valid"}
        )

    # If the user's email is not verified, raise a custom error indicating that email verification is required
    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required",
            msg="Verify your email first!",
        )

    # If the user's account is not active, raise a custom error indicating that the account is suspended
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!",
        )

    # Update the user's password with the new password provided in the request
    user.password = Hash.bcrypt(request.password)

    # Set the verification token to None
    user.verification_token = None

    # Update the user's updated_at field with the current datetime
    user.updated_at = datetime.utcnow()

    # Commit the changes to the database
    db.commit()

    # Refresh the user object
    db.refresh(user)

    # Return the updated user object
    return user


def updateProfile(request: schema.UpdateProfile, authToken: model.FrontendToken, db: Session):
    """
    Updates the profile of a user based on the provided data.

    Args:
        request (schema.UpdateProfile): The data containing the attributes to be updated.
        user (model.FrontendUser): The user object whose profile is being updated.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.FrontendUser: The updated user object.
    """
    user = authToken.user
    if request.username:
        existing_user = db.query(model.FrontendUser).filter_by(username=request.username).first()
        if existing_user:
            CustomValidations.customError(
                type="exist",
                loc="username",
                msg="Username already in use",
                inp=request.username,
                ctx={"username": "unique"}
            )
        user.username = request.username

    if request.timezone:
        exist_timezone = db.query(model.Timezone).filter_by(code=request.timezone).first()
        if not exist_timezone:
            CustomValidations.customError(
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

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def all_subscription_plans(limit: int, offset: int, db: Session):
    """
    Calls the `all_subscription_plans` function from the `backendusercontroller` module and returns the result.

    Args:
        limit (int): The maximum number of subscription plans to retrieve.
        offset (int): The number of subscription plans to skip before retrieving.
        db (Session): The SQLAlchemy database session.

    Returns:
        The result of the `all_subscription_plans` function call.
    """
    return backendusercontroller.all_subscription_plans(limit, offset, db)


def subscription_plan_detail(suid: str, db: Session):
    """
    Calls the subscription_plan_details function from the backendusercontroller module and returns its result.

    Args:
        suid (str): The ID of the subscription plan.
        db (Session): The SQLAlchemy database session.

    Returns:
        The result of the subscription_plan_details function.
    """
    return backendusercontroller.subscription_plan_details(suid, db)


def timezonesList(db: Session):
    """
    Retrieves a list of all timezones from the database.

    Args:
        db (Session): The SQLAlchemy database session.

    Returns:
        List: A list of all timezones from the database.
    """
    return db.query(model.Timezone).all()

def stripe_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, db: Session):
    """
    Adds a new order to the database.

    Args:
        request (schema.AddOrder): The request object containing the details of the order to be added.
        authtoken (model.FrontendToken): The authentication token of the user making the order.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Order: The newly created order object.
    """

    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, db)

    if not subscription or subscription.is_deleted:
        CustomValidations.customError(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convertCurrency(request.currency)

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
        coupon = backendusercontroller.couponDetails(request.coupon_code)
        if not coupon or not coupon.is_active:
            CustomValidations.customError(
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
    db.add(order)
    db.commit()
    db.refresh(order)

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
        # print(intent)
    except Exception as e:
        CustomValidations.customError(
            type="stripe_error",
            loc="currency",
            msg=str(e),
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

    db.add(order_product)
    db.commit()
    order.clientSecret = intent['client_secret']
    return order


def stripe_add_transaction(request: schema.StripeReturn, authToken: model.FrontendToken, db: Session) -> model.Transaction:
    """
    Updates the status of an order in the database based on the Stripe payment status.
    Creates a new transaction record for the order if it doesn't already exist.
    Updates the active plan of the user associated with the authentication token based on the product ID from the order.

    Args:
        request (schema.StripeReturn): An object containing the details of the Stripe payment.
        authToken (model.FrontendToken): The authentication token of the user.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Transaction: The transaction record associated with the order.
    """
    # Retrieve the order from the database based on the order unique ID provided in the request
    order = db.query(model.Order).filter_by(ouid=request.description).first()

    # Update the status of the order with the status from the request
    order.status = request.status

    # Add the updated order to the database and commit the changes
    db.add(order)
    db.commit()

    # Retrieve the transaction record associated with the order from the database
    transaction = db.query(model.Transaction).filter_by(order_id=order.id).first()

    # If the transaction record doesn't exist, create a new transaction record with the order ID, status, payment gateway, and payment ID from the request
    if not transaction:
        transaction = model.Transaction(
            order_id=order.id,
            status=request.status,
            payment_gateway="stripe",
            payment_id=request.id,
        )

        # Add the new transaction record to the database and commit the changes
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

    # Retrieve the user associated with the authentication token
    user = authToken.user

    # Retrieve the order product from the database based on the order ID
    order_product = db.query(model.OrderProduct).filter_by(order_id=order.id).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database and commit the changes
    db.add(user)
    db.commit()

    # Refresh the transaction record to include any changes made during the commit
    db.refresh(transaction)

    # Return the transaction record
    return transaction


def paypal_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, db: Session):
    """
    Adds a new order to the database.

    Args:
        request (schema.AddOrder): The request object containing the details of the order to be added.
        authtoken (model.FrontendToken): The authentication token of the user making the order.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Order: The newly created order object.
    """

    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, db)

    if not subscription or subscription.is_deleted:
        CustomValidations.customError(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convertCurrency(request.currency)

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
        coupon = backendusercontroller.couponDetails(request.coupon_code)
        if not coupon or not coupon.is_active:
            CustomValidations.customError(
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
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        # Create a PaymentIntent with the order amount and currency
        accessToken = generatePaypalAccessToken()
        url = f'{PAYPAL_BASE_URL}/v2/checkout/orders'
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": order.currency,
                    "value": round(order.final_amount, 2),
                },
            }],
        }

        response = requests.post(
            url=url,
            headers={"Authorization": f'Bearer {accessToken}'},
            json=payload
        )
        paypal = response.json()

    except Exception as e:
        print(e)
        CustomValidations.customError(
            type="paypal_error",
            loc="payment gateway",
            msg=str(e),
            inp="paypal",
            ctx={"paypal": "error"}
        )

    if 'id' not in paypal:
        CustomValidations.customError(
            type=paypal['name'],
            loc="paypal",
            msg=paypal['message'],
            inp='paypal',
            ctx={"paypal": paypal["links"]}
        )

    order_product = model.OrderProduct(
        product_price = subscription.price,
        product_sale_price = subscription.sale_price,
        order_id = order.id,
        product_id = subscription.id,
        quantity = 1,
    )

    db.add(order_product)
    db.commit()
    order.clientSecret = paypal['id']
    return order


def paypal_add_transaction(request: schema.StripeReturn, authToken: model.FrontendToken, db: Session):
    """
    Add a transaction to the database when a payment is made through PayPal.

    Args:
        request (schema.StripeReturn): An object containing the details of the PayPal payment.
        authToken (model.FrontendToken): The authentication token of the user making the payment.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Transaction: The newly created transaction object.
    """
    # Retrieve the order from the database based on the provided order ID
    order = db.query(model.Order).filter_by(ouid=request.description).first()

    # Update the status of the order with the status from the payment request
    order.status = request.status

    # Add the updated order to the database
    db.add(order)
    db.commit()

    # Check if a transaction already exists for the order
    transaction = db.query(model.Transaction).filter_by(order_id=order.id).first()
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
    db.add(transaction)
    db.commit()

    # Refresh the transaction object with the updated values
    db.refresh(transaction)

    # Retrieve the user associated with the authentication token
    user = authToken.user

    # Retrieve the order product from the database based on the order ID
    order_product = db.query(model.OrderProduct).filter_by(order_id=order.id).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database and commit the changes
    db.add(user)
    db.commit()

    # Refresh the transaction record to include any changes made during the commit
    db.refresh(transaction)

    # Return the transaction record
    return transaction


def razorpay_add_orders(request: schema.AddOrder, authtoken: model.FrontendToken, db: Session):
    """
    Adds a new order to the database.

    Args:
        request (schema.AddOrder): The request object containing the details of the order to be added.
        authtoken (model.FrontendToken): The authentication token of the user making the order.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Order: The newly created order object.
    """
    # Retrieve the subscription details based on the provided subscription ID
    subscription = backendusercontroller.subscription_plan_details(request.suid, db)

    if not subscription or subscription.is_deleted:
        CustomValidations.customError(
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist.",
            inp=request.suid,
            ctx={"suid": "exist"}
        )

    # Calculate the total amount of the order
    currency = convertCurrency(request.currency)
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
        coupon = backendusercontroller.couponDetails(request.coupon_code)
        if not coupon or not coupon.is_active:
            CustomValidations.customError(
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
    db.add(order)
    db.commit()
    db.refresh(order)

    try:
        # Create a PaymentIntent with the order amount and currency
        client = razorpay.Client(auth=(SETTINGS.RAZORPAY_CLIENT, SETTINGS.RAZORPAY_SECRET))
        client.set_app_details({"title" : SETTINGS.APP_NAME})
        payment = client.order.create(data={ "amount": int(order.final_amount * 100), "currency": order.currency, "receipt":  order.ouid })
    except Exception as e:
        CustomValidations.customError(
            type="stripe_error",
            loc="currency",
            msg=str(e),
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

    db.add(order_product)
    db.commit()
    order.clientSecret = payment['id']
    return order


def razorpay_add_transaction(request: schema.RazorpayReturn, authToken: model.FrontendToken, db: Session):
    """
    Updates the status of an order in the database and creates a new transaction record for the order.
    If a transaction record already exists for the order, it returns the existing record.
    It also updates the active plan of the user associated with the order.

    Args:
        request (schema.RazorpayReturn): An object containing the details of the Razorpay payment return.
        authToken (model.FrontendToken): The authentication token of the user.
        db (Session): The SQLAlchemy database session.

    Returns:
        model.Transaction: The newly created or existing transaction record for the order.
    """
    # Retrieve the order from the database based on the provided order unique ID (ouid)
    order = db.query(model.Order).filter_by(ouid=request.ouid).first()

    # Update the status of the order with the status provided in the request
    order.status = request.status

    # Add the updated order to the database and commit the changes
    db.add(order)
    db.commit()

    # Check if a transaction record already exists for the order
    transaction = db.query(model.Transaction).filter_by(order_id=order.id).first()

    if transaction:
        # If a transaction record exists, return the existing record
        return transaction

    # If a transaction record does not exist, create a new transaction record with the details from the request
    transaction = model.Transaction(
        order_id=order.id,
        status=request.status,
        payment_gateway="razorpay",
        payment_id=request.razorpay_payment_id,
    )

    # Add the new transaction record to the database and commit the changes
    db.add(transaction)
    db.commit()

    # Retrieve the user associated with the authentication token
    user = authToken.user

    # Retrieve the order product from the database based on the order ID
    order_product = db.query(model.OrderProduct).filter_by(order_id=order.id).first()

    # Update the active plan of the user with the product ID from the order product
    user.active_plan = order_product.product_id

    # Add the updated user to the database and commit the changes
    db.add(user)
    db.commit()

    # Create subscription-user mapping
    subscription_user = backendusercontroller.create_subscription_user(order_product.product_id, user.id, transaction.id, db)

    # Refresh the transaction record to include any changes made during the commit
    db.refresh(transaction)

    # Return the transaction record
    return transaction


