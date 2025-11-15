-- Location Intelligence Database Initialization
-- File: database/init.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable PostGIS for advanced geographic queries (optional)
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- Create indexes for performance
-- Additional indexes will be created by Alembic migrations

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE location_intelligence TO location_user;
