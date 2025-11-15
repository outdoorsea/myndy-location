# Location Intelligence Service - Change Log

## 2025-11-14 - Comprehensive Analysis & Migration Planning

### Comprehensive Codebase Analysis
- **myndy-ai exploration**: Analyzed all location ingestion and processing code
  - 1,617 lines in production_location_pipeline.py
  - 1,939 lines in location_ingest.py
  - 561 lines in location_export.py
  - 300+ lines in comprehensive_gps_download.py
  - Complete understanding of clustering, enrichment, visit detection, and movement tracking

- **myndy-coordinator exploration**: Analyzed timeline features and UI
  - 1,750+ lines in location_timeline.html
  - Full-featured timeline with date navigation, filtering, real-time updates
  - Identified 10+ critical features to preserve
  - Documented all API endpoints required for compatibility

### Documentation Created
- **MIGRATION_PLAN.md**: Comprehensive 500+ line migration plan
  - 9 detailed phases with task breakdowns
  - Code mapping from myndy-ai to myndy-location
  - API compatibility matrix
  - Database migration strategy
  - Timeline: 3-4 weeks estimated
  - Success metrics and risk mitigation

### Key Findings

**Existing Functionality Discovered**:
1. Smart incremental GPS download from Heroku myndy-api
2. iPhone GPS optimization (point count over duration)
3. Spatial-temporal clustering (50m radius, 1min duration)
4. Multi-source reverse geocoding (Nominatim, Google Places, Foursquare)
5. Visit detection with 60-minute gap threshold
6. Movement tracking with transport classification
7. Drive-through detection
8. Check-in integration from iOS app
9. Full-featured timeline UI in coordinator
10. Real-time "current location" status

**Architecture Insights**:
- myndy-ai uses dual storage: PostgreSQL + Qdrant
- myndy-location will use PostgreSQL + pgvector only (simpler)
- myndy-coordinator expects specific API format (documented)
- Data flow: iOS → Heroku myndy-api → sync script → processing → storage

**Code to Extract** (identified):
- Clustering engine (LocationClusterer class)
- Enrichment service (PlaceLearner class)
- Movement detector (MovementDetector class)
- Visit detection logic (from pipeline)
- GPS download with OAuth2
- All CRUD operations (adapt for new schema)

### Current Status Assessment
- **Infrastructure**: ✅ Complete (Phase 1)
- **Router Implementation**: ❌ Empty files (causes import errors)
- **Service Status**: ❌ Not running (port conflict + import errors)
- **Data Migration**: ⏳ Not started
- **API Client**: ⏳ Not started

### Issues Identified
1. Port 8003 conflict with coordinator-dashboard
2. Router files are empty (0 bytes) causing import failures
3. Services not added to docker-compose.unified.yml
4. Virtual environment not created
5. main.py imports all routers before they're implemented

### Next Immediate Steps (Week 1)
1. Create stub router implementations
2. Resolve port conflict (change to 8004)
3. Add services to docker-compose.unified.yml
4. Start location-postgres database
5. Run Alembic migrations
6. Verify health endpoint works
7. Begin implementing places and visits routers

### Migration Phases Defined
- Phase 1: Infrastructure ✅ Complete
- Phase 2: Core API (3-5 days) - Next
- Phase 3: Ingestion Pipeline (3-4 days)
- Phase 4: Processing Algorithms (5-7 days)
- Phase 5: Data Migration (2-3 days)
- Phase 6: API Client (1-2 days)
- Phase 7: myndy-ai Integration (3-4 days)
- Phase 8: Coordinator Compatibility (2-3 days)
- Phase 9: Cleanup (2-3 days)

**Total Timeline**: 3-4 weeks for complete migration

---

## 2025-01-14 - Initial Project Setup

### Architecture Decision
- **Separation of Concerns**: Extract location intelligence from myndy-ai into dedicated service
- **Rationale**: Myndy-AI should focus on personal memory, not be a data warehouse for historic GPS data
- **Design**: Independent service with PostgreSQL+pgvector, communicates via API

### Project Structure Created
```
myndy-location/
├── api/
│   ├── main.py              # FastAPI application
│   ├── routers/             # API endpoint routers
│   │   ├── health.py       # Health check endpoints
│   │   ├── places.py       # Places API (TODO)
│   │   ├── visits.py       # Visits API (TODO)
│   │   ├── movements.py    # Movements API (TODO)
│   │   ├── location_data.py # GPS data API (TODO)
│   │   └── analysis.py     # Analysis API (TODO)
│   └── services/            # Business logic services
├── core/
│   ├── models/              # Pydantic models
│   ├── crud/                # Database operations
│   └── analysis/            # Location intelligence algorithms
│       ├── clustering.py   # Place detection (TODO)
│       ├── enrichment.py   # Reverse geocoding (TODO)
│       ├── visit_detection.py  # Visit timeline (TODO)
│       └── movement_tracking.py # Movement analysis (TODO)
├── database/
│   ├── connection.py        # Database session management
│   ├── models.py            # SQLAlchemy models
│   └── init.sql             # Database initialization
├── scripts/
│   ├── ingest_gps.py        # GPS ingestion (TODO)
│   ├── ingest_checkins.py   # Check-in sync (TODO)
│   └── migrate_data.py      # Data migration (TODO)
├── alembic/                 # Database migrations
│   ├── env.py              # Alembic environment
│   └── versions/           # Migration scripts
├── tests/                   # Test suite
├── Dockerfile               # Container configuration
├── docker-compose.addition.yml # Docker compose services
├── requirements.txt         # Python dependencies
├── alembic.ini              # Alembic configuration
└── README.md                # Project documentation
```

