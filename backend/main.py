"""
BreastHealth Monitor - Main FastAPI Application
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import settings
from .database import init_db
from .routers import measurements_router, images_router, analysis_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting BreastHealth Monitor API...")
    await init_db()
    print("Database initialized")
    
    # Create uploads directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Shutdown
    print("Shutting down BreastHealth Monitor API...")


# Create FastAPI app
app = FastAPI(
    title="BreastHealth Monitor API",
    description="API для системы мониторинга температуры молочных желез",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(measurements_router, prefix=settings.API_PREFIX)
app.include_router(images_router, prefix=settings.API_PREFIX)
app.include_router(analysis_router, prefix=settings.API_PREFIX)

# Serve static files (frontend)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    """Serve the frontend index.html."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "BreastHealth Monitor API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api")
async def api_info():
    """API information."""
    return {
        "name": "BreastHealth Monitor API",
        "version": "1.0.0",
        "endpoints": {
            "measurements": "/api/measurements",
            "images": "/api/images",
            "analysis": "/api/analysis"
        },
        "docs": "/docs"
    }
