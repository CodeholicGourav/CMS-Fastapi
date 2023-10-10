"""
backenduser/controller.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import getpass
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm.exc import NoResultFound
from fastapi import status, BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session

from dependencies import (
    TOKEN_LIMIT, TOKEN_VALIDITY,
    BackendEmail,CustomValidations, Hash,
    generate_token,generate_uuid
)
from frontenduser import controller as frontendUserController

from . import model, schema


def all_backend_users(limit: int, offset: int, sql: Session):
    """
    Retrieves:
        Specified number of backend users from the database.
        Total count of all backend users.
    """
    total = sql.query(func.count(model.BackendUser.id)).scalar()
    users = sql.query(model.BackendUser).limit(limit).offset(offset).all()
    return {
        "users": users,
        "total": total
    }


def user_details(user_id: str, sql: Session):
    """
    Retrieves all details of a user based on the provided user_id.

    Raises:
        raize_custom_error: If the user does not exist in the database.
    """
    user = sql.query(model.BackendUser).filter_by(uuid=user_id).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=user_id,
            ctx={"user": "exist"}
        )
    return user


def create_user(user: schema.RegisterUser, sql: Session, background_tasks: BackgroundTasks):
    """
    Creates a new backend user in the database.
    """
    # Check if a user with the same email or username already exists in the database
    existing_user = sql.query(model.BackendUser).filter(
        (model.BackendUser.email == user.email) | (model.BackendUser.username == user.username)
    ).first()

    if existing_user:
        # If a user with the same username exists, raise an error
        if user.username == existing_user.username :
            CustomValidations.raize_custom_error(
                error_type="exist",
                loc="username",
                msg="Username already in use",
                inp=user.username,
                ctx={"username": "unique"},
            )

        # If a user with the same email exists, raise an error
        if user.email == existing_user.email :
            CustomValidations.raize_custom_error(
                error_type="exist",
                loc="email",
                msg="Email already in use",
                inp=user.email,
                ctx={"email": "unique"},
            )

    # Check if the specified role exists in the database
    role = sql.query(model.BackendRole).filter_by(
        ruid=user.role_id,
        is_deleted=False
    ).first()
    if not role:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=user.role_id,
            ctx={"role": "exist"},
        )

    # Create a new `BackendUser` instance with the provided user details and the generated UUID
    new_user = model.BackendUser(
        uuid=generate_uuid(user.username),
        username=user.username,
        email=user.email,
        role_id=role.id,
        password=Hash.bcrypt(user.password),
        verification_token=generate_token(32),
    )

     # Add the new user to the database session
    sql.add(new_user)
    sql.commit()

    # Refresh the new user object to get the updated values from the database
    sql.refresh(new_user)

    background_tasks.add_task(BackendEmail.send_email_verification_token(new_user))

    return new_user


def createsuperuser(sql: Session):
    """
    Create a superuser account from command line.
    """
    superuser = sql.query(model.BackendUser).filter_by(id=0).first()

    if superuser:
        print("Superuser already exists!")
        return None

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = ""
    c_password = ""
    while password != c_password or password == "":
        password = getpass.getpass("Enter password: ")
        c_password = getpass.getpass("Enter password to confirm: ")

        if password == "":
            print("Password cannot be blank.")
        if password != c_password:
            print("Password did not match, please try again.")

    superuserrole = sql.query(model.BackendRole).filter_by(id=0).first()
    if not superuserrole:
        superuserrole = model.BackendRole(id=0, ruid=generate_uuid("superuser"), role="superuser")

        sql.add(superuserrole)
        sql.commit()
        sql.refresh(superuserrole)

    superuser = model.BackendUser(
        id=0,
        uuid=generate_uuid(username),
        username=username,
        email=email,
        password=Hash.bcrypt(password),
        role_id=superuserrole.id,
        verification_token=secrets.token_urlsafe(32),
    )

    sql.add(superuser)
    sql.commit()
    sql.refresh(superuser)

    if not BackendEmail.send_email_verification_token(superuser):
        print("Can't send email.")

    print("Superuser account created successfully.")
    return True


def update_user_role(
    data: schema.UpdateUser,
    auth_token: model.BackendToken,
    sql: Session
):
    """
    Updates the role and status of a user in the database based on the provided data.
    """
    if auth_token.user.uuid==data.user_id:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="self_update",
            loc="user_id",
            msg="Can not update self.",
            inp=data.user_id,
            ctx={"user_id": "self"}
        )

    user = sql.query(model.BackendUser).filter_by(uuid=data.user_id).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="No user found.",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    if data.role_id:
        role = sql.query(model.BackendRole).filter_by(ruid=data.role_id).first()
        if not role:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="role_id",
                msg="Role not found",
                inp=data.role_id,
                ctx={"role_id": "exist"}
            )
        user.role_id = role.id

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
    user = sql.query(model.BackendUser).filter_by(
        verification_token=token,
        is_deleted=False
    ).first()

    if not user:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="not_exist",
            loc="token",
            msg="Invalid verification token",
            inp=token,
            ctx={"token": "exist"}
        )

    if not user.is_active:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="deactive",
            loc="account",
            msg="Your account is deactivated!",
            inp=token,
            ctx={"account": "active"}
        )

    user.email_verified_at = datetime.utcnow()
    user.verification_token = None
    sql.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, sql: Session):
    """
    Create a login token for backend user.
    """
    # Query the database to find the backend user based on the provided username or email
    user = sql.query(model.BackendUser).filter(
        (model.BackendUser.email == request.username_or_email) |
        (model.BackendUser.username == request.username_or_email)
    ).filter_by(is_deleted=False).first()


    # If the user does not exist, raise an HTTPException
    if not user:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="verification_failed",
            loc="username_or_email",
            msg="Email/Username is wrong!",
            inp=request.username_or_email,
            ctx={"username_or_email": "exist"}
        )

    # If it does not match the stored password, raise an HTTPException
    if not Hash.verify(user.password, request.password):
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="verification_failed",
            loc="password",
            msg="Password is wrong!",
            inp=request.password,
            ctx={"password": "match"}
        )

    # Check if user's email is not verified, raise an HTTPException
    if not user.email_verified_at:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="verification_required",
            msg="Verify your email first!",
        )

    # Check if the user's account is not active, raise an HTTPException
    if not user.is_active:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="suspended",
            msg="Your account is suspended!",
        )

    sql.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id,
        model.BackendToken.expire_at < datetime.now()
    ).delete()
    sql.commit()
    # If number of active tokens exceeds the token limit, raise an HTTPException
    tokens_count = sql.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id
    ).count()

    if tokens_count >= TOKEN_LIMIT:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="limit_exceed",
            msg=f"Login limit exceed (${TOKEN_LIMIT}).",
        )


    # Generate a new token, set its expiration time, and save it to the database
    token = model.BackendToken(
        token=generate_token(16),
        user_id=user.id,
        details=request.details.to_string(),
        expire_at=datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))

    )
    sql.add(token)
    sql.commit()
    sql.refresh(token)

    return token


def send_verification_mail(email: str, sql: Session):
    """
    Sends a verification token in an email for the forget password feature.
    """
    # Query the database to find the user with the given email address
    user = sql.query(model.BackendUser).filter_by(email=email, is_deleted=False).first()

    # If the user does not exist, raise an exception indicating that no account was found
    if not user:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="not_exist",
            loc="email",
            msg="No account found.",
            inp=email,
            ctx={"email": "exist"}
        )

    # If the user is not active, raise an exception indicating that the account is suspended
    if not user.is_active:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="suspended",
            msg="Your account is suspended!"
        )

    # Generate a verification token
    user.verification_token = generate_token(32)
    sql.commit()
    sql.refresh(user)

    # Send an email with the verification token
    if not BackendEmail.send_forget_password_token(user):
        # If the email cannot be sent, raise an exception
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            error_type="mail_sent_error",
            msg="Cannot send email."
        )
    return True


def create_new_password(request: schema.ForgotPassword, sql: Session):
    """
    Verify the token and change the password of the user.
    """
    user = sql.query(model.BackendUser).filter_by(
        verification_token=request.token,
        is_deleted=False
    ).first()

    if not user:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="expired",
            loc="token",
            msg="Token is expired!",
            inp=request.token,
            ctx={"token": "valid"}
        )

    if not user.email_verified_at:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="verification_required",
            msg="Verify your email first!",
        )

    if not user.is_active:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="suspended",
            msg="Your account is suspended!",
        )

    user.password = Hash.bcrypt(request.password)
    user.verification_token = None
    sql.commit()
    sql.refresh(user)
    return user


def create_permission(request: schema.BasePermission, sql: Session):
    """
    Creates a new permission in the database.
    """
    existing_permission = sql.query(model.BackendPermission).filter_by(
        codename=request.codename
    ).first()
    if existing_permission:
        CustomValidations.raize_custom_error(
            error_type="exist",
            loc="codename",
            msg="Permission already exists!",
            inp=request.codename,
            ctx={"codename": "unique"}
        )

    new_permission = model.BackendPermission(
        permission=request.permission,
        type=request.type,
        codename=request.codename
    )

    sql.add(new_permission)
    sql.commit()
    sql.refresh(new_permission)
    return new_permission


def get_roles_list(sql: Session):
    """ Returns all roles except superuser """
    return sql.query(model.BackendRole).filter(model.BackendRole.id!=0).all()


def add_role(request: schema.CreateRole, user: model.BackendToken, sql: Session):
    """
    Create a new role.
    """
    role = sql.query(model.BackendRole).filter_by(role=request.role).first()
    if role:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="role",
            msg="Role already exists",
            inp=request.role,
            ctx={"role": "unique"}
        )

    new_role = model.BackendRole(
        ruid=generate_uuid(request.role),
        role=request.role,
        created_by=user.id
    )
    sql.add(new_role)
    sql.commit()
    sql.refresh(new_role)
    return new_role


def assign_permissions(
    request: schema.AssignPermissions,
    auth_token: model.BackendToken,
    sql: Session
):
    """
    Assigns permissions to a role in the database.
    """
    if auth_token.user.role.ruid==request.ruid:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="self_update",
            loc="role_id",
            msg="Can not update self.",
            inp=request.ruid,
            ctx={"role_id": "self"}
        )

    role = sql.query(model.BackendRole).filter_by(ruid=request.ruid, is_deleted=False).first()

    if not role:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="ruid",
            msg="Role not found!",
            inp=request.ruid,
            ctx={"ruid": "exist"}
        )


    codenames = request.permissions
    permissions = sql.query(model.BackendPermission).filter(
        model.BackendPermission.codename.in_(codenames)
    ).all()

    sql.query(model.BackendRolePermission).filter_by(role_id=role.id).delete()

    sql.commit()
    for permission in permissions:
        role_permission = model.BackendRolePermission(role_id=role.id, permission_id=permission.id)
        sql.add(role_permission)

    sql.commit()
    sql.refresh(role)
    return role


def delete_token(auth_token: model.BackendToken, sql: Session):
    """
    Deletes the login token associated with a specific user.
    """
    sql.query(model.BackendToken).filter_by(token=auth_token.token).delete()
    sql.commit()
    return True


def delete_all_tokens(auth_token: model.BackendToken, sql: Session):
    """
    Deletes all the login token associated with a specific user.
    """
    sql.query(model.BackendToken).filter_by(user_id=auth_token.user_id).delete()
    sql.commit()
    return True


def all_subscription_plans(limit : int, offset : int, sql: Session):
    """ Returns all subscription plans """
    subscriptions =  sql.query(model.Subscription).limit(limit).offset(offset).all()
    return subscriptions


def subscription_plan_details(suid: str, sql: Session):
    """
    Retrieves details of a subscription plan based on the provided suid.
    If the subscription does not exist, it raises a custom error .
    """
    subscription = sql.query(model.Subscription).filter_by(suid=suid).first()
    if not subscription:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="suid",
            msg="Subscription does not exist",
            inp=suid,
            ctx={"subscription": "exist"}
        )
    return subscription


def add_subscription(
    data: schema.CreateSubscription,
    current_user: model.BackendUser,
    sql: Session
):
    """
    Creates a new subscription plan.
    """
    # Check if a subscription plan with the same name already exists in the database
    if sql.query(model.Subscription).filter_by(name=data.name).first():
        CustomValidations.raize_custom_error(
            error_type="exist",
            loc="name",
            msg="Name already exists!",
            inp=data.name,
            ctx={"name": "unique"}
        )

    # Create a new instance of the Subscription model with the provided data
    subscription = model.Subscription(
        suid=generate_uuid(data.name),
        name=data.name,
        description=data.description,
        price=data.price,
        sale_price=data.sale_price,
        validity=data.validity,
        created_by=current_user.id,
    )

    # Add the new subscription to the database session
    sql.add(subscription)
    sql.commit()
    sql.refresh(subscription)

    # Add any features associated with the subscription plan to the database
    for feature in data.features:
        feature_exit = sql.query(model.Feature).filter_by(
            feature_code=feature.feature_code
        ).first()
        if feature_exit:
            subscription_feature = model.SubscriptionFeature(
                subscription_id=subscription.id,
                feature_id=feature_exit.id,
                quantity=feature.quantity
            )
            sql.add(subscription_feature)

    sql.commit()

    # Refresh the subscription instance to ensure it reflects the latest state from the database
    sql.refresh(subscription)

    return subscription


def update_subscription_plan(data: schema.UpdateSubscription, sql: Session):
    """
    Updates the details of a subscription plan in the database.
    """
    # Query the database to find the subscription with the provided `suid`
    subscription = sql.query(model.Subscription).filter_by(suid=data.suid).first()

    # If the subscription does not exist, raise a custom error
    if not subscription:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="not_exist",
            loc="suid",
            msg="Subscription does not exist!",
            inp=data.suid,
            ctx={"suid": "exist"}
        )

    # Update the subscription's data based on the sent data
    if data.name is not None:
        subscription.name = data.name

    if data.description is not None:
        subscription.description = data.description

    if data.price is not None:
        subscription.price = data.price

    if data.sale_price is not None:
        subscription.sale_price = data.sale_price

    if data.validity is not None:
        subscription.validity = data.validity

    if data.is_deleted is not None:
        subscription.is_deleted = data.is_deleted

    # Commit the changes to the database
    sql.commit()
    # Refresh the subscription object to reflect the updated values
    sql.refresh(subscription)

    if data.features is not None:
        # Delete any existing subscription features
        sql.query(model.SubscriptionFeature).filter_by(
            subscription_id=subscription.id
        ).delete()

        # Add new subscription features
        for feature in data.features:
            feature_exsit = sql.query(model.Feature).filter_by(
                feature_code=feature.feature_code
            ).first()
            if feature_exsit:
                subscription_feature = model.SubscriptionFeature(
                    subscription_id=subscription.id,
                    feature_id=feature_exsit.id,
                    quantity=feature.quantity
                )
                sql.add(subscription_feature)

        # Commit the changes to the database
        sql.commit()
        sql.refresh(subscription_feature)

    # Return the updated subscription object
    return subscription


def delete_subscription_plan(suid: str, is_deleted: bool, sql: Session):
    """
    Deletes a subscription plan based on the provided `suid`.
    """
    # Query the database to find the subscription with the provided `suid`
    subscription = sql.query(model.Subscription).filter_by(suid=suid).first()

    # If the subscription does not exist, raise a custom error
    if not subscription:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="not_exist",
            loc="suid",
            msg="Subscription does not exist!",
            inp=suid,
            ctx={"suid": "exist"}
        )

    # Update the `is_deleted` attribute of the subscription
    subscription.is_deleted = is_deleted

    # Commit the changes to the database
    sql.commit()

    # Refresh the subscription object to reflect the updated values
    sql.refresh(subscription)

    # Return the updated subscription object
    return subscription


def frontenduser_details(user_id: str, sql: Session):
    """
    Retrieves the details of a frontend user.
    """
    return frontendUserController.user_details(user_id, sql)


def frontenduserlist(limit: int, offset: int, sql: Session):
    """
    Retrieves a list of frontend users from the database.
    """
    return frontendUserController.user_list(limit, offset, sql)


def update_frontend_user(data, sql: Session):
    """
    Updates the attributes of a user in the database based on the provided data.
    """
    return frontendUserController.update_user(data, sql)


def coupon_details(coupon_code: str, sql: Session):
    """
    Retrieves details of a coupon based on the provided coupon code.

    Raises:
        CustomValidations.raize_custom_error: If no coupon is found with the provided coupon code.
    """
    coupon = sql.query(model.Coupon).filter_by(coupon_code=coupon_code, is_active=True).first()

    if not coupon:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="coupon_code",
            msg="Coupon does not exist",
            inp=coupon_code,
            ctx={"coupon": "exist"}
        )

    return coupon


def get_all_features(sql: Session):
    """
    Retrieves all the features from the database.
    """
    return sql.query(model.Feature).all()


def create_subscription_user(
    subscription_id: int,
    user_id: int,
    transaction_id: int,
    sql: Session
):
    """
    Creates a new subscription user by associating a subscription, a user, and a transaction.
    Sets the expiry date of the subscription based on the validity of the subscription.
    """
    subscription = sql.query(model.Subscription).get(subscription_id)
    expiry = datetime.utcnow() + timedelta(days=int(subscription.validity))

    subscription_user = model.SubscriptionUser(
        subscription_id=subscription.id,
        user_id=user_id,
        transaction_id=transaction_id,
        expiry=expiry
    )

    sql.add(subscription_user)
    sql.commit()
    sql.refresh(subscription_user)
    return subscription_user
