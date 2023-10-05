"""
route.py
Author: Gourav Sahu
Date: 23/09/2023
"""
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from backenduser import model as backendModel
from database import get_db
from frontenduser import model as frontendModel
from frontenduser.middleware import authenticate_token

from . import controller, model, schema
from .middleware import check_feature, check_permission, organization_exist

organizationRoutes = APIRouter()

@organizationRoutes.get('/get-organizations',
    response_model=schema.BasicOrganizationList,
    dependencies=[Depends(authenticate_token)],
    status_code=status.HTTP_200_OK,
    description="Get list of all organizations.",
    name="List organizations"
)
def get_all_organizations(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of organizations from the database, 
    along with the total count of organizations.
    """
    return controller.all_organizations(limit, offset, sql)


@organizationRoutes.post('/create-organization',
    response_model=schema.ShowOrganization,
    status_code=status.HTTP_201_CREATED,
    description="Create a new organization.",
    name="Create organization"
)
def create_organization(
    data: schema.CreateOrganization,
    sql : Session = Depends(get_db),
    auth_token: frontendModel.FrontendToken = Depends(authenticate_token),
    feature: backendModel.SubscriptionFeature = Depends(check_feature("create_organization")),
):
    """
    Retrieves a specified number of organizations from the database, 
    along with the total count of organizations.
    """
    return controller.create_organization(data, sql, auth_token, feature)


@organizationRoutes.post('/register',
    response_model=schema.ShowOrgUser,
    status_code=status.HTTP_201_CREATED,
    description="Apply registration in a organization.",
    name="Register in organization"
)
def register_to_organization(
    data: schema.OrgUserRegister,
    sql : Session = Depends(get_db),
    auth_token: frontendModel.FrontendToken = Depends(authenticate_token),
):
    """
    Registers a user to an organization.
    """
    return controller.register_to_organization(data, sql, auth_token)


@organizationRoutes.get('/users',
    response_model=schema.ShowOrgUserList,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_user"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Fetch all the users in the organization.",
    name="List users"
)
def get_all_users(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Retrieves a specified number of users belonging to a specific organization, 
    along with the total count of users.
    """
    return controller.get_all_users(limit, offset, organization, sql)


@organizationRoutes.get('/users/{user_id}',
    response_model=schema.ShowOrgUser,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_user"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Get all the details of a user.",
    name="User details"
)
def get_user_details(
    user_id : str = Path(description="UUID of the frontend user to retrieve."),
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Retrieves the details of a user in an organization based on the user's UUID.
    """
    return controller.get_user_details(user_id, organization, sql)


@organizationRoutes.get('/roles',
    response_model=schema.ShowOrgRoleList,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_role"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Fetch all the roles in an organization.",
    name="List roles"
)
def get_all_roles(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Retrieves a specified number of roles belonging to a specific organization,
    along with the total count of roles.
    """
    return controller.get_all_roles(limit, offset, organization, sql)


@organizationRoutes.get('/roles/{role_id}',
    response_model=schema.ShowOrgRole,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["read_role"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Get all the details of a role.",
    name="Role details"
)
def get_role_details(
    role_id : str = Path(description="UUID of the role to retrieve."),
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Retrieves the details of a role in an organization based on the role's UUID.
    """
    return controller.get_role_details(role_id, organization, sql)


@organizationRoutes.get('/permissions',
    response_model=list[schema.BasicOrgPermission],
    status_code=status.HTTP_200_OK,
    description="Fetch all the permissions avilable for organization.",
    name="List permissions"
)
def get_all_permissions(
    sql : Session = Depends(get_db),
):
    """
    Retrieves all the organization permissions from the database.
    """
    return controller.get_all_permissions(sql)


@organizationRoutes.post('/create-role',
    response_model=schema.ShowOrgRole,
    dependencies=[Depends(check_permission(["create_role"]))],
    status_code=status.HTTP_201_CREATED,
    description="Create a new role in an organization.",
    name="Create role"
)
def create_role(
    data : schema.CreateRole,
    sql : Session = Depends(get_db),
    auth_token: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Creates a new role for an organization in the database, 
    performing validations to ensure the role does not already exist.
    """
    return controller.create_role(data, organization, auth_token, sql)


@organizationRoutes.post('/update-role',
    response_model=schema.ShowOrgRole,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["update_role"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Update the details of a role in organization.",
    name="Update role"
)
def update_role(
    data : schema.UpdateRole,
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Updates the role of an organization.
    """
    return controller.update_role(data, organization, sql)


@organizationRoutes.post('/assign-role',
    response_model=schema.ShowOrgUser,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["update_role"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Assign a role to an organization user.",
    name="Assign role"
)
def assign_role(
    data : schema.AssignRole,
    sql : Session = Depends(get_db),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
):
    """
    Assigns a role to a user in an organization.
    """
    return controller.assign_role(data, organization, sql)


@organizationRoutes.post('/assign-user-permission',
    response_model=schema.ShowOrgUser,
    dependencies=[
        Depends(authenticate_token),
        Depends(check_permission(["update_role"]))
    ],
    status_code=status.HTTP_200_OK,
    description="Assign individual permissions to an organization user.",
    name="Assign permission - user"
)
def assign_user_permission(
    data : schema.UpdateUserPermission,
    sql : Session = Depends(get_db),
    organization: model.Organization = Depends(organization_exist),
):
    """
    Assigns permissions to a user in an organization.
    """
    return controller.assign_user_permission(data, organization, sql)


@organizationRoutes.post('/create-project',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Creates a new project for an organization in the database, 
    ensure that the project name is unique within the organization.
    """
    return controller.create_project(data, authtoken, organization, sql)


@organizationRoutes.get('/projects',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of projects belonging to a specific organization,
    along with the total count of projects.
    """
    return controller.get_projects(limit, offset, organization, sql)


@organizationRoutes.post('/update-project',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Updates the details of a project in the database.
    """
    return controller.update_project(data, organization, sql)


@organizationRoutes.post('/assign-project-permission',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    This function assigns project permissions to a user in an organization 
    by creating new entries in the `ProjectUserPermission` table.
    """
    return controller.assign_project_permission(data, organization, sql)


@organizationRoutes.post('/create-task',
    response_model=schema.ShowTask,
    status_code=status.HTTP_201_CREATED,
    description="Create a new task.",
    name="Create task"
)
def create_task(
    data : schema.CreateTask,
    authtoken = Depends(authenticate_token),
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Creates a new project for an organization in the database, 
    ensure that the project name is unique within the organization.
    """
    return controller.create_task(data, authtoken, organization, sql)


@organizationRoutes.get('/tasks',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of tasks from the database, 
    either for a specific project within an organization or 
    for all tasks in the organization.
    """
    return controller.get_tasks(limit, offset, organization, project_id, sql)


@organizationRoutes.post('/update-task',
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
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Updates the details of a task in the project.
    """
    return controller.update_task(data, organization, sql)


@organizationRoutes.post('/assign-task',
    response_model=schema.ShowTask,
    status_code=status.HTTP_201_CREATED,
    description="Assign a task to a user.",
    name="Assign task"
)
def assign_task(
    data : schema.AssignTask,
    auth_token: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Assigns a task to multiple users in an organization.
    """
    return controller.assign_task(data, auth_token, organization, sql)


@organizationRoutes.post('/withdraw-task',
    response_model=schema.ShowTask,
    dependencies=[Depends(authenticate_token)],
    status_code=status.HTTP_200_OK,
    description="Withdraw a task from a user.",
    name="Withdreaw task"
)
def withdraw_task(
    data : schema.AssignTask,
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Withdraws a task assigned to a user in an organization.
    """
    return controller.withdraw_task(data, organization, sql)
