"""
taskmanagement/route.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from database import get_db
from frontenduser import model as frontendModel
from frontenduser.middleware import authenticate_token
from organization import model as orgModel
from frontenduser import model
from typing import Optional,List
from organization.middleware import check_permission, organization_exist

from . import controller
from . import schema

taskmanagementRoutes = APIRouter()

@taskmanagementRoutes.post('/create-project',
    response_model=schema.ShowProject,
    dependencies=[
        Depends(check_permission(["create_project"]))
    ],
    status_code=status.HTTP_201_CREATED,
    description="Create a new project.",
    name="Create project"
)
def create_project(
    data : schema.CreateProject,
    authtoken = Depends(authenticate_token),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Creates a new project for an organization in the database, 
    ensure that the project name is unique within the organization.
    """
    return controller.create_project(data, authtoken, organization, sql)


@taskmanagementRoutes.get('/projects',
    response_model=schema.ProjectList,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_project"]))
    ],
    status_code=status.HTTP_200_OK,
    description="List all the projects.",
    name="List projects"
)
def get_projects(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of projects belonging to a specific organization,
    along with the total count of projects.
    """
    return controller.get_projects(limit, offset, organization, sql)


@taskmanagementRoutes.get('/project/{project_id}',
    response_model=schema.ShowProject,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_project"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Get details of a project.",
    name="Project details"
)
def project_details(
    project_id: str = Path(title="Project ID"),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves the details of a project based on the provided project ID.
    """
    return controller.project_details(project_id, organization, sql)


@taskmanagementRoutes.post('/update-project',
    response_model=schema.ShowProject,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["update_project"]))
    ],
    status_code=status.HTTP_201_CREATED,
    description="Update an existing project.",
    name="Update project"
)
def update_project(
    data : schema.UpdateProject,
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Updates the details of a project in the database.
    """
    return controller.update_project(data, organization, sql)


@taskmanagementRoutes.post('/assign-project-permission',
    response_model=schema.ShowProject,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["update_project"]))
    ],
    status_code=status.HTTP_201_CREATED,
    description="Assign permission inside a project.",
    name="Assign project permission"
)
def assign_project_permission(
    data : schema.AssignPerojectPermission,
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    This function assigns project permissions to a user in an organization 
    by creating new entries in the `ProjectUserPermission` table.
    """
    return controller.assign_project_permission(data, organization, sql)


@taskmanagementRoutes.post('/create-task',
    response_model=schema.ShowTask,
    status_code=status.HTTP_201_CREATED,
    description="Create a new task.",
    name="Create task"
)
def create_task(
    data : schema.CreateTask,
    authtoken = Depends(authenticate_token),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Creates a new project for an organization in the database, 
    ensure that the project name is unique within the organization.
    """
    return controller.create_task(data, authtoken, organization, sql)


@taskmanagementRoutes.get('/tasks',
    response_model=schema.TaskList,
    dependencies=[
        Depends(authenticate_token),
    ],
    status_code=status.HTTP_200_OK,
    description="List all the tasks.",
    name="List tasks"
)
def get_tasks(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    project_id: str = Query(
        None,
        title="project ID",
        description="puid of a project"
    ),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of tasks from the database, 
    either for a specific project within an organization or 
    for all tasks in the organization.
    """
    return controller.get_tasks(limit, offset, organization, project_id, sql)


@taskmanagementRoutes.post('/update-task',
    response_model=schema.ShowTask,
    dependencies=[
        Depends(authenticate_token)
    ],
    status_code=status.HTTP_201_CREATED,
    description="Update an existing task.",
    name="Update task"
)
def update_task(
    data : schema.UpdateTask,
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Updates the details of a task in the project.
    """
    return controller.update_task(data, organization, sql)


@taskmanagementRoutes.post('/assign-task',
    response_model=schema.ShowTask,
    status_code=status.HTTP_201_CREATED,
    description="Assign a task to a user.",
    name="Assign task"
)
def assign_task(
    data : schema.AssignTask,
    auth_token: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Assigns a task to multiple users in an organization.
    """
    return controller.assign_task(data, auth_token, organization, sql)


@taskmanagementRoutes.post('/withdraw-task',
    response_model=schema.ShowTask,
    dependencies=[Depends(authenticate_token)],
    status_code=status.HTTP_200_OK,
    description="Withdraw a task from a user.",
    name="Withdreaw task"
)
def withdraw_task(
    data : schema.AssignTask,
    organization: orgModel.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Withdraws a task assigned to a user in an organization.
    """
    return controller.withdraw_task(data, organization, sql)


@taskmanagementRoutes.post('/add-custom-column',
    response_model=schema.ResponseCustomColumn,
    status_code=status.HTTP_201_CREATED,
    description="Create a new custom column for a project.",
    name="Create custo column"
)
def project_custom_column(
    data:schema.AddCustomColumn,
    organization: orgModel.Organization = Depends(organization_exist),
    authtoken:frontendModel.FrontendToken = Depends(authenticate_token),
    sql:Session = Depends(get_db)
):
    """
    Create a custom column for a project based on the provided data.
    """
    return controller.project_custom_column(data, organization, authtoken, sql)


@taskmanagementRoutes.delete('/delete-custom-column',
    response_model=schema.ResponseCustomColumn,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(authenticate_token)
    ],
    description="Delete a custom column from a project.",
    name="Delete custom column"
)
def delete_custom_column(
    column_id:str = Query(
        title="Column ID",
        description="cuid of a custom column to delete."
    ),
    organization:orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db)
):
    """
    Delete a custom column for a project based on the provided data.
    """
    return controller.delete_custom_column(column_id, organization, sql)


@taskmanagementRoutes.post('/update-column-expected-values',
    response_model=schema.ResponseCustomColumn,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_token)],
    description="Update expected values for a custom column.",
    name="Update custom column values"
)
def update_column_expected_value(
    data:schema.CreateCustomColumnExpected,
    organization: orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db)
):
    """
    Creates new entries in the `CustomColumnExpected` table 
    by adding expected values for a specific custom column 
    and delte previous values.
    """
    return controller.update_column_expected_value(data, organization, sql)


@taskmanagementRoutes.post('/assign-custom-column-value',
    response_model=schema.ShowTask,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(authenticate_token)],
    description="Assign or update a previous value in a custom column for a task.",
    name="Assign custom column value"
)
def assign_column_value(
    data:schema.AssignCustomColumnValue,
    organization: orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db)
):
    """
    This function assigns a custom column value to a task in a project. 
    It performs validations to ensure that the column,
    value, and task exist and are active and not deleted.
    """
    return controller.assign_column_value(data, organization, sql)


@taskmanagementRoutes.post('/remove-custom-column-value',
    response_model=schema.ShowTask,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(authenticate_token)],
    description="Remove any value assigned in a column for a task.",
    name="Remove custom column value"
)
def remove_column_value(
    data:schema.RemoveCustomColumnValue,
    organization: orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db)
):
    """
    Removes the assigned value of a custom column for a task.
    """
    return controller.remove_column_value(data, organization, sql)

@taskmanagementRoutes.post('/add-comments',response_model=schema.BaseComments,status_code=status.HTTP_201_CREATED)
def add_comments(
    data:schema.add_comments,
    authtoken:model.FrontendToken = Depends(authenticate_token),
    organization:orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db),
):
    return controller.add_comments(data,authtoken,sql)

@taskmanagementRoutes.get('/get-task-comments',response_model=schema.Responsecomment,status_code=status.HTTP_200_OK)
def all_comment(
    limit:Optional[int]=Query(default=10,ge=10,le=100),
    offset:Optional[int]=0,
    authtoken:model.FrontendToken = Depends(authenticate_token),
    organization:orgModel.Organization = Depends(organization_exist),
    sql:Session = Depends(get_db)
):
    return controller.get_all_task_comments(limit,offset,sql)


