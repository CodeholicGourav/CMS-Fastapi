"""
schema.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field


class BasicOrganization(BaseModel):
    """
    A pydantic model
    """
    orguid: str
    org_name: str
    admin_id: int
    gtoken: str
    registration_type: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ShowUser(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    username: str
    email: str


class ShowOrganization(BaseModel):
    """
    A pydantic model
    """
    orguid: str
    org_name: str
    admin: ShowUser
    registration_type: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class BasicOrganizationList(BaseModel):
    """
    A pydantic model
    """
    total: int
    organizations: List[ShowOrganization]


class CreateOrganization(BaseModel):
    """
    A pydantic model
    """
    org_name: str = Field(
        ...,
        ge=5,
        le=50,
        title="organization's name"
    )
    gtoken: dict = Field(
        ...,
        title="google token json"
    )
    registration_type: str = Field(
        ...,
        title="Registration type",
        description="Use one of these value only(e.g., 'open', 'approval_required', 'admin_only')"
    )


class OrgUserRegister(BaseModel):
    """
    A pydantic model
    """
    org_uid: str = Field(..., title="Organization's ouid")


class BasicRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: str


class BasicOrgPermission(BaseModel):
    """
    A pydantic model
    """
    type: int
    permission: str
    codename: str


class BasicOrgRolePermission(BaseModel):
    """
    A pydantic model
    """
    permission: BasicOrgPermission


class ShowOrgUser(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    user: ShowUser
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    role: BasicRole
    permissions: List[BasicOrgRolePermission]


class ShowOrgUserList(BaseModel):
    """
    A pydantic model
    """
    total: int
    users: List[ShowOrgUser]


class ShowOrgRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: str
    created_by: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    permissions: List[BasicOrgRolePermission]


class ShowOrgRoleList(BaseModel):
    """
    A pydantic model
    """
    total: int
    roles: List[ShowOrgRole]


class CreateRole(BaseModel):
    """
    A pydantic model
    """
    role: str = Field(title="Name of the role")
    permissions: List[str] = Field(
        title="permission code"
    )


class UpdateRole(BaseModel):
    """
    A pydantic model
    """
    ruid: str
    role: Annotated[
        str,
        Field(None, title="Name of the role")
    ]
    permissions: Annotated[
        List[str],
        Field(None, title="permission code")
    ]


class UpdateUserPermission(BaseModel):
    """
    A pydantic model
    """
    uuid: str
    permissions: Annotated[List[str], Field(None, title="permission code")]


class AssignRole(BaseModel):
    """
    A pydantic model
    """
    user_id: str
    role_id: str


class BaseProject(BaseModel):
    puid: str
    project_name: str


class ShowProject(BaseModel):
    """
    A pydantic model
    """
    puid: str
    project_name: str
    description: str
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    creator: ShowUser


class ProjectList(BaseModel):
    """
    A pydantic model
    """
    total: int
    projects: List[ShowProject]


class CreateProject(BaseModel):
    """
    A pydantic model
    """
    project_name: Annotated[str, Field(
        ...,
        min_length=3,
        max_length=50,
        title="Project name"
    )]
    description: str


class UpdateProject(BaseModel):
    """
    A pydantic model
    """
    project_id: Annotated[str, Field(
        ...,
        title="Project ID",
        description="puid of project"
    )]
    project_name: Annotated[str, Field(
        None,
        min_length=3,
        max_length=50,
        title="Project name"
    )]
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_deleted: Optional[bool] = None


class ShowTask(BaseModel):
    """
    A pydantic model
    """
    tuid: str
    task_name: str
    description: str
    event_id: Optional[str]
    estimate_hours: Optional[int]
    deadline: Optional[datetime]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    creator: ShowUser
    project: BaseProject


class TaskList(BaseModel):
    """
    A pydantic model
    """
    total: int
    tasks: List[ShowTask]


class CreateTask(BaseModel):
    """
    A pydantic model
    """
    task_name: Annotated[str, Field(
        min_length=3,
        max_length=50,
        title="Task name"
    )]
    description: Annotated[str, Field(
        title="Task description",
        description="Description for task."
    )]
    project_id: Annotated[str, Field(
        title="Project ID",
        description="puid of a project to create task under this project."
    )]
    event_id: Annotated[str, Field(
        None,
        title="Event ID",
        description="Google calendar event ID"
    )]
    estimate_hours: Annotated[int, Field(
        None,
        title="Estimate hours",
        description="Estimate number of hours to complete the task."
    )]
    deadline_date: Annotated[datetime, Field(
        None,
        title="Deadline date",
        description="Estimate date to complete the task."
    )]
    start_date: Annotated[datetime, Field(
        None,
        title="Start-date",
        description="Start date for this task."
    )]
    end_date: Annotated[datetime, Field(
        None,
        title="End-date",
        description="End date for this task"
    )]


class UpdateTask(BaseModel):
    """
    A pydantic model
    """
    task_name: Annotated[str, Field(
        None,
        min_length=3,
        max_length=50,
        title="Task name"
    )]
    description: Annotated[str, Field(
        None,
        title="Task description",
        description="Description for task."
    )]
    task_id: Annotated[str, Field(
        title="Task ID",
        description="tuid of a task to update."
    )]
    event_id: Annotated[str, Field(
        None,
        title="Event ID",
        description="Google calendar event ID"
    )]
    estimate_hours: Annotated[int, Field(
        None,
        title="Estimate hours",
        description="Estimate number of hours to complete the task."
    )]
    deadline_date: Annotated[datetime, Field(
        None,
        title="Deadline date",
        description="Estimate date to complete the task."
    )]
    start_date: Annotated[datetime, Field(
        None,
        title="Start-date",
        description="Start date for this task."
    )]
    end_date: Annotated[datetime, Field(
        None,
        title="End-date",
        description="End date for this task"
    )]
    is_active: Annotated[bool, Field(
        None,
        title="Deactivate",
        description="De-activate the task"
    )]
    is_deleted: Annotated[bool, Field(
        None,
        title="Delete",
        description="Delete the task?"
    )]
