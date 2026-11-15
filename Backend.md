# Backend Implementation Guide
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Date:** 2026-11-15

> This document is the **implementation reference** for the backend developer.  
> It tells you: what to build, in what order, and what each file should contain.

---

## 1. Build Order (Strict)

```
Step 1: Project skeleton + config
Step 2: Database models + migrations
Step 3: Pydantic schemas
Step 4: Database layer (connection + session)
Step 5: Auth (JWT)
Step 6: Classification Engine ← MOST IMPORTANT UNIT
Step 7: Vitals Simulator
Step 8: REST API routes
Step 9: WebSocket + Redis pub/sub
Step 10: NASA Integration layer
Step 11: Alert Router
Step 12: Report Generator
Step 13: Tests
Step 14: Deploy
```

---

## 2. File-by-File Implementation Guide

---

### `app/main.py`
**Purpose:** FastAPI application factory. Registers all routers, starts background tasks.

```python
# What it must do:
# 1. Create FastAPI app with metadata (title, description, version)
# 2. Configure CORS (allow all origins for hackathon)
# 3. Include all routers with /api prefix
# 4. Register /ws/mission-feed WebSocket endpoint
# 5. On startup: init DB tables, start simulator background task
# 6. On shutdown: stop simulator, close DB connections
# 7. GET /health endpoint
```

---

### `app/config.py`
**Purpose:** Pydantic Settings model — reads from `.env` file.

```python
# Fields needed:
# APP_ENV, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
# NASA_API_KEY
# DATABASE_URL
# REDIS_URL
# SIMULATOR_TICK_SECONDS (default: 5)
# DEMO_MODE (default: False)

# Usage:
# from app.config import settings
# settings.NASA_API_KEY
```

---

### `app/database.py`
**Purpose:** Async SQLAlchemy engine + session factory + Base model.

```python
# What it must do:
# 1. Create async engine from settings.DATABASE_URL
# 2. Create AsyncSessionLocal factory
# 3. Define Base = declarative_base()
# 4. get_db() dependency — yields session, closes on exit
# 5. init_db() — called on startup, creates all tables
```

---

### `app/models/` — ORM Models

#### `app/models/crew.py`
```python
# CrewMember model:
# id: UUID (PK, server_default=gen_random_uuid())
# name: String(100)
# role: String(50)
# responder_name: String(100)
# created_at: DateTime (default=utcnow)
# 
# Relationships:
# vitals: List["VitalsReading"] (backref)
# events: List["HealthEvent"] (backref)
```

#### `app/models/vitals.py`
```python
# VitalsReading model:
# id: UUID (PK)
# crew_member_id: UUID (FK → crew_members.id)
# timestamp: DateTime
# heart_rate: Float
# spo2: Float
# temperature: Float
# radiation_dose: Float
# sleep_hours: Float
# stress_index: Float
# status: String(20)        ← classified status
# triggered_by: String(50)  ← which vital triggered it
# raw_payload: JSON         ← full original payload
```

#### `app/models/events.py`
```python
# HealthEvent model:
# id: UUID (PK)
# crew_member_id: UUID (FK)
# event_type: String(30)      ← STATUS_CHANGE / ALERT_SENT / RECOVERY
# from_status: String(20)
# to_status: String(20)
# triggered_by: String(50)
# guidance_text: Text
# responder_name: String(100)
# acknowledged: Boolean (default=False)
# acknowledged_by: String(100)
# acknowledged_at: DateTime
# created_at: DateTime
```

#### `app/models/reports.py`
```python
# MissionReport model:
# id: UUID (PK)
# generated_at: DateTime
# mission_day: Integer
# total_events: Integer
# emergency_count: Integer
# anomaly_count: Integer
# summary_text: Text
# pdf_filename: String(255)
# report_data: JSON
```

---

### `app/schemas/` — Pydantic Schemas

One schema file per domain. Each file has:
- `Base` schema (shared fields)
- `Create` schema (POST request body)
- `Response` schema (what API returns)

