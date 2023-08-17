from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse
from backenduser.routes import backendUserRoutes 
from dependencies import authenticate_token

app = FastAPI()


# app.include_router(agorameter.router)
app.include_router(
    backendUserRoutes,
    prefix="/backend-user",
    tags=["backend-user"],
    dependencies=[Depends(authenticate_token)],
    responses={404: {"description": "User not authenticated"}},
)