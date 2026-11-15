# 02 — System Architecture

## Big Picture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (PWA)                    │
│         React App — Crew View + Mission Control     │
│                  (Frontend Team)                    │
└──────────────────────┬──────────────────────────────┘
                       │  REST API + WebSocket
┌──────────────────────▼──────────────────────────────┐
│                 BACKEND (FastAPI)                   │
│                  Render.com (Cloud)                 │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Vitals     │  │Classification│  │  Alert    │  │
│  │  Simulator  │→ │  Engine      │→ │  Router   │  │
│  └─────────────┘  └──────────────┘  └───────────┘  │
│         ↓                 ↓                ↓        │
│  ┌──────────────────────────────────────────────┐   │
│  │            WebSocket Broadcaster            │   │
│  │         (Real-time feed to Frontend)        │   │
│  └──────────────────────────────────────────────┘   │
│         ↓                                  ↓        │
│  ┌─────────────┐              ┌───────────────────┐  │
│  │  NASA API   │              │  Report Generator │  │
│  │  Layer      │              │  (Auto PDF)       │  │
│  │  DONKI/EPIC │              └───────────────────┘  │
│  └─────────────┘                                    │
└───────────┬─────────────────────────┬───────────────┘
            │                         │
┌───────────▼──────────┐  ┌───────────▼──────────────┐
│  PostgreSQL          │  │  Redis (Upstash)          │
│  (Neon.tech)         │  │  Live state + pub/sub     │
│  Vitals, Events,     │  │  Current crew status      │
│  Reports, Crew       │  │  WebSocket channel        │
└──────────────────────┘  └──────────────────────────┘
            │
┌───────────▼──────────┐
│  NASA APIs           │
│  api.nasa.gov        │
│  DONKI / EPIC / APOD │
└──────────────────────┘
```

---

## Core Data Flow (Step by Step)

```
1. SIMULATOR ticks every 5 seconds
   → generates vitals for each crew member
   → POST /api/vitals/ingest

2. CLASSIFICATION ENGINE evaluates vitals
   → checks all 6 vital signs against thresholds
   → returns: status level + which vital triggered it

3. STATUS CHANGE detected?
   → YES → create health_event record in DB
           → ALERT ROUTER sends guidance to named responder
   → NO  → just store vitals reading

4. REDIS publish to "mission-feed" channel

5. WEBSOCKET broadcasts new data to ALL connected clients
   → Crew member sees their own status update
   → Mission Control sees all crew status update

6. Every 15 minutes: NASA DONKI check
   → Solar flare detected? → radiation level adjusted in simulator

7. Every 24 hours OR on-demand: REPORT GENERATOR
   → Pulls all events from DB
   → Generates PDF mission health report
```

---

## Component Responsibilities

| Component | File | What it does |
|-----------|------|-------------|
| **Simulator** | `core/simulator.py` | Generates realistic vitals with drift + anomaly injection |
| **Classifier** | `core/classification.py` | Evaluates vitals → 4-level status |
| **Alert Router** | `core/alert_router.py` | Picks guidance text, marks responder, publishes alert |
| **Report Generator** | `core/report_generator.py` | Builds PDF from mission events |
| **NASA Client** | `integrations/nasa_client.py` | Calls DONKI, EPIC, APOD APIs |
| **Redis Client** | `integrations/redis_client.py` | Pub/sub + live state cache |
| **WebSocket** | `api/routes/websocket.py` | Pushes real-time data to frontend |

---

## Role-Based Access

| Role | Access |
|------|--------|
| `crew` | Own vitals + status + guidance only |
| `mission_control` | All crew data + alerts + reports |
| `admin` | Everything + simulator control + anomaly injection |

---

## Why No Docker Locally?

- **Database** → Neon.tech (cloud PostgreSQL, free, zero setup)
- **Redis** → Upstash (cloud Redis, free, zero setup)
- **Local dev** → just `uvicorn` + virtual environment
- **Production** → Render.com builds and deploys automatically from GitHub
