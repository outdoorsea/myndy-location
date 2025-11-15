"""
Health Check Router
File: api/routers/health.py

Health check and status endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")

        return {
            "status": "healthy",
            "service": "location-intelligence",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "location-intelligence",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """Get service status with statistics"""
    try:
        from database.models import LocationData, Place, Visit, Movement, Checkin

        # Get counts
        location_count = db.query(LocationData).count()
        place_count = db.query(Place).count()
        visit_count = db.query(Visit).count()
        movement_count = db.query(Movement).count()
        checkin_count = db.query(Checkin).count()

        # Get date ranges
        earliest_location = (
            db.query(LocationData).order_by(LocationData.timestamp).first()
        )
        latest_location = (
            db.query(LocationData).order_by(LocationData.timestamp.desc()).first()
        )

        return {
            "status": "operational",
            "service": "location-intelligence",
            "version": "1.0.0",
            "statistics": {
                "total_gps_points": location_count,
                "total_places": place_count,
                "total_visits": visit_count,
                "total_movements": movement_count,
                "total_checkins": checkin_count,
            },
            "date_range": {
                "earliest": (
                    earliest_location.timestamp.isoformat()
                    if earliest_location
                    else None
                ),
                "latest": (
                    latest_location.timestamp.isoformat() if latest_location else None
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "status": "error",
            "service": "location-intelligence",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
