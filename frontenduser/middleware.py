from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import CustomValidations

from .model import FrontendToken, FrontendUser


async def authenticate_token(authtoken: Annotated[str, Header()], db: Session = Depends(get_db)) -> FrontendUser:
    """
    Check token from header and return details of current user

    Args:
        authtoken (str): The authentication token provided in the header of the request.
        db (Session): The database session.

    Returns:
        FrontendUser: The details of the user associated with the valid authentication token.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    user_token = db.query(FrontendToken).filter_by(token=authtoken).first()

    if not user_token or not user_token.user or not user_token.user.is_active or user_token.user.is_deleted:
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if datetime.now() > user_token.expire_at:
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="expired",
            loc="authtoken",
            msg="Token is expired, try login again.",
            inp=authtoken,
            ctx={"authtoken": "active"}
        )

    return user_token


