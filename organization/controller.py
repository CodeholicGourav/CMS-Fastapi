"""
controller.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import json

from fastapi import status
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from backenduser import model as backendModel
from dependencies import CustomValidations, generate_uuid
from frontenduser import model as frontendModel

from . import model, schema


def all_organizations(
    limit: int,
    offset: int,
    sql: Session
):
    """
    Retrieves a specified number of organizations from the database, 
    along with the total count of organizations.
    """
    count = sql.query(model.Organization).count()
    organizations = sql.query(
        model.Organization
    ).limit(limit).offset(offset).all()

    return {
        "total": count,
        "organizations": organizations
    }


def create_organization(
    data: schema.CreateOrganization,
    sql: Session,
    auth_token: frontendModel.FrontendToken,
    subscription: backendModel.SubscriptionFeature
):
    """
    Creates a new organization in the database, 
    performing several validations before saving the organization.
    """

    # Number of organizations can subscription allows.
    org_quantity = subscription.quantity

    total_organizations = sql.query(model.Organization.id).filter_by(
        admin_id=auth_token.id
    ).count()

    if total_organizations >= org_quantity:
        CustomValidations.custom_error(
            type="limit_exceed",
            loc="organization",
            msg=f"Can not create more than '{org_quantity}' organizations.",
            inp=data.org_name,
            ctx={"organization": "limited_creation"}
        )

    # Check if the organization name already exists in the database.
    existing_name = sql.query(model.Organization).filter_by(
        org_name=data.org_name
    ).first()
    if existing_name:
        CustomValidations.custom_error(
            type="existing",
            loc="org_name",
            msg="Organization name already exists.",
            inp=data.org_name,
            ctx={"org_name": "unique"}
        )

    # Check if the registration type provided is allowed.
    if data.registration_type not in model.Organization.allowed_registration:
        CustomValidations.custom_error(
            type="invalid",
            loc="registration_type",
            msg=f"Allowed values are {model.Organization.allowed_registration}",
            inp=data.registration_type,
            ctx={"registration_type": "valid"}
        )

    # Create an instance of OAuth 2.0 credentials using the dictionary
    creds = Credentials.from_authorized_user_info(data.gtoken)

    # Check if the Google token provided is valid.
    if not creds or not creds.valid:
        CustomValidations.custom_error(
            type="Invalid",
            loc="gtoken",
            msg="Not a valid Google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )

    organization = model.Organization(
        orguid=generate_uuid(data.org_name),
        org_name=data.org_name,
        admin_id=auth_token.user_id,
        gtoken=json.dumps(data.gtoken),
        registration_type=data.registration_type
    )

    sql.add(organization)
    sql.commit()
    sql.refresh(organization)

    # Create default role
    org_role = model.OrganizationRole(
        ruid = generate_uuid(data.org_name+"Default"),
        role = 'Default',
        created_by = auth_token.user_id,
        org_id = organization.id
    )
    sql.add(org_role)
    sql.commit()

    return organization


def register_to_organization(
    data: schema.OrgUserRegister,
    sql: Session,
    auth_token: frontendModel.FrontendToken
):
    """
    Registers a user to an organization.
    """
    user = auth_token.user
    organization = sql.query(model.Organization).filter_by(
        orguid=data.org_uid
    ).first()

    if not organization:
        CustomValidations.custom_error(
            type="not_exist",
            loc="org_uid",
            msg="Organization does not exist.",
            inp=str(data.org_uid),
            ctx={"org_uid": "exist"}
        )

    if organization.registration_type == "admin_only":
        CustomValidations.custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="not_allowed",
            loc="org_uid",
            msg="Organization does allow new registration.",
            inp=str(data.org_uid),
            ctx={"registration": "admin_only"}
        )

    admin = organization.admin
    feature = sql.query(backendModel.Feature).filter_by(
        feature_code="add_member"
    ).first()

    subscription_feature = sql.query(
        backendModel.SubscriptionFeature
    ).filter_by(
        subscription_id=admin.active_plan,
        feature_id=feature.id
    ).first()

    user_quantity = subscription_feature.quantity

    total_users = sql.query(
        model.OrganizationUser.id
    ).filter_by(
        org_id=organization.id,
        is_deleted=False,
        is_active=True
    ).count()

    if total_users >= user_quantity:
        CustomValidations.custom_error(
            type="limit_exceed",
            loc="organization",
            msg=f"Can not add more than '{user_quantity}' users.",
            inp=data.org_uid,
            ctx={"organization": "limited_creation"}
        )

    org_user = sql.query(
        model.OrganizationUser
    ).filter_by(
        org_id=organization.id,
        user_id=user.id
    ).first()

    if org_user:
        CustomValidations.custom_error(
            type="already_exist",
            loc="organization",
            msg="User already registered.",
            inp=data.org_uid,
            ctx={"organization": "new_registration"}
        )

    org_user = model.OrganizationUser(
        uuid=generate_uuid(organization.org_name + user.username),
        user_id=user.id,
        org_id=organization.id,
        role_id=1  # Assign default role
    )

    if organization.registration_type == "approval_required":
        org_user.is_active = False

    sql.add(org_user)
    sql.commit()
    sql.refresh(org_user)
    return org_user


def get_all_users(
    limit: int,
    offset: int,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves a specified number of users belonging to a specific organization, 
    along with the total count of users.
    """
    users = sql.query(model.OrganizationUser).filter_by(
        org_id=organization.id
    ).limit(limit).offset(offset).all()
    count = sql.query(model.OrganizationUser.id).filter_by(
        org_id=organization.id
    ).count()

    return {
        "total": count,
        "users": users
    }


