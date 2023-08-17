from fastapi import APIRouter, Request
# from dependencies import createDBConnection

backendUserRoutes = APIRouter()

@backendUserRoutes.get("/get-users",)
async def get_users_list(request: Request):
    ret = {
        "users" : [],
    }
    return {"status": True, "data": ret}