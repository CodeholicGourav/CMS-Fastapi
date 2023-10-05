"""
controller.py
Author: Gourav Sahu
Date: 23/09/2023
"""
import json

from fastapi import status
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session

from backenduser import model as backendModel
from dependencies import CustomValidations, generate_uuid
from frontenduser import model as frontendModel

from . import model, schema


def all_organizations(
    limit: int,
    offset: int,
    sql: Session
):
    """
    Retrieves a specified number of organizations from the database, 
    along with the total count of organizations.
    """
    count = sql.query(model.Organization).count()
    organizations = sql.query(
        model.Organization
    ).limit(limit).offset(offset).all()

    return {
        "total": count,
        "organizations": organizations
    }


def create_organization(
    data: schema.CreateOrganization,
    sql: Session,
    auth_token: frontendModel.FrontendToken,
    subscription: backendModel.SubscriptionFeature
):
    """
    Creates a new organization in the database, 
    performing several validations before saving the organization.
    """

    # Number of organizations can subscription allows.
    org_quantity = subscription.quantity

    total_organizations = sql.query(model.Organization.id).filter_by(
        admin_id=auth_token.id
    ).count()

    if total_organizations >= org_quantity:
        CustomValidations.raize_custom_error(
            error_type="limit_exceed",
            loc="organization",
            msg=f"Can not create more than '{org_quantity}' organizations.",
            inp=data.org_name,
            ctx={"organization": "limited_creation"}
        )

    # Check if the organization name already exists in the database.
    existing_name = sql.query(model.Organization).filter_by(
        org_name=data.org_name
    ).first()
    if existing_name:
        CustomValidations.raize_custom_error(
            error_type="existing",
            loc="org_name",
            msg="Organization name already exists.",
            inp=data.org_name,
            ctx={"org_name": "unique"}
        )

    # Check if the registration type provided is allowed.
    if data.registration_type not in model.Organization.allowed_registration:
        CustomValidations.raize_custom_error(
            error_type="invalid",
            loc="registration_type",
            msg=f"Allowed values are {model.Organization.allowed_registration}",
            inp=data.registration_type,
            ctx={"registration_type": "valid"}
        )

    # Create an instance of OAuth 2.0 credentials using the dictionary
    creds = Credentials.from_authorized_user_info(data.gtoken)

    # Check if the Google token provided is valid.
    if not creds or not creds.valid:
        CustomValidations.raize_custom_error(
            error_type="Invalid",
            loc="gtoken",
            msg="Not a valid Google token.",
            inp=str(data.gtoken),
            ctx={"gtoken": "valid"}
        )

    organization = model.Organization(
        orguid=generate_uuid(data.org_name),
        org_name=data.org_name,
        admin_id=auth_token.user_id,
        gtoken=json.dumps(data.gtoken),
        registration_type=data.registration_type
    )

    sql.add(organization)
    sql.commit()
    sql.refresh(organization)

    # Create default role
    org_role = model.OrganizationRole(
        ruid = generate_uuid(data.org_name+"Default"),
        role = 'Default',
        created_by = auth_token.user_id,
        org_id = organization.id
    )
    sql.add(org_role)
    sql.commit()

    return organization


def register_to_organization(
    data: schema.OrgUserRegister,
    sql: Session,
    auth_token: frontendModel.FrontendToken
):
    """
    Registers a user to an organization.
    """
    user = auth_token.user
    organization = sql.query(model.Organization).filter_by(
        orguid=data.org_uid
    ).first()

    if not organization:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="org_uid",
            msg="Organization does not exist.",
            inp=str(data.org_uid),
            ctx={"org_uid": "exist"}
        )

    if organization.registration_type == "admin_only":
        CustomValidations.raize_custom_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="not_allowed",
            loc="org_uid",
            msg="Organization does allow new registration.",
            inp=str(data.org_uid),
            ctx={"registration": "admin_only"}
        )

    admin = organization.admin
    feature = sql.query(backendModel.Feature).filter_by(
        feature_code="add_member"
    ).first()

    subscription_feature = sql.query(
        backendModel.SubscriptionFeature
    ).filter_by(
        subscription_id=admin.active_plan,
        feature_id=feature.id
    ).first()

    user_quantity = subscription_feature.quantity

    total_users = sql.query(
        model.OrganizationUser.id
    ).filter_by(
        org_id=organization.id,
        is_deleted=False,
        is_active=True
    ).count()

    if total_users >= user_quantity:
        CustomValidations.raize_custom_error(
            error_type="limit_exceed",
            loc="organization",
            msg=f"Can not add more than '{user_quantity}' users.",
            inp=data.org_uid,
            ctx={"organization": "limited_creation"}
        )

    org_user = sql.query(
        model.OrganizationUser
    ).filter_by(
        org_id=organization.id,
        user_id=user.id
    ).first()

    if org_user:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="organization",
            msg="User already registered.",
            inp=data.org_uid,
            ctx={"organization": "new_registration"}
        )

    org_user = model.OrganizationUser(
        user_id=user.id,
        org_id=organization.id,
        role_id=1  # Assign default role
    )

    if organization.registration_type == "approval_required":
        org_user.is_active = False

    sql.add(org_user)
    sql.commit()
    sql.refresh(org_user)
    return org_user


