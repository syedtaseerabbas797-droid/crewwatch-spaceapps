# System Design Document
## CrewWatch — NASA Space Apps Challenge 2026
**Version:** 1.0 | **Author:** CrewWatch Engineering Team | **Date:** 2026-11-15

---

## 1. Executive Summary

CrewWatch is a real-time astronaut health monitoring system built as a Progressive Web App. It ingests simulated crew vitals, classifies health status using threshold-based rules, routes alerts with actionable guidance, and produces automated mission health reports — all integrated with live NASA space weather data.

---

## 2. System Goals

| Goal | Metric |
|------|--------|
| Real-time status visibility | < 1 second from ingest to WebSocket delivery |
| Alert accuracy | Zero false negatives on EMERGENCY classification |
| Availability | 99% uptime during hackathon demo window |
| NASA data integration | Minimum 3 live NASA APIs consumed |
| Demo reliability | Anomaly injection → full pipeline → ack in < 10 seconds |

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        INTERNET / CLIENTS                            │
│                                                                      │
│  ┌─────────────────┐          ┌──────────────────────────────────┐   │
│  │   Crew PWA      │          │   Mission Control PWA            │   │
│  │   (Phone/Tablet)│          │   (Desktop Browser)              │   │
│  └────────┬────────┘          └───────────────┬──────────────────┘   │
│           │ HTTPS + WSS                       │ HTTPS + WSS          │
└───────────┼───────────────────────────────────┼──────────────────────┘
            │                                   │
┌───────────▼───────────────────────────────────▼──────────────────────┐
│                      RENDER.COM (Cloud Hosting)                       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                         │   │
│  │                                                                │   │
│  │  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐   │   │
│  │  │  Auth    │  │  REST API   │  │WebSocket │  │Background│   │   │
│  │  │  (JWT)   │  │  Router     │  │ Manager  │  │  Tasks   │   │   │
│  │  └──────────┘  └──────┬──────┘  └────┬─────┘  └────┬─────┘   │   │
│  │                        │              │              │          │   │
│  │  ┌─────────────────────▼──────────────▼──────────────▼──────┐  │   │
│  │  │                  Core Business Logic                      │  │   │
│  │  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐    │  │   │
│  │  │  │Simulator │  │Classification│  │  Alert Router    │    │  │   │
│  │  │  │ Engine   │→ │   Engine     │→ │  + Guidance      │    │  │   │
│  │  │  └──────────┘  └──────────────┘  └──────────────────┘    │  │   │
│  │  │                        ↓                   ↓              │  │   │
│  │  │  ┌───────────────────────────────────────────────────┐    │  │   │
│  │  │  │           Report Generator (PDF)                  │    │  │   │
│  │  │  └───────────────────────────────────────────────────┘    │  │   │
│  │  └────────────────────────────────────────────────────────┘  │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │               NASA Integration Layer                     │ │   │
│  │  │   DONKI (Solar)  │  EPIC (Earth)  │  APOD  │  NeoWs     │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                │                                │                      │
│  ┌─────────────▼──────────┐  ┌─────────────────▼────────────────┐    │
│  │   Neon.tech            │  │   Upstash Redis                  │    │
│  │   PostgreSQL           │  │   • Live crew state cache        │    │
│  │   • crew_members       │  │   • WebSocket pub/sub channel    │    │
│  │   • vitals_readings    │  │   • NASA API response cache      │    │
│  │   • health_events      │  └──────────────────────────────────┘    │
│  │   • mission_reports    │                                           │
│  └────────────────────────┘                                           │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                   ┌────────────────▼─────────────────┐
                   │        api.nasa.gov               │
                   │  DONKI / EPIC / APOD / NeoWs      │
                   └───────────────────────────────────┘
