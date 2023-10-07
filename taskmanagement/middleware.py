"""
taskmanagement/middleware.py
Author: Gourav Sahu
Date: 05/09/2023
"""
# from datetime import datetime
# from typing import Annotated

# from fastapi import Depends, Header, status
# from sqlalchemy.orm import Session

# from backenduser import model as backendModel
# from database import get_db
# from dependencies import CustomValidations
# from frontenduser import model as frontendModel

# from . import model



# def check_task_permission(codenames: list[str]):
#     """
#     Returns a dependency function `has_permission`
#     that checks if a user has a specific permission
#     based on their authentication token.
#     """
#     def has_permissions(
#         authtoken: Annotated[str, Header(
#             title="Authentication token",
#             description="The token you get from login."
#         )],
#         orguid: Annotated[str, Header(
#             title="Organization id",
#             description="orguid of the organization you are accessing."
#         )],
#         sql: Session = Depends(get_db)
#     ):
#         pass

#     return has_permissions