def get_all_users(
    limit: int,
    offset: int,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves a specified number of users belonging to a specific organization, 
    along with the total count of users.
    """
    users = sql.query(model.OrganizationUser).filter_by(
        org_id=organization.id
    ).limit(limit).offset(offset).all()
    count = sql.query(model.OrganizationUser.id).filter_by(
        org_id=organization.id
    ).count()
    print(count)
    print(users)

    return {
        "total": count,
        "users": users
    }


def get_user_details(
    uuid: str,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves the details of a user in an organization based on the user's UUID.
    """
    user = sql.query(frontendModel.FrontendUser).filter_by(uuid=uuid).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=uuid,
            ctx={"user": "exist"}
        )
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id, org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist in organization",
            inp=uuid,
            ctx={"user": "exist"}
        )

    return org_user


def get_all_roles(
    limit: int,
    offset: int,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves a specified number of roles belonging to a specific organization,
    along with the total count of roles.
    """
    roles = sql.query(model.OrganizationRole).filter_by(
        org_id=organization.id
    ).limit(limit).offset(offset).all()
    count = sql.query(model.OrganizationRole).filter_by(
        org_id=organization.id
    ).count()

    return {
        "total": count,
        "roles": roles
    }


def get_role_details(
    role_id: str,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves the details of a role in an organization based on the role's UUID.
    """
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=role_id, org_id=organization.id
    ).first()
    if not role:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role_id",
            msg="User does not exist",
            inp=role_id,
            ctx={"role": "exist"}
        )

    return role


def get_all_permissions(
    sql: Session
):
    """
    Retrieves all the organization permissions from the database.
    """
    return sql.query(model.OrganizationPermission).all()


def create_role(
    data: schema.CreateRole,
    organization: model.Organization,
    authtoken: frontendModel.FrontendToken,
    sql:Session
):
    """
    Creates a new role for an organization in the database, 
    performing validations to ensure the role does not already exist.
    """
    # Check if a role with the same name already exists in the organization
    role = sql.query(model.OrganizationRole).filter_by(
        role=data.role, org_id=organization.id
    ).first()
    if role:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="role",
            msg="Role already exists",
            inp=data.role,
            ctx={"role": "unique"}
        )

    # Create a new role object
    new_role = model.OrganizationRole(
        ruid=generate_uuid(data.role),
        role=data.role,
        org_id=organization.id,
        created_by=authtoken.user_id
    )
    sql.add(new_role)
    sql.commit()
    sql.refresh(new_role)

    # Retrieve the permissions associated with the role from the input data
    codenames = data.permissions
    permissions = sql.query(model.OrganizationPermission).filter(
        model.OrganizationPermission.codename.in_(codenames)
    ).all()

    # Create role_permission objects and add them to the database
    role_permissions = [
        model.OrganizationRolePermission(
            role_id=new_role.id,
            permission_id=permission.id
        )
        for permission in permissions
    ]
    sql.add_all(role_permissions)
    sql.commit()

    return new_role


