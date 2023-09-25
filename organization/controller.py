from typing import Optional
import math
import time
import requests
import json
from datetime import datetime, timedelta

from fastapi import UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import model, schema
from frontenduser import model as frontendModel
from backenduser import model as backendModel
from dependencies import CustomValidations
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dependencies import generate_uuid


def all_organizations(limit: int, offset: int, db: Session):
    """
    Retrieves a specified number of organizations from the database, along with the total count of organizations.

    Args:
        limit (int): The maximum number of organizations to retrieve.
        offset (int): The number of organizations to skip before retrieving.
        db (Session): A SQLAlchemy Session object representing the database connection.

    Returns:
        dict: A dictionary containing the total count of organizations and the retrieved organizations.
            - "total": The total count of organizations in the database.
            - "organizations": A list of organization objects retrieved from the database.
    """
    count = db.query(model.Organization).count()
    organizations = db.query(model.Organization).limit(limit).offset(offset).all()

    return {
        "total": count,
        "organizations": organizations
    }


def create_organization(data: schema.CreateOrganization, db: Session, authToken: frontendModel.FrontendToken, subscription: backendModel.SubscriptionFeature) -> model.Organization:
    """
    Creates a new organization in the database, performing several validations before saving the organization.

    Args:
        data (schema.CreateOrganization): The data required to create a new organization.
        db (Session): A SQLAlchemy Session object representing the database connection.
        authToken (frontendModel.FrontendToken): An authentication token for the frontend user.
        subscription (backendModel.SubscriptionFeature): The subscription plan for the backend user.

    Returns:
        model.Organization: The newly created organization object.
    """

    # Check if the number of organizations created by the user exceeds the limit defined in the subscription plan.
    org_quantity = subscription.quantity
    total_organizations = db.query(model.Organization).filter_by(admin_id=authToken.user_id).count()

    if total_organizations >= org_quantity:
        CustomValidations.customError(
            type="limit_exceed",
            loc="organization",
            msg=f"Can not create more than '{org_quantity}' organizations.",
            inp=data.org_name,
            ctx={"organization": "limited_creation"}
        )

    # Check if the organization name already exists in the database.
    existing_name = db.query(model.Organization).filter(model.Organization.org_name == data.org_name).first()
    if existing_name:
        CustomValidations.customError(
            type="existing",
            loc="org_name",
            msg="Organization name already exists.",
            inp=data.org_name,
            ctx={"org_name": "unique"}
        )

    # Check if the registration type provided is allowed.
    if data.registration_type not in model.Organization.allowed_registration:
        CustomValidations.customError(
            type="invalid",
            loc="registration_type",
            msg=f"Allowed values are {model.Organization.allowed_registration}",
            inp=data.registration_type,
            ctx={"registration_type": "valid"}
        )

    # Check if the Google token provided is valid.
    try:
        # Create an instance of OAuth 2.0 credentials using the dictionary
        creds = Credentials.from_authorized_user_info(data.gtoken)
    except Exception as e:
        CustomValidations.customError(
            type="Invalid",
            loc="gtoken",
            msg="Not a valid Google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )
    if not creds or not creds.valid:
        CustomValidations.customError(
            type="Invalid",
            loc="gtoken",
            msg="Not a valid Google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )

    organization = model.Organization(
        orguid=generate_uuid(data.org_name),
        org_name=data.org_name,
        admin_id=authToken.user_id,
        gtoken=json.dumps(data.gtoken),
        registration_type=data.registration_type
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    # Create default role
    org_role = model.OrganizationRoles(
        ruid = generate_uuid(data.org_name+"Default"),
        role = 'Default',
        created_by = authToken.user_id,
        org_id = organization.id
    )
    db.add(org_role)
    db.commit()

    return organization


def register_to_organization(data: schema.OrgUserRegister, db: Session, authToken: frontendModel.FrontendToken):
    user = authToken.user
    organization = db.query(model.Organization).filter_by(orguid=data.org_uid).first()

    if not organization:
        CustomValidations.customError(
            type="not_exist",
            loc="org_uid",
            msg="Organization does not exist.",
            inp=str(data.org_uid),
            ctx={"org_uid": "exist"}
        )

    if organization.registration_type=="admin_only":
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="not_allowed",
            loc="org_uid",
            msg="Organization does allow new registration.",
            inp=str(data.org_uid),
            ctx={"registration": "admin_only"}
        )

    org_user = model.OrganizationUser(
        uuid = generate_uuid(organization.org_name + user.username),
        user_id = user.id,
        org_id = organization.id,
        role_id = 1 # Assign default role
    )

    if organization.registration_type=="approval_required":
        org_user.is_active = False

    db.add(org_user)
    db.commit()
    db.refresh(org_user)
    return org_user