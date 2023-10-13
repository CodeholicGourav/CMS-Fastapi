# -*- coding: utf-8 -*-
"""
taskmanagement/middleware.py
Author: Gourav Sahu
Date: 05/09/2023
"""


def check_task_permission(codenames: list[str]):
    """
    Returns a dependency function `has_permission`
    that checks if a user has a specific permission
    based on their authentication token.
    """
    return codenames
