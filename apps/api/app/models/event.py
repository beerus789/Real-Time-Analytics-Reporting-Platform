from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID
from app.models.enums import IngestStatus, SourceType


class RawEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "raw_events"
    __table_args__ = (
        Index("ix_raw_events_org_status_created", "organization_id", "status", "created_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    api_key_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("api_keys.id"), nullable=True
    )
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    status: Mapped[IngestStatus] = mapped_column(
        Enum(IngestStatus, native_enum=False), default=IngestStatus.PENDING, nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_org_occurred_at", "organization_id", "occurred_at"),
        Index("ix_events_org_event_name_time", "organization_id", "event_name", "occurred_at"),
        Index("ix_events_org_source_time", "organization_id", "source_type", "occurred_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    raw_event_id: Mapped[UUID | None] = mapped_column(
        GUID(), ForeignKey("raw_events.id", ondelete="SET NULL"), nullable=True
    )
    event_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(180), index=True, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False), nullable=False
    )
    properties: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
