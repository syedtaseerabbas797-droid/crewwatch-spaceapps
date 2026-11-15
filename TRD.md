# Technical Requirements Document (TRD)
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Date:** 2026-11-15 | **Status:** FINAL

---

## 1. System Overview

CrewWatch backend is a Python FastAPI application providing:
- Async REST API (JSON)
- WebSocket server (real-time broadcast)
- Background simulation task
- NASA API proxy layer
- PostgreSQL persistence (Neon.tech)
- Redis pub/sub + cache (Upstash)

---

## 2. Technology Stack (Locked)

### Backend
```
Language:        Python 3.11+
Framework:       FastAPI 0.115+
ASGI Server:     Uvicorn (with websockets support)
ORM:             SQLAlchemy 2.0 (async mode)
DB Driver:       asyncpg (async PostgreSQL)
Migrations:      Alembic
Validation:      Pydantic v2
Auth:            python-jose (JWT) + passlib (bcrypt)
HTTP Client:     HTTPX (async)
Redis Client:    redis-py (async)
PDF Generator:   ReportLab
Templating:      Jinja2
Numerics:        NumPy
Environment:     python-dotenv + pydantic-settings
```

### Infrastructure
```
Database:        PostgreSQL 16 (Neon.tech — serverless cloud)
Cache/PubSub:    Redis 7 (Upstash — serverless cloud)
Hosting:         Render.com (free web service)
Version Control: GitHub (public repo)
CI/CD:           Render auto-deploy on GitHub push
```

---

## 3. API Technical Specifications

### 3.1 Protocol
- **REST:** HTTP/1.1, JSON body, JSON response
- **WebSocket:** RFC 6455, JSON message payload
- **Auth:** Bearer token (JWT) in `Authorization` header
- **CORS:** Allow all origins (hackathon — tighten in production)

### 3.2 Response Format (Standard)

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-11-15T19:00:00Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "CREW_NOT_FOUND",
    "message": "Crew member with id 'xyz' not found",
    "field": null
  },
  "timestamp": "2026-11-15T19:00:00Z"
}
```

### 3.3 HTTP Status Codes Used

| Code | When |
|------|------|
| `200` | Successful GET / POST |
| `201` | Resource created |
| `400` | Validation error |
| `401` | Missing/invalid JWT |
| `403` | Insufficient role |
| `404` | Resource not found |
| `422` | Pydantic validation error |
| `500` | Unhandled server error |
| `503` | NASA API unreachable |

---

## 4. Database Technical Requirements

### 4.1 Connection
```python
# Async SQLAlchemy engine
DATABASE_URL = "postgresql+asyncpg://user:pass@ep-xxx.neon.tech/neondb?ssl=require"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### 4.2 UUID Strategy
All primary keys use **UUID v4** (`gen_random_uuid()` in PostgreSQL).
Reason: Avoids sequential ID guessing, safe for public API.

### 4.3 Timestamp Strategy
All timestamps stored as **UTC TIMESTAMP** (no timezone offset in DB).
API responses include `Z` suffix (ISO 8601 UTC).

### 4.4 JSONB Usage
`vitals_readings.raw_payload` and `mission_reports.report_data` use PostgreSQL **JSONB** for:
- Flexible schema extension without migrations
- Native PostgreSQL JSON querying
- Efficient binary storage

### 4.5 Indexing Requirements

```sql
-- Performance critical indexes
CREATE INDEX idx_vitals_crew_timestamp ON vitals_readings(crew_member_id, timestamp DESC);
CREATE INDEX idx_events_crew_created ON health_events(crew_member_id, created_at DESC);
CREATE INDEX idx_events_unacknowledged ON health_events(acknowledged) WHERE acknowledged = false;
CREATE INDEX idx_events_status ON health_events(to_status);
```

---

## 5. Classification Engine Technical Spec

### 5.1 Function Signature
```python
def classify_vitals(reading: VitalsInput) -> ClassificationResult:
    """
    Pure function. No side effects. No I/O.
    
    Args:
        reading: VitalsInput pydantic model
    
    Returns:
        ClassificationResult(
            status: Literal["NOMINAL", "ELEVATED", "ANOMALY", "EMERGENCY"],
            triggered_by: str | None,
            triggered_value: float | None,
            threshold_exceeded: float | None,
            all_checks: list[VitalCheck]
        )
    """
```