def update_role(
    data: schema.UpdateRole,
    organization: model.Organization,
    sql:Session
):
    """
    Updates the role of an organization.
    """
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=data.ruid, org_id=organization.id
    ).first()

    # If the role does not exist, raise a custom error
    if not role:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.ruid,
            ctx={"ruid": "exist"}
        )

    # Check if there is already a role with the same name in the organization.
    exit_role = sql.query(model.OrganizationRole).filter_by(
        role=data.role, org_id=organization.id
    ).first()
    if exit_role:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="role",
            msg="Role already exists",
            inp=data.role,
            ctx={"role": "unique"}
        )

    if data.role:
        role.role = data.role

    if data.permissions:
        # Delete existing permissions for the role from the database
        sql.query(model.OrganizationRolePermission).filter_by(
            role_id=role.id
        ).delete()

        # Retrieve the permissions associated with the provided permission codenames
        codenames = data.permissions
        permissions = sql.query(model.OrganizationPermission).filter(
            model.OrganizationPermission.codename.in_(codenames)
        ).all()

        # Assign new permissions to the role
        role_permissions = [
            model.OrganizationRolePermission(
                role_id=role.id,
                permission_id=permission.id
            )
            for permission in permissions
        ]
        sql.add_all(role_permissions)
    sql.commit()
    sql.refresh(role)

    return role


def assign_role(
    data: schema.AssignRole,
    organization: model.Organization,
    sql:Session
):
    """
    Assigns a role to a user in an organization.
    """

    # Get role with the specified role ID which belong to the given organization
    role = sql.query(model.OrganizationRole).filter_by(
        ruid=data.role_id,
        org_id=organization.id
    ).first()
    if not role:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.user_id,
            ctx={"ruid": "exist"}
        )

    # Find the user with the specified user ID
    user = sql.query(frontendModel.FrontendUser).filter_by(
        uuid=data.user_id
    ).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.user_id,
            ctx={"ruid": "exist"}
        )

    # Find the organization user entry for the user and organization
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id, org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="role",
            msg="Role does not exist",
            inp=data.role_id,
            ctx={"ruid": "exist"}
        )

    # Update the role ID of the organization user entry
    org_user.role_id = role.id

    # Commit the changes to the database
    sql.commit()
    # Refresh the organization user entry
    sql.refresh(org_user)

    return org_user



def assign_user_permission(
    data: schema.UpdateUserPermission,
    organization: model.Organization,
    sql: Session
):
    """
    Assigns permissions to a user in an organization.
    """
    # Retrieve the user object based on the provided UUID
    user = sql.query(frontendModel.FrontendUser).filter_by(
        uuid=data.uuid
    ).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="uuid",
            msg="user does not exist",
            inp=data.uuid,
            ctx={"uuid": "exist"}
        )

    # Get organization user object based on the user ID and organization ID
    org_user = sql.query(model.OrganizationUser).filter_by(
        user_id=user.id,
        org_id=organization.id
    ).first()
    if not org_user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="uuid",
            msg="user does not exist in the organization",
            inp=data.ruid,
            ctx={"uuid": "exist"}
        )

    # Delete any existing role permissions for the organization user
    sql.query(model.OrganizationRolePermission).filter_by(
        user_id=org_user.id
    ).delete()

    # Retrieve the requested permissions from the database
    codenames = data.permissions
    permissions = sql.query(model.OrganizationPermission).filter(
        model.OrganizationPermission.codename.in_(codenames)
    ).all()

    # Assign new permissions for the organization user
    role_permissions = [
        model.OrganizationRolePermission(
            user_id=org_user.id,
            permission_id=permission.id
        )
        for permission in permissions
    ]

    # Add the new role permissions to the database
    sql.add_all(role_permissions)
    sql.commit()
    sql.refresh(org_user)

    return org_user


def get_projects(
    limit: int,
    offset: int,
    organization: model.Organization,
    sql: Session
):
    """
    Retrieves a specified number of projects belonging to a specific organization,
    along with the total count of projects.
    """
    count = sql.query(model.Project).filter_by(
        org_id=organization.id
    ).count()
    projects = sql.query(model.Project).filter_by(
        org_id=organization.id
    ).limit(limit).offset(offset).all()

    return {
        "total": count,
        "projects": projects
    }


def create_project(
    data: schema.CreateProject,
    authtoken: frontendModel.FrontendToken,
    organization: model.Organization,
    sql: Session
):
    """
    Creates a new project for an organization in the database, 
    ensure that the project name is unique within the organization.
    """
    # Check if a project with the same name already exists in the organization.
    exist_name = sql.query(model.Project).filter_by(
        project_name=data.project_name,
        org_id=organization.id
    ).first()

    if exist_name:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="project_name",
            msg="Project name already exists",
            inp=data.project_name,
            ctx={"project_name": "unique"}
        )

    # Create a new project object
    project = model.Project(
        puid=generate_uuid(data.project_name),
        project_name=data.project_name,
        description=data.description,
        created_by=authtoken.user_id,
        org_id=organization.id
    )

    # Add the new project to the session.
    sql.add(project)
    # Commit the session to save the changes to the database.
    sql.commit()
    # Refresh the project object to get the updated values from the database.
    sql.refresh(project)

    return project


