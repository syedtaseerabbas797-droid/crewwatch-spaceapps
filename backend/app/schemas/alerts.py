from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AlertResponse(BaseModel):
    id: UUID
    crew_member_id: UUID
    crew_member_name: str | None = None
    event_type: str
    from_status: str | None
    to_status: str
    triggered_by: str | None
    guidance_text: str | None
    responder_name: str | None
    acknowledged: bool
    acknowledged_by: str | None
    acknowledged_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True

class AlertAcknowledge(BaseModel):
    acknowledged_by: str
