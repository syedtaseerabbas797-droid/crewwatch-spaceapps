from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from datetime import datetime, timezone
from app.database import get_db
from app.models.events import HealthEvent
from app.models.crew import CrewMember
from app.schemas.alerts import AlertResponse, AlertAcknowledge
from app.integrations.redis_client import redis_publish

router = APIRouter(prefix="/api/alerts", tags=["Alerts & Guidance"])

@router.get("", response_model=list[AlertResponse])
async def list_alerts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthEvent).order_by(desc(HealthEvent.created_at)).limit(limit)
    )
    events = result.scalars().all()
    
    out = []
    for ev in events:
        crew = await db.get(CrewMember, ev.crew_member_id)
        out.append(
            AlertResponse(
                id=ev.id,
                crew_member_id=ev.crew_member_id,
                crew_member_name=crew.name if crew else "Unknown",
                event_type=ev.event_type,
                from_status=ev.from_status,
                to_status=ev.to_status,
                triggered_by=ev.triggered_by,
                guidance_text=ev.guidance_text,
                responder_name=ev.responder_name,
                acknowledged=ev.acknowledged,
                acknowledged_by=ev.acknowledged_by,
                acknowledged_at=ev.acknowledged_at,
                created_at=ev.created_at,
            )
        )
    return out

@router.get("/active", response_model=list[AlertResponse])
async def list_active_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthEvent)
        .where(HealthEvent.acknowledged == False)  # noqa: E712
        .order_by(desc(HealthEvent.created_at))
    )
    events = result.scalars().all()
    
    out = []
    for ev in events:
        crew = await db.get(CrewMember, ev.crew_member_id)
        out.append(
            AlertResponse(
                id=ev.id,
                crew_member_id=ev.crew_member_id,
                crew_member_name=crew.name if crew else "Unknown",
                event_type=ev.event_type,
                from_status=ev.from_status,
                to_status=ev.to_status,
                triggered_by=ev.triggered_by,
                guidance_text=ev.guidance_text,
                responder_name=ev.responder_name,
                acknowledged=ev.acknowledged,
                acknowledged_by=ev.acknowledged_by,
                acknowledged_at=ev.acknowledged_at,
                created_at=ev.created_at,
            )
        )
    return out

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    payload: AlertAcknowledge,
    db: AsyncSession = Depends(get_db)
):
    event = await db.get(HealthEvent, alert_id)
    if not event:
        raise HTTPException(status_code=404, detail="Alert not found")

    event.acknowledged = True
    event.acknowledged_by = payload.acknowledged_by
    event.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()

    # Broadcast acknowledgement to WebSocket feed
    await redis_publish("mission:feed", {
        "type": "ALERT_ACKNOWLEDGED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_id": str(alert_id),
        "crew_id": str(event.crew_member_id),
        "acknowledged_by": payload.acknowledged_by,
    })

    return {
        "success": True,
        "message": f"Alert {alert_id} acknowledged by {payload.acknowledged_by}",
        "acknowledged_at": event.acknowledged_at.isoformat(),
    }
