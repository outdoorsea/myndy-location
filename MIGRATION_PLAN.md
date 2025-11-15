# Location Intelligence Migration Plan

**Project**: myndy-location
**Purpose**: Extract location intelligence from myndy-ai into dedicated microservice
**Status**: Phase 1 Complete (Infrastructure Setup)
**Last Updated**: 2025-11-14

---

## 📋 Executive Summary

This document outlines the complete migration plan for extracting location intelligence functionality from the monolithic `myndy-ai` service into a dedicated `myndy-location` microservice. The goal is to create a specialized location data warehouse and analytics service, allowing `myndy-ai` to focus on personal memory management.

### Key Objectives

1. **Separate Concerns**: Extract all location processing from myndy-ai
2. **Maintain Features**: Preserve all existing location timeline functionality
3. **API Compatibility**: Ensure myndy-coordinator continues working seamlessly
4. **Single Database**: Use PostgreSQL with pgvector (no Qdrant dependency)
5. **Improve Performance**: Optimize for location-specific queries and analytics

---

## 🎯 Existing Functionality Overview

### A. Location Ingestion (from myndy-api Heroku)

**Current Implementation**: `myndy-ai/ingestion/locations/`

1. **GPS Data Download**
   - Smart incremental download from Heroku myndy-api
   - OAuth2 authentication
   - Deduplication logic
   - Batch processing (1000 points per request)
   - Automatic gap detection
   - Progress tracking

2. **Manual Check-in Sync**
   - iOS app manual check-ins
   - Place category mapping
   - Notes and descriptions
   - Integration with visit timeline

3. **iPhone GPS Optimization**
   - Prioritizes point count over duration
   - Handles intermittent GPS sampling
   - 5-point threshold for significance
   - Brief but significant visit detection

### B. Location Processing Pipeline

**Current Implementation**: `myndy-ai/ingestion/locations/location_ingest.py`

1. **Place Detection (Clustering)**
   - Spatial-temporal clustering with Haversine distance
   - 50m radius for place grouping
   - 1-minute minimum duration
   - Significance scoring (point count + duration + frequency)
   - iPhone GPS behavior accommodation

2. **Reverse Geocoding & Enrichment**
   - Nominatim (OpenStreetMap) for addresses
   - Google Places API (via coordinator)
   - Foursquare API (via coordinator)
   - Grid-based caching (100m precision)
   - Rate limiting (1 req/sec)
   - Place type classification

3. **Visit Detection**
   - Temporal grouping with 60-minute gap threshold
   - Movement metrics extraction (speed, direction)
   - Transport mode detection
   - Check-in integration
   - Drive-through detection
   - Confidence scoring

4. **Movement Tracking**
   - Point-to-point distance calculation
   - Speed analysis (avg, max, variance)
   - Transport classification:
     - Stationary: <0.5 m/s
     - Walking: 0.5-2.2 m/s
     - Cycling: 2.2-6.7 m/s
     - Driving: 6.7+ m/s
   - Directional analysis (cardinal directions)
   - Route descriptions (approach/departure)

### C. Location Timeline Features (myndy-coordinator)

**Current Implementation**: `myndy-coordinator/frontend/templates/location_timeline.html`

1. **Timeline Visualization**
   - Visit timeline with places and durations
   - Travel timeline with movements
   - Combined view (visits + travel)
   - Visual timeline with connector lines
   - Color-coded entries (visits=green, travel=yellow)
   - Animated pulsing for ongoing visits

2. **Date Navigation**
   - Single day view (default)
   - Date range view
   - Week view
   - Quick navigation (Today, Yesterday, Last Week)
   - Custom date picker
   - Previous/Next day buttons

3. **Real-time Current Location**
   - "Where am I now?" status
   - Movement state indicator
   - Duration at current location
   - Confidence score
   - Auto-refresh every 30 seconds

4. **Filtering Capabilities**
   - Location type (All, Home, Work, Travel)
   - Duration (Short <1hr, Medium 1-4hr, Long 4hr+)
   - Time of day (Morning, Afternoon, Evening)
   - Minimum duration threshold (0, 1, 5, 15, 60 min)

5. **Summary Statistics**
   - Total places visited
   - Total trips taken
   - Time spent at places
   - Travel time
   - Total distance

