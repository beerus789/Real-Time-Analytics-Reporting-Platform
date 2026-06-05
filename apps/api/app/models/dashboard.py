from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID
from app.models.enums import DashboardVisibility, WidgetKind


class Dashboard(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "dashboards"
    __table_args__ = (
        Index("ix_dashboards_org_owner", "organization_id", "created_by_id"),
        Index("ix_dashboards_share_token", "share_token"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_by_id: Mapped[UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[DashboardVisibility] = mapped_column(
        Enum(DashboardVisibility, native_enum=False),
        default=DashboardVisibility.TEAM,
        nullable=False,
    )
    auto_refresh_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    widgets: Mapped[list["Widget"]] = relationship(
        "Widget", back_populates="dashboard", cascade="all, delete-orphan"
    )


class Widget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "widgets"
    __table_args__ = (Index("ix_widgets_dashboard", "dashboard_id"),)

    dashboard_id: Mapped[UUID] = mapped_column(
        GUID(), ForeignKey("dashboards.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    kind: Mapped[WidgetKind] = mapped_column(Enum(WidgetKind, native_enum=False), nullable=False)
    query: Mapped[dict] = mapped_column(JSONB, nullable=False)
    layout: Mapped[dict] = mapped_column(JSONB, nullable=False)

    dashboard: Mapped[Dashboard] = relationship("Dashboard", back_populates="widgets")

