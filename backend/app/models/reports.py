import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class MissionReport(Base):
    __tablename__ = "mission_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    mission_day: Mapped[int] = mapped_column(Integer, default=1)
    total_events: Mapped[int] = mapped_column(Integer, default=0)
    emergency_count: Mapped[int] = mapped_column(Integer, default=0)
    anomaly_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    report_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
