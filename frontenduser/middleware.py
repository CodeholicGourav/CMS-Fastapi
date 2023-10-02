"""
middleware.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import CustomValidations

from .model import FrontendToken


async def authenticate_token(
    authtoken: Annotated[str, Header(
        title="Authentication token",
        description="The token you get from login."
    )],
    sql: Session = Depends(get_db)
):
    """
    Check token from header and return details of current user

    Args:
        authtoken (str): The authentication token provided in the header of the request.
        sql (Session): The database session.

    Returns:
        FrontendUser: The details of the user associated with the valid authentication token.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    user_token = sql.query(FrontendToken).filter_by(
        token=authtoken
    ).first()

    if (
        not user_token or
        not user_token.user or
        not user_token.user.is_active or
        user_token.user.is_deleted
    ):
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if datetime.now() > user_token.expire_at:
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="expired",
            loc="authtoken",
            msg="Token is expired, try login again.",
            inp=authtoken,
            ctx={"authtoken": "active"}
        )

    return user_token
