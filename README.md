# 🚀 CrewWatch
### NASA Space Apps Challenge 2026 — "The Next Frontier"
> **Health Monitoring Software for Astronauts on Space Missions**  
> Team: Kenya · India · Pakistan

---

## What is CrewWatch?
A Progressive Web App (PWA) that **continuously monitors simulated astronaut vitals**, classifies status in real time, routes early warnings with specific action guidance, and auto-generates mission health reports.

```
📡 Receive Vitals  →  🧠 Classify Status  →  🚨 Alert Responder  →  📋 Log & Report
     (Simulator)         (4-Level System)       (Named Guidance)      (Auto PDF)
```

## Status Levels
| Level | Color | Meaning |
|-------|-------|---------|
| NOMINAL | 🟢 Green | All vitals within safe range |
| ELEVATED | 🟡 Yellow | One or more vitals trending out of range |
| ANOMALY | 🟠 Orange | Significant deviation — action required |
| EMERGENCY | 🔴 Red | Immediate intervention required |

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI (Python) |
| Database | PostgreSQL on **Neon.tech** (cloud, no Docker) |
| Cache / Pub-Sub | Redis on **Upstash** (cloud, no Docker) |
| Real-time | WebSockets (built into FastAPI) |
| Background Jobs | FastAPI BackgroundTasks |
| NASA APIs | DONKI, EPIC, APOD, NeoWs |
| Deployment | Render.com (free tier) |
| Frontend | React PWA (separate team) |

---

## Documentation Index
| File | Description |
|------|-------------|
| [docs/01-setup.md](docs/01-setup.md) | Environment setup — no Docker required |
| [docs/02-architecture.md](docs/02-architecture.md) | System architecture + data flow |
| [docs/03-database.md](docs/03-database.md) | Database schema + Neon.tech setup |
| [docs/04-api-reference.md](docs/04-api-reference.md) | All REST API endpoints |
| [docs/05-websocket-protocol.md](docs/05-websocket-protocol.md) | WebSocket contract (for frontend team) |
| [docs/06-nasa-apis.md](docs/06-nasa-apis.md) | NASA API integrations guide |
| [docs/07-deployment.md](docs/07-deployment.md) | Deploy to Render.com |

---

## Quick Start
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # Fill in your keys
uvicorn app.main:app --reload
```
API Docs auto-available at: `http://localhost:8000/docs`

---

## NASA APIs Used
- **DONKI** — Solar flare data → drives radiation simulation
- **EPIC** — Earth imagery → mission context display
- **APOD** — Astronomy Picture of the Day → mission home screen
- **NeoWs** — Near-Earth objects → space environment risk

**NASA API Key:** stored in `.env` as `NASA_API_KEY`  
**Earthdata Login:** Username `spaceninja` (activated ✅)

---

## Team
CrewWatch — Kenya · India · Pakistan
*NASA Space Apps Challenge 2026*