6. **Place Information Display**
   - Place name
   - Full address
   - Coordinates (6 decimal precision)
   - Place category
   - Confidence score
   - Google Maps integration
   - Visit count

---

## 📊 Feature List & Requirements

### Must-Have Features (Phase 1-3)

#### Ingestion
- [ ] Download GPS data from myndy-api (Heroku)
- [ ] Incremental download with deduplication
- [ ] Sync manual check-ins from iOS app
- [ ] Store raw GPS points in PostgreSQL
- [ ] Progress tracking and statistics

#### Processing
- [ ] Spatial-temporal clustering for place detection
- [ ] Reverse geocoding with Nominatim
- [ ] Place deduplication and consolidation
- [ ] Visit detection with gap analysis
- [ ] Movement tracking between visits
- [ ] Transport mode classification
- [ ] Drive-through detection

#### API Endpoints
- [ ] Get visits by date/date range
- [ ] Get current ongoing visit
- [ ] Get places with filtering
- [ ] Search places by name/location
- [ ] Get timeline for date
- [ ] Get movement tracks
- [ ] Get statistics

#### Timeline Display (via myndy-coordinator)
- [ ] Day/week/range views
- [ ] Real-time current location status
- [ ] Visit filtering (type, duration, time)
- [ ] Summary statistics
- [ ] Google Maps integration

### Nice-to-Have Features (Phase 4+)

- [ ] Pattern detection (routine places, commute patterns)
- [ ] Anomaly detection (unusual locations/times)
- [ ] Place recommendations based on history
- [ ] Export to GPX/KML formats
- [ ] Photo tagging by location
- [ ] Weather integration for visits
- [ ] Advanced analytics dashboard

---

## 🗺️ Migration Phases

### **Phase 1: Infrastructure Setup** ✅ COMPLETE

**Status**: Complete (as of initial setup)

**Deliverables**:
- [x] Project structure created
- [x] Database schema designed (5 tables)
- [x] SQLAlchemy models created
- [x] Docker configuration defined
- [x] Alembic migrations setup
- [x] Health check router implemented
- [x] Comprehensive documentation

**Next**: Fix import errors and get service running

---

### **Phase 2: Core API Implementation** 🔄 IN PROGRESS

**Goal**: Implement basic CRUD operations for all entities

**Tasks**:

1. **Fix Router Import Errors** (Priority 1)
   - [ ] Create stub implementations for empty routers
   - [ ] Fix port conflict (change from 8003 to 8004)
   - [ ] Add services to docker-compose.unified.yml
   - [ ] Start location-postgres database
   - [ ] Run Alembic migrations
   - [ ] Verify health endpoint works

2. **Implement Places Router** (`api/routers/places.py`)
   - [ ] `GET /api/v1/places` - List places with pagination
   - [ ] `GET /api/v1/places/{id}` - Get place by ID
   - [ ] `POST /api/v1/places` - Create place
   - [ ] `PUT /api/v1/places/{id}` - Update place
   - [ ] `GET /api/v1/places/search` - Search by name/description
   - [ ] `GET /api/v1/places/nearby` - Search by coordinates + radius

3. **Implement Visits Router** (`api/routers/visits.py`)
   - [ ] `GET /api/v1/visits` - List visits with filtering
   - [ ] `GET /api/v1/visits/{id}` - Get visit by ID
   - [ ] `GET /api/v1/visits/current` - Get ongoing visits
   - [ ] `POST /api/v1/visits` - Create visit
   - [ ] `PATCH /api/v1/visits/{id}/end` - End visit
   - [ ] `GET /api/v1/visits/place/{place_id}` - Visits for place

4. **Implement Movements Router** (`api/routers/movements.py`)
   - [ ] `GET /api/v1/movements` - List movements with filtering
   - [ ] `GET /api/v1/movements/{id}` - Get movement by ID
   - [ ] `POST /api/v1/movements` - Create movement

5. **Implement Location Data Router** (`api/routers/location_data.py`)
   - [ ] `GET /api/v1/location-data/points` - Query GPS points
   - [ ] `POST /api/v1/location-data/ingest` - Bulk GPS upload
   - [ ] `DELETE /api/v1/location-data/cleanup` - Remove old data

