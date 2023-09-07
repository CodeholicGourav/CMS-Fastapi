from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token, generate_uuid, CustomValidations, TOKEN_LIMIT, TOKEN_VALIDITY
from . import schema, model
from datetime import datetime, timedelta
from fastapi import status
import getpass
import secrets


def all_backend_users(limit : int, offset : int, db: Session):
    """ Returns all backend users """
    return db.query(model.BackendUser).limit(limit).offset(offset).all()


def userDetails(user_id: str, db: Session):
    """ Returns all details of the user """
    user =  db.query(model.BackendUser).filter_by(uuid=user_id).first()
    if not user: 
        CustomValidations.customError(
            type="not_exist", 
            loc= "user_id", 
            msg= "User does not exist", 
            inp= user_id,
            ctx={"user": "exist"}
        )
    return user


def create_user(user: schema.RegisterUser, db: Session):
    """ Creates a new backend user user """
    existing_user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == user.email) 
        | 
        (model.BackendUser.username == user.username)
    ).first()

    if existing_user:
        if user.username == existing_user.username :
            CustomValidations.customError(
                type="exist", 
                loc= "username", 
                msg= "Username already in use", 
                inp= user.username,
                ctx={"username": "unique"}
            )
        
        if user.email == existing_user.email :
            CustomValidations.customError(
                type="exist", 
                loc= "email", 
                msg= "Email already in use", 
                inp= user.email,
                ctx={"email": "unique"}
            )
        
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid == user.role_id,
        model.BackendRole.is_deleted == False
    ).first()
    if not role:
        CustomValidations.customError(
            type="not_exist", 
            loc= "role", 
            msg= "role does not exist", 
            inp= user.role_id,
            ctx={"role": "exist"}
        )

    new_user = model.BackendUser(
        uuid=generate_uuid(user.username),
        username=user.username,
        email=user.email,
        role_id=role.id,
        password=Hash.bcrypt(user.password),
        verification_token = generate_token(32),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    backendEmail = BackendEmail()
    if backendEmail.sendEmailVerificationToken(new_user):
        return new_user
    else:
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="Internal", 
            loc= "email", 
            msg= "Cannot send email.", 
            inp= user.email,
        )


def createsuperuser(db: Session):
    """ Create a superuser account from command line. """
    superuser = db.query(model.BackendUser).filter(model.BackendUser.id==0).first()

    if superuser:
        print("Superuser already exist!")
        return

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = ""
    c_password = ""
    while password!=c_password or password=="":
        password = getpass.getpass("Enter password: ")
        c_password = getpass.getpass("Enter password to confirm: ")

        if password=="": print("Password can not be blank.")
        if password!=c_password: print("Password did not match, please try again.")

    superuserrole = db.query(model.BackendRole).filter(model.BackendRole.id==0).first()
    if not superuserrole:
        superuserrole = model.BackendRole(id=0, role="superuser") 

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
        verification_token = secrets.token_urlsafe(32)  # Generates a URL-safe token of 32 characters
    )

    db.add(superuser)
    db.commit()
    db.refresh(superuser)
    backendEmail = BackendEmail()
    if not backendEmail.sendEmailVerificationToken(superuser):
        print("Can't send email.")

    print("Superuser account created successfully.")
    return True


def updateUserRole(data: schema.UpdateUser ,  db: Session):
    user = db.query(model.BackendUser).filter(model.BackendUser.uuid==data.user_id).first()
    if not user:
        CustomValidations.customError(
            type="not_exist", 
            loc= "user_id", 
            msg= "No user found.", 
            inp= data.user_id,
            ctx={"user_id": "exist"}
        )
    
    
    if data.role_id:
        role = db.query(model.BackendRole).filter(model.BackendRole.ruid==data.role_id).first()
        if not role:
            CustomValidations.customError(
                type="not_exist", 
                loc= "role_id", 
                msg= "Role not found", 
                inp= data.role_id,
                ctx={"role_id": "exist"}
            )
        user.role_id = role.id
    
    if data.is_active is not None: user.is_active = data.is_active

    if data.is_deleted is not None: user.is_deleted = data.is_deleted

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def verify_email(token: str, db: Session):
    """ Verify email through token and enable user account login """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == token,
        model.BackendUser.is_deleted == False
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
    db.commit()
    return {"details": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, db: Session):
    """ Create a login token for backend user """
    user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == request.username_or_email) |
        (model.BackendUser.username == request.username_or_email),
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed", 
            loc= "username_or_email", 
            msg= "Email/Userame is wrong!", 
            inp= request.username_or_email,
            ctx={"username_or_email": "exist"}
        )
    
    if not Hash.verify(user.password, request.password):
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_failed", 
            loc= "password", 
            msg= "Password is wrong!", 
            inp= request.password,
            ctx={"password": "match"}
        )
    
    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required", 
            msg= "Verify your email first!", 
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended", 
            msg= "Your account is suspended!", 
        )
    
    tokens_count = db.query(model.BackendToken).filter(
        model.BackendToken.user_id == user.id, 
        model.BackendToken.expire_at > datetime.now()
    ).count()
    if tokens_count>=TOKEN_LIMIT:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="limit_exceed", 
            msg= f"Login limit exceed (${TOKEN_LIMIT}).", 
        )
    
    token = model.BackendToken(
        token = generate_token(16),
        user_id = user.id,
        expire_at = datetime.utcnow() + timedelta(hours=int(TOKEN_VALIDITY))
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def send_verification_mail(email: str, db: Session):
    """ sends a token in mail for forget password """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.email == email,
        model.BackendUser.is_deleted == False
    ).first()
    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist", 
            loc= "email", 
            msg= "No account found.", 
            inp= email,
            ctx={"email": "exist"}
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended", 
            msg= "Your account is suspended!", 
        )
    
    user.verification_token = generate_token(32)
    db.commit() 
    db.refresh(user)
    backendEmail = BackendEmail()
    if backendEmail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else :
        CustomValidations.customError(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            type="mail_sent_error", 
            msg= "Cannot send email.", 
        )


