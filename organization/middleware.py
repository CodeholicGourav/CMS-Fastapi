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
            CustomValidations.customError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if not user_token.user.active_plan:
            CustomValidations.customError(
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
            CustomValidations.customError(
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

        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="unauthenticated",
            loc="feature",
            msg="feature not available.",
            inp=authtoken,
            ctx={"feature": "not_available"}
        )

    return has_feature


def organization_exist(orguid: str = Header(title="Organization id", description="orguid of the organization you are accessing."), db: Session = Depends(get_db)):
    organization = db.query(model.Organization).filter_by(orguid=orguid).first()

    if not organization:
        CustomValidations.customError(
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
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="unauthenticated",
            loc="subscription",
            msg="No active subscription.",
            inp=str(),
            ctx={"subscription": "not found" if not subscription_user else "expired"}
        )

    return organization

