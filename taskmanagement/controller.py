"""
taskmanagement/controller.py
Author: Gourav Sahu
Date: 05/09/2023
"""

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from dependencies import CustomValidations, generate_uuid
from frontenduser import model as frontendModel
from organization import model as orgModel
from sqlalchemy import func
from . import model, schema


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

    # Add the new project to the session.
    sql.add(project)
    # Commit the session to save the changes to the database.
    sql.commit()
    # Refresh the project object to get the updated values from the database.
    sql.refresh(project)

    return project


def update_project(data: schema.UpdateProject, organization: orgModel.Organization, sql: Session):
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
    task = sql.query(
        model.Task
    ).join(
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

    # If the column does not exist, raise a custom error
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

    # Add all the `CustomColumnExpected` objects to the session
    sql.add_all(values)

    # Commit the session to persist the changes
    sql.commit()

    # Refresh the custom column object to reflect the newly added expected values
    sql.refresh(column)

    # Return the updated custom column object
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

    :param data: The input data containing the column ID, value ID, and task ID.
    :param organization: The organization to which the project and task belong.
    :param sql: The SQLAlchemy session object for database operations.
    :return: The updated task object with the assigned custom column value.
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
    value_assigned = sql.query(model.CustomColumnAssigned).filter_by(
        column_id=column.id,
        task_id=task.id
    ).first()

    # If not, create a new custom column assignment object and add it to the session
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

    :param data: The input data containing the column ID, value ID, and task ID.
    :param organization: The organization to which the project and task belong.
    :param sql: The SQLAlchemy session object for database operations.
    :return: The updated task object with the assigned custom column value.
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
    try:
        all_task_comments = sql.query(model.Comments).limit(limit).offset(offset).all()
        total = sql.query(func.count(model.Comments.id)).scalar()
        return {"result":all_task_comments,
                "total":total
                }
    except NoResultFound:
        return {
            "result":[],
            "total":0
        }
