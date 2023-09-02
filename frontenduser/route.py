from fastapi import APIRouter, status, Query, Depends, Path
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from . import controller, model, schema
from middleware import authenticate_token, check_permission

frontendUserRoutes = APIRouter()

@frontendUserRoutes.post("/register", response_model=schema.BaseUser, status_code=status.HTTP_201_CREATED) #Create user
def register(
    data: schema.RegisterUser, 
    db: Session = Depends(get_db),
): return controller.create_user(data, db)