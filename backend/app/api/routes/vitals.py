from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from app.database import get_db
from app.models.crew import CrewMember
from app.models.vitals import VitalsReading
from app.models.events import HealthEvent
from app.schemas.vitals import VitalsIngest, VitalsIngestResult, SimulatorScenario
from app.core.classification import classify_vitals
from app.core.alert_router import get_guidance
from app.core.simulator import inject_scenario
from app.integrations.redis_client import redis_publish, redis_get, redis_set

router = APIRouter(prefix="/api/vitals", tags=["Vitals & Telemetry"])

@router.post("/ingest", response_model=VitalsIngestResult)
async def ingest_vitals(reading: VitalsIngest, db: AsyncSession = Depends(get_db)):
    # 1. Classify
    result = classify_vitals(
        heart_rate=reading.heart_rate,
        spo2=reading.spo2,
        temperature=reading.temperature,
        radiation_dose=reading.radiation_dose,
        sleep_hours=reading.sleep_hours,
        stress_index=reading.stress_index,
    )

    # 2. Check previous status from Redis or DB
    cache_key = f"crew:{reading.crew_member_id}:status"
    prev_status = await redis_get(cache_key) or "NOMINAL"
    status_changed = (prev_status != result.status)

    # 3. Store vitals reading
    vital_entry = VitalsReading(
        crew_member_id=reading.crew_member_id,
        heart_rate=reading.heart_rate,
        spo2=reading.spo2,
        temperature=reading.temperature,
        radiation_dose=reading.radiation_dose,
        sleep_hours=reading.sleep_hours,
        stress_index=reading.stress_index,
        status=result.status,
        triggered_by=result.triggered_by,
        raw_payload=reading.model_dump(mode="json"),
    )
    db.add(vital_entry)

    guidance = None
    event_created = False

    # 4. If status changed or severity elevated, create HealthEvent
    if status_changed and result.status != "NOMINAL":
        crew = await db.get(CrewMember, reading.crew_member_id)
        responder = crew.responder_name if crew and crew.responder_name else "Earth Flight Surgeon"
        guidance = get_guidance(result.triggered_by, result.status, responder)
        
        event = HealthEvent(
            crew_member_id=reading.crew_member_id,
            event_type="STATUS_ALERT",
            from_status=prev_status,
            to_status=result.status,
            triggered_by=result.triggered_by,
            guidance_text=guidance,
            responder_name=responder,
        )
        db.add(event)
        event_created = True

        # Broadcast critical alert via WebSocket channel
        await redis_publish("mission:feed", {
            "type": "ALERT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crew_id": str(reading.crew_member_id),
            "crew_name": crew.name if crew else "Astronaut",
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

    await db.commit()
    await db.refresh(vital_entry)

    # Update cache
    await redis_set(cache_key, result.status, ex=60)

    return VitalsIngestResult(
        reading_id=vital_entry.id,
        status=result.status,
        triggered_by=result.triggered_by,
        event_created=event_created,
        guidance=guidance,
    )

@router.get("/live")
async def get_live_vitals(db: AsyncSession = Depends(get_db)):
    crew_res = await db.execute(select(CrewMember))
    crew_list = crew_res.scalars().all()

    crew_data = []
    for c in crew_list:
        v_res = await db.execute(
            select(VitalsReading)
            .where(VitalsReading.crew_member_id == c.id)
            .order_by(desc(VitalsReading.timestamp))
            .limit(1)
        )
        latest = v_res.scalar_one_or_none()
        crew_data.append({
            "crew_id": str(c.id),
            "name": c.name,
            "role": c.role,
            "status": latest.status if latest else "NOMINAL",
            "heart_rate": latest.heart_rate if latest else 70.0,
            "spo2": latest.spo2 if latest else 98.0,
            "temperature": latest.temperature if latest else 36.6,
            "radiation_dose": latest.radiation_dose if latest else 35.0,
            "sleep_hours": latest.sleep_hours if latest else 7.5,
            "stress_index": latest.stress_index if latest else 0.25,
            "triggered_by": latest.triggered_by if latest else None,
        })

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "crew": crew_data,
    }

@router.post("/simulator/inject")
async def inject_sim_scenario(req: SimulatorScenario):
    success = inject_scenario(str(req.crew_member_id), req.scenario)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Could not inject scenario '{req.scenario}' for crew {req.crew_member_id}. Ensure simulator is running."
        )
    return {
        "success": True,
        "message": f"Scenario '{req.scenario}' injected successfully for crew {req.crew_member_id}",
    }
