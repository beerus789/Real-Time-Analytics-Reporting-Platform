export type Role = "Owner" | "Admin" | "Analyst" | "Viewer";
export type WidgetKind = "line" | "bar" | "pie" | "kpi" | "table";

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  organization_name: string;
  role: Role;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}

export interface ApiKeyRecord {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  revoked_at: string | null;
  last_used_at: string | null;
}

export interface ApiKeyCreated extends ApiKeyRecord {
  key: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: Role;
  expires_at: string;
  accepted_at: string | null;
}

export interface OutboxMessage {
  id: string;
  recipient_email: string;
  subject: string;
  body: string;
  payload: { token?: string; role?: Role };
  created_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: Role;
}

export interface WidgetQuery {
  aggregate: "count" | "unique_users";
  event_name?: string | null;
  group_by?: string | null;
  time_bucket?: "minute" | "hour" | "day" | null;
  filters: Array<{ field: string; op: "eq" | "neq" | "contains"; value: string | number | boolean }>;
  from_ts?: string | null;
  to_ts?: string | null;
}

export interface Widget {
  id: string;
  dashboard_id: string;
  title: string;
  kind: WidgetKind;
  query: WidgetQuery;
  layout: { x: number; y: number; w: number; h: number };
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  visibility: "team" | "public";
  auto_refresh_seconds: number;
  share_token: string | null;
  created_at: string;
  updated_at: string;
  widgets?: Widget[];
}

export interface WidgetData {
  widget_id: string;
  kind: WidgetKind;
  rows: Array<Record<string, string | number | null>>;
}

export interface IngestResponse {
  accepted: number;
  rejected: number;
  raw_event_ids: string[];
  errors: Array<Record<string, unknown>>;
}

