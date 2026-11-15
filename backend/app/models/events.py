import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class HealthEvent(Base):
    __tablename__ = "health_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crew_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("crew_members.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    triggered_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    guidance_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    responder_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    crew_member: Mapped["CrewMember"] = relationship("CrewMember", back_populates="events")
