from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token
from . import schema, model
from datetime import datetime, timedelta
from fastapi import HTTPException,status
from dateutil.relativedelta import relativedelta


def all_backend_users(limit : int, offset : int, db: Session):
    """ Returns all backend users """
    return db.query(model.BackendUser).limit(limit).offset(offset).all()


def userDetails(user_id: str, db: Session):
    """ Returns all details of the user """
    return db.query(model.BackendUser).filter(model.BackendUser.uuid==user_id).first()


def create_user(user: schema.RegisterUser, db: Session):
    """ Creates a new backend user user """
    existing_user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == user.email) 
        | 
        (model.BackendUser.username == user.username)
    ).first()

    if existing_user:
        if user.username == existing_user.username :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username already in use")
        
        if user.email == existing_user.email :
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email already in use")
        
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid == user.role_id,
        model.BackendRole.is_deleted == False
        ).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role does not exist.")

    new_user = model.BackendUser(
        username=user.username,
        email=user.email,
        role_id=user.role_id,
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
        raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail="Cannot send email.")


def updateUserRole(data: schema.UpdateUser ,  db: Session):
    user = db.query(model.BackendUser).filter(model.BackendUser.uuid==data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No user found.")
    
    if data.role_id:
        role = db.query(model.BackendRole).filter(model.BackendRole.ruid==data.role_id).first()
        if not role:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role not found")
        user.role_id = data.role_id
    
    if data.is_active is not None: user.is_active = data.is_active

    if data.is_deleted is not None: user.is_deleted = data.is_deleted

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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid verification token")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    
    user.email_verified_at = datetime.utcnow()
    user.verification_token = None 
    db.commit()
    return {"message": "Email verified successfully"}


def create_auth_token(request: schema.LoginUser, db: Session):
    """ Create a login token for backend user """
    user = db.query(model.BackendUser).filter(
        (model.BackendUser.email == request.username_or_email) 
        |
        (model.BackendUser.username == request.username_or_email),
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not Hash.verify(user.password, request.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email or password is wrong!")
    
    if not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your email first!")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    token = model.BackendToken(
        token = generate_token(16),
        user_id = user.uuid,
        expire_at = datetime.utcnow() + timedelta(hours=24)
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    token.user = user
    return token


def send_verification_mail(email: str, db: Session):
    """ sends a token in mail for forget password """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.email == email,
        model.BackendUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No account found.")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    user.verification_token = generate_token(32)
    db.commit() 
    db.refresh(user)
    backendEmail = BackendEmail()
    if backendEmail.sendForgetPasswordToken(user):
        return {"message": "Email sent successfully"}
    else :
        raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail="Cannot send email.")


def create_new_password(request: schema.ForgotPassword, db: Session):
    """ Verify the token and change the password of the user """
    user = db.query(model.BackendUser).filter(
        model.BackendUser.verification_token == request.token,
        model.BackendUser.is_deleted == False
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token is expired!")
    
    if not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verify your email first!")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account is suspended!")
    
    user.password = Hash.bcrypt(request.password)
    user.verification_token = None 
    db.commit()
    db.refresh(user)
    return user


def create_permission(request: schema.BasePermission, db: Session) :
    """ Creates a new permission """
    existingPermission = db.query(model.BackendPermission).filter(model.BackendPermission.codename==request.codename).first()
    if existingPermission:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already exist!")
    
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
    roles_list = db.query(model.BackendRole).filter(model.BackendRole.id!=0).all()
    for role in roles_list:
        creator = db.query(model.BackendUser).filter(model.BackendUser.uuid==role.created_by).first()
        permissions = db.query(model.BackendRolePermission).filter(model.BackendRolePermission.role_id==role.ruid).all()

        role.creator = creator
        role.permissions = permissions
    
    return roles_list


def add_role(request: schema.CreateRole, user: schema.CreateRole, db : Session):
    """ Create a new role """
    new_role = model.BackendRole(
        role = request.role,
        created_by = user.uuid
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    new_role.creator = user
    new_role.permissions = []
    return new_role


def assign_permissions(request : schema.AssignPermissions, db : Session):
    """ Assign permission to a role """
    role = db.query(model.BackendRole).filter(
        model.BackendRole.ruid==request.ruid, 
        model.BackendRole.is_deleted==False
    ).first()

    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role not found!")
    
    codenames = request.permissions
    permissions = db.query(model.BackendPermission).filter(model.BackendPermission.codename.in_(codenames)).all()
    role.permissions = permissions
    
    for permission in permissions:
        role_permission = model.BackendRolePermission(role_id=role.ruid, permission_id=permission.codename)
        db.add(role_permission)
    
    db.commit()
    db.refresh(role)

    creator = db.query(model.BackendUser).filter(model.BackendUser.uuid==role.created_by).first()
    role.creator = creator
    return role


def delete_token(user: model.BackendUser, db: Session):
    """ Deletes the login token """
    db.query(model.BackendToken).filter(model.BackendToken.user_id==user.uuid).delete()
    db.commit()
    return True


def all_subscription_plans(limit : int, offset : int, db: Session):
    """ Returns all subscription plans """
    subscriptions =  db.query(model.Subscription).limit(limit).offset(offset).all()
    return subscriptions


def add_subscription(data: schema.CreateSubscription, current_user: schema.ShowUser, db: Session):
    """ Creates a new subscription plan """
    if db.query(model.Subscription).filter(model.Subscription.name==data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name already exist!")
    
    subscription = model.Subscription(
        name = data.name,
        description = data.description,
        price = data.price,
        validity = data.validity,
        created_by = current_user.uuid,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    subscription.creator = current_user
    return subscription


def test(db: Session):
    """ Just for testing """
    user = db.query(model.BackendUser).first()
    print(user.created_at + relativedelta(days=10))
    return user.created_at