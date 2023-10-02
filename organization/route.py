"""
model.py
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

@organizationRoutes.get(
    path='/get-organizations',
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


@organizationRoutes.post(
    path='/create-organization',
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


@organizationRoutes.post(
    path='/register',
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


@organizationRoutes.get(
    path='/users',
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


@organizationRoutes.get(
    path='/users/{user_id}',
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


@organizationRoutes.get(
    path='/roles',
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


@organizationRoutes.get(
    path='/roles/{role_id}',
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


@organizationRoutes.get(
    path='/permissions',
    response_model=schema.BasicOrgPermission,
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


@organizationRoutes.post(
    path='/create-role',
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


@organizationRoutes.post(
    path='/update-role',
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


@organizationRoutes.post(
    path='/assign-role',
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


@organizationRoutes.post(
    path='/assign-user-permission',
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


@organizationRoutes.post(
    path='/create-project',
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


@organizationRoutes.get(
    path='/projects',
    response_model=schema.ProjectList,
    dependencies=[
        Depends(check_permission(["read_project"]))
    ],
    status_code=status.HTTP_200_OK,
    description="List all the projects.",
    name="List projects"
)
def get_projects(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"),
    offset : int = Query(0, ge=0, description="Number of results to skip."),
    authtoken = Depends(authenticate_token),
    organization: model.Organization = Depends(organization_exist),
    sql : Session = Depends(get_db),
):
    """
    Retrieves a specified number of projects belonging to a specific organization,
    along with the total count of projects.
    """
    return controller.get_projects(limit, offset, organization, sql)


@organizationRoutes.post(
    path='/update-project',
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
