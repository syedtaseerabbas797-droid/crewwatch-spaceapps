import asyncio
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.crew import CrewMember

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_CREW = [
    {
        "name": "Dr. Sarah Chen",
        "role": "Mission Commander",
        "responder_name": "Dr. James Liu (Earth Flight Surgeon)",
    },
    {
        "name": "Maj. Alex Odhiambo",
        "role": "Lead Flight Pilot",
        "responder_name": "Dr. James Liu (Earth Flight Surgeon)",
    },
    {
        "name": "Dr. Priya Sharma",
        "role": "Payload & Medical Specialist",
        "responder_name": "Dr. James Liu (Earth Flight Surgeon)",
    },
]

async def seed_crew():
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CrewMember))
        existing = result.scalars().all()
        if not existing:
            logger.info("Seeding initial CrewWatch astronaut crew...")
            for c in INITIAL_CREW:
                member = CrewMember(
                    name=c["name"],
                    role=c["role"],
                    responder_name=c["responder_name"],
                )
                session.add(member)
            await session.commit()
            logger.info("Successfully seeded 3 crew members in Neon DB!")
        else:
            logger.info(f"Crew already exists ({len(existing)} astronauts registered).")

if __name__ == "__main__":
    asyncio.run(seed_crew())
