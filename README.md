# Location Intelligence Service

**Purpose**: Dedicated service for location data warehousing, analysis, and intelligence generation. Separates historic GPS data management from personal memory (myndy-ai).

## 🎯 Architecture Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    Location Intelligence Service                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐     ┌───────────────┐     ┌─────────────┐  │
│  │  FastAPI     │     │  Location     │     │  Analysis   │  │
│  │  Server      │────▶│  Intelligence │────▶│  Engine     │  │
│  │              │     │  Core         │     │             │  │
│  │  Port 8004   │     │               │     │  Clustering │  │
│  └──────────────┘     └───────────────┘     │  Enrichment │  │
│                                              │  Timeline   │  │
│                                              └─────────────┘  │
│                              │                                │
│                              ↓                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │     PostgreSQL + pgvector Database                   │    │
│  │                                                       │    │
│  │  • location_data (GPS points)                       │    │
│  │  • locations (clustered locations)                  │    │
│  │  • places (semantic places)                         │    │
│  │  • visits (visit timeline)                          │    │
│  │  • movements (movement tracks)                      │    │
│  │  • place_embeddings (vector search)                 │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                              ↑
                              │ API Queries for Context
                              │
┌────────────────────────────────────────────────────────────────┐
│                         Myndy-AI System                        │
│                                                                │
│  • Stores notable places only (home, work, favorites)         │
│  • References location-intelligence via place_id              │
│  • Queries for "where was I on Tuesday?" context              │
│  • Lightweight location context, not data warehouse           │
└────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Design Principles

### 1. Separation of Concerns
- **Location-Intelligence**: Historic GPS data warehouse + analytics
- **Myndy-AI**: Personal memory and notable places only

### 2. Single Source of Truth
- All historic location data lives in location-intelligence
- Myndy-AI stores only user-meaningful places (home, work, etc.)
- References maintained via place_id

### 3. API-First Integration
- Location-intelligence exposes REST API for queries
- Myndy-AI queries for context: "where was I on [date]?"
- No direct database access between services

## 📊 Database Schema

### Core Tables

#### location_data (GPS Points)
```sql
CREATE TABLE location_data (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    speed DOUBLE PRECISION,
    course DOUBLE PRECISION,
    source VARCHAR(50),
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_location_data_timestamp ON location_data(timestamp DESC);
CREATE INDEX idx_location_data_coords ON location_data(latitude, longitude);
```

#### places (Semantic Places)
```sql
CREATE TABLE places (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    place_type VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    radius_meters DOUBLE PRECISION DEFAULT 50.0,
    address JSONB,
    metadata JSONB,
    visit_count INTEGER DEFAULT 0,
    first_visit_at TIMESTAMPTZ,
    last_visit_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    embedding VECTOR(384)  -- pgvector for semantic search
);

CREATE INDEX idx_places_coords ON places(latitude, longitude);
CREATE INDEX idx_places_embedding ON places USING ivfflat (embedding vector_cosine_ops);
```

#### visits (Visit Timeline)
```sql
CREATE TABLE visits (
    id UUID PRIMARY KEY,
    place_id UUID REFERENCES places(id),
    arrival_time TIMESTAMPTZ NOT NULL,
    departure_time TIMESTAMPTZ,
    duration_minutes DOUBLE PRECISION,
    is_ongoing BOOLEAN DEFAULT FALSE,
    confidence_score DOUBLE PRECISION DEFAULT 0.8,

    -- Movement metrics (Phase 5.2)
    avg_speed_ms DOUBLE PRECISION,
    max_speed_ms DOUBLE PRECISION,
    detected_transport_mode VARCHAR(50),
    arrival_direction DOUBLE PRECISION,
    departure_direction DOUBLE PRECISION,
    is_drive_through BOOLEAN DEFAULT FALSE,

    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_visits_place_id ON visits(place_id);
CREATE INDEX idx_visits_arrival_time ON visits(arrival_time DESC);
```

#### movements (Movement Tracks)
```sql
CREATE TABLE movements (
    id UUID PRIMARY KEY,
    start_visit_id UUID REFERENCES visits(id),
    end_visit_id UUID REFERENCES visits(id),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    start_lat DOUBLE PRECISION NOT NULL,
    start_lng DOUBLE PRECISION NOT NULL,
    end_lat DOUBLE PRECISION NOT NULL,
    end_lng DOUBLE PRECISION NOT NULL,
    distance_meters DOUBLE PRECISION,
    duration_minutes DOUBLE PRECISION,
    avg_speed_ms DOUBLE PRECISION,
    movement_type VARCHAR(50),
    gps_track JSONB,  -- Array of GPS points
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_movements_start_time ON movements(start_time DESC);
```

#### checkins (Manual Check-ins from iOS App)
```sql
CREATE TABLE checkins (
    id UUID PRIMARY KEY,
    place_id UUID REFERENCES places(id),
    place_name VARCHAR(255) NOT NULL,
    place_category VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    notes TEXT,
    checked_in_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_checkins_checked_in_at ON checkins(checked_in_at DESC);
CREATE INDEX idx_checkins_place_id ON checkins(place_id);
```

