from typing import Optional
import getpass
import secrets
from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy.orm import Session
from sqlalchemy import func

from dependencies import (
    TOKEN_LIMIT, TOKEN_VALIDITY, 
    BackendEmail, CustomValidations, Hash, 
    generate_token, generate_uuid
)

from . import model, schema


def all_backend_users(limit: int, offset: int, db: Session):
    """
    Retrieves a specified number of backend users from the database, along with the total count of all backend users.

    Args:
        limit (int): The maximum number of backend users to retrieve.
        offset (int): The number of backend users to skip before retrieving.
        db (Session): An instance of the SQLAlchemy Session class representing the database session.

    Returns:
        dict: A dictionary containing the retrieved backend users and the total count of all backend users.
    """
    total = db.query(func.count(model.BackendUser.id)).scalar()
    users = db.query(model.BackendUser).limit(limit).offset(offset).all()
    return {
        "users": users,
        "total": total
    }


def userDetails(user_id: str, db: Session):
    """
    Retrieves all details of a user from the database based on the provided user_id.

    Args:
        user_id (str): The unique identifier of the user.
        db (Session): An instance of the SQLAlchemy Session class representing the database session.

    Returns:
        BackendUser: An instance of the BackendUser model representing the user details.

    Raises:
        CustomError: If the user does not exist in the database.
    """
    user = db.query(model.BackendUser).filter_by(uuid=user_id).first()
    if not user:
        CustomValidations.customError(
            type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=user_id,
            ctx={"user": "exist"}
        )
    return user


def create_user(user: schema.RegisterUser, db: Session) -> (model.BackendUser | None):
    """
    Creates a new backend user in the database.

    Args:
        user: An instance of the `RegisterUser` schema class containing the user details.
        db: An instance of the SQLAlchemy `Session` class representing the database session.

    Returns:
        The newly created `BackendUser` object if the email is sent successfully, None otherwise.
    """
    # Check if a user with the same email or username already exists in the database
    existing_user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == user.email) | (model.BackendUser.username == user.username)
    ).first()

    if existing_user:
        # If a user with the same username exists, raise an error indicating that the username is already in use
        if user.username == existing_user.username :
            CustomValidations.customError(
                type="exist",
                loc="username",
                msg="Username already in use",
                inp=user.username,
                ctx={"username": "unique"},
            )

        # If a user with the same email exists, raise an error indicating that the email is already in use
        if user.email == existing_user.email :
            CustomValidations.customError(
                type="exist",
                loc="email",
                msg="Email already in use",
                inp=user.email,
                ctx={"email": "unique"},
            )
        
    # Check if the specified role exists in the database
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid == user.role_id, model.BackendRole.is_deleted == False
    ).first()
    if not role:
        CustomValidations.customError(
            type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=user.role_id,
            ctx={"role": "exist"},
        )

    # Create a new `BackendUser` instance with the provided user details and the generated UUID
    new_user = model.BackendUser(
        uuid=generate_uuid(user.username), # Generate a unique UUID for the new user based on their username
        username=user.username,
        email=user.email,
        role_id=role.id,
        password=Hash.bcrypt(user.password),
        verification_token=generate_token(32),
    )
    
     # Add the new user to the database session
    db.add(new_user)
    db.commit()

    # Refresh the new user object to get the updated values from the database
    db.refresh(new_user)

    # Create an instance of `BackendEmail` to send the email verification token
    backend_email = BackendEmail()
    if backend_email.sendEmailVerificationToken(new_user):
        return new_user
    else:
        CustomValidations.customError(
        status_code=status.HTTP_417_EXPECTATION_FAILED,
        type="Internal",
        loc="email",
        msg="Cannot send email.",
        inp=user.email,
    )


