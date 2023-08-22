from fastapi import Depends, FastAPI
from backenduser.routes import backendUserRoutes 
from backenduser import model as backendModel
from database import engine
import sys
import uvicorn
# from dependencies import authenticate_token

def run():
    app = FastAPI()

    app.include_router(
        backendUserRoutes,
        prefix="/backend-user",
        tags=["backend-user"],
        responses={404: {"description": "User not authenticated"}},
    )

    host = "127.0.0.1"
    port = 8000
    uvicorn.run(app, host=host, port=port, log_level="info")

def main():
    if sys.argv[1] == 'migrate':
        print("Migrating all tables...")
        backendModel.Base.metadata.create_all(bind=engine)

    elif sys.argv[1] == 'run':
        print("Running server")
        run()
    
    else:
        print("No command found. Try 'run' or 'migrate' instead.")

if __name__ == '__main__':
    main()