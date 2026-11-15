# Data Flow Document
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Date:** 2026-11-15

---

## 1. Primary Data Flows

### Flow 1: Normal Vitals Tick (Every 5 Seconds)

```
┌─────────────────┐
│ Simulator Engine │
│ (Background Task)│
└────────┬─────────┘
         │ 1. Generate vitals for each crew member
         │    heart_rate, spo2, temp, radiation,
         │    sleep, stress — with realistic drift
         ▼
┌─────────────────┐
│ POST /vitals    │
│ /ingest         │
│ (FastAPI Route) │
└────────┬─────────┘
         │ 2. Validate payload (Pydantic)
         ▼
┌─────────────────────────┐
│ Classification Engine   │
│ classify_vitals(reading)│
└────────┬────────────────┘
         │ 3. Returns: status="NOMINAL", triggered_by=None
         ▼
┌─────────────────┐
│ PostgreSQL      │
│ (Neon.tech)     │
│ INSERT INTO     │
│ vitals_readings │
└────────┬─────────┘
         │ 4. Reading saved with status=NOMINAL
         ▼
┌─────────────────┐
│ Redis (Upstash) │
│ PUBLISH         │
│ "mission:feed"  │
└────────┬─────────┘
         │ 5. Message published to channel
         ▼
┌─────────────────┐
│ WebSocket       │
│ Manager         │
│ (subscriber)    │
└────────┬─────────┘
         │ 6. Broadcast VITALS_UPDATE to all connected clients
         ▼
┌──────────────────────────────────────┐
│  All Connected WebSocket Clients     │
│  • Crew Member PWA (phone)           │
│  • Mission Control Dashboard         │
└──────────────────────────────────────┘
```

---

### Flow 2: Status Change → Alert (Critical Path)

```
Simulator ticks → Classification Engine
                         │
                         │ status = "EMERGENCY"
                         │ triggered_by = "radiation_dose"
                         │ triggered_value = 540.0
                         ▼
              ┌────────────────────┐
              │ Compare with last  │
              │ known status       │
              │ (from Redis cache) │
              └────────┬───────────┘
                       │ Status CHANGED: NOMINAL → EMERGENCY
                       ▼
         ┌─────────────────────────────┐
         │   Parallel writes:          │
         │                             │
         │  1. INSERT vitals_readings  │
         │     (PostgreSQL)            │
         │                             │
         │  2. INSERT health_events    │
         │     event_type=ALERT        │
         │     from_status=NOMINAL     │
         │     to_status=EMERGENCY     │
         │     triggered_by=radiation  │
         │     guidance_text=(see      │
         │     Alert Guidance doc)     │
         │     (PostgreSQL)            │
         │                             │
         │  3. SET crew:{id}:status    │
         │     = "EMERGENCY"           │
         │     (Redis — update cache)  │
         └─────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   Alert Router              │
         │   pick_guidance(            │
         │     trigger="radiation",    │
         │     status="EMERGENCY"      │
         │   )                         │
         │   → "RADIATION ALERT:       │
         │      Seek shielded area     │
         │      immediately..."        │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   Redis PUBLISH             │
         │   channel: "mission:feed"   │
         │   message type: "ALERT"     │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   WebSocket Broadcast       │
         │   → Crew PWA: sees          │
         │     🔴 EMERGENCY banner     │
         │     + guidance text         │
         │   → Mission Control: sees   │
         │     alert with [ACKNOWLEDGE]│
         └─────────────────────────────┘
```

---

### Flow 3: Alert Acknowledgement

```
Mission Controller clicks [ACKNOWLEDGE]
         │
         ▼
POST /api/alerts/{alert_id}/acknowledge
{ "acknowledged_by": "Dr. James Liu" }
         │
         ▼
┌─────────────────────────────┐
│ UPDATE health_events SET    │
│   acknowledged = true       │
│   acknowledged_by = "..."   │
│   acknowledged_at = now()   │
│ WHERE id = alert_id         │
│ (PostgreSQL)                │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Redis PUBLISH               │
│ type: "ALERT_ACKNOWLEDGED"  │
│ alert_id, acknowledged_by   │
└─────────────────────────────┘
         │
         ▼
All clients see alert marked as acknowledged
```

---

### Flow 4: NASA DONKI → Simulator Feedback

