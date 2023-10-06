"""
taskmanagement/route.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from frontenduser import model as frontendModel
from frontenduser.middleware import authenticate_token
from organization import model as orgModel
from organization.middleware import check_permission, organization_exist

from . import controller, schema

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
