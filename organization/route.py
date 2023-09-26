from fastapi import APIRouter, status, Query, Depends, UploadFile, File, Path
from fastapi.responses import FileResponse
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from dependencies import ALLOWED_EXTENSIONS, TEMPLATES
import os
from . import model, controller, schema
from frontenduser import model as frontendModel
from backenduser import model as backendModel
from .middleware import check_feature, organization_exist
from frontenduser.middleware import authenticate_token

organizationRoutes = APIRouter()

@organizationRoutes.get('/get-organizations', response_model=schema.BasicOrganizationList)
def get_all_organizations(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"), 
    offset : int = Query(0, ge=0, description="Number of results to skip."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
): return controller.all_organizations(limit, offset, db)


@organizationRoutes.post('/create-organization', response_model=schema.ShowOrganization)
def create_organization(
    data: schema.CreateOrganization,
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    feature: backendModel.SubscriptionFeature = Depends(check_feature("create_organization")),
): return controller.create_organization(data, db, authToken, feature)


@organizationRoutes.post('/register', response_model=schema.ShowOrgUser)
def register_to_organization(
    data: schema.OrgUserRegister,
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    # subscription: backendModel.SubscriptionFeature = Depends(check_feature("create_organization")),
): return controller.register_to_organization(data, db, authToken)


@organizationRoutes.get('/users', response_model=schema.ShowOrgUserList)
def get_all_users(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"), 
    offset : int = Query(0, ge=0, description="Number of results to skip."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
): return controller.get_all_users(limit, offset, organization, db)


@organizationRoutes.get('/users/{user_id}', response_model=schema.ShowOrgUser)
def get_user_details(
    user_id : str = Path(description="UUID of the user to retrieve."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
): return controller.get_user_details(user_id, organization, db)


@organizationRoutes.get('/roles', response_model=schema.ShowOrgRoleList)
def get_all_roles(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"), 
    offset : int = Query(0, ge=0, description="Number of results to skip."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
): return controller.get_all_roles(limit, offset, organization, db)


@organizationRoutes.get('/roles/{role_id}', response_model=schema.ShowOrgRole)
def get_role_details(
    role_id : str = Path(description="UUID of the role to retrieve."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    organization: backendModel.SubscriptionFeature = Depends(organization_exist),
): return controller.get_role_details(role_id, organization, db)