### 5.2 Priority Resolution
When multiple vitals are out of range, **highest severity wins**:
```python
PRIORITY = ["EMERGENCY", "ANOMALY", "ELEVATED", "NOMINAL"]
```

### 5.3 Threshold Data Structure
```python
THRESHOLDS = {
    "heart_rate": {
        "NOMINAL":    (60, 100),
        "ELEVATED":   [(100, 120), (50, 60)],
        "ANOMALY":    [(120, 150), (45, 50)],
        "EMERGENCY":  lambda v: v > 150 or v < 45
    },
    # ... other vitals
}
```

---

## 6. WebSocket Technical Spec

### 6.1 Connection Lifecycle
```
Client → WS Handshake → Server accepts
Server → {"type": "CONNECTED", "connection_id": "uuid", "crew_count": 3}
Server → VITALS_UPDATE (every 5s)
Server → ALERT (on status change)
Client disconnects → Server removes from registry
```

### 6.2 Message Schema (TypeScript-compatible)

```typescript
// From backend to frontend
type WSMessage =
  | { type: "CONNECTED"; connection_id: string; crew_count: number }
  | { type: "VITALS_UPDATE"; timestamp: string; crew: CrewVitals[] }
  | { type: "ALERT"; alert_id: string; crew_id: string; crew_name: string;
      from_status: Status; to_status: Status; triggered_by: string;
      guidance_text: string; responder_name: string; severity: string }
  | { type: "ALERT_ACKNOWLEDGED"; alert_id: string; acknowledged_by: string }

type Status = "NOMINAL" | "ELEVATED" | "ANOMALY" | "EMERGENCY"
```

### 6.3 Connection Registry
```python
# Global in-memory registry
active_connections: dict[str, WebSocket] = {}

# Thread-safe with asyncio.Lock
connection_lock = asyncio.Lock()
```

---

## 7. NASA API Technical Spec

### 7.1 HTTP Client Configuration
```python
nasa_client = httpx.AsyncClient(
    base_url="https://api.nasa.gov",
    timeout=10.0,           # 10 second timeout
    params={"api_key": NASA_API_KEY}
)
```

### 7.2 Error Handling
```python
try:
    response = await nasa_client.get("/DONKI/FLR", params={...})
    response.raise_for_status()
    return response.json()
except httpx.TimeoutException:
    return get_cached_or_default("nasa:donki", default=[])
except httpx.HTTPStatusError as e:
    logger.error(f"NASA API error: {e.response.status_code}")
    return get_cached_or_default("nasa:donki", default=[])
```

### 7.3 DONKI → Radiation Multiplier Mapping
```python
FLARE_RADIATION_MAP = {
    "A": 1.0,   # Baseline
    "B": 1.1,   # +10%
    "C": 1.3,   # +30%
    "M": 1.7,   # +70% → likely ELEVATED for some crew
    "X": 2.5,   # +150% → likely ANOMALY/EMERGENCY
}
```

---

## 8. Performance Requirements

| Operation | Target Latency |
|-----------|---------------|
| Vitals ingest → DB write | < 100ms |
| Vitals ingest → Redis publish | < 50ms |
| Redis publish → WS client receive | < 200ms |
| **End-to-end (ingest → UI update)** | **< 500ms** |
| Classification engine | < 5ms (pure Python) |
| NASA API proxy (cached) | < 20ms |
| NASA API proxy (live) | < 2000ms |
| PDF report generation | < 5000ms |

---

## 9. Dependencies & Versions (`requirements.txt`)

```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.0
pydantic-settings==2.6.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.28.0
redis==5.2.0
python-multipart==0.0.12
reportlab==4.2.5
jinja2==3.1.4
numpy==2.2.0
python-dotenv==1.0.1
websockets==14.1
```

---

## 10. Testing Requirements

| Test Type | Coverage Target | Tool |
|-----------|----------------|------|
| Unit — Classification Engine | 100% threshold combinations | pytest |
| Unit — Simulator | Baseline + anomaly outputs | pytest |
| Integration — API Endpoints | All 20+ endpoints | pytest + httpx |
| Integration — WebSocket | Connect + receive + disconnect | pytest + websockets |
| Integration — NASA APIs | Mocked responses | pytest + respx |
| Manual — Demo Scenario | Full pipeline end-to-end | Manual before submission |