**Example — `app/schemas/vitals.py`:**
```python
class VitalsIngest(BaseModel):
    crew_member_id: UUID
    heart_rate: float = Field(ge=0, le=300)
    spo2: float = Field(ge=0, le=100)
    temperature: float = Field(ge=30, le=45)
    radiation_dose: float = Field(ge=0)
    sleep_hours: float = Field(ge=0, le=24)
    stress_index: float = Field(ge=0.0, le=1.0)

class VitalsResponse(BaseModel):
    status: str
    triggered_by: str | None
    reading_id: UUID
    class Config:
        from_attributes = True
```

---

### `app/core/classification.py` ⭐ MOST IMPORTANT

**Purpose:** The brain. Stateless pure function.

```python
# WHAT TO BUILD:
#
# 1. THRESHOLDS dict — defines ranges for each vital at each level
#
# 2. check_vital(vital_name, value) → (status, vital_name) | None
#    Returns worst status for a single vital
#
# 3. classify_vitals(reading: VitalsIngest) → ClassificationResult
#    Checks all 6 vitals, returns worst overall status
#
# 4. ClassificationResult dataclass:
#    status: str
#    triggered_by: str | None
#    triggered_value: float | None
#    threshold_exceeded: float | None
#
# RULES:
# - Emergency always overrides everything
# - If multiple vitals at same level, return first triggered
# - Must be 100% testable with no DB/Redis dependencies
# - Import NOTHING except standard library + pydantic
```

---

### `app/core/simulator.py`

**Purpose:** Generate realistic astronaut vitals over time.

```python
# WHAT TO BUILD:
#
# 1. CrewBaseline dataclass — per-crew member normal ranges
#    (Commander: HR 65-75, Pilot: HR 60-72, etc.)
#
# 2. VitalsState class — tracks current simulated state per crew
#    Uses numpy random walk for realistic drift
#
# 3. generate_tick(crew_id) → VitalsIngest
#    Applies:
#    a. Normal drift (small random delta from current)
#    b. DONKI radiation multiplier (from Redis)
#    c. Active scenario injection (from Redis key)
#
# 4. SCENARIOS dict — pre-scripted anomaly scenarios:
#    "radiation_spike": radiation → 520+ μSv/hr over 3 ticks
#    "low_oxygen": spo2 → drops to 86% over 5 ticks
#    "cardiac_event": HR → spikes to 160+ in 2 ticks
#    "high_fever": temp → rises to 39.5 over 8 ticks
#    "fatigue_accumulation": sleep → 4.5, stress → 0.75
#    "full_recovery": all → nominal over 10 ticks
#
# 5. run_simulator(tick_seconds) — asyncio loop
#    for each crew member → generate_tick → POST /api/vitals/ingest
#    runs as FastAPI startup background task
```

---

### `app/core/alert_router.py`

**Purpose:** Given a classification result, return appropriate guidance text and responder info.

```python
# GUIDANCE TEMPLATES dict:
# Key: (triggered_by, status)
# Value: guidance string with {responder} placeholder
#
# Example entries:
GUIDANCE = {
    ("radiation_dose", "EMERGENCY"): 
        "⚠️ RADIATION ALERT: Seek shielded compartment immediately. "
        "Mission control and {responder} have been notified. "
        "Do NOT exit shielded area until clearance given.",
    
    ("spo2", "ANOMALY"):
        "Oxygen saturation critically low. Activate supplemental O₂ system. "
        "Alert {responder} immediately. Check suit integrity.",
    
    ("heart_rate", "EMERGENCY"):
        "Cardiac emergency detected. Lie flat, reduce all activity immediately. "
        "{responder} has been alerted. Administer emergency cardiac protocol.",
    
    # ... 20+ entries covering all vital + status combinations
}

# route_alert(result: ClassificationResult, responder_name: str) → str
# Returns formatted guidance text
```

---

### `app/api/routes/websocket.py`

**Purpose:** WebSocket connection manager + Redis subscriber.

```python
# WHAT TO BUILD:
#
# 1. ConnectionManager class:
#    - connect(websocket) → str (connection_id)
#    - disconnect(connection_id)
#    - broadcast(message: dict)
#
# 2. redis_subscriber() — asyncio task
#    Subscribes to "mission:feed" Redis channel
#    On message: ConnectionManager.broadcast(message)
#
# 3. /ws/mission-feed WebSocket route:
#    - Accept connection
#    - Register with ConnectionManager
#    - Send CONNECTED confirmation
#    - Keep alive until disconnect
#    - On disconnect: unregister
```

