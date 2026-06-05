from enum import StrEnum


class Role(StrEnum):
    OWNER = "Owner"
    ADMIN = "Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"


class SourceType(StrEnum):
    API = "api"
    CSV = "csv"
    WEBHOOK = "webhook"


class IngestStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class WidgetKind(StrEnum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    KPI = "kpi"
    TABLE = "table"


class DashboardVisibility(StrEnum):
    TEAM = "team"
    PUBLIC = "public"