6. **Create CRUD Modules** (`core/crud/`)
   - [ ] `place_crud.py` - Place database operations
   - [ ] `visit_crud.py` - Visit database operations
   - [ ] `movement_crud.py` - Movement database operations
   - [ ] `location_data_crud.py` - GPS point operations
   - [ ] `checkin_crud.py` - Check-in operations

**Code to Extract**:
- `myndy-ai/memory/crud/place_crud.py` → adapt for new schema
- `myndy-ai/memory/crud/location_visit_crud.py` → adapt for new schema

**Estimated Time**: 3-5 days

---

### **Phase 3: Ingestion Pipeline** 🔜 NEXT

**Goal**: Download and process location data from myndy-api (Heroku)

**Tasks**:

1. **GPS Download Script** (`scripts/ingest_gps.py`)
   - [ ] OAuth2 authentication with myndy-api
   - [ ] Incremental download logic
   - [ ] Deduplication
   - [ ] Batch processing
   - [ ] Progress tracking
   - [ ] Store in `location_data` table

2. **Check-in Sync Script** (`scripts/ingest_checkins.py`)
   - [ ] Download check-ins from myndy-api
   - [ ] Match to existing places
   - [ ] Create place if not exists
   - [ ] Store in `checkins` table

3. **Processing Pipeline** (`scripts/process_locations.py`)
   - [ ] Trigger clustering
   - [ ] Trigger enrichment
   - [ ] Trigger visit detection
   - [ ] Trigger movement tracking

**Code to Extract**:
- `myndy-ai/ingestion/locations/comprehensive_gps_download.py` → `scripts/ingest_gps.py`
- `myndy-ai/ingestion/locations/location_export.py` → OAuth logic
- Adapt `sync-location-data.sh` → call new ingestion scripts

**Estimated Time**: 3-4 days

---

### **Phase 4: Processing Algorithms** 🔜 UPCOMING

**Goal**: Implement location intelligence algorithms

**Tasks**:

1. **Clustering Engine** (`core/analysis/clustering.py`)
   - [ ] Spatial-temporal clustering (DBSCAN-like)
   - [ ] Haversine distance calculations
   - [ ] Significance scoring
   - [ ] iPhone GPS optimization
   - [ ] Cluster consolidation

2. **Enrichment Service** (`core/analysis/enrichment.py`)
   - [ ] Nominatim integration
   - [ ] Grid-based caching
   - [ ] Rate limiting (1 req/sec)
   - [ ] Place type classification
   - [ ] Business category mapping

3. **Visit Detection** (`core/analysis/visit_detection.py`)
   - [ ] Temporal grouping
   - [ ] Gap detection (60-min threshold)
   - [ ] Movement metrics extraction
   - [ ] Transport mode detection
   - [ ] Check-in integration
   - [ ] Drive-through detection

4. **Movement Tracking** (`core/analysis/movement_tracking.py`)
   - [ ] Distance calculation
   - [ ] Speed analysis
   - [ ] Transport classification
   - [ ] Directional analysis
   - [ ] Route descriptions

5. **Analysis Router** (`api/routers/analysis.py`)
   - [ ] `POST /api/v1/analysis/process` - Trigger processing
   - [ ] `GET /api/v1/analysis/timeline` - Get comprehensive timeline
   - [ ] `GET /api/v1/analysis/patterns` - Detect patterns

**Code to Extract**:
- `myndy-ai/ingestion/locations/location_ingest.py` → Split into modules:
  - `LocationClusterer` class → `core/analysis/clustering.py`
  - `PlaceLearner` class → `core/analysis/enrichment.py`
  - Visit detection logic → `core/analysis/visit_detection.py`
  - Movement detection logic → `core/analysis/movement_tracking.py`
- `myndy-ai/ingestion/locations/production_location_pipeline.py` → `core/analysis/pipeline.py`

**Estimated Time**: 5-7 days

---

### **Phase 5: Data Migration** 🔜 UPCOMING

**Goal**: Migrate existing location data from myndy-ai to myndy-location

**Tasks**:

1. **Migration Script** (`scripts/migrate_from_myndy_ai.py`)
   - [ ] Export GPS points from myndy-ai PostgreSQL
   - [ ] Export places from myndy-ai PostgreSQL + Qdrant
   - [ ] Export visits from myndy-ai PostgreSQL
   - [ ] Export movements from myndy-ai PostgreSQL
   - [ ] Transform data to new schema
   - [ ] Import into myndy-location PostgreSQL
   - [ ] Verify data integrity
   - [ ] Generate statistics

