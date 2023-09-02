from fastapi import APIRouter, status, Query, Depends, Path
from typing import List, Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from . import controller, model, schema
from middleware import authenticate_token, check_permission

frontendUserRoutes = APIRouter()

