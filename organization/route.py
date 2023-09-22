from fastapi import APIRouter, status, Query, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from dependencies import ALLOWED_EXTENSIONS, TEMPLATES
import os
from . import model, controller, schema
from frontenduser import model as frontendModel
from frontenduser.middleware import authenticate_token

organizationRoutes = APIRouter()

@organizationRoutes.get('get-organizations', response_model=List[schema.BasicOrganization])
def get_all_organizations(
    limit : Optional[int]=10, 
    offset : Optional[int]=0, 
    db : Session = Depends(get_db), 
    authToken: frontendModel.FrontendToken = Depends(authenticate_token),
    # permissions: model.BackendUser = Depends(check_permission(["read_user"])),
): return controller.all_organizations(limit, offset, db)

