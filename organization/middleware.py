"""
organization/middleware.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from backenduser import model as backendModel
from database import get_db
from dependencies import CustomValidations
from frontenduser import model as frontendModel

from . import model


def check_feature(feature_code: str):
    """
    Returns a dependency function `has_feature` 
    that checks if a user has a specific feature 
    based on their authentication token.
    """
    def has_feature(
        authtoken: Annotated[str, Header(
            title="Authentication token",
            description="The token you get from login."
        )],
        sql: Session = Depends(get_db)
    ):
        """
        Function that checks if the user has the specified feature.
        """
        user_token = sql.query(frontendModel.FrontendToken).filter_by(
            token=authtoken
        ).first()

        if not user_token or not user_token.user:
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if not user_token.user.active_plan:
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="unauthenticated",
                loc="subscription",
                msg="No active subscription.",
                inp=authtoken,
                ctx={"subscription": "not found"}
            )

        subscription_user = sql.query(backendModel.SubscriptionUser).filter(
            backendModel.SubscriptionUser.subscription_id==user_token.user.active_plan,
            backendModel.SubscriptionUser.user_id==user_token.user.id,
        ).first()

        if not subscription_user or subscription_user.expiry<=datetime.utcnow():
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="unauthenticated",
                loc="subscription",
                msg="No active subscription.",
                inp=authtoken,
                ctx={"subscription": "not found" if not subscription_user else "expired"}
            )

        subscription_features = sql.query(backendModel.SubscriptionFeature).filter(
            backendModel.SubscriptionFeature.subscription_id==user_token.user.active_plan
        ).all()

        for feature in subscription_features:
            if feature.feature.feature_code == feature_code:
                return feature

        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="unauthenticated",
            loc="feature",
            msg="feature not available.",
            inp=authtoken,
            ctx={"feature": "not_available"}
        )
        return False

    return has_feature


def organization_exist(
    orguid: str = Header(
        title="Organization id",
        description="orguid of the organization you are accessing."
    ),
    sql: Session = Depends(get_db)
):
    """
    Checks if an organization with the given orguid exists in the database 
    and if the organization's admin has an active subscription.
    """
    organization = sql.query(model.Organization).filter_by(
        orguid=orguid
    ).first()

    if not organization:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="org_uid",
            msg="Organization does not exist.",
            inp=str(orguid),
            ctx={"org_uid": "exist"}
        )

    admin = organization.admin

    subscription_user = sql.query(backendModel.SubscriptionUser).filter(
        backendModel.SubscriptionUser.subscription_id==admin.active_plan,
        backendModel.SubscriptionUser.user_id==admin.id,
    ).first()

    if not subscription_user or subscription_user.expiry<=datetime.utcnow():
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="unauthenticated",
            loc="subscription",
            msg="No active subscription.",
            inp=str(),
            ctx={"subscription": "not found" if not subscription_user else "expired"}
        )

    return organization


def check_permission(codenames: list[str]):
    """
    Returns a dependency function `has_permission` 
    that checks if a user has a specific permission 
    based on their authentication token.
    """
    def has_permissions(
        authtoken: Annotated[str, Header(
            title="Authentication token",
            description="The token you get from login."
        )],
        orguid: Annotated[str, Header(
            title="Organization id",
            description="orguid of the organization you are accessing."
        )],
        sql: Session = Depends(get_db)
    ):
        """
        Check if a user has the required permissions 
        to access a specific organization.
        """
        organization = sql.query(model.Organization).filter_by(orguid=orguid).first()

        if not organization:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="org_uid",
                msg="Organization does not exist.",
                inp=str(orguid),
                ctx={"org_uid": "exist"}
            )

        user_token = sql.query(frontendModel.FrontendToken).filter_by(
            token=authtoken
        ).first()

        if not user_token or not user_token.user:
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if user_token.user.id == organization.admin_id:
            return "__all__"

        org_user = sql.query(model.OrganizationUser).filter(
            model.OrganizationUser.user_id == user_token.user_id,
            model.OrganizationUser.org_id == organization.id
        ).first()
        role_permissions = org_user.role.permissions
        user_permission_codenames = [
            item.permission.codename for item in role_permissions
        ]

        user_permissions = org_user.permissions
        for item in user_permissions:
            user_permission_codenames.append(item.permission.codename)

        if not all(codename in user_permission_codenames for codename in codenames):
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_403_FORBIDDEN,
                error_type="unauthenticated",
                loc="permission",
                msg="Permission not granted.",
                inp=", ".join(codenames),
                ctx={"permission": ", ".join(codenames)}
            )

        return user_permission_codenames

    return has_permissions