## 🔄 Data Flow

### 1. GPS Ingestion
```
iOS App → myndy-api (Heroku) → myndy-api-postgres
                                      ↓
                              sync-location-data.sh
                                      ↓
                        location-intelligence postgres
                                      ↓
                          ingestion pipeline processes:
                          • Clustering (detect places)
                          • Enrichment (reverse geocoding)
                          • Visit detection (timeline)
                          • Movement tracking
```

### 2. Check-in Ingestion
```
iOS App → myndy-api (Heroku) → myndy-api-postgres (checkins table)
                                      ↓
                              sync-checkin-data.sh
                                      ↓
                        location-intelligence postgres
                                      ↓
                          • Link to existing places or create new
                          • Add to visit timeline
```

### 3. Myndy-AI Integration
```
User Query: "Where was I last Tuesday?"
                ↓
        Myndy-AI receives query
                ↓
        GET /api/v1/visits?date=2025-01-07
                ↓
        Location-Intelligence API
                ↓
        Returns: [{place_name, arrival_time, duration, ...}]
                ↓
        Myndy-AI formats response with context
```

## 🛠️ API Endpoints

### GPS & Location Data

#### `POST /api/v1/location-data/ingest`
Ingest GPS data from myndy-api-postgres (called by scheduler)
```json
{
  "days_back": 7,
  "trigger_sync": true
}
```

#### `GET /api/v1/location-data/points`
Query raw GPS points by time range
```
?start_time=2025-01-01T00:00:00Z&end_time=2025-01-07T23:59:59Z&limit=1000
```

### Places

#### `GET /api/v1/places`
List all discovered places
```
?limit=50&offset=0&place_type=restaurant
```

#### `GET /api/v1/places/{place_id}`
Get place details

#### `GET /api/v1/places/nearby`
Find places near coordinates
```
?latitude=47.6205&longitude=-122.3493&radius_meters=1000
```

#### `GET /api/v1/places/search`
Semantic search for places by name/description
```
?query=coffee shop downtown&limit=10
```

### Visits

#### `GET /api/v1/visits`
Get visit timeline
```
?start_date=2025-01-01&end_date=2025-01-07&place_id=uuid
```

#### `GET /api/v1/visits/{visit_id}`
Get visit details with movement metrics

#### `GET /api/v1/visits/current`
Get current ongoing visit (if any)

#### `GET /api/v1/visits/stats`
Get visit statistics
```
?period=weekly&place_id=uuid
```

### Movements

#### `GET /api/v1/movements`
Get movement tracks between visits
```
?start_date=2025-01-01&end_date=2025-01-07
```

#### `GET /api/v1/movements/{movement_id}`
Get movement details with GPS track

### Check-ins

#### `GET /api/v1/checkins`
Get manual check-ins from iOS app
```
?start_date=2025-01-01&end_date=2025-01-07
```

### Analysis & Intelligence

#### `POST /api/v1/analysis/process`
Trigger location intelligence processing
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-07",
  "auto_create_places": true,
  "auto_deduplicate": true
}
```

#### `GET /api/v1/analysis/timeline`
Get comprehensive timeline with visits, movements, and check-ins
```
?date=2025-01-07
```

#### `GET /api/v1/analysis/patterns`
Detect routine patterns (work commute, weekly errands, etc.)
```
?days_back=30
```

## 🔧 Ingestion Pipeline

### Pipeline Stages

1. **GPS Download** (`scripts/ingest_gps.py`)
   - Run sync-location-data.sh
   - Query location_data from postgres
   - Filter for new points since last run

2. **Clustering** (`core/clustering.py`)
   - Detect significant location clusters
   - Calculate center points and radiuses
   - Score by visit frequency and duration

3. **Enrichment** (`core/enrichment.py`)
   - Reverse geocoding (Nominatim)
   - Business lookup (Overpass API)
   - Place type classification

4. **Visit Detection** (`core/visit_detection.py`)
   - Group GPS points into visits
   - Calculate arrival/departure times
   - Compute movement metrics (speed, direction)
   - Detect transportation modes

5. **Movement Tracking** (`core/movement_tracking.py`)
   - Identify movements between visits
   - Calculate distance and duration
   - Store GPS tracks

6. **Check-in Integration** (`scripts/ingest_checkins.py`)
   - Sync check-ins from myndy-api
   - Match to existing places or create new
   - Integrate into visit timeline

### Scheduler Configuration

Run ingestion on schedule:
```yaml
schedules:
  - name: gps_ingestion
    cron: "*/15 * * * *"  # Every 15 minutes
    task: ingest_gps

  - name: location_analysis
    cron: "0 * * * *"  # Every hour
    task: analyze_locations

  - name: checkin_sync
    cron: "*/15 * * * *"  # Every 15 minutes
    task: ingest_checkins