### Database Schema Designed
**5 Core Tables:**
1. `location_data` - Raw GPS points (timestamp, lat/lng, speed, course, accuracy)
2. `places` - Semantic places with vector embeddings for search
3. `visits` - Visit timeline with movement metrics
4. `movements` - Movement tracks between visits
5. `checkins` - Manual check-ins from iOS app

**Key Features:**
- PostgreSQL 16 with pgvector extension
- Vector embeddings (384 dimensions) for semantic place search
- Optimized indexes (BRIN for timestamps, spatial for coordinates)
- JSONB fields for flexible metadata storage

### Docker Configuration
- **Service**: myndy-location (port 8003)
- **Database**: location-postgres (port 5435)
- **Image**: pgvector/pgvector:pg16 for vector search support
- **Networks**: Connected to myndy-network
- **Volumes**: Persistent data storage for postgres

### API Design
**Planned Endpoints:**
- `/api/v1/health` - Health check ✅
- `/api/v1/status` - Service statistics ✅
- `/api/v1/location-data/*` - GPS data management
- `/api/v1/places/*` - Place discovery and search
- `/api/v1/visits/*` - Visit timeline queries
- `/api/v1/movements/*` - Movement track analysis
- `/api/v1/checkins/*` - Manual check-in sync
- `/api/v1/analysis/*` - Location intelligence processing

### Dependencies Installed
- **Web**: FastAPI, Uvicorn
- **Database**: SQLAlchemy, Alembic, psycopg2, pgvector
- **Location**: geopy, shapely, pyproj
- **HTTP**: httpx, requests
- **Caching**: redis
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code Quality**: black, flake8, mypy

### Files Created
1. `README.md` - Comprehensive architecture and setup documentation
2. `requirements.txt` - Python dependencies
3. `Dockerfile` - Container build configuration
4. `.env.example` - Environment variable template
5. `.gitignore` - Git ignore patterns
6. `api/main.py` - FastAPI application entry point
7. `database/connection.py` - Database connection management
8. `database/models.py` - SQLAlchemy models for all tables
9. `database/init.sql` - Database initialization script
10. `api/routers/health.py` - Health check endpoints
11. `alembic.ini` - Alembic configuration
12. `alembic/env.py` - Alembic environment setup
13. `docker-compose.addition.yml` - Docker services definition

### Integration Design with Myndy-AI
**Myndy-AI Changes Needed:**
1. Create `LocationIntelligenceClient` API client
2. Store only "notable places" (home, work, favorites)
3. Reference myndy-location data via `place_id`
4. Query for context: "where was I on Tuesday?"
5. Remove direct location intelligence CRUD operations

**Data Flow:**
```
iOS App → myndy-api → myndy-api-postgres
                            ↓
                    sync-location-data.sh
                            ↓
                  myndy-location postgres
                            ↓
                  Ingestion Pipeline:
                  • Clustering → places
                  • Visit detection → visits
                  • Movement tracking → movements
                            ↓
                  Location Intelligence API
                            ↑
                  Myndy-AI queries for context
```

### Next Steps
1. **Implement Router Endpoints** - Places, Visits, Movements, Location Data, Analysis
2. **Extract Location Code from Myndy-AI** - Copy models, CRUD, analysis algorithms
3. **Create Ingestion Scripts** - GPS sync, check-in sync, processing pipeline
4. **Data Migration** - Export from myndy-ai, import to myndy-location
5. **Test API Endpoints** - Integration testing
6. **Create Myndy-AI Client** - API client for myndy-ai to use
7. **Update Myndy-AI** - Replace direct CRUD with API calls
8. **Remove Old Code** - Clean up myndy-ai location intelligence code

### Design Decisions
- **Single-User Architecture**: No multi-tenancy, personal data warehouse
- **API-First**: All access through REST API, no direct database access
- **Vector Search**: pgvector for semantic place search
- **Separation**: Historic data in myndy-location, notable places in myndy-ai
- **PostgreSQL**: Relational + vector for best of both worlds

### Performance Optimizations
- BRIN indexes for time-series data (GPS points, visits)
- Spatial indexes for coordinate queries
- IVFFlat index for vector similarity search
- Redis caching for frequently accessed places
- Connection pooling (pool_size=10, max_overflow=20)

### Documentation
- **README.md**: 400+ lines comprehensive architecture guide
- **API Endpoints**: OpenAPI/Swagger at `/docs`
- **Database Schema**: Detailed table definitions
- **Integration Guide**: How myndy-ai should interact
- **Deployment Guide**: Docker setup and configuration

---

## Future Enhancements (Backlog)

### Code Extraction
- Copy clustering algorithms from myndy-ai
- Extract enrichment service (reverse geocoding)
- Port visit detection logic
- Migrate movement tracking code

### Ingestion Pipeline
- GPS download from myndy-api-postgres
- Check-in sync from myndy-api
- Scheduled processing (cron jobs)
- Incremental updates

### API Implementation
- Complete all router endpoints
- Add authentication middleware
- Implement caching layer
- Add rate limiting

### Testing
- Unit tests for all CRUD operations
- Integration tests for API endpoints
- Performance tests for queries
- Load tests for ingestion

### Monitoring
- Prometheus metrics export
- Grafana dashboards
- Alert configuration
- Log aggregation

### Documentation
- API usage examples
- Client library documentation
- Deployment procedures
- Troubleshooting guide