def createsuperuser(db: Session) -> Optional[bool]:
    """
    Create a superuser account from command line.

    Args:
        db (Session): The database session.

    Returns:
        Optional[bool]: True if the superuser account is created successfully, None otherwise.
    """
    superuser = db.query(model.BackendUser).filter(model.BackendUser.id == 0).first()

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

    superuserrole = db.query(model.BackendRole).filter(model.BackendRole.id == 0).first()
    if not superuserrole:
        superuserrole = model.BackendRole(id=0, ruid=generate_uuid("superuser"), role="superuser")

        db.add(superuserrole)
        db.commit()
        db.refresh(superuserrole)

    superuser = model.BackendUser(
        id=0,
        uuid=generate_uuid(username),
        username=username,
        email=email,
        password=Hash.bcrypt(password),
        role_id=superuserrole.id,
        verification_token=secrets.token_urlsafe(32),
    )

    db.add(superuser)
    db.commit()
    db.refresh(superuser)

    backend_email = BackendEmail()
    if not backend_email.sendEmailVerificationToken(superuser):
        print("Can't send email.")

    print("Superuser account created successfully.")
    return True


def updateUserRole(data: schema.UpdateUser, db: Session):
    """
    Updates the role and status of a user in the database based on the provided data.

    Args:
        data (schema.UpdateUser): The data containing the user ID, role ID, and status to be updated.
        db (Session): The database session object.

    Returns:
        model.BackendUser: The updated user object with the role and status updated.
    """
    user = db.query(model.BackendUser).filter(model.BackendUser.uuid == data.user_id).first()
    if not user:
        CustomValidations.customError(
            type="not_exist",
            loc="user_id",
            msg="No user found.",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    if data.role_id:
        role = db.query(model.BackendRole).filter(model.BackendRole.ruid == data.role_id).first()
        if not role:
            CustomValidations.customError(
                type="not_exist",
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

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def verify_email(token: str, db: Session):
    """
    Verify email through token and enable user account login.

    Args:
        token (str): The verification token provided by the user.
        db (Session): The database session object used to query and update the database.

    Returns:
        dict: A dictionary with a "details" key indicating that the email has been verified successfully.
    """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == token,
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc="token",
            msg="Invalid verification token",
            inp=token,
            ctx={"token": "exist"}
        )

    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="deactive",
            loc="account",
            msg="Your account is deactivated!",
            inp=token,
            ctx={"account": "active"}
        )

    user.email_verified_at = datetime.utcnow()
    user.verification_token = None
    db.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, db: Session):
    """
    Create a login token for backend user

    Args:
        request: An instance of the LoginUser schema class containing the username or email and password of the user.
        db: An instance of the SQLAlchemy Session class representing the database session.

    Returns:
        The generated login token for the backend user.
    """
    # Query the database to find the backend user based on the provided username or email
    user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == request.username_or_email) |
        (model.BackendUser.username == request.username_or_email),
        model.BackendUser.is_deleted == False,    
    ).first()


    # If the user does not exist, raise an HTTPException with a 403 status code and an error message
    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="username_or_email",
            msg="Email/Username is wrong!",
            inp=request.username_or_email,
            ctx={"username_or_email": "exist"}
        )

    # Verify the password provided by the user. If it does not match the stored password, raise an HTTPException with a 403 status code and an error message
    if not Hash.verify(user.password, request.password):
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed",
            loc="password",
            msg="Password is wrong!",
            inp=request.password,
            ctx={"password": "match"}
        )

    # Check if the user's email has been verified. If not, raise an HTTPException with a 403 status code and an error message
    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required",
            msg="Verify your email first!",
        )

    # Check if the user's account is active. If not, raise an HTTPException with a 403 status code and an error message
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!",
        )

    db.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id,
        model.BackendToken.expire_at < datetime.now()
    ).delete()
    db.commit()
    # Count the number of active tokens for the user. If it exceeds the token limit, raise an HTTPException with a 403 status code and an error message
    tokens_count = db.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id
    ).count()
    
    if tokens_count >= TOKEN_LIMIT:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="limit_exceed",
            msg=f"Login limit exceed (${TOKEN_LIMIT}).",
        )

    

    # Generate a new token, set its expiration time, and save it to the database
    token = model.BackendToken(
        token=generate_token(16),
        user_id=user.id,
        details=request.details.to_string(),
        expire_at=datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))

    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return token