2. **Data Validation**
   - [ ] Compare record counts
   - [ ] Verify place deduplication
   - [ ] Check visit timeline continuity
   - [ ] Validate GPS point accuracy

**Expected Migration Volume**:
- GPS points: ~10,000+ records
- Places: ~50-100 places
- Visits: ~500+ visits
- Movements: ~300+ movements
- Check-ins: ~50+ check-ins

**Estimated Time**: 2-3 days

---

### **Phase 6: API Client for myndy-ai** 🔜 UPCOMING

**Goal**: Create client library for myndy-ai to query myndy-location

**Tasks**:

1. **Client Library** (`myndy-ai/ingestion/shared/location_intelligence_client.py`)
   - [ ] HTTP client with retry logic
   - [ ] API key authentication
   - [ ] Methods for all endpoints
   - [ ] Error handling
   - [ ] Response parsing

2. **Client Methods**:
   ```python
   class LocationIntelligenceClient:
       def get_timeline(self, date: str) -> List[Dict]
       def get_current_visit(self) -> Optional[Dict]
       def search_places(self, query: str) -> List[Dict]
       def get_visits_by_date_range(self, start: str, end: str) -> List[Dict]
       def get_place_by_id(self, place_id: str) -> Dict
       def get_nearby_places(self, lat: float, lng: float, radius: int) -> List[Dict]
   ```

**Estimated Time**: 1-2 days

---

### **Phase 7: Myndy-AI Integration** 🔜 UPCOMING

**Goal**: Update myndy-ai to use myndy-location API instead of direct CRUD

**Tasks**:

1. **Update Location Tools** (`myndy-ai/tools/location/`)
   - [ ] Replace CRUD imports with `LocationIntelligenceClient`
   - [ ] Update tool logic to use API
   - [ ] Test tool functionality

2. **Update API Routers** (`myndy-ai/api/routers/`)
   - [ ] Proxy location requests to myndy-location
   - [ ] Update response formats if needed
   - [ ] Maintain backward compatibility

3. **Notable Places in Myndy-AI**
   - [ ] Keep only "notable places" (home, work, favorites)
   - [ ] Add `location_intelligence_place_id` reference field
   - [ ] Update place model to store reference
   - [ ] Query myndy-location for context

4. **Remove Direct CRUD**
   - [ ] Remove location CRUD operations
   - [ ] Keep place CRUD for notable places only
   - [ ] Update imports across codebase

**Files to Update**:
- `myndy-ai/tools/location/get_location_tool.py`
- `myndy-ai/tools/location/save_location_history_tool.py`
- `myndy-ai/api/routers/location_*.py`
- `myndy-ai/memory/place_model.py` (add reference field)

**Estimated Time**: 3-4 days

---

### **Phase 8: Myndy-Coordinator Compatibility** 🔜 UPCOMING

**Goal**: Ensure myndy-coordinator timeline features continue working

**Tasks**:

1. **API Compatibility**
   - [ ] Verify all coordinator API calls work
   - [ ] Match response formats exactly
   - [ ] Test date range queries
   - [ ] Test filtering parameters
   - [ ] Test current visit endpoint

2. **Update Coordinator Configuration**
   - [ ] Point coordinator to myndy-location for location data
   - [ ] Keep myndy-ai for memory/AI features
   - [ ] Update environment variables

3. **End-to-End Testing**
   - [ ] Test timeline visualization
   - [ ] Test date navigation
   - [ ] Test filtering
   - [ ] Test real-time current location
   - [ ] Test summary statistics
   - [ ] Test map integration

**Required API Endpoints** (must match myndy-ai format):
- `GET /api/v1/location-visits/visits`
- `GET /api/v1/location-visits/visits/current`
- `GET /api/v1/location-visits/visits/{id}`
- `POST /api/v1/location-visits/visits`
- `PATCH /api/v1/location-visits/visits/{id}/end`
- `GET /api/v1/location-timeline/current-status`
- `GET /api/v1/location-timeline/timeline/{date}`
- `GET /api/v1/location-timeline/range`
- `GET /api/v1/memory/places`
- `POST /api/v1/memory/places`

**Estimated Time**: 2-3 days

---

### **Phase 9: Cleanup & Deprecation** 🔜 FINAL

