"""
app.py - FastAPI Application and Routing Configuration
Author: Gourav Sahu
Date: 20/08/2023
"""

import os
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backenduser.route import backendUserRoutes
from dependencies import SETTINGS, TEMPLATES
from frontenduser.route import frontendUserRoutes
from organization.route import organizationRoutes
from taskmanagement.route import taskmanagementRoutes


# Create a FastAPI instance
app = FastAPI(
    title="Code CMS",
    debug=SETTINGS.DEBUG,
    summary="An backend apis for a basic CMS web application made on fastapi.",
    description=(
        "A FastAPI-based Content Management System (CMS) empowers users to "
        "efficiently manage digital content for their websites or web applications."
    ),
    contact={
        "owner":"hello@codeholic.in"
    },
)


# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# Define a route for the root URL ("/")
@app.get(
    path='/',
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    description="It is a welcome page of the app.",
    name="Welcome page"
)
def index():
    """
    Returns the content of an HTML file located at a specific path.
    """
    html_file_path = os.path.join(TEMPLATES, "index.html")
    return FileResponse(html_file_path, media_type="text/html")


# Include routers for different endpoints
app.include_router(
    backendUserRoutes,
    prefix="/backend-user",
    tags=["Backend user"],
)

app.include_router(
    frontendUserRoutes,
    prefix="/frontend-user",
    tags=["Frontend user"],
)

app.include_router(
    organizationRoutes,
    prefix="/organization",
    tags=["Organization"],
)

app.include_router(
    taskmanagementRoutes,
    prefix="/task-management",
    tags=["Task Management"],
)
