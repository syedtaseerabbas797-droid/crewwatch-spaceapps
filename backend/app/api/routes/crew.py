from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from app.database import get_db
from app.models.crew import CrewMember
from app.models.vitals import VitalsReading
from app.models.events import HealthEvent
from app.schemas.crew import CrewMemberCreate, CrewMemberResponse, CrewMemberUpdate
from app.schemas.vitals import VitalsResponse
from app.schemas.alerts import AlertResponse

router = APIRouter(prefix="/api/crew", tags=["Crew Management"])

@router.get("", response_model=list[CrewMemberResponse])
async def list_crew(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CrewMember))
    crew_list = result.scalars().all()
    
    response = []
    for c in crew_list:
        # Get latest vital for status
        vital_res = await db.execute(
            select(VitalsReading)
            .where(VitalsReading.crew_member_id == c.id)
            .order_by(desc(VitalsReading.timestamp))
            .limit(1)
        )
        latest_vital = vital_res.scalar_one_or_none()
        status = latest_vital.status if latest_vital else "NOMINAL"

        response.append(
            CrewMemberResponse(
                id=c.id,
                name=c.name,
                role=c.role,
                responder_name=c.responder_name,
                current_status=status,
                created_at=c.created_at,
            )
        )
    return response

@router.post("", response_model=CrewMemberResponse, status_code=201)
async def create_crew(crew_in: CrewMemberCreate, db: AsyncSession = Depends(get_db)):
    crew = CrewMember(
        name=crew_in.name,
        role=crew_in.role,
        responder_name=crew_in.responder_name,
    )
    db.add(crew)
    await db.commit()
    await db.refresh(crew)
    return CrewMemberResponse(
        id=crew.id,
        name=crew.name,
        role=crew.role,
        responder_name=crew.responder_name,
        current_status="NOMINAL",
        created_at=crew.created_at,
    )

@router.get("/{crew_id}", response_model=CrewMemberResponse)
async def get_crew_member(crew_id: UUID, db: AsyncSession = Depends(get_db)):
    crew = await db.get(CrewMember, crew_id)
    if not crew:
        raise HTTPException(status_code=404, detail="Crew member not found")

    vital_res = await db.execute(
        select(VitalsReading)
        .where(VitalsReading.crew_member_id == crew.id)
        .order_by(desc(VitalsReading.timestamp))
        .limit(1)
    )
    latest_vital = vital_res.scalar_one_or_none()
    status = latest_vital.status if latest_vital else "NOMINAL"

    return CrewMemberResponse(
        id=crew.id,
        name=crew.name,
        role=crew.role,
        responder_name=crew.responder_name,
        current_status=status,
        created_at=crew.created_at,
    )

@router.get("/{crew_id}/vitals", response_model=list[VitalsResponse])
async def get_crew_vitals(crew_id: UUID, limit: int = 30, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(VitalsReading)
        .where(VitalsReading.crew_member_id == crew_id)
        .order_by(desc(VitalsReading.timestamp))
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{crew_id}/events", response_model=list[AlertResponse])
async def get_crew_events(crew_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HealthEvent)
        .where(HealthEvent.crew_member_id == crew_id)
        .order_by(desc(HealthEvent.created_at))
        .limit(50)
    )
    return result.scalars().all()
