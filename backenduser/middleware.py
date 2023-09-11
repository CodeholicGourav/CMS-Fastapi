from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backenduser.model import BackendToken, BackendUser
from database import get_db
from dependencies import CustomValidations


async def authenticate_token(authtoken: Annotated[str, Header()], db: Session = Depends(get_db)) -> BackendUser:
    """
    Check the validity of the provided token and return the associated user.

    Args:
        authtoken (str): The token provided in the header of the request.
        db (Session): The database session used to query the token and associated user.

    Returns:
        User: The user object associated with the provided token.

    Raises:
        HTTPException: If the token is invalid, expired, or associated with an inactive or deleted user.
    """
    user_token = db.query(BackendToken).filter_by(token = authtoken).first()

    if not user_token:
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if not user_token.user or not user_token.user.is_active or user_token.user.is_deleted:
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="Invalid",
            loc="authtoken",
            msg="Invalid auth token",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    if datetime.utcnow() > user_token.expire_at:
        CustomValidations.customError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            type="expired",
            loc="authtoken",
            msg="Token is expired, try login again.",
            inp=authtoken,
            ctx={"authtoken": "valid"}
        )

    return user_token


def check_permission(codenames: list[str]):
    """
    Returns a function to check if a user has the required permissions.
    
    Args:
        codenames (list[str]): A list of permission codenames that the user must have to pass the permission check.
    
    Returns:
        function: A function that can be used as a dependency in FastAPI routes to check if a user has the required permissions.
        
    Raises:
        HTTPException: If the user is not found or does not have the required permissions.
    """
    def has_permissions(authtoken: str = Header(), db: Session = Depends(get_db)) -> bool:
        """
        Checks if a user has the required permissions.
        
        Args:
            authtoken (str): The authentication token of the user.
            db (Session): The database session.
        
        Returns:
            bool: True if the user has the required permissions, False otherwise.
        
        Raises:
            HTTPException: If the user is not found or does not have the required permissions.
        """
        user_token = db.query(BackendToken).filter_by(token=authtoken).first()
        
        if not user_token or not user_token.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth token")
        
        if user_token.user.role.id == 0:
            return True

        user_permissions = user_token.user.role.permissions
        if not user_permissions:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permission not granted.")
        
        return all(permission in user_permissions for permission in codenames)
    
    return has_permissions
    
