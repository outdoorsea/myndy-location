"""
Location Intelligence Service - FastAPI Application
File: api/main.py

Main FastAPI application for location intelligence data warehouse and analytics.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import health, places, visits, movements, location_data, analysis
from database.connection import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting Location Intelligence Service...")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    yield

    # Cleanup
    logger.info("👋 Shutting down Location Intelligence Service...")


# Create FastAPI application
app = FastAPI(
    title="Location Intelligence Service",
    description="Location data warehouse and intelligence analytics API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Single-user system, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(places.router, prefix="/api/v1", tags=["places"])
app.include_router(visits.router, prefix="/api/v1", tags=["visits"])
app.include_router(movements.router, prefix="/api/v1", tags=["movements"])
app.include_router(location_data.router, prefix="/api/v1", tags=["location-data"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Location Intelligence",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
