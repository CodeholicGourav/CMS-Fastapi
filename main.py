from fastapi import Depends, FastAPI
from backenduser.routes import backendUserRoutes 
from backenduser import model as backendModel
from database import engine
# from dependencies import authenticate_token

app = FastAPI()

backendModel.Base.metadata.create_all(engine)

# app.include_router(agorameter.router)
app.include_router(
    backendUserRoutes,
    prefix="/backend-user",
    tags=["backend-user"],
    # dependencies=[Depends(authenticate_token)],
    responses={404: {"description": "User not authenticated"}},
)