"""
taskmanagement/controller.py
Author: Gourav Sahu
Date: 05/09/2023
"""
import json
from fastapi import UploadFile
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from dependencies import (
    ALLOWED_FILE_EXTENSIONS,
    CustomValidations, SETTINGS,
    allowed_file, generate_uuid, create_folder_if_not_exists, upload_to_drive
)
from frontenduser import model as frontendModel
from organization import model as orgModel
from . import (model, schema)


def get_projects(
    limit: int,
    offset: int,
    organization: orgModel.Organization,
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
    organization: orgModel.Organization,
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

    sql.add(project)
    sql.commit()
    sql.refresh(project)

    return project


def update_project(
    data: schema.UpdateProject,
    organization: orgModel.Organization,
    sql: Session
):
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
    organization: orgModel.Organization,
    sql: Session
):
    """
    Creates a new task for an organization in the database
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

    if data.group_id is not None:
        # If the task group does not exist, raise a custom error
        group_task = sql.query(model.TaskGroup).join(
            model.Project,
            model.TaskGroup.project_id == model.Project.id
        ).filter(
            # pylint: disable=singleton-comparison
            model.TaskGroup.guid == data.group_id,
            model.TaskGroup.is_deleted == False,
            model.Project.org_id == organization.id
        ).first()
        if not group_task:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="group_id",
                msg="Group does not exist",
                inp=data.group_id
            )

        task.group_id = group_task.id

    if data.parent_id is not None:
        parent_task = sql.query(
            model.Task
        ).join(
            model.Project,
            model.Task.project_id == model.Project.id
        ).filter(
            model.Task.tuid == data.parent_id,
            model.Project.org_id == organization.id
        ).first()
        if not task:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="parent_id",
                msg="Task does not exist",
                inp=data.parent_id,
                ctx={"parent_id": "exist"}
            )
        task.parent_id = parent_task.id

    sql.add(task)
    sql.commit()
    sql.refresh(task)
    return task


async def upload_task_media(
    task_id: str,
    files: list[UploadFile],
    organization: orgModel.Organization,
    sql:Session
):
    """
    Uploads media files to Google Drive for a specific task in an organization.
    """
    task = sql.query(model.Task).join(
            model.Project,
            model.Task.project_id == model.Project.id
        ).filter(
            model.Task.tuid == task_id,
            model.Project.org_id == organization.id
        ).first()
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=task_id,
            ctx={"task_id": "exist"}
        )

    if not organization.gtoken:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="google token",
            msg="Google token does not exist",
            inp="",
            ctx={"google token": "exist"}
        )

    # Create an instance of OAuth 2.0 credentials using the dictionary
    creds = Credentials.from_authorized_user_info(json.loads(organization.gtoken))

    # Check if the Google token provided is valid.
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    folder_path = f'{SETTINGS.APP_NAME}/media/{organization.org_name}/{task.task_name}'
    folder_id = create_folder_if_not_exists(folder_path, creds)

    file_ids = {}
    for index, file in enumerate(files):
        if not allowed_file(file.filename, ALLOWED_FILE_EXTENSIONS):
            CustomValidations.raize_custom_error(
                error_type="invalid",
                loc="files",
                msg=f"Allowed extensions are {ALLOWED_FILE_EXTENSIONS}",
                inp=file.filename,
                ctx={"image": "invalid type"}
            )

        created_file = await upload_to_drive(file, creds, folder_id)
        file_ids[index] = created_file.get('id', '')

    task.medias = file_ids
    sql.commit()
    sql.refresh(task)
    return task


def get_tasks(
    limit: int,
    offset: int,
    organization: orgModel.Organization,
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


def project_details(
    project_id: str,
    organization: orgModel.Organization,
    sql: Session
):
    """
    Retrieves the details of a project based on the provided project ID.
    """
    project = sql.query(model.Project).filter_by(
        puid=project_id,
        org_id=organization.id
    ).first()
    if not project:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="project_id",
            msg="Project does not exist",
            inp=project_id,
            ctx={"project_id": "exist"}
        )
    return project


def update_task(
    data: schema.UpdateTask,
    organization: orgModel.Organization,
    sql: Session
):
    """
    Updates the details of a task in the database based on the provided input data.
    """
    task = sql.query(model.Task).join(
        model.Project,
        model.Task.project_id == model.Project.id
    ).filter(
        model.Task.tuid == data.task_id,
        model.Project.org_id == organization.id
    ).first()
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id,
            ctx={"task_id": "exist"}
        )

    task.task_name = data.task_name or task.task_name
    task.description = data.description or task.description
    task.event_id = data.event_id or task.event_id
    task.estimate_hours = data.estimate_hours or task.estimate_hours
    task.deadline = data.deadline_date or task.deadline
    task.start_date = data.start_date or task.start_date
    task.end_date = data.end_date or task.end_date
    task.is_active = data.is_active or task.is_active
    task.is_deleted = data.is_deleted or task.is_deleted

    if data.group_id is not None:
        group_task = sql.query(model.TaskGroup).join(
            model.Project,
            model.TaskGroup.project_id == model.Project.id
        ).filter(
            # pylint: disable=singleton-comparison
            model.TaskGroup.guid == data.group_id,
            model.TaskGroup.is_deleted == False,
            model.Project.org_id == organization.id
        ).first()
        if not group_task:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="group_id",
                msg="Group does not exist",
                inp=data.group_id
            )
        task.group_id = group_task.id

    if data.parent_id is not None:
        parent_task = sql.query(
            model.Task
        ).join(
            model.Project,
            model.Task.project_id == model.Project.id
        ).filter(
            model.Task.tuid == data.parent_id,
            model.Project.org_id == organization.id
        ).first()
        if not task:
            CustomValidations.raize_custom_error(
                error_type="not_exist",
                loc="parent_id",
                msg="Task does not exist",
                inp=data.parent_id,
                ctx={"parent_id": "exist"}
            )
        task.parent_id = parent_task.id

    sql.commit()
    sql.refresh(task)

    return task


def assign_project_permission(
    data: schema.AssignPerojectPermission,
    organization: orgModel.Organization,
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
    user = sql.query(orgModel.OrganizationUser).join(
        frontendModel.FrontendUser,
        orgModel.OrganizationUser.user_id == frontendModel.FrontendUser.id
    ).filter(
        orgModel.OrganizationUser.org_id == organization.id,
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
    organization: orgModel.Organization,
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
    user = sql.query(orgModel.OrganizationUser).join(
        frontendModel.FrontendUser,
        orgModel.OrganizationUser.user_id == frontendModel.FrontendUser.id
    ).filter(
        orgModel.OrganizationUser.org_id == organization.id,
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
    organization: orgModel.Organization,
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

    user = sql.query(orgModel.OrganizationUser).join(
        frontendModel.FrontendUser,
        orgModel.OrganizationUser.user_id == frontendModel.FrontendUser.id
    ).filter(
        orgModel.OrganizationUser.org_id == organization.id,
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


def project_custom_column(
    data:schema.AddCustomColumn,
    organization: orgModel.Organization,
    authtoken:frontendModel.FrontendToken,
    sql:Session
):
    """
    Create a custom column for a project based on the provided data.
    """
    project = sql.query(model.Project).filter_by(
        puid=data.project_id,
        is_active=True,
        is_deleted=False,
        org_id=organization.id
    ).first()
    if not project:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="project_id",
            msg="project  does not exist",
            inp=data.project_id
        )

    existing_column_name = sql.query(model.CustomColumn).filter_by(
        column_name=data.column_name,
        project_id=project.id
    ).first()
    if existing_column_name:
        CustomValidations.raize_custom_error(
            error_type="already_exist",
            loc="column_name",
            msg="Column  already exists in this project.",
            inp=data.column_name,
        )
    customcolumn = model.CustomColumn(
        cuid = generate_uuid(data.column_name),
        type = data.type,
        column_name = data.column_name,
        created_by = authtoken.user_id,
        project_id = project.id,
        )
    sql.add(customcolumn)

    sql.commit()
    sql.refresh(customcolumn)
    return customcolumn


def update_column_expected_value(
    data: schema.CreateCustomColumnExpected,
    organization: orgModel.Organization,
    sql: Session
):
    """
    Creates new entries in the `CustomColumnExpected` table 
    by adding expected values for a specific custom column 
    and removing the old values.
    """
    # Retrieve the custom column object from the database based on the provided column ID
    column = sql.query(
        model.CustomColumn
    ).join(
        model.Project,
        model.Project.id == orgModel.Organization.id
    ).filter(
        # pylint: disable=singleton-comparison
        model.CustomColumn.cuid == data.column_id,
        model.CustomColumn.is_deleted == False,
        orgModel.Organization.orguid == organization.orguid
    ).first()
    if not column:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="column_id",
            msg="Column does not exist",
            inp=data.column_id
        )

    # Remove previous values for custom column
    sql.query(
        model.CustomColumnExpected
    ).filter_by(
        column_id=column.id
    ).delete()

    # Create a list of `CustomColumnExpected` objects
    # using the provided values and the ID of the column
    values = [
        model.CustomColumnExpected(
            vuid=generate_uuid(value),
            value=value,
            column_id=column.id
        ) for value in data.values
    ]
    sql.add_all(values)

    sql.commit()
    sql.refresh(column)
    return column


def delete_custom_column(
    column_id: str,
    organization: orgModel.Organization,
    sql: Session
):
    """
    Deletes a custom column from the database.
    """
    # Check custom column exist in project
    column = sql.query(model.CustomColumn).filter(
        # pylint: disable=singleton-comparison
        model.CustomColumn.cuid == column_id,
        model.CustomColumn.is_deleted == False,
        model.Project.org_id == organization.id
    ).first()
    if not column or column.project.org_id != organization.id:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="column_id",
            msg="Column does not exist",
            inp=column_id
        )

    column.is_deleted = True
    sql.commit()
    sql.refresh(column)
    return column


def assign_column_value(
    data: schema.AssignCustomColumnValue,
    organization: orgModel.Organization,
    sql: Session
):
    """
    This function assigns a custom column value to a task in a project. 
    It performs validations to ensure that the column,
    value, and task exist and are active and not deleted.
    """
    column = sql.query(
        model.CustomColumn
    ).join(
        model.Project,
        model.CustomColumn.project_id == model.Project.id
    ).filter(
        # pylint: disable=singleton-comparison
        model.CustomColumn.cuid == data.column_id, # column uid
        model.CustomColumn.is_deleted == False, # column not deleted
        model.Project.org_id == organization.id, # Project under current organization
        model.Project.is_active == True, # project is active
        model.Project.is_deleted == False, # proect is not deleted
    ).first()
    if not column:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="column_id",
            msg="Column does not exist",
            inp=data.column_id
        )

    value = sql.query(
        model.CustomColumnExpected
    ).filter_by(
        vuid=data.value_id, #value uid
        column_id=column.id, # value expecting for this column
        is_deleted=False # value not deleted
    ).first()
    if not value:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="value_id",
            msg="Value does not exist",
            inp=data.value_id
        )

    task = sql.query(
        model.Task
    ).join(
        model.Project,
        model.Task.project_id == model.Project.id
    ).filter(
        # pylint: disable=singleton-comparison
        model.Task.tuid == data.task_id, # task uid
        model.Task.is_active == True, # task active
        model.Task.is_deleted == False, # task not deleted
        model.Task.project_id == column.project_id, # task and column under same project
        model.Project.org_id == organization.id, # project under current organization
        model.Project.is_active == True, # project is active
        model.Project.is_deleted == False, # project not deleted
    ).first()
    # If the task does not exist, raise a custom error
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id
        )

    # Query the database to check if a custom column value has already been assigned to the task
    value_assigned = sql.query(
        model.CustomColumnAssigned
    ).filter_by(
        column_id=column.id,
        task_id=task.id
    ).first()
    if not value_assigned:
        value_assigned = model.CustomColumnAssigned(
            column_id=column.id,
            task_id=task.id
        )
        sql.add(value_assigned)

    # Update the value ID of the custom column assignment object with the provided value ID
    value_assigned.value_id = value.id

    # Commit the changes to the database and refresh the custom column assignment object
    sql.commit()
    sql.refresh(value_assigned)
    return task


def remove_column_value(
    data: schema.RemoveCustomColumnValue,
    organization: orgModel.Organization,
    sql: Session
):
    """
    Removes the assigned value of a custom column for a task.
    """
    column_sql = sql.query(
        model.CustomColumn
    ).join(
        model.Project,
        model.CustomColumn.project_id == model.Project.id
    ).filter(
        # pylint: disable=singleton-comparison
        model.CustomColumn.cuid == data.column_id, # column uid
        model.CustomColumn.is_deleted == False, # column not deleted
        model.Project.org_id == organization.id, # Project under current organization
        model.Project.is_active == True, # project is active
        model.Project.is_deleted == False, # proect is not deleted
    )
    print(column_sql)
    column = column_sql.first()
    if not column:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="column_id",
            msg="Column does not exist",
            inp=data.column_id
        )

    task = sql.query(model.Task).join(
        model.Project,
        model.Task.project_id == model.Project.id
    ).filter(
        # pylint: disable=singleton-comparison
        model.Task.tuid == data.task_id, # task uid
        model.Task.is_active == True, # task active
        model.Task.is_deleted == False, # task not deleted
        model.Task.project_id == column.project_id, # task and column under same project
        model.Project.org_id == organization.id, # project under current organization
        model.Project.is_active == True, # project is active
        model.Project.is_deleted == False, # project not deleted
    ).first()
    if not task:
        CustomValidations.raize_custom_error(
            error_type="not_exist",
            loc="task_id",
            msg="Task does not exist",
            inp=data.task_id
        )

    # Query the database to check if a custom column value has already been assigned to the task
    sql.query(model.CustomColumnAssigned).filter_by(
        column_id=column.id,
        task_id=task.id
    ).delete()

    sql.commit()
    sql.refresh(task)
    return task

def add_comments(
    data:schema.add_comments,
    authtoken:frontendModel.FrontendToken,
    sql:Session
):
    """
    Add a comment for a task.

    This function adds a comment to a task. 
    The comment can be a reply to another comment if a parent_id is provided.

    Raises:
    - CustomValidationError: If the task is not found or the parent comment is not found.
    by devanshu 10-10-2023
    """
    task_id = sql.query(model.Task).filter_by(
        tuid=data.task_uid,is_deleted=False
    ).first()


    if not task_id:
        CustomValidations.raize_custom_error(
            error_type="task not found",
            loc="task_id",
            msg="task not found",
            inp=data.task_uid
        )
    # Initialize parent_id to None if not provided
    parent_id = None
    if data.parent_id:
         # Check if the parent comment exists
        parent_comment = sql.query(model.Comments).filter_by(cuid=data.parent_id).first()
        if not parent_comment:
            CustomValidations.raize_custom_error(
                error_type="parent comment not found",
                loc="parent_id",
                msg="Parent comment not found",
                inp=data.parent_id
            )
        parent_id = parent_comment.id

    comments = model.Comments(
        cuid = generate_uuid(data.comment),
        comment = data.comment,
        user_id = authtoken.id,
        task_id = task_id.id,
        parent_id = parent_id
    )
    sql.add(comments)
    sql.commit()
    sql.refresh(comments)

    return comments

def get_all_task_comments(limit,offset,sql:Session):
    """
     Retrieves all comments for tasks with pagination.
    """
    all_task_comments = sql.query(model.Comments).limit(limit).offset(offset).all()
    total = sql.query(model.Comments.id).count()

    return {
        "result": all_task_comments, 
        "total": total
        }