---

### `app/integrations/nasa_client.py`

**Purpose:** Async NASA API client with Redis caching.

```python
# CLASS: NASAClient
#
# async def get_solar_flares(days_back=1) → list[dict]
#   Cache key: "nasa:donki:flr:{date}"
#   TTL: 900 (15 min)
#
# async def get_epic_image() → dict
#   Cache key: "nasa:epic:latest"
#   TTL: 3600 (1 hour)
#
# async def get_apod() → dict
#   Cache key: "nasa:apod:{date}"
#   TTL: 86400 (24 hours)
#
# async def get_neo_feed() → dict
#   Cache key: "nasa:neo:{date}"
#   TTL: 3600 (1 hour)
#
# async def get_radiation_multiplier() → float
#   Calls get_solar_flares()
#   Maps worst flare class → multiplier
#   Stores in Redis: "simulator:radiation_multiplier"
```

---

### `app/core/report_generator.py`

**Purpose:** Query events from DB, build PDF.

```python
# async def generate_mission_report(session, mission_day) → MissionReport
#
# Steps:
# 1. Query last 24hrs health_events for all crew
# 2. Count by status level
# 3. Build narrative summary (string)
# 4. Get NASA space weather context from Redis cache
# 5. ReportLab: create PDF with:
#    - Header: CrewWatch + mission day + generated timestamp
#    - Section 1: Crew Status Summary (table)
#    - Section 2: Event Timeline (sorted by time)
#    - Section 3: Space Weather Context (DONKI data)
#    - Section 4: Recommendations
# 6. Save PDF to /tmp/report_day_{n}.pdf
# 7. INSERT mission_reports record
# 8. Return MissionReport object
```

---

## 3. Environment & Running

```bash
# Setup
cd d:\Nasa_2026\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Database tables
alembic upgrade head

# Seed 3 crew members
python -m app.scripts.seed_data

# Run server
uvicorn app.main:app --reload --port 8000

# Access
# Swagger: http://localhost:8000/docs
# Health:  http://localhost:8000/health
```

---

## 4. Development Checklist

### Day 1 — Morning
- [ ] `app/main.py` — FastAPI app skeleton
- [ ] `app/config.py` — Settings from .env
- [ ] `app/database.py` — Neon connection
- [ ] `app/models/` — All 4 ORM models
- [ ] `alembic init` + first migration
- [ ] `alembic upgrade head` — tables in Neon ✅
- [ ] `app/schemas/` — All Pydantic schemas
- [ ] `app/api/routes/auth.py` — JWT login
- [ ] `app/api/routes/crew.py` — CRUD
- [ ] Seed script — 3 crew members

### Day 1 — Afternoon
- [ ] `app/core/classification.py` — ENGINE COMPLETE + TESTED
- [ ] `app/core/simulator.py` — baseline vitals working
- [ ] `POST /api/vitals/ingest` — full pipeline working
- [ ] `app/integrations/redis_client.py` — Upstash connected
- [ ] `app/api/routes/websocket.py` — WS feed live
- [ ] Test: simulator → classify → WebSocket → browser console ✅

### Day 2 — Morning
- [ ] `app/core/alert_router.py` — all guidance templates
- [ ] `app/api/routes/alerts.py` — CRUD + acknowledge
- [ ] `app/integrations/nasa_client.py` — DONKI + EPIC + APOD
- [ ] `app/api/routes/nasa.py` — proxy routes
- [ ] `POST /api/simulator/inject` — 6 scenarios working
- [ ] Test: inject radiation_spike → EMERGENCY → alert → WebSocket ✅

### Day 2 — Afternoon
- [ ] `app/core/report_generator.py` — PDF generation
- [ ] `app/api/routes/reports.py` — generate + download
- [ ] Dockerfile written
- [ ] Push to GitHub
- [ ] Render deploy working
- [ ] UptimeRobot configured
- [ ] All Swagger docs clean
- [ ] Full demo rehearsed ✅
