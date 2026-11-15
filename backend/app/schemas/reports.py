from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class ReportGenerateRequest(BaseModel):
    mission_day: int = 1

class ReportResponse(BaseModel):
    id: UUID
    generated_at: datetime
    mission_day: int
    total_events: int
    emergency_count: int
    anomaly_count: int
    summary_text: str | None
    pdf_filename: str | None

    class Config:
        from_attributes = True
