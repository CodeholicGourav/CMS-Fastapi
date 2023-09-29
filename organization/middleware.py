from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import CustomValidations

from . import model
from frontenduser import model as frontendModel
from backenduser import model as backendModel


def check_feature(feature_code: str):
    """
    Returns a dependency function `has_feature` that checks if a user has a specific feature based on their authentication token.
    
    Args:
        feature_code (str): The code of the feature to check if the user has.
    
    Returns:
        has_feature (function): Dependency function that checks if the user has the specified feature.
    """
    def has_feature(authtoken: Annotated[str, Header(title="Authentication token", description="The token you get from login.")], db: Session = Depends(get_db)):
        """
        Dependency function that checks if the user has the specified feature.
        
        Args:
            authtoken (str): The authentication token of the user.
            db (Session): The database session.
        
        Returns:
            feature (Feature): The feature if the user has it.
        
        Raises:
            HTTPException: If the token is expired or the user does not have the feature.
        """
        user_token = db.query(frontendModel.FrontendToken).filter_by(token=authtoken).first()
        
        if not user_token or not user_token.user:
            CustomValidations.custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if not user_token.user.active_plan:
            CustomValidations.custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                type="unauthenticated",
                loc="subscription",
                msg="No active subscription.",
                inp=authtoken,
                ctx={"subscription": "not found"}
            )

        subscription_user = db.query(backendModel.SubscriptionUser).filter(
            backendModel.SubscriptionUser.subscription_id==user_token.user.active_plan,
            backendModel.SubscriptionUser.user_id==user_token.user.id,
        ).first()

        if not subscription_user or subscription_user.expiry<=datetime.utcnow():
            CustomValidations.custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                type="unauthenticated",
                loc="subscription",
                msg="No active subscription.",
                inp=authtoken,
                ctx={"subscription": "not found" if not subscription_user else "expired"}
            )

        subscription_features = db.query(backendModel.SubscriptionFeature).filter(
            backendModel.SubscriptionFeature.subscription_id==user_token.user.active_plan
        ).all()

        for feature in subscription_features:
            if feature.feature.feature_code == feature_code:
                return feature

        CustomValidations.custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="unauthenticated",
            loc="feature",
            msg="feature not available.",
            inp=authtoken,
            ctx={"feature": "not_available"}
        )

    return has_feature


def organization_exist(orguid: str = Header(title="Organization id", description="orguid of the organization you are accessing."), db: Session = Depends(get_db)):
    """
    Checks if an organization with the given orguid exists in the database and if the organization's admin has an active subscription.

    Args:
        orguid (str): The unique identifier of the organization.
        db (Session): The database session object.

    Returns:
        Organization: The organization object if it exists and the admin has an active subscription.

    Raises:
        custom_error: If the organization does not exist or if there is no active subscription for the admin.
    """
    organization = db.query(model.Organization).filter_by(orguid=orguid).first()

    if not organization:
        CustomValidations.custom_error(
            type="not_exist",
            loc="org_uid",
            msg="Organization does not exist.",
            inp=str(orguid),
            ctx={"org_uid": "exist"}
        )

    admin = organization.admin

    subscription_user = db.query(backendModel.SubscriptionUser).filter(
        backendModel.SubscriptionUser.subscription_id==admin.active_plan,
        backendModel.SubscriptionUser.user_id==admin.id,
    ).first()

    if not subscription_user or subscription_user.expiry<=datetime.utcnow():
        CustomValidations.custom_error(
            status_code=status.HTTP_403_FORBIDDEN,
            type="unauthenticated",
            loc="subscription",
            msg="No active subscription.",
            inp=str(),
            ctx={"subscription": "not found" if not subscription_user else "expired"}
        )

    return organization


def check_permission(codenames: list[str]):

    def has_permissions(
        authtoken: Annotated[str, Header(title="Authentication token", description="The token you get from login.")],
        orguid: str = Header(title="Organization id", description="orguid of the organization you are accessing."),
        db: Session = Depends(get_db)
    ):
        """
        Check if a user has the required permissions to access a specific organization.

        Args:
            authtoken (str): The authentication token obtained from login.
            orguid (str): The organization ID being accessed.
            db (Session): The database session.

        Returns:
            Union[str, List[str]]: The user's permission codenames if the user has the required permissions.

        Raises:
            HTTPException: If the organization does not exist, the token is expired, or the user does not have the required permissions.
        """
        organization = db.query(model.Organization).filter_by(orguid=orguid).first()

        if not organization:
            CustomValidations.custom_error(
                type="not_exist",
                loc="org_uid",
                msg="Organization does not exist.",
                inp=str(orguid),
                ctx={"org_uid": "exist"}
            )

        user_token = db.query(frontendModel.FrontendToken).filter_by(token=authtoken).first()

        if not user_token or not user_token.user:
            CustomValidations.custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if user_token.user.id == organization.admin_id:
            return "__all__"

        org_user = db.query(model.OrganizationUser).filter(
            model.OrganizationUser.user_id == user_token.user_id,
            model.OrganizationUser.org_id == organization.id
        ).first()
        role_permissions = org_user.role.permissions
        user_permission_codenames = [item.permission.codename for item in role_permissions]

        user_permissions = org_user.permissions
        for item in user_permissions:
            user_permission_codenames.append(item.permission.codename)

        print(user_permission_codenames)


        if not all(codename in user_permission_codenames for codename in codenames):
            CustomValidations.custom_error(
                status_code=status.HTTP_403_FORBIDDEN,
                type="unauthenticated",
                loc="permission",
                msg="Permission not granted.",
                inp=", ".join(codenames),
                ctx={"permission": ", ".join(codenames)}
            )

        return user_permission_codenames

    return has_permissions


