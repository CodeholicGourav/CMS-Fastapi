"""
taskmanagement/model.py
Author: Gourav Sahu
Date: 05/09/2023
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, exc
)
from sqlalchemy.orm import relationship

from database import Base, SessionLocal
from dependencies import predefined_project_permissions


class Project(Base):
    """
    Represents a table in a database called 'projects'.
    """
    __tablename__ = 'projects'

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    puid = Column(
        String(50),
        index=True,
        unique=True
    )
    project_name = Column(
        String(50),
        nullable=False
    )
    description = Column(
        Text,
        nullable=True
    )
    created_by = Column(
        Integer,
        ForeignKey("frontendusers.id")
    )
    org_id = Column(
        Integer,
        ForeignKey("organizations.id")
    )
    is_active = Column(
        Boolean,
        default=True
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    creator = relationship(
        "FrontendUser",
        foreign_keys=created_by
    )

    def __repr__(self):
        return (
            "<Project("
                f"id={self.id}, "
                f"project_name='{self.project_name}'"
                f"created_by='{self.created_by}'"
                f"org_id='{self.org_id}'"
                f"is_active='{self.is_active}'"
                f"is_deleted='{self.is_deleted}'"
                f"created_at='{self.created_at}'"
                f"updated_at='{self.updated_at}'"
            ")>"
        )

    def __str__(self):
        return self.project_name


class Task(Base):
    """
    Represents a table in a database called 'tasks'.
    """
    __tablename__ = 'tasks'

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    tuid = Column(
        String(50),
        index=True,
        unique=True
    )
    task_name = Column(
        String(50),
        nullable=False
    )
    description = Column(
        Text,
        nullable=True
    )
    created_by = Column(
        Integer,
        ForeignKey("frontendusers.id")
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id")
    )
    event_id = Column(
        String(100),
        nullable=True
    )
    estimate_hours = Column(
        Integer,
        comment="in hours"
    )
    deadline = Column(
        DateTime,
        nullable=True
    )
    start_date = Column(
        DateTime,
        nullable=True
    )
    end_date = Column(
        DateTime,
        nullable=True
    )
    is_active = Column(
        Boolean,
        default=True
    )
    is_deleted = Column(
        Boolean,
        default=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    creator = relationship(
        "FrontendUser",
        foreign_keys=created_by
    )
    project = relationship(
        "Project",
        foreign_keys=project_id
    )
    assigned_to = relationship(
        "UserTask",
        back_populates="task"
    )

    def __repr__(self):
        return (
            "<Project("
                f"id={self.id}, "
                f"project_name='{self.task_name}'"
                f"created_by='{self.created_by}'"
                f"org_id='{self.project_id}'"
                f"is_active='{self.is_active}'"
                f"is_deleted='{self.is_deleted}'"
                f"created_at='{self.created_at}'"
                f"updated_at='{self.updated_at}'"
            ")>"
        )

    def __str__(self):
        return self.task_name


class ProjectPermission(Base):
    """
    Represents a table in a database called 'project_permissions'.
    """
    __tablename__ = "project_permissions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    permission = Column(
        String(255),
        nullable=False
    )
    type = Column(
        Integer,
        nullable=False
    )
    codename = Column(
        String(50),
        index=True,
        unique=True,
        nullable=False
    )


    def __repr__(self):
        return (
            "<ProjectPermission("
                f"id={self.id}, "
                f"permission='{self.permission}'"
                f"type='{self.type}'"
                f"codename='{self.codename}'"
            ")>"
        )

    def __str__(self):
        return f"Project Permission: {self.permission}"


def create_proj_permissions():
    """
    Create predefined project permissions in the database.
    """
    try:
        print("Creating project permissions data...")
        sql = SessionLocal()
        permissions = [
            ProjectPermission(**permission)
            for permission in predefined_project_permissions
        ]
        sql.add_all(permissions)
        sql.commit()
        return {
            "message": "Project Permissions created successfully"
        }
    except exc.IntegrityError as error:
        sql.rollback()
        return {"error": str(error)}
    except exc.SQLAlchemyError as error:
        sql.rollback()
        return {"error": str(error)}
    finally:
        sql.close()


class ProjectUserPermission(Base):
    """
    Represents a table in a database called 'project_user_permissions'.
    """
    __tablename__ = 'project_user_permissions'

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("frontendusers.id"),
        nullable=True
    )
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True
    )
    permission_id = Column(
        Integer,
        ForeignKey("project_permissions.id"),
        nullable=False
    )

    user = relationship(
        "FrontendUser",
        foreign_keys=user_id
    )
    project = relationship(
        "Project",
        foreign_keys=project_id
    )
    permission = relationship(
        "ProjectPermission",
        foreign_keys=permission_id
    )

    def __repr__(self):
        return (
            "ProjectUserPermission("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"project_id={self.project_id}, "
                f"permission_id={self.permission_id}"
            ")"
        )

    def __str__(self):
        return (
            "ProjectUserPermission("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"project_id={self.project_id}, "
                f"permission_id={self.permission_id}"
            ")"
        )


class UserTask(Base):
    """
    Represents a table in a database called 'user_tasks'.
    """
    __tablename__ = 'user_tasks'

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    task_id = Column(
        Integer,
        ForeignKey("tasks.id")
    )
    user_id = Column(
        Integer,
        ForeignKey("frontendusers.id")
    )
    created_by = Column(
        Integer,
        ForeignKey("frontendusers.id")
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    task = relationship(
        "Task",
        foreign_keys=task_id
    )
    user = relationship(
        "FrontendUser",
        foreign_keys=user_id
    )
    assigned_by = relationship(
        "FrontendUser",
        foreign_keys=created_by
    )

    def __repr__(self):
        return (
            "ProjectUserPermission("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"project_id={self.task_id}, "
                f"permission_id={self.created_by}"
            ")"
        )

    def __str__(self):
        return (
            "ProjectUserPermission("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"project_id={self.task_id}, "
                f"permission_id={self.created_by}"
            ")"
        )