"""
main.py
Author: Gourav Sahu
Date: 20/08/2023
"""
import sys

import uvicorn

from app import app
from backenduser import model as backendModel
from backenduser.controller import createsuperuser
from database import SessionLocal, engine
from frontenduser import model as frontendModel
from organization import model as organizationdModel
from taskmanagement import model as taskModel


def run():
    """
    Run the application using the Uvicorn server.
    
    The server is run on the host "127.0.0.1" and port 8000.
    The log level is set to "info".
    """
    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")


def migrate_tables():
    """
    Migrates all tables in the database and populates them with initial data.
    """
    print("Migrating all tables...")
    backendModel.Base.metadata.create_all(bind=engine)
    frontendModel.Base.metadata.create_all(bind=engine)
    organizationdModel.Base.metadata.create_all(bind=engine)
    taskModel.Base.metadata.create_all(bind=engine)
    backendModel.create_permissions()
    backendModel.create_features()
    organizationdModel.create_org_permissions()
    taskModel.create_proj_permissions()
    frontendModel.create_timezones()


def drop_tables():
    """
    Prompts the user for confirmation to delete all tables in the database.
    
    If the user confirms, it drops all tables related to the backend and frontend models.
    If the user does not confirm, it prints "Exited."
    """
    confirmation = input("Are you sure to delete all tables? (y/n): ")
    if confirmation.lower() == "y":
        print("Dropping all tables...")
        backendModel.Base.metadata.drop_all(bind=engine)
        frontendModel.Base.metadata.drop_all(bind=engine)
    print("Exited.")


def main():
    """
    The `main` function is the entry point of the program.
    It takes command line arguments and performs different actions based on the provided command.
    """
    command = sys.argv[1] if len(sys.argv) > 1 else None

    if command == 'migrate':
        migrate_tables()
    elif command == 'drop':
        drop_tables()
    elif command == 'run':
        run()
    elif command == 'createsuperuser':
        createsuperuser(db=SessionLocal())
    else:
        print("No command found. Try 'run', 'migrate', 'createsuperuser' instead.")


if __name__ == '__main__':
    main()
