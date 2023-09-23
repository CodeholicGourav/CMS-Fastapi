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
from dependencies import CustomValidations
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dependencies import generate_uuid


def all_organizations(limit: int, offset: int, db: Session):
    return db.query(model.Organization).all()


def create_organization(data: schema.CreateOrganization, db: Session, authToken: frontendModel.FrontendToken):
    exiting_name = db.query(model.Organization).filter(model.Organization==data.org_name).first()
    if exiting_name:
        CustomValidations.customError(
            type="existing",
            loc="org_name",
            msg="Organization name already exist.",
            inp=data.org_name,
            ctx={"org_name": "unique"}
        )

    if data.registration_type not in model.Organization.allowed_registration:
        CustomValidations.customError(
            type="invalid",
            loc="registration_type",
            msg="Allowed values are 'open', 'approval_required', 'admin_only'",
            inp=data.registration_type,
            ctx={"registration_type": "valid"}
        )

    try:
        # Create an instance of OAuth 2.0 credentials using the dictionary
        creds = Credentials.from_authorized_user_info(data.gtoken)
    except Exception as e:
        CustomValidations.customError(
            type="Invalid",
            loc="gtoken",
            msg="Not valid google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )

    if not creds or not creds.valid:
        CustomValidations.customError(
            type="Invalid",
            loc="gtoken",
            msg="Not valid google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )
    
    organization = model.Organization(
        orguid = generate_uuid(data.org_name),
        org_name = data.org_name,
        admin_id = authToken.user_id,
        gtoken = json.dumps(data.gtoken),
        registration_type = data.registration_type
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization

