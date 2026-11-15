# 04 — API Reference (All Endpoints)

**Base URL (Local):** `http://localhost:8000`  
**Base URL (Production):** `https://crewwatch-api.onrender.com`  
**Swagger Docs:** `{base_url}/docs`

---

## Authentication

### `POST /api/auth/login`
Login karke JWT token lo.

**Request:**
```json
{
  "username": "mission_control",
  "password": "password123"
}
```
**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "role": "mission_control"
}
```

---

## Crew Endpoints

### `GET /api/crew`
Sab crew members ki list.

**Response:**
```json
[
  {
    "id": "uuid-here",
    "name": "Dr. Sarah Chen",
    "role": "Commander",
    "current_status": "NOMINAL",
    "responder_name": "Dr. James Liu"
  }
]
```

### `GET /api/crew/{crew_id}`
Ek crew member ki detail + current status.

### `GET /api/crew/{crew_id}/vitals?limit=20`
Us crew member ki last N vitals readings.

### `GET /api/crew/{crew_id}/events`
Us crew member ke saare health events.

---

## Vitals Endpoints

### `POST /api/vitals/ingest`
Vitals receive karo (simulator ya external source se).

**Request:**
```json
{
  "crew_member_id": "uuid",
  "heart_rate": 95.2,
  "spo2": 97.1,
  "temperature": 36.8,
  "radiation_dose": 45.0,
  "sleep_hours": 7.5,
  "stress_index": 0.35
}
```
**Response:**
```json
{
  "status": "NOMINAL",
  "triggered_by": null,
  "event_created": false,
  "reading_id": "uuid"
}
```

### `GET /api/vitals/live`
Abhi ke moment mein sab crew ki latest vitals (dashboard ke liye).

**Response:**
```json
{
  "timestamp": "2026-11-15T19:00:00Z",
  "crew": [
    {
      "crew_id": "uuid",
      "name": "Dr. Sarah Chen",
      "status": "NOMINAL",
      "heart_rate": 72,
      "spo2": 98,
      "temperature": 36.6,
      "radiation_dose": 42,
      "stress_index": 0.3
    }
  ]
}
```

---

## Simulator Endpoints (Admin Only)

### `POST /api/simulator/start`
Simulator shuru karo — har 5 second mein vitals generate hona shuru.

**Request:**
```json
{ "tick_seconds": 5 }
```

### `POST /api/simulator/stop`
Simulator band karo.

### `POST /api/simulator/inject`
**DEMO ke liye sabse important endpoint!**  
Ek crew member mein specific scenario inject karo.

**Request:**
```json
{
  "crew_member_id": "uuid",
  "scenario": "radiation_spike"
}
```

**Available Scenarios:**
| Scenario | Kya hoga |
|----------|----------|
| `radiation_spike` | Radiation → EMERGENCY level |
| `low_oxygen` | SpO₂ → ANOMALY level |
| `cardiac_event` | Heart rate → EMERGENCY level |
| `high_fever` | Temperature → ANOMALY level |
| `fatigue_accumulation` | Sleep + stress → ELEVATED level |
| `full_recovery` | Sab kuch NOMINAL par wapas |

---

## Alerts Endpoints

### `GET /api/alerts`
Saare alerts (recent first).

**Response:**
```json
[
  {
    "id": "uuid",
    "crew_member_name": "Dr. Sarah Chen",
    "status": "EMERGENCY",
    "triggered_by": "radiation_dose",
    "guidance_text": "RADIATION ALERT: Seek shielded area immediately.",
    "responder_name": "Dr. James Liu",
    "acknowledged": false,
    "created_at": "2026-11-15T19:00:00Z"
  }
]
```

### `GET /api/alerts/active`
Sirf unacknowledged alerts.

### `POST /api/alerts/{alert_id}/acknowledge`
Alert acknowledge karo.

**Request:**
```json
{ "acknowledged_by": "Dr. James Liu" }
```

---

## Reports Endpoints

### `POST /api/reports/generate`
Mission health report trigger karo (background mein banta hai).

**Request:**
```json
{ "mission_day": 1 }
```

### `GET /api/reports`
Saare past reports ki list.

### `GET /api/reports/{report_id}/download`
PDF report download karo.

---

## NASA Data Endpoints

### `GET /api/nasa/space-weather`
NASA DONKI se latest solar flare / CME data.

**Response:**
```json
{
  "latest_flare": {
    "flare_id": "2026-11-15T12:00:00-FLR-001",
    "class": "M2.5",
    "peak_time": "2026-11-15T14:30:00Z",
    "radiation_impact": "moderate"
  },
  "simulator_radiation_adjustment": 1.4
}
```

### `GET /api/nasa/epic-image`
NASA EPIC se latest Earth image.

**Response:**
```json
{
  "image_url": "https://epic.gsfc.nasa.gov/archive/natural/...",
  "date": "2026-11-15",
  "caption": "Earth as seen from DSCOVR satellite"
}
```

### `GET /api/nasa/apod`
Astronomy Picture of the Day.

**Response:**
```json
{
  "title": "...",
  "explanation": "...",
  "url": "https://apod.nasa.gov/...",
  "date": "2026-11-15"
}
```

---

## Health Check

### `GET /health`
Backend alive hai ya nahi check karo.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "nasa_api": "reachable",
  "simulator_running": true
}
```