**Goal**: Remove deprecated location code from myndy-ai

**Tasks**:

1. **Remove Old Code**
   - [ ] Delete `myndy-ai/ingestion/locations/` directory
   - [ ] Delete `myndy-ai/memory/location_model.py`
   - [ ] Delete `myndy-ai/memory/location_visit_model.py`
   - [ ] Delete `myndy-ai/memory/location_movement_model.py`
   - [ ] Delete `myndy-ai/memory/crud/location_*.py`
   - [ ] Delete location routers (keep proxies if needed)

2. **Update Documentation**
   - [ ] Update myndy-ai README (remove location features)
   - [ ] Update myndy-location README (mark as production)
   - [ ] Update architecture docs
   - [ ] Update API documentation
   - [ ] Update deployment guides

3. **Archive Migrations**
   - [ ] Archive old location-related Alembic migrations
   - [ ] Document migration history

4. **Final Testing**
   - [ ] Full regression testing
   - [ ] Performance testing
   - [ ] Load testing

**Estimated Time**: 2-3 days

---

## 🗂️ Code Mapping: myndy-ai → myndy-location

### Ingestion Code

| myndy-ai | myndy-location | Purpose |
|----------|----------------|---------|
| `ingestion/locations/comprehensive_gps_download.py` | `scripts/ingest_gps.py` | GPS download from Heroku |
| `ingestion/locations/location_export.py` | `scripts/ingest_gps.py` | OAuth & API client |
| `ingestion/locations/simple_enrichment_service.py` | `core/analysis/enrichment.py` | Reverse geocoding |
| Check-in sync (not found) | `scripts/ingest_checkins.py` | Check-in download |

### Processing Code

| myndy-ai | myndy-location | Purpose |
|----------|----------------|---------|
| `ingestion/locations/location_ingest.py::LocationClusterer` | `core/analysis/clustering.py` | Place detection |
| `ingestion/locations/location_ingest.py::PlaceLearner` | `core/analysis/enrichment.py` | Place enrichment |
| `ingestion/locations/location_ingest.py::MovementDetector` | `core/analysis/movement_tracking.py` | Movement analysis |
| `ingestion/locations/production_location_pipeline.py` | `core/analysis/pipeline.py` | Main orchestration |
| Visit detection logic (in pipeline) | `core/analysis/visit_detection.py` | Visit timeline |

### Database Models

| myndy-ai | myndy-location | Changes |
|----------|----------------|---------|
| `memory/location_model.py::LocationPoint` | `database/models.py::LocationData` | Simplified schema |
| `memory/place_model.py::Place` | `database/models.py::Place` | Added pgvector embedding |
| `memory/location_visit_model.py::LocationVisit` | `database/models.py::Visit` | Simplified schema |
| `memory/location_movement_model.py` (not found) | `database/models.py::Movement` | New implementation |
| N/A | `database/models.py::Checkin` | New table |

### CRUD Operations

| myndy-ai | myndy-location | Changes |
|----------|----------------|---------|
| `memory/crud/location_crud.py` | `core/crud/location_data_crud.py` | PostgreSQL only (no Qdrant) |
| `memory/crud/place_crud.py` | `core/crud/place_crud.py` | PostgreSQL + pgvector |
| `memory/crud/location_visit_crud.py` | `core/crud/visit_crud.py` | PostgreSQL only |
| `memory/crud/location_movement_crud.py` (not found) | `core/crud/movement_crud.py` | New implementation |
| N/A | `core/crud/checkin_crud.py` | New implementation |

### API Routers

| myndy-ai | myndy-location | Changes |
|----------|----------------|---------|
| `api/routers/location_router.py` | `api/routers/location_data.py` | Renamed, restructured |
| `api/routers/location_visits_router.py` | `api/routers/visits.py` | Renamed, simplified |
| `api/routers/location_timeline_router.py` | `api/routers/analysis.py` | Merged into analysis |
| N/A | `api/routers/places.py` | New dedicated router |
| N/A | `api/routers/movements.py` | New dedicated router |

---

## 🔌 API Compatibility Matrix

### Required Endpoints for myndy-coordinator