def get_user_details(
    uuid: str,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves the details of a user in an organization based on the user's UUID.
    """
    user = sql.query(frontendModel.FrontendUser).filter_by(uuid=uuid).first()
    if not user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=uuid,
            ctx={"user": "exist"}
        )
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id, org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="user_id",
            msg="User does not exist in organization",
            inp=uuid,
            ctx={"user": "exist"}
        )

    return org_user


def get_all_roles(
    limit: int,
    offset: int,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves a specified number of roles belonging to a specific organization,
    along with the total count of roles.
    """
    roles = sql.query(model.OrganizationRole).filter_by(
        org_id=organization.id
    ).limit(limit).offset(offset).all()
    count = sql.query(model.OrganizationRole).filter_by(
        org_id=organization.id
    ).count()

    return {
        "total": count,
        "roles": roles
    }


def get_role_details(
    uuid: str,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves the details of a role in an organization based on the role's UUID.
    """
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=uuid, org_id=organization.id
    ).first()
    if not role:
        CustomValidations.custom_error(
            type="not_exist",
            loc="role_id",
            msg="User does not exist",
            inp=uuid,
            ctx={"role": "exist"}
        )

    return role


def get_all_permissions(
    sql: Session
):
    """
    Retrieves all the organization permissions from the database.
    """
    return sql.query(model.OrganizationPermission).all()


def create_role(
    data: schema.CreateRole,
    organization: model.Organization,
    authtoken: frontendModel.FrontendToken,
    sql:Session
):
    """
    Creates a new role for an organization in the database, 
    performing validations to ensure the role does not already exist.
    """
    # Check if a role with the same name already exists in the organization
    role = sql.query(model.OrganizationRole).filter_by(
        role=data.role, org_id=organization.id
    ).first()
    if role:
        CustomValidations.custom_error(
            type="already_exist",
            loc="role",
            msg="Role already exists",
            inp=data.role,
            ctx={"role": "unique"}
        )

    # Create a new role object
    new_role = model.OrganizationRole(
        ruid=generate_uuid(data.role),
        role=data.role,
        org_id=organization.id,
        created_by=authtoken.user_id
    )
    sql.add(new_role)
    sql.commit()
    sql.refresh(new_role)

    # Retrieve the permissions associated with the role from the input data
    codenames = data.permissions
    permissions = sql.query(model.OrganizationPermission).filter(
        model.OrganizationPermission.codename.in_(codenames)
    ).all()

    # Create role_permission objects and add them to the database
    role_permissions = [
        model.OrganizationRolePermission(
            role_id=new_role.id,
            permission_id=permission.id
        )
        for permission in permissions
    ]
    sql.add_all(role_permissions)
    sql.commit()

    return new_role


def update_role(
    data: schema.UpdateRole,
    organization: model.Organization,
    sql:Session
):
    """
    Updates the role of an organization.
    """
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=data.ruid, org_id=organization.id
    ).first()

    # If the role does not exist, raise a custom error
    if not role:
        CustomValidations.custom_error(
            type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.ruid,
            ctx={"ruid": "exist"}
        )

    # Check if there is already a role with the same name in the organization.
    exit_role = sql.query(model.OrganizationRole).filter_by(
        role=data.role, org_id=organization.id
    ).first()
    if exit_role:
        CustomValidations.custom_error(
            type="already_exist",
            loc="role",
            msg="Role already exists",
            inp=data.role,
            ctx={"role": "unique"}
        )

    if data.role:
        role.role = data.role

    if data.permissions:
        # Delete existing permissions for the role from the database
        sql.query(model.OrganizationRolePermission).filter_by(
            role_id=role.id
        ).delete()

        # Retrieve the permissions associated with the provided permission codenames
        codenames = data.permissions
        permissions = sql.query(model.OrganizationPermission).filter(
            model.OrganizationPermission.codename.in_(codenames)
        ).all()

        # Assign new permissions to the role
        role_permissions = [
            model.OrganizationRolePermission(
                role_id=role.id,
                permission_id=permission.id
            )
            for permission in permissions
        ]
        sql.add_all(role_permissions)
    sql.commit()
    sql.refresh(role)

    return role


def assign_role(
    data: schema.AssignRole,
    organization: model.Organization,
    sql:Session
):
    """
    Assigns a role to a user in an organization.
    """

    # Get role with the specified role ID which belong to the given organization
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=data.role_id,
        org_id=organization.id
    ).first()
    if not role:
        CustomValidations.custom_error(
            type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.user_id,
            ctx={"ruid": "exist"}
        )

    # Find the user with the specified user ID
    user = sql.query(frontendModel.FrontendUser).filter_by(
        uuid=data.user_id
    ).first()
    if not user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.user_id,
            ctx={"ruid": "exist"}
        )

    # Find the organization user entry for the user and organization
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id, org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.role_id,
            ctx={"ruid": "exist"}
        )

    # Update the role ID of the organization user entry
    org_user.role_id = role.id

    # Commit the changes to the database
    sql.commit()
    # Refresh the organization user entry
    sql.refresh(org_user)

    return org_user



def assign_user_permission(
    data: schema.UpdateUserPermission,
    organization: model.Organization,
    sql: Session
):
    """
    Assigns permissions to a user in an organization.
    """
    # Retrieve the user object based on the provided UUID
    user = sql.query(frontendModel.FrontendUser).filter_by(
        uuid=data.uuid
    ).first()
    if not user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="uuid",
            msg="user does not exist",
            inp=data.uuid,
            ctx={"uuid": "exist"}
        )

    # Get organization user object based on the user ID and organization ID
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id,
        org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.custom_error(
            type="not_exist",
            loc="uuid",
            msg="user does not exist in the organization",
            inp=data.ruid,
            ctx={"uuid": "exist"}
        )

    # Delete any existing role permissions for the organization user
    sql.query(model.OrganizationRolePermission).filter_by(
        user_id=org_user.id
    ).delete()

    # Retrieve the requested permissions from the database
    codenames = data.permissions
    permissions = sql.query(model.OrganizationPermission).filter(
        model.OrganizationPermission.codename.in_(codenames)
    ).all()

    # Assign new permissions for the organization user
    role_permissions = [
        model.OrganizationRolePermission(
            user_id=org_user.id,
            permission_id=permission.id
        )
        for permission in permissions
    ]

    # Add the new role permissions to the database
    sql.add_all(role_permissions)
    sql.commit()
    sql.refresh(org_user)

    return org_user
