import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backenduser.route import backendUserRoutes
from frontenduser.route import frontendUserRoutes

app = FastAPI()
allowed_origins = os.getenv('ALLOWED_ORIGINS')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    backendUserRoutes,
    prefix="/backend-user",
    tags=["backend-user"],
)

app.include_router(
    frontendUserRoutes,
    prefix="/frontend-user",
    tags=["frontend-user"],
)