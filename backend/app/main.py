from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .database import engine, Base
from .routers import activities, auth, strava, users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}", tags=["users"])
app.include_router(strava.router, prefix=f"{settings.API_V1_STR}", tags=["strava"])
app.include_router(activities.router, prefix=f"{settings.API_V1_STR}", tags=["activities"])


@app.get("/api/health")
def health_check():
    """
    Health check endpoint for Docker healthchecks
    """
    return {"status": "ok"}


@app.get("/")
def root():
    """
    Root endpoint for the API
    """
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
    }