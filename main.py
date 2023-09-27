from typing import Optional
import sys

import uvicorn

from app import app
from database import SessionLocal, engine
from backenduser.controller import createsuperuser
from backenduser import model as backendModel
from frontenduser import model as frontendModel
from organization import model as organizationdModel


def run():
    """
    Run the application using the Uvicorn server.
    
    The server is run on the host "127.0.0.1" and port 8000.
    The log level is set to "info".
    """
    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")


def migrate_tables() -> None:
    """
    Migrates all tables in the database and populates them with initial data.

    Args:
        engine: The database engine to use. Defaults to None.

    Returns:
        None
    """
    print("Migrating all tables...")
    backendModel.Base.metadata.create_all(bind=engine)
    frontendModel.Base.metadata.create_all(bind=engine)
    backendModel.create_permissions()
    backendModel.create_features()
    organizationdModel.create_permissions()
    frontendModel.create_timezones()


def drop_tables() -> None:
    """
    Prompts the user for confirmation to delete all tables in the database.
    If the user confirms by entering 'y', the function drops all tables by calling the `drop_all` method on the metadata
    of the backend and frontend models. If the user enters any other input or 'n', the function exits without dropping any tables.
    """
    confirmation = input("Are you sure to delete all tables? (y/n): ")
    if confirmation.lower() == "y":
        print("Dropping all tables...")
        backendModel.Base.metadata.drop_all(bind=engine)
        frontendModel.Base.metadata.drop_all(bind=engine)
    print("Exited.")


def main():
    """
    The `main` function is the entry point of the program. It takes command line arguments and performs different actions based on the provided command.
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