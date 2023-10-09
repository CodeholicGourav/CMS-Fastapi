"""
taskmanagement/schema.py
Author: Gourav Sahu
Date: 05/09/2023
"""
from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

from dependencies import ShowUser

class BaseProject(BaseModel):
    """
    A pydantic model
    """
    puid: str
    project_name: str


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


class TaskAssigned(BaseModel):
    """
    A pydantic model
    """
    user: ShowUser
    assigned_by: ShowUser
    created_at: datetime
    updated_at: datetime


class AddCustomColumn(BaseModel):
    """
    A pydantic model
    """
    project_id:str
    column_name:str
    type:Optional[str]


class ShowCustomColumn(BaseModel):
    """
    A pydantic model
    """
    cuid: str
    column_name: str
    type: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class ExpectedValues(BaseModel):
    """
    A pydantic model
    """
    vuid: str
    value: str


class ShowAssignedValue(BaseModel):
    """
    A pydantic model
    """
    vuid: str
    value: str


class ValueAssigned(BaseModel):
    """
    A pydantic model
    """
    column: ShowCustomColumn
    value: ShowAssignedValue
    created_at: datetime
    updated_at: datetime


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
    assigned_to: Optional[list[TaskAssigned]] = []
    column_values: Optional[list[ValueAssigned]] = []
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


class AssignPerojectPermission(BaseModel):
    """
    A pydantic model
    """
    project_id: str
    user_id: str
    permissions: List[str]


class AssignTask(BaseModel):
    """
    A pydantic model
    """
    task_id: str = Field(
        title="Task ID",
        description="tuid of the task to assign"
    )
    user_id: str = Field(
        title="User ID",
        description="UUID of frontend user."
    )


class BasicUser(BaseModel):
    """
    A pydantic model
    """
    uuid:str
    username:str
    email:str


class ResponseCustomColumn(BaseModel):
    """
    A pydantic model
    """
    column_name:str
    cuid: str
    creator:BasicUser
    created_at:datetime
    updated_at:datetime
    is_deleted:bool
    values: List[ExpectedValues]


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
    columns: List[ResponseCustomColumn]


class ProjectList(BaseModel):
    """
    A pydantic model
    """
    total: int
    projects: List[ShowProject]


class CreateCustomColumnExpected(BaseModel):
    """
    A pydantic model
    """
    column_id: str
    values: List[str]


class AssignCustomColumnValue(BaseModel):
    """
    A pydantic model
    """
    task_id: str
    column_id: str
    value_id: str
