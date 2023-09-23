from fastapi import APIRouter, status, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from dependencies import ALLOWED_EXTENSIONS, TEMPLATES
import os
from . import model, controller, schema
from frontenduser import model as frontendModel
from .middleware import check_feature
from frontenduser.middleware import authenticate_token

organizationRoutes = APIRouter()

@organizationRoutes.get('get-organizations', response_model=List[schema.BasicOrganization])
def get_all_organizations(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    subscription: frontendModel.FrontendToken = Depends(check_feature("create_organization")),
): return controller.all_organizations(limit, offset, db)


@organizationRoutes.post('create-organization')
def create_organization(
    data: schema.CreateOrganization,
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    subscription: frontendModel.FrontendToken = Depends(check_feature("create_organization")),
): return controller.create_organization(data, db, authToken)