def update_project(data: schema.UpdateProject, organization: model.Organization, sql: Session):
    """
    Updates the details of a project in the database.
    """
    project = sql.query(model.Project).filter_by(
        puid=data.project_id,
        org_id=organization.id
    ).first()
    if not project:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="project_id",
            msg="Project does not exist",
            inp=data.project_id,
            ctx={"project_id": "exist"}
        )

    if data.project_name:
        exist_name = sql.query(model.Project).filter_by(
            project_name=data.project_name,
            org_id=organization.id
        ).first()

        if exist_name:
            CustomValidations.raize_custom_error(
                error_type="already_exist",
                loc="project_name",
                msg="Project name already exists",
                inp=data.project_name,
                ctx={"project_name": "unique"}
            )
        project.project_name = data.project_name

    if data.description:
        project.description = data.description

    if data.is_active is not None:
        project.is_active = data.is_active

    if data.is_deleted is not None:
        project.is_deleted = data.is_deleted

    sql.commit()
    sql.refresh(project)
    return project


def create_task(
    data: schema.CreateTask,
    authtoken: frontendModel.FrontendToken,
    organization: model.Organization,
    sql: Session
):
    """
    Creates a new task for an organization in the database,
    performing validations to ensure 
    project exist in organization and 
    the task name should be unique in project.
    """
    # Check if the project specified by the project ID exists in the organization
    exist_project = sql.query(model.Project).filter_by(
        puid=data.project_id, org_id=organization.id
    ).first()
    if not exist_project:
        CustomValidations.raize_custom_error(
            error_type="not_xist",
            loc="project_id",
            msg="project does not exist",
            inp=data.project_id,
            ctx={"project_id": "exist"}
        )

    # Check if a task with the same name already exists in the project
    exist_name = sql.query(model.Task).filter_by(
        task_name=data.task_name,
        project_id=exist_project.id
    ).first()
    if exist_name:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="task_name",
            msg="Task name already exists",
            inp=data.task_name,
            ctx={"task_name": "unique"}
        )

    # Create a new task object
    task = model.Task(
        tuid=generate_uuid(data.task_name),
        task_name=data.task_name,
        description=data.description,
        created_by=authtoken.user_id,
        project_id = exist_project.id,
    )

    if data.event_id is not None:
        task.event_id = data.event_id
    if data.estimate_hours is not None:
        task.estimate_hours = data.estimate_hours
    if data.deadline_date is not None:
        task.deadline = data.deadline_date
    if data.start_date is not None:
        task.start_date = data.start_date
    if data.end_date is not None:
        task.end_date = data.end_date

    # Add the new task to the session
    sql.add(task)
    # Commit the session to save the changes to the database
    sql.commit()
    # Refresh the task object to get the updated values from the database
    sql.refresh(task)

    return task


def get_tasks(
    limit: int,
    offset: int,
    organization: model.Organization,
    project_id: str | None,
    sql: Session
):
    """
    Retrieves a specified number of tasks from the database, 
    either for a specific project within an organization or 
    for all tasks in the organization.
    """
    if project_id is not None:
        # Check if the project specified by the project ID exists in the organization
        exist_project = sql.query(model.Project).filter_by(
            puid=project_id,
            org_id=organization.id
        ).first()

        if not exist_project:
            CustomValidations.raize_custom_error(
                error_type="not_xist",
                loc="project_id",
                msg="project does not exist",
                inp=project_id,
                ctx={"project_id": "exist"}
            )

        count = sql.query(model.Task).filter_by(
            project_id=exist_project.id
        ).count()

        tasks = sql.query(model.Task).filter_by(
            project_id=exist_project.id
        ).order_by(model.Task.id).limit(limit).offset(offset).all()

    else:
        count = sql.query(model.Task).count()
        tasks = sql.query(model.Task).limit(limit).order_by(model.Task.id).offset(offset).all()

    return {
        "total": count,
        "tasks": tasks
    }