def send_verification_mail(email: str, db: Session):
    """
    Sends a verification token in an email for the forget password feature.

    Args:
        email (str): The email address of the user for whom the verification token is to be sent.
        db (Session): The database session object used to query and update the database.

    Returns:
        dict: A dictionary with a success message if the email is sent successfully.

    Raises:
        CustomError: If the user does not exist or the account is suspended.
        CustomError: If the email cannot be sent.
    """
    # Query the database to find the user with the given email address
    user = db.query(model.BackendUser).filter(
        model.BackendUser.email == email,
        model.BackendUser.is_deleted == False
    ).first()

    # If the user does not exist, raise an exception indicating that no account was found
    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc="email",
            msg="No account found.",
            inp=email,
            ctx={"email": "exist"}
        )

    # If the user is not active, raise an exception indicating that the account is suspended
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended",
            msg="Your account is suspended!"
        )

    # Generate a verification token
    user.verification_token = generate_token(32)
    db.commit()
    db.refresh(user)

    # Create an instance of the BackendEmail class
    backendEmail = BackendEmail()

    # Send an email with the verification token using the sendForgetPasswordToken method of the BackendEmail instance
    if backendEmail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else:
        # If the email cannot be sent, raise an exception indicating the failure to send the email
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="mail_sent_error",
            msg="Cannot send email."
        )