def create_new_password(request: schema.ForgotPassword, db: Session):
    """ Verify the token and change the password of the user """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == request.token,
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="expired", 
            loc= "token", 
            msg= "Token is expired!", 
            inp= request.token,
            ctx={"token": "valid"}
        )
    
    if not user.email_verified_at:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="verification_required", 
            msg= "Verify your email first!", 
        )
    
    if not user.is_active:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="suspended", 
            msg= "Your account is suspended!", 
        )
    
    user.password = Hash.bcrypt(request.password)
    user.verification_token = None 
    user.updated_at = datetime.utcnow 
    db.commit()
    db.refresh(user)
    return user


def create_permission(request: schema.BasePermission, db: Session) :
    """ Creates a new permission """
    existingPermission = db.query(model.BackendPermission).filter(model.BackendPermission.codename==request.codename).first()
    if existingPermission:
        CustomValidations.customError(
            type="exist", 
            loc= "codename", 
            msg= "Permission already exist!", 
            inp= request.codename,
            ctx={"codename": "unique"}
        )
    
    newPermission = model.BackendPermission(
        permission = request.permission,
        type = request.type,
        codename = request.codename
    )

    db.add(newPermission)
    db.commit()
    db.refresh(newPermission)
    return newPermission


def get_roles_list(db: Session):
    """ Returns all roles except superuser """
    return db.query(model.BackendRole).filter(model.BackendRole.id!=0).all()


def add_role(request: schema.CreateRole, user: model.BackendToken, db : Session):
    """ Create a new role """
    role = db.query(model.BackendRole).filter_by(role=request.role).first()
    print(role)
    if role :
        CustomValidations.customError(
            type="already_exist", 
            loc= "role", 
            msg= "Role already exist", 
            inp= request.role, 
            ctx= {"role":"unique"}
        )
    
    new_role = model.BackendRole(
        ruid=generate_uuid(request.role),
        role = request.role,
        created_by = user.id
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


def assign_permissions(request : schema.AssignPermissions, db : Session):
    """ Assign permission to a role """
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid==request.ruid, 
        model.BackendRole.is_deleted==False
    ).first()

    if not role:
        CustomValidations.customError(
            type="not_exist", 
            loc= "ruid", 
            msg= "Role not found!", 
            inp= request.ruid,
            ctx={"ruid": "exist"}
        )
    
    codenames = request.permissions
    permissions = db.query(model.BackendPermission).filter(model.BackendPermission.codename.in_(codenames)).all()
    
    for permission in permissions:
        if not (
            db.query(model.BackendRolePermission).filter(
                model.BackendRolePermission.role_id==role.id, 
                model.BackendRolePermission.permission_id==permission.id
            ).first()
        ) :
            role_permission = model.BackendRolePermission(role_id=role.id, permission_id=permission.id)
            db.add(role_permission)
    
    db.commit()
    db.refresh(role)
    return role


def delete_token(user: model.BackendUser, db: Session):
    """ Deletes the login token """
    db.query(model.BackendToken).filter(model.BackendToken.user_id==user.id).delete()
    db.commit()
    return True


def all_subscription_plans(limit : int, offset : int, db: Session):
    """ Returns all subscription plans """
    subscriptions =  db.query(model.Subscription).limit(limit).offset(offset).all()
    return subscriptions


def add_subscription(data: schema.CreateSubscription, current_user: model.BackendUser, db: Session):
    """ Creates a new subscription plan """
    if db.query(model.Subscription).filter(model.Subscription.name==data.name).first():
        CustomValidations.customError(
            type="exist", 
            loc= "name", 
            msg= "Name already exist!", 
            inp= data.name,
            ctx={"name": "unique"}
        )
    
    subscription = model.Subscription(
        suid=generate_uuid(data.name),
        name = data.name,
        description = data.description,
        price = data.price,
        validity = data.validity,
        created_by = current_user.id,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription_plan(data: schema.UpdateSubscription, db: Session):
    subscription = db.query(model.Subscription).filter(model.Subscription.suid==data.suid).first()
    if not subscription:
        CustomValidations.customError(
            status_code=status.HTTP_403_FORBIDDEN,
            type="not_exist", 
            loc= "suid", 
            msg= "Subscription does not exist!", 
            inp= data.suid,
            ctx={"suid": "exist"}
        )
    
    subscription.is_deleted = data.is_deleted
    db.commit()
    db.refresh(subscription)
    return subscription


from frontenduser import controller as frontendUserController

def frontenduserdetails(user_id: str, db: Session):
    """ Returns all details of the user """
    return frontendUserController.userDetails(user_id, db)


def frontenduserlist(limit: int, offset: int, db: Session):
    return frontendUserController.userList(limit, offset, db)


def updateBackendUser(data, db: Session):
    return frontendUserController.updateUser(data, db)