def update_task(
    data: schema.UpdateTask,
    organization: model.Organization,
    sql: Session
):
    """
    Updates the details of a task in the database based on the provided input data.
    """
    task = sql.query(
        model.Task
    ).join(
        model.Project,
        model.Task.project_id == model.Project.id
    ).filter(
        model.Task.tuid==data.task_id,
        model.Project.org_id==organization.id
    ).first()

    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id,
            ctx={"task_id": "exist"}
        )

    if data.task_name is not None:
        task.task_name = data.task_name

    if data.description is not None:
        task.description = data.description

    if data.event_id is not None:
        task.event_id = data.event_id

    if data.estimate_hours is not None:
        task.estimate_hours = data.estimate_hours

    if data.deadline_date is not None:
        task.deadline = data.deadline_date

    if data.start_date is not None:
        task.start_date = data.start_date

    if data.end_date is not None:
        task.end_date = data.end_date

    if data.is_active is not None:
        task.is_active = data.is_active

    if data.is_deleted is not None:
        task.is_deleted = data.is_deleted

    sql.commit()
    sql.refresh(task)

    return task


def assign_project_permission(
    data: schema.AssignPerojectPermission,
    organization: model.Organization,
    sql: Session
):
    """
    This function assigns project permissions to a user in an organization 
    by creating new entries in the `ProjectUserPermission` table.
    """
    # Retrieve the project object from the database
    project = sql.query(model.Project).filter_by(
        puid=data.project_id, org_id=organization.id
    ).first()
    if not project:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="project_id",
            msg="Project does not exist",
            inp=data.project_id,
            ctx={"project_id": "exist"}
        )

    # Check user exist in this organization
    user = sql.query(model.OrganizationUser).join(
        frontendModel.FrontendUser,
        model.OrganizationUser.user_id==frontendModel.FrontendUser.id
    ).filter(
        model.OrganizationUser.org_id==organization.id,
        frontendModel.FrontendUser.uuid==data.user_id
    ).first()
    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    # Retrieve the requested permissions from the database
    permissions = sql.query(model.ProjectPermission).filter(
        model.ProjectPermission.codename.in_(data.permissions)
    ).all()

    # Delete any existing project permissions for the user
    sql.query(model.ProjectUserPermission).filter_by(
        user_id=user.id,
        project_id=project.id
    ).delete()

    # Assign new project permissions for the user
    proj_permissions = [
        model.ProjectUserPermission(
            user_id=user.id,
            project_id=project.id,
            permission_id=permission.id
        ) for permission in permissions
    ]

    # Add the new project permissions to the database
    sql.add_all(proj_permissions)
    sql.commit()
    return project


def assign_task(
    data: schema.AssignTask,
    auth_token: frontendModel.FrontendToken,
    organization: model.Organization,
    sql: Session
):
    """
    Assigns a task to multiple users in an organization.
    """
    task = sql.query(model.Task).filter_by(
        tuid=data.task_id
    ).first()
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id,
            ctx={"task_id": "exist"}
        )

    # Check user exist in this organization
    user = sql.query(model.OrganizationUser).join(
        frontendModel.FrontendUser,
        model.OrganizationUser.user_id==frontendModel.FrontendUser.id
    ).filter(
        model.OrganizationUser.org_id==organization.id,
        frontendModel.FrontendUser.uuid==data.user_id
    ).first()

    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    user_task = sql.query(model.UserTask).filter_by(
        task_id=task.id,
        user_id=user.id,
    ).first()
    if not user_task:
        user_task = model.UserTask(
            task_id=task.id,
            user_id=user.id,
            created_by=auth_token.user_id
        )
    sql.add(user_task)
    sql.commit()

    return task


def withdraw_task(
    data: schema.AssignTask,
    organization: model.Organization,
    sql: Session
):
    """
    Withdraws a task assigned to a user in an organization.
    """
    task = sql.query(model.Task).filter_by(
        tuid=data.task_id
    ).first()
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id,
            ctx={"task_id": "exist"}
        )

    user = sql.query(model.OrganizationUser).join(
        frontendModel.FrontendUser,
        model.OrganizationUser.user_id == frontendModel.FrontendUser.id
    ).filter(
        model.OrganizationUser.org_id == organization.id,
        frontendModel.FrontendUser.uuid == data.user_id
    ).first()

    if not user:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="user_id",
            msg="User does not exist",
            inp=data.user_id,
            ctx={"user_id": "exist"}
        )

    sql.query(model.UserTask).filter_by(
        task_id=task.id,
        user_id=user.id,
    ).delete()
    sql.commit()
    sql.refresh(task)

    return task
