from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import DashboardVisibility, WidgetKind
from app.schemas.common import LayoutSpec, ORMModel


class Aggregate(StrEnum):
    COUNT = "count"
    UNIQUE_USERS = "unique_users"


class TimeBucket(StrEnum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


class QueryFilter(BaseModel):
    field: str = Field(min_length=1, max_length=80)
    op: str = Field(pattern="^(eq|neq|contains)$")
    value: str | int | float | bool


class WidgetQuery(BaseModel):
    aggregate: Aggregate = Aggregate.COUNT
    event_name: str | None = Field(default=None, max_length=160)
    group_by: str | None = Field(default=None, max_length=80)
    time_bucket: TimeBucket | None = TimeBucket.HOUR
    filters: list[QueryFilter] = Field(default_factory=list, max_length=10)
    from_ts: datetime | None = None
    to_ts: datetime | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "WidgetQuery":
        if self.from_ts and self.to_ts and self.from_ts >= self.to_ts:
            raise ValueError("from_ts must be before to_ts")
        return self


class DashboardCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=1000)
    auto_refresh_seconds: int = Field(default=60)

    @field_validator("auto_refresh_seconds")
    @classmethod
    def validate_refresh(cls, value: int) -> int:
        if value not in {30, 60, 300}:
            raise ValueError("auto_refresh_seconds must be one of 30, 60, 300")
        return value


class DashboardUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=1000)
    auto_refresh_seconds: int | None = None

    @field_validator("auto_refresh_seconds")
    @classmethod
    def validate_refresh(cls, value: int | None) -> int | None:
        if value is not None and value not in {30, 60, 300}:
            raise ValueError("auto_refresh_seconds must be one of 30, 60, 300")
        return value


class DashboardResponse(ORMModel):
    id: UUID
    name: str
    description: str | None
    visibility: DashboardVisibility
    auto_refresh_seconds: int
    share_token: str | None
    created_at: datetime
    updated_at: datetime


class WidgetCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    kind: WidgetKind
    query: WidgetQuery
    layout: LayoutSpec


class WidgetUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    kind: WidgetKind | None = None
    query: WidgetQuery | None = None
    layout: LayoutSpec | None = None


class WidgetResponse(ORMModel):
    id: UUID
    dashboard_id: UUID
    title: str
    kind: WidgetKind
    query: dict[str, Any]
    layout: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DashboardDetailResponse(DashboardResponse):
    widgets: list[WidgetResponse] = Field(default_factory=list)


class ShareResponse(BaseModel):
    dashboard_id: UUID
    share_token: str
    public_url: str


class WidgetDataResponse(BaseModel):
    widget_id: UUID
    kind: WidgetKind
    rows: list[dict[str, Any]]