```

---

## 4. Component Design

### 4.1 Vitals Simulator

**Purpose:** Generate realistic, time-correlated astronaut vitals since real telemetry is restricted.

**Design Decisions:**
- Each crew member has an **individual baseline** (Commander slightly lower resting HR, etc.)
- **Gradual drift algorithm** — vitals don't jump randomly, they move in physiologically realistic curves
- **DONKI integration** — simulator queries DONKI every 15 min; real solar events adjust radiation output
- **Anomaly injection API** — single endpoint triggers pre-scripted scenarios for demos

**Tick Architecture:**
```
FastAPI startup → BackgroundTask → asyncio loop (every 5s)
  → generate_vitals(crew_member)
  → POST /api/vitals/ingest (internal)
  → classify → store → publish
```

---

### 4.2 Classification Engine

**Purpose:** Convert raw numeric vitals into a human-readable 4-level status.

**Design:** Stateless pure function — takes vitals, returns (status, trigger). No DB calls, no I/O. Testable in isolation.

**Priority Rule:** Worst vital determines overall status.

```
classify(vitals) → worst_status_across_all_vitals
```

**Threshold Table:**
```
Vital            NOMINAL          ELEVATED         ANOMALY          EMERGENCY
─────────────────────────────────────────────────────────────────────────────
Heart Rate (bpm) 60–100           100–120 | 50–60  120–150 | 45–50  >150 | <45
SpO₂ (%)         95–100           92–94            88–91            <88
Temperature (°C) 36.0–37.5        37.5–38.5        38.5–40.0        >40 | <35
Radiation μSv/hr 0–50             50–150           150–500          >500
Stress Index     0.0–0.4          0.4–0.6          0.6–0.8          >0.8
Sleep (hrs)      7–9              6–7              5–6              <5
```

---

### 4.3 WebSocket Architecture

**Pattern:** Fan-out broadcast — one channel, all connected clients receive all crew updates.

```
Vitals Ingest → Redis PUBLISH "mission:feed" → Redis SUBSCRIBE listener
  → iterate all active WebSocket connections
  → asyncio.gather(*[ws.send(msg) for ws in connections])
```

**Connection Management:**
- In-memory connection registry (dict: `connection_id → WebSocket`)
- On disconnect: automatically removed from registry
- No authentication on WS connect for hackathon (keep it simple)

---

### 4.4 NASA Data Integration

**Caching Strategy:** Redis with TTL — prevents rate limit exhaustion.

| API | TTL | Trigger |
|-----|-----|---------|
| DONKI/FLR | 15 min | Scheduled background task |
| EPIC | 60 min | On-demand from frontend |
| APOD | 24 hours | Daily cache refresh |
| NeoWs | 60 min | On-demand |

**DONKI → Simulator Feedback Loop:**
```
DONKI response → parse flare class → map to radiation multiplier
  → update Redis key "simulator:radiation_multiplier"
  → Simulator reads this key on each tick
```

---

## 5. Scalability Notes

> [!NOTE]
> This is a hackathon project. The architecture below supports a working demo, not production scale. Notes are included for judge Q&A readiness.

| Concern | Current Approach | Production Path |
|---------|-----------------|----------------|
| Multiple crew | Loops in simulator | Parallel async tasks per crew |
| WebSocket scale | In-memory registry | Redis pub/sub + multiple pods |
| DB load | Direct asyncpg | Connection pooling + read replicas |
| NASA rate limits | Redis cache | CDN cache + webhook subscriptions |

---

## 6. Technology Decisions Log

| Decision | Options Considered | Choice | Reason |
|----------|--------------------|--------|--------|
| Backend language | Python, Node.js, Go | **Python** | NASA data ecosystem, numpy, ML libs |
| Framework | FastAPI, Flask, Django | **FastAPI** | Async native, auto Swagger, WebSocket built-in |
| Database | SQLite, Neon, Supabase | **Neon** | Free cloud PostgreSQL, no Docker, hackathon-fast |
| Cache/Pub-Sub | Local dict, Redis | **Upstash Redis** | Cloud Redis, no Docker, WebSocket pub/sub |
| Deployment | Heroku, Railway, Render | **Render** | Free tier + GitHub auto-deploy + no sleep on paid |
| Vitals source | Real API, simulation | **Simulation + DONKI** | NASA rules + demonstrates real data integration |