def create_new_password(request: schema.ForgotPassword, db: Session):
    """
    Verify the token and change the password of the user

    Args:
        request: An instance of the `ForgotPassword` schema class, containing the token and new password.
        db: An instance of the `Session` class from SQLAlchemy, representing the database session.

    Returns:
        The updated user object with the new password and updated timestamp.
    """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == request.token,
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="expired",
            loc="token",
            msg="Token is expired!",
            inp=request.token,
            ctx={"token": "valid"}
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

    user.password = Hash.bcrypt(request.password)
    user.verification_token = None
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_permission(request: schema.BasePermission, db: Session) -> model.BackendPermission:
    """
    Creates a new permission in the database.

    Args:
        request (schema.BasePermission): The request object containing the permission details.
        db (Session): The database session object.

    Returns:
        model.BackendPermission: The newly created permission object.
    """
    existing_permission = db.query(model.BackendPermission).filter_by(codename=request.codename).first()
    if existing_permission:
        CustomValidations.customError(
            type="exist",
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

    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    return new_permission


def get_roles_list(db: Session):
    """ Returns all roles except superuser """
    return db.query(model.BackendRole).filter(model.BackendRole.id!=0).all()


def add_role(request: schema.CreateRole, user: model.BackendToken, db: Session) -> model.BackendRole:
    """
    Create a new role.

    Args:
        request: An instance of the `CreateRole` schema class, which contains the role name.
        user: An instance of the `BackendToken` model class, representing the user who is creating the role.
        db: An instance of the `Session` class from SQLAlchemy, representing the database session.

    Returns:
        The newly created role as an instance of the `BackendRole` model class.
    """
    role = db.query(model.BackendRole).filter_by(role=request.role).first()
    if role:
        CustomValidations.customError(
            type="already_exist",
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
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role




def assign_permissions(request: schema.AssignPermissions, db: Session):
    """
    Assigns permissions to a role in the database.

    Args:
        request (schema.AssignPermissions): An object containing the role ID (`ruid`) and a list of permissions (`permissions`) to be assigned to the role.
        db (Session): An instance of the SQLAlchemy `Session` class representing the database session.

    Returns:
        model.BackendRole: The updated role object with the assigned permissions.
    """
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid == request.ruid,
        model.BackendRole.is_deleted == False
    ).first()

    if not role:
        CustomValidations.customError(
            type="not_exist",
            loc="ruid",
            msg="Role not found!",
            inp=request.ruid,
            ctx={"ruid": "exist"}
        )


    codenames = request.permissions
    permissions = db.query(model.BackendPermission).filter(model.BackendPermission.codename.in_(codenames)).all()

    db.query(model.BackendRolePermission).filter(model.BackendRolePermission.role_id ==role.id).delete()

    db.commit()
    for permission in permissions:
        role_permission = model.BackendRolePermission(role_id=role.id, permission_id=permission.id)
        db.add(role_permission)

    db.commit()
    db.refresh(role)
    return role


def delete_token(authToken: model.BackendToken, db: Session):
    """
    Deletes the login token associated with a specific user from the database.

    Args:
        user (model.BackendUser): An instance of the BackendUser model representing the user for whom the token needs to be deleted.
        db (Session): An instance of the Session class representing the database session.

    Returns:
        bool: True if the token has been successfully deleted.
    """
    db.query(model.BackendToken).filter_by(token=authToken.token).delete()
    db.commit()
    return None


def delete_all_tokens(authToken: model.BackendToken, db: Session):
    """
    Deletes all the login token associated with a specific user from the database.

    Args:
        user (model.BackendUser): An instance of the BackendUser model representing the user for whom the token needs to be deleted.
        db (Session): An instance of the Session class representing the database session.

    Returns:
        bool: True if the tokens has been successfully deleted.
    """
    db.query(model.BackendToken).filter(model.BackendToken.user_id == authToken.user_id).delete()
    db.commit()
    return None


def all_subscription_plans(limit : int, offset : int, db: Session):
    """ Returns all subscription plans """
    subscriptions =  db.query(model.Subscription).limit(limit).offset(offset).all()
    return subscriptions


def add_subscription(data: schema.CreateSubscription, current_user: model.BackendUser, db: Session):
    """
    Creates a new subscription plan.

    Args:
        data (schema.CreateSubscription): An instance of the CreateSubscription schema class containing the details of the new subscription plan.
        current_user (model.BackendUser): An instance of the BackendUser model representing the current user who is creating the subscription plan.
        db (Session): An instance of the Session class representing the database session.

    Returns:
        model.Subscription: An instance of the Subscription model representing the newly created subscription plan.
    """
    # Check if a subscription plan with the same name already exists in the database
    if db.query(model.Subscription).filter(model.Subscription.name == data.name).first():
        CustomValidations.customError(
            type="exist",
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
        validity=data.validity,
        created_by=current_user.id,
    )

    # Add the new subscription to the database session
    db.add(subscription)
    db.commit()

    # Refresh the subscription instance to ensure it reflects the latest state from the database
    db.refresh(subscription)

    return subscription


def delete_subscription_plan(data: schema.UpdateSubscription, db: Session):
    """
    Deletes a subscription plan from the database based on the provided `suid` (subscription ID).

    Args:
        data (schema.UpdateSubscription): The data object containing the `suid` (subscription ID) and `is_deleted` flag.
        db (Session): The database session object.

    Returns:
        model.Subscription: The updated subscription object.
    """
    # Query the database to find the subscription with the provided `suid`
    subscription = db.query(model.Subscription).filter(model.Subscription.suid == data.suid).first()

    # If the subscription does not exist, raise a custom error indicating that the subscription does not exist
    if not subscription:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist",
            loc="suid",
            msg="Subscription does not exist!",
            inp=data.suid,
            ctx={"suid": "exist"}
        )

    # Update the `is_deleted` attribute of the subscription to the value specified in the `data` parameter
    subscription.is_deleted = data.is_deleted

    # Commit the changes to the database
    db.commit()

    # Refresh the subscription object to reflect the updated values
    db.refresh(subscription)

    # Return the updated subscription object
    return subscription



from frontenduser import controller as frontendUserController

def frontenduserdetails(user_id: str, db: Session):
    """
    Calls the userDetails function from the frontendUserController module to retrieve the details of a frontend user.

    Args:
        user_id (str): The ID of the frontend user.
        db (Session): The SQLAlchemy database session.

    Returns:
        The details of the frontend user.
    """
    return frontendUserController.userDetails(user_id, db)


def frontenduserlist(limit: int, offset: int, db: Session):
    """
    Calls the `userList` function from the `frontendUserController` module to retrieve a list of frontend users from the database.

    Args:
        limit (int): The maximum number of users to retrieve.
        offset (int): The number of users to skip before starting to retrieve.
        db (Session): The SQLAlchemy database session.

    Returns:
        list: The list of frontend users retrieved from the database.
    """
    return frontendUserController.userList(limit, offset, db)


def updateBackendUser(data, db: Session):
    """
    Calls the `updateUser` function from the `frontendUserController` module to update the attributes of a user in the database based on the provided data.

    Args:
        data: The data containing the user ID and the attributes to be updated.
        db: The SQLAlchemy database session.

    Returns:
        The updated user object.
    """
    return frontendUserController.updateUser(data, db)


def create_order(data, db: Session):
    pass