| Endpoint | Priority | Status | Notes |
|----------|----------|--------|-------|
| `GET /api/v1/location-visits/visits` | Critical | ❌ To-do | List visits with filtering |
| `GET /api/v1/location-visits/visits/current` | Critical | ❌ To-do | Current ongoing visits |
| `GET /api/v1/location-visits/visits/{id}` | High | ❌ To-do | Visit details |
| `POST /api/v1/location-visits/visits` | High | ❌ To-do | Create visit |
| `PATCH /api/v1/location-visits/visits/{id}/end` | High | ❌ To-do | End visit |
| `GET /api/v1/location-timeline/current-status` | Critical | ❌ To-do | Real-time status |
| `GET /api/v1/location-timeline/timeline/{date}` | Critical | ❌ To-do | Day timeline |
| `GET /api/v1/location-timeline/range` | High | ❌ To-do | Date range timeline |
| `GET /api/v1/memory/places` | High | ❌ To-do | List places |
| `POST /api/v1/memory/places` | Medium | ❌ To-do | Create place |
| `GET /api/v1/health` | High | ✅ Done | Health check |

### Request/Response Format Examples

**GET /api/v1/location-visits/visits**

Query Parameters:
```
?start_date=2025-11-14&end_date=2025-11-14&limit=100&offset=0
```

Response:
```json
{
  "success": true,
  "visits": [
    {
      "id": "visit_uuid",
      "place_id": "place_uuid",
      "place_name": "Starbucks",
      "arrival_time": "2025-11-14T09:30:00Z",
      "departure_time": "2025-11-14T10:15:00Z",
      "duration_minutes": 45,
      "visit_category": "cafe",
      "confidence_score": 0.92,
      "is_ongoing": false,
      "day_of_week": "Thursday",
      "time_of_day": "morning",
      "duration_category": "short"
    }
  ],
  "total": 10,
  "page": 1,
  "limit": 100
}
```

**GET /api/v1/location-visits/visits/current**

Response:
```json
{
  "success": true,
  "current_visit": {
    "id": "visit_uuid",
    "place_name": "Home",
    "arrival_time": "2025-11-14T12:00:00Z",
    "duration_minutes": 150,
    "is_ongoing": true,
    "confidence_score": 0.95
  }
}
```

**GET /api/v1/location-timeline/current-status**

Response:
```json
{
  "success": true,
  "current_status": {
    "movement_state": "stationary",
    "current_place": {
      "name": "Home",
      "latitude": 47.606209,
      "longitude": -122.332071
    },
    "duration_at_location": "2h 30m",
    "confidence": 0.95,
    "last_movement_time": "2025-11-14T12:00:00Z"
  }
}
```

---

## 🗄️ Database Migration Strategy

### 1. Export from myndy-ai

**PostgreSQL Tables**:
- `location_data` → `location_data` (GPS points)
- `places` → `places` (with transformations)
- `location_visits` → `visits` (with transformations)

**Qdrant Collections**:
- `places` → Extract embeddings, store in PostgreSQL `places.embedding`

### 2. Data Transformations

**Place Model**:
```python
# myndy-ai (PostgreSQL + Qdrant)
{
    "id": "qdrant_place_id",
    "name": "...",
    "coordinates": {...},
    "qdrant_id": "uuid"
}

# myndy-location (PostgreSQL only)
{
    "id": "uuid",
    "name": "...",
    "latitude": float,
    "longitude": float,
    "embedding": vector(384)  # from Qdrant
}
```

**Visit Model**:
```python
# myndy-ai
{
    "id": "visit_id",
    "place_id": "place_id",
    "arrival_time": "...",
    "metrics": {...}
}

# myndy-location (flattened)
{
    "id": "visit_id",
    "place_id": "place_id",
    "arrival_time": "...",
    "avg_speed_ms": float,  # extracted from metrics
    "max_speed_ms": float,
    ...
}
```

### 3. Migration Script Flow

```
┌─────────────────────────────────────────────┐
│  1. Export from myndy-ai                    │
│     - Query PostgreSQL                      │
│     - Query Qdrant for embeddings           │
│     - Save to intermediate JSON             │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  2. Transform Data                          │
│     - Convert IDs                           │
│     - Flatten nested structures             │
│     - Extract embeddings                    │
│     - Validate schemas                      │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  3. Import to myndy-location                │
│     - Insert into location_data             │
│     - Insert into places (with embeddings)  │
│     - Insert into visits                    │
│     - Insert into movements                 │
│     - Insert into checkins                  │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  4. Validate                                │
│     - Compare record counts                 │
│     - Verify data integrity                 │
│     - Check relationships                   │
│     - Generate statistics                   │
└─────────────────────────────────────────────┘
```

