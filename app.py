import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backenduser.route import backendUserRoutes
from frontenduser.route import frontendUserRoutes
from dependencies import SETTINGS, TEMPLATES

app = FastAPI()
allowed_origins = SETTINGS.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    html_file_path = os.path.join(TEMPLATES, "index.html")
    
    return FileResponse(html_file_path, media_type="text/html")


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