from sqlalchemy.orm import Session
from dependencies import Hash, BackendEmail, generate_token, TOKEN_LIMIT, TOKEN_VALIDITY
from . import schema, model
from datetime import datetime, timedelta
from fastapi import HTTPException,status
from dateutil.relativedelta import relativedelta
import getpass
import secrets


