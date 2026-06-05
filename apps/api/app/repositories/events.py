from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IngestStatus, SourceType
from app.models.event import Event, RawEvent
from app.schemas.dashboard import Aggregate, WidgetQuery


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_raw(
        self,
        *,
        organization_id: UUID,
        api_key_id: UUID | None,
        payload: dict,
        source_type: SourceType,
    ) -> RawEvent:
        raw_event = RawEvent(
            organization_id=organization_id,
            api_key_id=api_key_id,
            source_type=source_type,
            payload=payload,
            status=IngestStatus.PENDING,
        )
        self.session.add(raw_event)
        return raw_event

    async def get_raw_for_org(
        self,
        *,
        organization_id: UUID,
        raw_event_id: UUID,
    ) -> RawEvent | None:
        result = await self.session.execute(
            select(RawEvent).where(
                RawEvent.id == raw_event_id,
                RawEvent.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_raw(self, raw_event_id: UUID) -> RawEvent | None:
        result = await self.session.execute(select(RawEvent).where(RawEvent.id == raw_event_id))
        return result.scalar_one_or_none()

    def add_event(
        self,
        *,
        organization_id: UUID,
        raw_event_id: UUID,
        event_name: str,
        occurred_at: datetime,
        user_id: str | None,
        source_type: SourceType,
        properties: dict,
    ) -> Event:
        event = Event(
            organization_id=organization_id,
            raw_event_id=raw_event_id,
            event_name=event_name,
            occurred_at=occurred_at,
            user_id=user_id,
            source_type=source_type,
            properties=properties,
        )
        self.session.add(event)
        return event

    async def query_widget(self, *, organization_id: UUID, spec: WidgetQuery) -> list[dict]:
        statement = self._build_widget_statement(organization_id=organization_id, spec=spec)
        result = await self.session.execute(statement)
        return [dict(row._mapping) for row in result.all()]

    def _build_widget_statement(self, *, organization_id: UUID, spec: WidgetQuery) -> Select:
        value_expression = func.count(Event.id)
        if spec.aggregate == Aggregate.UNIQUE_USERS:
            value_expression = func.count(func.distinct(Event.user_id))

        columns = [value_expression.label("value")]
        group_columns = []

        if spec.time_bucket:
            bucket = func.date_trunc(spec.time_bucket.value, Event.occurred_at).label("bucket")
            columns.insert(0, bucket)
            group_columns.append(bucket)

        if spec.group_by:
            if spec.group_by == "event_name":
                group_col = Event.event_name.label("group")
            elif spec.group_by == "user_id":
                group_col = Event.user_id.label("group")
            elif spec.group_by == "source_type":
                group_col = Event.source_type.label("group")
            elif spec.group_by.startswith("property:"):
                key = spec.group_by.split(":", 1)[1]
                group_col = Event.properties[key].astext.label("group")
            else:
                group_col = Event.event_name.label("group")
            columns.insert(-1, group_col)
            group_columns.append(group_col)

        statement = select(*columns).where(Event.organization_id == organization_id)
        if spec.event_name:
            statement = statement.where(Event.event_name == spec.event_name)
        if spec.from_ts:
            statement = statement.where(Event.occurred_at >= spec.from_ts)
        if spec.to_ts:
            statement = statement.where(Event.occurred_at <= spec.to_ts)

        for item in spec.filters:
            if item.field == "event_name":
                column = Event.event_name
            elif item.field == "user_id":
                column = Event.user_id
            elif item.field.startswith("property:"):
                key = item.field.split(":", 1)[1]
                column = Event.properties[key].astext
            else:
                continue

            if item.op == "eq":
                statement = statement.where(column == str(item.value))
            elif item.op == "neq":
                statement = statement.where(column != str(item.value))
            elif item.op == "contains":
                statement = statement.where(column.ilike(f"%{item.value}%"))

        if group_columns:
            statement = statement.group_by(*group_columns)
        return statement.order_by(*group_columns).limit(500)