---

## 🚀 Deployment Strategy

### Development Environment

```yaml
services:
  myndy-location:
    ports: 8004:8000  # Changed from 8003 to avoid conflict
  location-postgres:
    ports: 5435:5432
```

### Production Environment

1. **Deploy myndy-location service**
2. **Migrate existing data**
3. **Update myndy-coordinator to point to myndy-location**
4. **Update myndy-ai to use LocationIntelligenceClient**
5. **Verify all features work**
6. **Remove old location code from myndy-ai**

---

## 📈 Success Metrics

### Phase 2-3 (Core API + Ingestion)
- [ ] All API endpoints returning valid responses
- [ ] GPS download working from Heroku
- [ ] Check-in sync working
- [ ] Data stored in PostgreSQL

### Phase 4 (Processing)
- [ ] Places detected from GPS clusters
- [ ] Visits created automatically
- [ ] Movements tracked between visits
- [ ] Reverse geocoding working

### Phase 5 (Migration)
- [ ] 100% of existing data migrated
- [ ] No data loss or corruption
- [ ] All relationships maintained

### Phase 6-8 (Integration)
- [ ] myndy-coordinator timeline fully functional
- [ ] myndy-ai location tools working via API
- [ ] No performance degradation
- [ ] API response times <200ms (95th percentile)

### Phase 9 (Cleanup)
- [ ] Old code removed from myndy-ai
- [ ] Documentation updated
- [ ] All tests passing

---

## ⚠️ Risks & Mitigation

### Risk 1: Data Loss During Migration
**Mitigation**:
- Dry-run mode for migration script
- Keep myndy-ai data until verification complete
- Automated validation checks
- Rollback plan

### Risk 2: API Incompatibility
**Mitigation**:
- Match myndy-ai response formats exactly
- Comprehensive integration tests
- Gradual rollout (dev → staging → prod)

### Risk 3: Performance Degradation
**Mitigation**:
- Proper database indexing (BRIN, BTree, IVFFlat)
- Query optimization
- Caching layer (Redis)
- Load testing before production

### Risk 4: Breaking myndy-coordinator
**Mitigation**:
- Test all coordinator features before deploying
- Feature flag for switching between myndy-ai and myndy-location
- Quick rollback capability

---

## 📅 Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Infrastructure | ✅ Complete | None |
| Phase 2: Core API | 3-5 days | Phase 1 |
| Phase 3: Ingestion | 3-4 days | Phase 2 |
| Phase 4: Processing | 5-7 days | Phase 3 |
| Phase 5: Migration | 2-3 days | Phase 4 |
| Phase 6: API Client | 1-2 days | Phase 2 |
| Phase 7: myndy-ai Integration | 3-4 days | Phase 6 |
| Phase 8: Coordinator Compatibility | 2-3 days | Phase 7 |
| Phase 9: Cleanup | 2-3 days | Phase 8 |

**Total Estimated Time**: 3-4 weeks (15-20 working days)

---

## 🎯 Next Immediate Actions

### This Week (Week 1)

1. **Day 1-2: Fix Service Startup**
   - Create stub routers
   - Fix port conflict
   - Add to docker-compose
   - Start services
   - Verify health endpoint

2. **Day 3-5: Implement Core Routers**
   - Places router (basic CRUD)
   - Visits router (basic CRUD)
   - Create corresponding CRUD modules

### Next Week (Week 2)

1. **GPS Ingestion**
   - Implement ingest_gps.py
   - Test download from Heroku
   - Verify data storage

2. **Start Processing**
   - Implement clustering.py
   - Implement enrichment.py

---

## 📚 Additional Resources

- **Geocaching API**: https://staging.api.groundspeak.com/api-docs/index (v1 API)
- **Nominatim API**: https://nominatim.org/release-docs/latest/api/Overview/
- **pgvector**: https://github.com/pgvector/pgvector
- **FastAPI**: https://fastapi.tiangolo.com/
- **Alembic**: https://alembic.sqlalchemy.org/

---

**Document Version**: 1.0
**Last Updated**: 2025-11-14
**Next Review**: After Phase 2 completion
