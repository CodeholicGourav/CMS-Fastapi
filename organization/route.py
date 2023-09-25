from fastapi import APIRouter, status, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from dependencies import ALLOWED_EXTENSIONS, TEMPLATES
import os
from . import model, controller, schema
from frontenduser import model as frontendModel
from backenduser import model as backendModel
from .middleware import check_feature
from frontenduser.middleware import authenticate_token

organizationRoutes = APIRouter()

@organizationRoutes.get('get-organizations', response_model=schema.BasicOrganizationList)
def get_all_organizations(
    limit: int = Query(10, ge=1, le=100, description="number of results to retrieve"), 
    offset : int = Query(0, ge=0, description="Number of results to skip."), 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    subscription: frontendModel.FrontendToken = Depends(check_feature("create_organization")),
): return controller.all_organizations(limit, offset, db)


@organizationRoutes.post('create-organization')
def create_organization(
    data: schema.CreateOrganization,
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    subscription: backendModel.SubscriptionFeature = Depends(check_feature("create_organization")),
): return controller.create_organization(data, db, authToken, subscription)