```

## 🐳 Docker Setup

### Service Configuration

```yaml
services:
  location-intelligence:
    build: ./location-intelligence
    ports:
      - "8004:8000"
    environment:
      - DATABASE_URL=postgresql://location_user:password@location-postgres:5432/location_intelligence
      - MYNDY_API_POSTGRES_URL=postgresql://myndy_user:password@myndy-api-postgres:5432/myndy_api
      - REDIS_URL=redis://redis:6380
    depends_on:
      - location-postgres
      - redis

  location-postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5435:5432"
    environment:
      - POSTGRES_USER=location_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=location_intelligence
    volumes:
      - location-postgres-data:/var/lib/postgresql/data

volumes:
  location-postgres-data:
```

### Build & Run

```bash
# Build service
cd /Users/jeremy/myndy-core
docker-compose -f docker-compose.unified.yml build location-intelligence

# Start service
docker-compose -f docker-compose.unified.yml up -d location-intelligence location-postgres

# Check logs
docker-compose -f docker-compose.unified.yml logs -f location-intelligence

# Run migrations
docker-compose -f docker-compose.unified.yml exec location-intelligence alembic upgrade head
```

## 🔗 Myndy-AI Integration

### Notable Places in Myndy-AI

Myndy-AI stores only user-meaningful places:

```python
# In myndy-ai memory system
class NotablePlace(BaseMemoryModel):
    """Notable place stored in myndy-ai for quick reference"""

    id: str
    name: str
    description: str
    place_type: str  # home, work, favorite

    # Reference to location-intelligence
    location_intelligence_place_id: str

    # Personal significance
    visit_frequency: str  # daily, weekly, monthly
    significance: str  # high, medium, low
    notes: str
```

### Context Queries

```python
# Query location-intelligence for context
from ingestion.shared.api_client import LocationIntelligenceClient

client = LocationIntelligenceClient()

# Get timeline for specific date
timeline = client.get_timeline(date="2025-01-07")

# Get current location
current = client.get_current_visit()

# Search places
places = client.search_places(query="coffee shop", limit=5)
```

## 📈 Performance Considerations

### Indexing Strategy
- GPS points: indexed by timestamp and coordinates
- Places: spatial index for location queries
- Visits: indexed by time and place
- Embeddings: IVFFlat index for vector search

### Caching
- Frequently accessed places cached in Redis
- Timeline queries cached for 5 minutes
- Current visit cached until departure detected

### Query Optimization
- Limit GPS point queries to specific time windows
- Use spatial indexes for proximity searches
- Paginate large result sets
- Pre-compute visit statistics

## 🔐 Security

### Data Privacy
- All location data is user's own data
- No multi-user access (single-user system)
- API requires authentication token
- Data encrypted at rest

### API Authentication
```python
headers = {
    "X-API-Key": os.getenv("LOCATION_INTELLIGENCE_API_KEY")
}
```

## 📝 Migration Plan

### Phase 1: Setup Infrastructure
1. Create location-postgres database with pgvector
2. Create Docker service configuration
3. Set up database migrations (Alembic)

### Phase 2: Extract Code
1. Copy models, CRUD, routers from myndy-ai
2. Adapt to new database schema
3. Update imports and dependencies

### Phase 3: Data Migration
1. Export existing data from myndy-ai postgres
2. Import into location-intelligence postgres
3. Validate data integrity

### Phase 4: Update Myndy-AI
1. Create LocationIntelligenceClient
2. Replace direct CRUD with API calls
3. Store only notable places locally
4. Update tools to query location-intelligence API

### Phase 5: Remove Old Code
1. Delete location CRUD from myndy-ai
2. Remove location models
3. Clean up routers
4. Archive old migration files

## 🧪 Testing

### Unit Tests
- Model validation
- CRUD operations
- Clustering algorithms
- Enrichment service

### Integration Tests
- GPS ingestion pipeline
- Check-in sync
- Visit detection
- API endpoints

### Performance Tests
- Query response times
- Batch processing speed
- Vector search performance
- Cache hit rates

## 📚 Documentation

- **API Reference**: OpenAPI/Swagger at `/docs`
- **Architecture**: This README
- **Database Schema**: `docs/schema.md`
- **Deployment**: `docs/deployment.md`
- **Development**: `docs/development.md`

## 🚦 Getting Started

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 16+ with pgvector
- Python 3.11+
- Access to myndy-api-postgres

### Quick Start

```bash
# Clone and navigate
cd /Users/jeremy/myndy-core/location-intelligence

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up database
alembic upgrade head

# Run development server
uvicorn api.main:app --reload --port 8004

# Test API
curl http://localhost:8004/api/v1/health
```

### First Ingestion

```bash
# Sync GPS data from myndy-api
../sync-location-data.sh

# Run initial analysis
python scripts/ingest_gps.py --days-back 30

# Check results
curl http://localhost:8004/api/v1/places
curl http://localhost:8004/api/v1/visits
```

## 🎯 Future Enhancements

- Machine learning for place type classification
- Commute prediction and optimization
- Anomaly detection (unusual locations/times)
- Export to standard formats (GPX, KML)
- Privacy controls and data retention policies
- Shared location features (future multi-user support)
- Integration with mapping services
- Automatic photo tagging by location

## 📄 License

MIT License - See LICENSE file for details

---

**Status**: 🚧 In Development
**Version**: 1.0.0
**Last Updated**: 2025-01-14
