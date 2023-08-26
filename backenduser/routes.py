from fastapi import APIRouter, status, Query, Request
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db
from . import controller, model, schema
from middleware import authenticate_token, check_permission, perm_req

backendUserRoutes = APIRouter()

@backendUserRoutes.get("/get", response_model=List[schema.ShowUser], status_code=status.HTTP_200_OK)
async def get_users_list(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.all_backend_users(limit, offset, db)


@backendUserRoutes.post("/register", response_model=schema.ShowUser, status_code=status.HTTP_201_CREATED)
def register(
    request: schema.RegisterUser, 
    db: Session = Depends(get_db)
): return controller.create_user(request, db)


@backendUserRoutes.get("/verify-token", status_code=status.HTTP_200_OK)
def verify_token(
    token: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.verify_email(token, db)


@backendUserRoutes.post("/login", response_model= schema.ShowToken, status_code=status.HTTP_200_OK)
def login(
    request: schema.LoginUser, 
    db: Session = Depends(get_db)
): return controller.create_auth_token(request, db)


@backendUserRoutes.get("/send-token", status_code=status.HTTP_200_OK)
def send_token(
    email: str = Query(..., description="Email verification token"), 
    db: Session = Depends(get_db)
): return controller.send_verification_mail(email, db)


@backendUserRoutes.post('/create-password', response_model=schema.ShowUser, status_code=status.HTTP_200_OK)
def create_new_password(
    request: schema.ForgotPassword, 
    db: Session = Depends(get_db)
): return controller.create_new_password(request, db)


@backendUserRoutes.get('/permissions', response_model=List[schema.BasePermission], status_code=status.HTTP_200_OK)
def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return db.query(model.BackendPermission).all()


@backendUserRoutes.post('/create-permission', response_model=schema.BasePermission, status_code=status.HTTP_201_CREATED)
def create_permission(
    request : schema.BasePermission,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.create_permission(request, db)


@backendUserRoutes.get('/roles', response_model=List[schema.ShowRole], status_code=status.HTTP_200_OK)
def get_all_roles(
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.get_roles_list(db)


@backendUserRoutes.post('/add-role', response_model=schema.ShowRole, status_code=status.HTTP_201_CREATED)
def create_new_roles(
    request : schema.CreateRole,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token)
): return controller.add_role(request, current_user, db)


""" @backendUserRoutes.get('/test-permission', status_code=status.HTTP_200_OK)
@perm_req(["create_user"], db = Depends(get_db))
def test_permission(
    request : Request,
    db: Session = Depends(get_db),
    current_user: model.BackendUser = Depends(authenticate_token),
    # permissions: bool = Depends(check_permission('create_user', Request()))
): 
    return {"message": "You have access to this route!"} """
