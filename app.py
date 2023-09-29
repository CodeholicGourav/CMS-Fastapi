"""
app.py - FastAPI Application and Routing Configuration
Author: Gourav Sahu
Date: 20/08/2023
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from backenduser.route import backendUserRoutes
from dependencies import SETTINGS, TEMPLATES
from frontenduser.route import frontendUserRoutes
from organization.route import organizationRoutes

# Create a FastAPI instance
app = FastAPI()

# Get allowed origins from settings
allowed_origins = SETTINGS.ALLOWED_ORIGINS

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a route for the root URL ("/")
@app.get("/")
def index():
    """
    Returns the content of an HTML file located at a specific path.

    :return: FileResponse object with the content of the HTML file
    :rtype: FileResponse
    """
    html_file_path = os.path.join(TEMPLATES, "index.html")
    return FileResponse(html_file_path, media_type="text/html")

# Include routers for different endpoints
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

app.include_router(
    organizationRoutes,
    prefix="/organization",
    tags=["organization"],
)