```
┌────────────────────────┐
│ Background Task        │
│ (every 15 minutes)     │
└──────────┬─────────────┘
           │
           ▼
GET https://api.nasa.gov/DONKI/FLR
?startDate={today}&api_key={key}
           │
           ▼
┌────────────────────────┐       ┌─────────────────────┐
│ Parse response         │  YES  │ Cache in Redis       │
│ Any flares today?      │──────▶│ nasa:donki:latest    │
└──────────┬─────────────┘       │ TTL: 15 minutes      │
           │ YES                 └─────────────────────┘
           ▼
┌────────────────────────┐
│ Map flare class to     │
│ radiation multiplier:  │
│  M-class → 1.7x        │
│  X-class → 2.5x        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Redis SET              │
│ "simulator:radiation   │
│  _multiplier" = 1.7    │
│ TTL: 15 minutes        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Next Simulator Tick    │
│ reads multiplier       │
│ radiation_base × 1.7   │
│ → ANOMALY territory    │
│ → Alert fires          │
└────────────────────────┘
```

---

### Flow 5: Report Generation

```
POST /api/reports/generate
{ "mission_day": 1 }
         │
         ▼
FastAPI BackgroundTask.add_task(generate_report, mission_day=1)
         │ (returns 202 immediately — non-blocking)
         ▼
┌──────────────────────────────────────────┐
│ Report Generator (background)            │
│                                          │
│ 1. Query all health_events (past 24hrs)  │
│    PostgreSQL                            │
│                                          │
│ 2. Query NASA DONKI context              │
│    Redis cache                           │
│                                          │
│ 3. Build report_data dict:               │
│    {                                     │
│      mission_day: 1,                     │
│      crew_summary: [...],               │
│      events: [...],                      │
│      emergency_count: 2,                │
│      anomaly_count: 5,                  │
│      space_weather: {...},              │
│      generated_at: "..."                │
│    }                                     │
│                                          │
│ 4. ReportLab → generate PDF             │
│    save to /tmp/report_day1.pdf          │
│                                          │
│ 5. INSERT mission_reports               │
│    PostgreSQL                            │
│                                          │
│ 6. Redis PUBLISH                         │
│    type: "REPORT_READY"                 │
│    report_id: "uuid"                    │
└──────────────────────────────────────────┘
         │
         ▼
Client downloads: GET /api/reports/{id}/download
```

---

## 2. Data Models Flow

```
crew_members
    │
    ├── id ──────────────────────────────────────────────┐
    │                                                     │
    ▼                                                     ▼
vitals_readings                                   health_events
    │                                                     │
    │ crew_member_id (FK)                                 │ crew_member_id (FK)
    │ timestamp                                           │ event_type
    │ heart_rate                                          │ from_status → to_status
    │ spo2                                                │ triggered_by
    │ temperature                                         │ guidance_text
    │ radiation_dose                                      │ acknowledged
    │ sleep_hours                                         │ acknowledged_by
    │ stress_index                                        │ created_at
    │ status (classified)                                 │
    │ triggered_by                                        │
    └─────────────────────────────────────────────────────┘
                              │
                              │ aggregated into
                              ▼
                      mission_reports
                          report_data (JSONB)
                          pdf_filename
                          generated_at
```

---

## 3. Redis Key Schema

```
Key Pattern                          Type    TTL       Purpose
─────────────────────────────────────────────────────────────────
crew:{uuid}:status                   STRING  30s       Current status per crew
crew:{uuid}:vitals:latest            JSON    30s       Last vitals reading
simulator:radiation_multiplier       STRING  15min     DONKI-driven radiation factor
simulator:running                    STRING  —         "true"/"false"
nasa:donki:latest                    JSON    15min     Cached DONKI response
nasa:epic:latest                     JSON    60min     Cached EPIC response
nasa:apod:today                      JSON    24hr      Cached APOD response
mission:feed                         CHANNEL —         WebSocket pub/sub channel
alerts:active                        SET     —         Set of unacknowledged alert IDs
```

---

## 4. External API Data Flow

```
CrewWatch Backend ←──── api.nasa.gov
        │
        │  GET /DONKI/FLR      → Solar flare events
        │  GET /EPIC/api/natural → Earth images
        │  GET /planetary/apod  → Astronomy picture
        │  GET /neo/rest/v1/feed → Near Earth objects
        │
        └─→ Cache in Redis (TTL based)
        └─→ Serve to frontend via /api/nasa/* proxy routes
        └─→ DONKI → adjust simulator radiation
```
