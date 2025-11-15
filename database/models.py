"""
Database Models for Location Intelligence
File: database/models.py

SQLAlchemy models for location intelligence database.
"""

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from database.connection import Base


class LocationData(Base):
    """Raw GPS location points"""

    __tablename__ = "location_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float)
    altitude = Column(Float)
    speed = Column(Float)
    course = Column(Float)
    source = Column(String(50))
    data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_location_data_timestamp", "timestamp", postgresql_using="brin"),
        Index("idx_location_data_coords", "latitude", "longitude"),
    )


class Place(Base):
    """Semantic places discovered from GPS clustering"""

    __tablename__ = "places"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    place_type = Column(String(100))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=50.0)
    address = Column(JSONB)
    metadata = Column(JSONB)
    visit_count = Column(Integer, default=0)
    first_visit_at = Column(DateTime(timezone=True))
    last_visit_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    embedding = Column(Vector(384))  # Vector embedding for semantic search

    # Relationships
    visits = relationship("Visit", back_populates="place")
    checkins = relationship("Checkin", back_populates="place")

    __table_args__ = (
        Index("idx_places_coords", "latitude", "longitude"),
        Index("idx_places_embedding", "embedding", postgresql_using="ivfflat"),
    )


class Visit(Base):
    """Visit timeline - periods spent at places"""

    __tablename__ = "visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    arrival_time = Column(DateTime(timezone=True), nullable=False, index=True)
    departure_time = Column(DateTime(timezone=True))
    duration_minutes = Column(Float)
    is_ongoing = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.8)

    # Movement metrics
    avg_speed_ms = Column(Float)
    max_speed_ms = Column(Float)
    detected_transport_mode = Column(String(50))
    arrival_direction = Column(Float)
    departure_direction = Column(Float)
    is_drive_through = Column(Boolean, default=False)

    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    place = relationship("Place", back_populates="visits")

    __table_args__ = (
        Index("idx_visits_place_id", "place_id"),
        Index("idx_visits_arrival_time", "arrival_time", postgresql_using="brin"),
    )


class Movement(Base):
    """Movement tracks between visits"""

    __tablename__ = "movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    start_visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"))
    end_visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"))
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    start_lat = Column(Float, nullable=False)
    start_lng = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lng = Column(Float, nullable=False)
    distance_meters = Column(Float)
    duration_minutes = Column(Float)
    avg_speed_ms = Column(Float)
    movement_type = Column(String(50))
    gps_track = Column(JSONB)  # Array of GPS points
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_movements_start_time", "start_time", postgresql_using="brin"),
    )


class Checkin(Base):
    """Manual check-ins from iOS app"""

    __tablename__ = "checkins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"))
    place_name = Column(String(255), nullable=False)
    place_category = Column(String(100))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    notes = Column(Text)
    checked_in_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    place = relationship("Place", back_populates="checkins")

    __table_args__ = (
        Index("idx_checkins_checked_in_at", "checked_in_at", postgresql_using="brin"),
        Index("idx_checkins_place_id", "place_id"),
    )
