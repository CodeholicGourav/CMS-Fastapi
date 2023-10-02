"""
middleware.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from backenduser.model import BackendToken
from database import get_db
from dependencies import CustomValidations


async def authenticate_token(
        authtoken: Annotated[str, Header(
            title="Authentication token",
            description="The token you get from login."
        )],
        sql: Session = Depends(get_db)
):
    """
    Check the validity of the provided token and return the associated user.
    """
    user_token = sql.query(BackendToken).filter_by(token = authtoken).first()

    if not user_token:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if not user_token.user or not user_token.user.is_active or user_token.user.is_deleted:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if datetime.utcnow() > user_token.expire_at:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="expired",
            loc="authtoken",
            msg="Token is expired, try login again.",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    return user_token


def check_permission(codenames: list[str]):
    """
    Returns a function to check if a user has the required permissions.
    """
    def has_permissions(
            authtoken: Annotated[str, Header(
                title="Authentication token",
                description="The token you get from login."
            )],
            sql: Session = Depends(get_db)):
        """
        Checks if a user has the required permissions.
        Comparing the user's permission codenames with the provided list of codenames.
        """
        user_token = sql.query(BackendToken).filter_by(token=authtoken).first()

        if not user_token or not user_token.user:
            CustomValidations.raize_custom_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_type="expired",
                loc="authtoken",
                msg="Token is expired, try login again.",
                inp=authtoken,
                ctx={"authtoken": "valid"}
            )

        if user_token.user.role.id == 0:
            return "__all__"

        user_permissions = user_token.user.role.permissions
        user_permission_codenames = [item.permission.codename for item in user_permissions]

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
