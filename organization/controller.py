from typing import Optional
import math
import time
import requests
from datetime import datetime, timedelta

from fastapi import UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from . import model


def all_organizations(limit: int, offset: int, db: Session):
    return db.query(model.Organization).all()
