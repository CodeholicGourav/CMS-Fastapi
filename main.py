import sys
import uvicorn
from database import engine
from backenduser import model as backendModel
from backenduser.controller import createsuperuser
from dependencies import BackendEmail
from dependencies import Hash
from database import SessionLocal
from app import app



def run():
    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    match sys.argv[1]:
        case 'migrate':
            print("Migrating all tables...")
            backendModel.Base.metadata.create_all(bind=engine)
            print(backendModel.create_permissions())
        
        case 'drop':
            ans = input("Are you sure to delete all tables? (y/n) :")
            if ans=="y" or ans=="Y":
                print("Dropping all tables...")
                backendModel.Base.metadata.drop_all(bind=engine)
            print("exited.")

        case 'run':
            run()

        case 'createsuperuser':
            createsuperuser(db=SessionLocal())
        
        case _:
            print("No command found. Try 'run', 'migrate', 'createsuperuser' instead.")


if __name__ == '__main__':
    main()

