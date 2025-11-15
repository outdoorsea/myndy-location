"""
Location Data Router
File: api/routers/location_data.py

API endpoints for GPS data management and ingestion.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class LocationPointResponse(BaseModel):
    """Location point response model"""
    id: str
    timestamp: datetime
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    course: Optional[float] = None


class IngestionRequest(BaseModel):
    """Ingestion request model"""
    days_back: int = 7
    trigger_sync: bool = True


class IngestionResponse(BaseModel):
    """Ingestion response model"""
    success: bool
    points_downloaded: int = 0
    points_processed: int = 0
    message: str


@router.get("/location-data/points", response_model=List[LocationPointResponse])
async def get_location_points(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """
    Query raw GPS points by time range.

    TODO: Implement actual database query
    """
    return []


@router.post("/location-data/ingest", response_model=IngestionResponse)
async def ingest_gps_data(request: IngestionRequest):
    """
    Ingest GPS data from myndy-api (Heroku).

    TODO: Implement GPS download and processing
    """
    return IngestionResponse(
        success=False,
        message="Not implemented yet"
    )


@router.delete("/location-data/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(90, ge=1)):
    """
    Remove GPS data older than specified days.

    TODO: Implement data cleanup
    """
    return {"success": True, "message": "No cleanup performed (not implemented)"}
