from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
import uvicorn
import time
from datetime import datetime

from app.api.routes import topics_router, explanations_router, related_topics_router
from app.core.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Curiosity Blocks API",
    description="API for exploring educational topics with personalized content",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(topics_router, prefix="/api/v1", tags=["Topics"])
app.include_router(explanations_router, prefix="/api/v1", tags=["Explanations"])
app.include_router(related_topics_router, prefix="/api/v1", tags=["Related Topics"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that provides basic API information.
    """
    return {
        "message": "Welcome to Curiosity Blocks API",
        "version": "1.0.0",
        "documentation": "/docs",
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    Returns status information about the API and its dependencies.
    """
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "timestamp": import_time(),
        "dependencies": {
            "openai": "connected" if settings.OPENAI_API_KEY else "not configured",
            "exa_search": "connected" if settings.EXA_API_KEY else "not configured"
        }
    }

def import_time():
    """Get the current time as an ISO formatted string"""
    return datetime.now().isoformat()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
