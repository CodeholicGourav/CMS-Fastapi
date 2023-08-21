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
        # dependencies=[Depends(authenticate_token)],
        responses={404: {"description": "User not authenticated"}},
    )

    host = "127.0.0.1"  # Host IP (use "0.0.0.0" to allow external connections)
    port = 8000       # Port number
    uvicorn.run(app, host=host, port=port, log_level="info")

def main():
    if sys.argv[1] == 'migrate':
        print("Migrating all tables...")
        backendModel.Base.metadata.create_all(bind=engine)

    if sys.argv[1] == 'run':
        print("Running server")
        run()

if __name__ == '__main__':
    main()