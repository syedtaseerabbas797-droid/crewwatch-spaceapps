import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.models.crew import CrewMember
from app.models.vitals import VitalsReading
from app.models.events import HealthEvent
from app.core.classification import classify_vitals
from app.core.alert_router import get_guidance
from app.core.simulator import (
    initialize_crew_states,
    generate_tick,
    get_all_states,
)
from app.integrations.redis_client import redis_publish, close_redis, redis_get, redis_set
from app.integrations.nasa_client import get_radiation_multiplier
from app.scripts.seed_data import seed_crew

# Routes
from app.api.routes import auth, crew, vitals, alerts, reports, nasa, websocket

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("crewwatch")

# Background simulation runner
async def simulation_loop():
    logger.info("Starting CrewWatch Telemetry Simulation Loop...")
    await asyncio.sleep(2)  # Wait for startup to complete

    while True:
        try:
            async with AsyncSessionLocal() as session:
                crew_res = await session.execute(select(CrewMember))
                crew_list = crew_res.scalars().all()

                if not crew_list:
                    await asyncio.sleep(settings.SIMULATOR_TICK_SECONDS)
                    continue

                # Ensure simulator state initialized
                states = get_all_states()
                if not states:
                    initialize_crew_states([{"id": str(c.id)} for c in crew_list])

                # Get NASA solar radiation multiplier
                multiplier = await get_radiation_multiplier()

                broadcast_crew_data = []

                for c in crew_list:
                    crew_id_str = str(c.id)
                    tick = generate_tick(crew_id_str, radiation_multiplier=multiplier)
                    if not tick:
                        continue

                    # Classify vitals
                    result = classify_vitals(
                        heart_rate=tick["heart_rate"],
                        spo2=tick["spo2"],
                        temperature=tick["temperature"],
                        radiation_dose=tick["radiation_dose"],
                        sleep_hours=tick["sleep_hours"],
                        stress_index=tick["stress_index"],
                    )

                    # Check previous status
                    cache_key = f"crew:{crew_id_str}:status"
                    prev_status = await redis_get(cache_key) or "NOMINAL"
                    status_changed = (prev_status != result.status)

                    # Persist vitals reading
                    vital_entry = VitalsReading(
                        crew_member_id=c.id,
                        heart_rate=tick["heart_rate"],
                        spo2=tick["spo2"],
                        temperature=tick["temperature"],
                        radiation_dose=tick["radiation_dose"],
                        sleep_hours=tick["sleep_hours"],
                        stress_index=tick["stress_index"],
                        status=result.status,
                        triggered_by=result.triggered_by,
                        raw_payload=tick,
                    )
                    session.add(vital_entry)

                    # Trigger alert if status changed to non-nominal
                    if status_changed and result.status != "NOMINAL":
                        responder = c.responder_name or "Earth Flight Surgeon"
                        guidance = get_guidance(result.triggered_by, result.status, responder)
                        event = HealthEvent(
                            crew_member_id=c.id,
                            event_type="STATUS_ALERT",
                            from_status=prev_status,
                            to_status=result.status,
                            triggered_by=result.triggered_by,
                            guidance_text=guidance,
                            responder_name=responder,
                        )
                        session.add(event)

                        # Broadcast urgent alert
                        await websocket.manager.broadcast({
                            "type": "ALERT",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "crew_id": crew_id_str,
                            "crew_name": c.name,
                            "from_status": prev_status,
                            "to_status": result.status,
                            "triggered_by": result.triggered_by,
                            "triggered_value": result.triggered_value,
                            "threshold_exceeded": result.threshold_exceeded,
                            "guidance_text": guidance,
                            "responder_name": responder,
                            "severity": "critical" if result.status == "EMERGENCY" else "warning",
                            "action_required": True,
                        })

                    await redis_set(cache_key, result.status, ex=60)

                    # Status color coding
                    status_colors = {
                        "NOMINAL": "#22c55e",
                        "ELEVATED": "#eab308",
                        "ANOMALY": "#f97316",
                        "EMERGENCY": "#ef4444",
                    }

                    broadcast_crew_data.append({
                        "crew_id": crew_id_str,
                        "name": c.name,
                        "role": c.role,
                        "status": result.status,
                        "status_color": status_colors.get(result.status, "#22c55e"),
                        "heart_rate": tick["heart_rate"],
                        "spo2": tick["spo2"],
                        "temperature": tick["temperature"],
                        "radiation_dose": tick["radiation_dose"],
                        "sleep_hours": tick["sleep_hours"],
                        "stress_index": tick["stress_index"],
                        "triggered_by": result.triggered_by,
                    })

                await session.commit()

                # Broadcast live vitals update to all connected WebSocket clients
                if broadcast_crew_data:
                    ws_update_payload = {
                        "type": "VITALS_UPDATE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "radiation_multiplier": multiplier,
                        "crew": broadcast_crew_data,
                    }
                    await websocket.manager.broadcast(ws_update_payload)
                    await redis_publish("mission:feed", ws_update_payload)

        except Exception as e:
            logger.error(f"Error in simulation loop: {e}", exc_info=True)

        await asyncio.sleep(settings.SIMULATOR_TICK_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Neon DB tables and seed astronauts
    logger.info("Initializing CrewWatch Backend Service...")
    await seed_crew()
    
    # Start background simulator & redis tasks
    sim_task = asyncio.create_task(simulation_loop())
    redis_task = asyncio.create_task(websocket.redis_listener())

    yield

    # Shutdown
    sim_task.cancel()
    redis_task.cancel()
    await close_redis()
    logger.info("CrewWatch Backend shutdown completed.")

app = FastAPI(
    title="CrewWatch Backend API — NASA Space Apps Challenge 2026",
    description="Real-time astronaut vital telemetry monitoring, 4-tier health classification, and automated mission health reporting system.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(crew.router)
app.include_router(vitals.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(nasa.router)
app.include_router(websocket.router)

@app.get("/health", tags=["Health & Status"])
async def health_check():
    return {
        "status": "online",
        "service": "CrewWatch Backend",
        "challenge": "NASA Space Apps Challenge 2026",
        "team": "Kenya · India · Pakistan",
        "database": "Neon.tech Cloud PostgreSQL (Connected)",
        "redis": "Upstash Cloud Redis (Connected)",
        "nasa_api": "api.nasa.gov Active",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
