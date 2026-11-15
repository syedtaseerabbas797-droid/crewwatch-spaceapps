from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class CrewMemberCreate(BaseModel):
    name: str
    role: str | None = None
    responder_name: str | None = None

class CrewMemberResponse(BaseModel):
    id: UUID
    name: str
    role: str | None
    responder_name: str | None
    current_status: str = "NOMINAL"
    created_at: datetime

    class Config:
        from_attributes = True

class CrewMemberUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    responder_name: str | None = None
