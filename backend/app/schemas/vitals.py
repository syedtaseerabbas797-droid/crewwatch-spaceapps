from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class VitalsIngest(BaseModel):
    crew_member_id: UUID
    heart_rate: float = Field(ge=0, le=300)
    spo2: float = Field(ge=0, le=100)
    temperature: float = Field(ge=30, le=50)
    radiation_dose: float = Field(ge=0, le=10000)
    sleep_hours: float = Field(ge=0, le=24)
    stress_index: float = Field(ge=0.0, le=1.0)

class VitalsResponse(BaseModel):
    id: UUID
    crew_member_id: UUID
    timestamp: datetime
    heart_rate: float
    spo2: float
    temperature: float
    radiation_dose: float
    sleep_hours: float
    stress_index: float
    status: str
    triggered_by: str | None

    class Config:
        from_attributes = True

class VitalsIngestResult(BaseModel):
    reading_id: UUID
    status: str
    triggered_by: str | None
    event_created: bool
    guidance: str | None = None

class SimulatorScenario(BaseModel):
    crew_member_id: UUID
    scenario: str
