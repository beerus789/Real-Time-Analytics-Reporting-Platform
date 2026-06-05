# Pulseboard Analytics API Guide

This guide describes the REST API for Pulseboard Analytics: authentication, organization membership, API keys, event ingestion, dashboards, widgets, sharing, and public read-only dashboard access.

## Base URLs

Production API:

```text
https://real-time-analytics-reporting-platform.onrender.com/api/v1
```

Local API:

```text
http://localhost:8000/api/v1
```

Interactive OpenAPI documentation is available at:

```text
https://real-time-analytics-reporting-platform.onrender.com/docs
```

## Authentication

User-facing endpoints use a short-lived JWT access token:

```http
Authorization: Bearer <access_token>
```

`POST /auth/signin`, `POST /auth/signup`, and `POST /auth/refresh` return an `access_token`. Refresh tokens are stored in an HTTP-only cookie named `refresh_token`.

Ingestion endpoints use organization API keys:

```http
X-API-Key: <api_key>
```

API keys are shown only once when created. The server stores only hashed key values.

## Error Format

All application errors use this shape:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {},
    "request_id": "string"
  }
}
```

Common status codes:

| Status | Meaning |
| --- | --- |
| `400` | Invalid application request |
| `401` | Missing, expired, revoked, or invalid credentials |
| `403` | Authenticated but not allowed |
| `404` | Resource not found or inaccessible in this organization |
| `409` | Conflict with existing data |
| `422` | Request validation failed |
| `429` | Ingestion rate limit exceeded |

## Roles And Permissions

Supported roles:

| Role | Typical access |
| --- | --- |
| `Owner` | Full organization access |
| `Admin` | Team, API key, dashboard, and ingestion management |
| `Analyst` | Dashboard and analytics work, API key listing |
| `Viewer` | Read-only organization/dashboard access |

Tenant isolation is enforced server-side. A token from one organization cannot read or mutate another organization.

## Health

### Check API Health

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

## Auth Endpoints

### Sign Up

Creates a user, creates an organization, and assigns the user as `Owner`.

```http
POST /auth/signup
Content-Type: application/json
```

Request:

```json
{
  "organization_name": "Acme Analytics",
  "full_name": "Acme Owner",
  "email": "owner@example.com",
  "password": "StrongPassword123!"
}
```

Response `201`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Sign In

```http
POST /auth/signin
Content-Type: application/json
```

Request:

```json
{
  "email": "owner@example.com",
  "password": "StrongPassword123!"
}
```

Response `200`:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Refresh Access Token

Uses the HTTP-only refresh cookie.

```http
POST /auth/refresh
```

Response `200`:

```json
{
  "access_token": "<new_jwt>",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Logout

Revokes the current refresh token and clears the cookie.

```http
POST /auth/logout
```

Response:

```json
{
  "message": "Logged out."
}
```

### Current User

```http
GET /auth/me
Authorization: Bearer <access_token>
```

Response:

```json
{
  "id": "9de0a9fb-0a7c-4d6f-a302-1e3fa51e4f1d",
  "email": "owner@example.com",
  "full_name": "Acme Owner",
  "organization_id": "7bb3fdb4-0635-43a9-bf74-7a0ccdfdb8db",
  "organization_name": "Acme Analytics",
  "role": "Owner"
}
```

## Organization And Invites

### List Members

```http
GET /organizations/members
Authorization: Bearer <access_token>
```

Response:

```json
[
  {
    "id": "0d53c464-d46d-4a90-a12c-7d9644cf2fb7",
    "user_id": "9de0a9fb-0a7c-4d6f-a302-1e3fa51e4f1d",
    "email": "owner@example.com",
    "full_name": "Acme Owner",
    "role": "Owner"
  }
]
```

### Create Invite

Allowed roles: `Owner`, `Admin`.

```http
POST /organizations/invites
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "email": "teammate@example.com",
  "role": "Analyst"
}
```

Response `201`:

```json
{
  "id": "9327cbce-7acb-4b49-aef2-88daf0e3cc01",
  "email": "teammate@example.com",
  "role": "Analyst",
  "expires_at": "2026-06-12T10:00:00Z",
  "accepted_at": null
}
```

### List Invites

Allowed roles: `Owner`, `Admin`.

```http
GET /organizations/invites
Authorization: Bearer <access_token>
```

### Local Dev Outbox

Allowed roles: `Owner`, `Admin`.

The outbox exposes invite tokens for local/demo delivery instead of real email.

```http
GET /organizations/dev-outbox
Authorization: Bearer <access_token>
```

Response:

```json
[
  {
    "id": "7e0443ea-3796-4657-a6b2-ed9d1039ad8d",
    "recipient_email": "teammate@example.com",
    "subject": "You're invited to Pulseboard Analytics",
    "body": "Use this local invite token to join: ...",
    "payload": {
      "token": "<invite_token>",
      "role": "Analyst"
    },
    "created_at": "2026-06-05T10:00:00Z"
  }
]
```

### Accept Invite

```http
POST /organizations/invites/accept
Content-Type: application/json
```

Request:

```json
{
  "token": "<invite_token>",
  "full_name": "Teammate User",
  "password": "StrongPassword123!"
}
```

Response:

```json
{
  "message": "Invite accepted."
}
```

## API Keys

### List API Keys

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
GET /api-keys
Authorization: Bearer <access_token>
```

Response:

```json
[
  {
    "id": "313c9815-eed0-48cf-83f6-0c1858532e3c",
    "name": "Production ingestion",
    "prefix": "pa_xxxxxxxx",
    "created_at": "2026-06-05T10:00:00Z",
    "revoked_at": null,
    "last_used_at": null
  }
]
```

### Create API Key

Allowed roles: `Owner`, `Admin`.

```http
POST /api-keys
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "name": "Production ingestion"
}
```

Response `201`:

```json
{
  "id": "313c9815-eed0-48cf-83f6-0c1858532e3c",
  "name": "Production ingestion",
  "prefix": "pa_xxxxxxxx",
  "key": "pa_<secret_value_shown_once>",
  "created_at": "2026-06-05T10:00:00Z"
}
```

### Rotate API Key

Allowed roles: `Owner`, `Admin`.

```http
POST /api-keys/{api_key_id}/rotate
Authorization: Bearer <access_token>
```

Response includes a new `key` value. The previous key value is no longer valid.

### Revoke API Key

Allowed roles: `Owner`, `Admin`.

```http
DELETE /api-keys/{api_key_id}
Authorization: Bearer <access_token>
```

Response:

```json
{
  "message": "API key revoked."
}
```

## Event Ingestion

Ingestion endpoints require:

```http
X-API-Key: <api_key>
```

Events are first stored as raw events, then Celery normalizes them asynchronously into the queryable events table.

### Ingest One Event

```http
POST /ingest/event
X-API-Key: <api_key>
Content-Type: application/json
```

Request:

```json
{
  "event_name": "page_view",
  "timestamp": "2026-06-05T10:15:00Z",
  "user_id": "user_123",
  "properties": {
    "path": "/pricing",
    "plan": "team",
    "campaign": "paid-search"
  }
}
```

Response `202`:

```json
{
  "accepted": 1,
  "rejected": 0,
  "raw_event_ids": ["9d536d93-f506-4466-98a3-b372be2fdc16"],
  "errors": []
}
```

### Ingest Batch

Maximum events per request: `500`.

```http
POST /ingest/batch
X-API-Key: <api_key>
Content-Type: application/json
```

Request:

```json
{
  "events": [
    {
      "event_name": "page_view",
      "timestamp": "2026-06-05T10:15:00Z",
      "user_id": "user_123",
      "properties": {
        "path": "/pricing"
      }
    },
    {
      "event_name": "signup_completed",
      "timestamp": "2026-06-05T10:16:00Z",
      "user_id": "user_123",
      "properties": {
        "plan": "team"
      }
    }
  ]
}
```

### Upload CSV

Required CSV columns:

```text
event_name,timestamp,user_id,properties
```

`properties` must be a valid JSON object string.

```http
POST /ingest/csv
X-API-Key: <api_key>
Content-Type: multipart/form-data
```

Example CSV:

```csv
event_name,timestamp,user_id,properties
page_view,2026-06-05T10:15:00Z,user_123,"{""path"":""/pricing"",""plan"":""team""}"
signup_completed,2026-06-05T10:16:00Z,user_123,"{""plan"":""team""}"
```

Response with partial failure:

```json
{
  "filename": "events.csv",
  "accepted": 10,
  "rejected": 2,
  "raw_event_ids": ["..."],
  "errors": [
    {
      "row": 7,
      "message": "timestamp: Input should be a valid datetime"
    }
  ]
}
```

## Dashboards

### List Dashboards

```http
GET /dashboards
Authorization: Bearer <access_token>
```

### Create Dashboard

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
POST /dashboards
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "name": "Growth Overview",
  "description": "Core acquisition and conversion metrics.",
  "auto_refresh_seconds": 30
}
```

Allowed `auto_refresh_seconds` values:

```text
30, 60, 300
```

Response `201`:

```json
{
  "id": "b9fb25ec-ed6d-43ed-9d6e-7e7c28a41993",
  "name": "Growth Overview",
  "description": "Core acquisition and conversion metrics.",
  "visibility": "team",
  "auto_refresh_seconds": 30,
  "share_token": null,
  "created_at": "2026-06-05T10:00:00Z",
  "updated_at": "2026-06-05T10:00:00Z"
}
```

### Get Dashboard

```http
GET /dashboards/{dashboard_id}
Authorization: Bearer <access_token>
```

Response includes `widgets`.

### Update Dashboard

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
PATCH /dashboards/{dashboard_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "name": "Updated Growth Overview",
  "auto_refresh_seconds": 60
}
```

### Delete Dashboard

Allowed roles: `Owner`, `Admin`.

```http
DELETE /dashboards/{dashboard_id}
Authorization: Bearer <access_token>
```

## Widgets

Supported widget kinds:

```text
line, bar, pie, kpi, table
```

Supported aggregates:

```text
count, unique_users
```

Supported time buckets:

```text
minute, hour, day
```

Supported filter operators:

```text
eq, neq, contains
```

Allowed group-by fields:

```text
event_name
user_id
source_type
property:<property_name>
```

### Add Widget

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
POST /dashboards/{dashboard_id}/widgets
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request:

```json
{
  "title": "Page views by day",
  "kind": "line",
  "query": {
    "aggregate": "count",
    "event_name": "page_view",
    "group_by": null,
    "time_bucket": "day",
    "filters": [
      {
        "field": "property:plan",
        "op": "eq",
        "value": "team"
      }
    ],
    "from_ts": "2026-05-01T00:00:00Z",
    "to_ts": "2026-06-05T23:59:59Z"
  },
  "layout": {
    "x": 0,
    "y": 0,
    "w": 8,
    "h": 4
  }
}
```

Layout rules:

| Field | Rule |
| --- | --- |
| `x` | `>= 0` |
| `y` | `>= 0` |
| `w` | `1..12` |
| `h` | `1..12` |

### Update Widget

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
PATCH /dashboards/widgets/{widget_id}
Authorization: Bearer <access_token>
Content-Type: application/json
```

Request can include any of:

```json
{
  "title": "Updated title",
  "kind": "bar",
  "query": {
    "aggregate": "count",
    "event_name": "signup_completed",
    "group_by": "property:plan",
    "time_bucket": null,
    "filters": []
  },
  "layout": {
    "x": 0,
    "y": 4,
    "w": 6,
    "h": 4
  }
}
```

### Delete Widget

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
DELETE /dashboards/widgets/{widget_id}
Authorization: Bearer <access_token>
```

### Get Widget Data

```http
GET /dashboards/widgets/{widget_id}/data
Authorization: Bearer <access_token>
```

Example response:

```json
{
  "widget_id": "e8aa4b94-b360-4ce1-b21b-df72e3c186819",
  "kind": "line",
  "rows": [
    {
      "bucket": "2026-06-05T00:00:00Z",
      "value": 42
    }
  ]
}
```

Grouped response example:

```json
{
  "widget_id": "e8aa4b94-b360-4ce1-b21b-df72e3c186819",
  "kind": "bar",
  "rows": [
    {
      "group": "team",
      "value": 12
    },
    {
      "group": "enterprise",
      "value": 4
    }
  ]
}
```

## Sharing

### Create Public Share Link

Allowed roles: `Owner`, `Admin`, `Analyst`.

```http
POST /dashboards/{dashboard_id}/share
Authorization: Bearer <access_token>
```

Response:

```json
{
  "dashboard_id": "b9fb25ec-ed6d-43ed-9d6e-7e7c28a41993",
  "share_token": "public_share_token",
  "public_url": "https://your-frontend.example.com/share/public_share_token"
}
```

Public share links are read-only.

### Get Public Dashboard

No authentication required.

```http
GET /public/dashboards/{share_token}
```

### Get Public Widget Data

No authentication required.

```http
GET /public/dashboards/{share_token}/widgets/{widget_id}/data
```

## Curl Examples

Set a base URL:

```bash
export API_BASE_URL="https://real-time-analytics-reporting-platform.onrender.com/api/v1"
```

Sign in:

```bash
curl -sS -X POST "$API_BASE_URL/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"StrongPassword123!"}'
```

Create an API key:

```bash
curl -sS -X POST "$API_BASE_URL/api-keys" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Server ingestion"}'
```

Send one event:

```bash
curl -sS -X POST "$API_BASE_URL/ingest/event" \
  -H "X-API-Key: <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "page_view",
    "timestamp": "2026-06-05T10:15:00Z",
    "user_id": "user_123",
    "properties": {
      "path": "/pricing",
      "plan": "team"
    }
  }'
```

Create a dashboard:

```bash
curl -sS -X POST "$API_BASE_URL/dashboards" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Growth Overview",
    "description": "Core acquisition metrics",
    "auto_refresh_seconds": 30
  }'
```

Create a KPI widget:

```bash
curl -sS -X POST "$API_BASE_URL/dashboards/<dashboard_id>/widgets" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Total page views",
    "kind": "kpi",
    "query": {
      "aggregate": "count",
      "event_name": "page_view",
      "group_by": null,
      "time_bucket": null,
      "filters": []
    },
    "layout": {
      "x": 0,
      "y": 0,
      "w": 3,
      "h": 3
    }
  }'
```

## Operational Notes

- Timestamps should be ISO 8601 strings.
- Request bodies should use `application/json`, except CSV upload which uses `multipart/form-data`.
- Ingestion is asynchronous. Dashboard rows can take a few seconds to appear after event acceptance.
- Public dashboard endpoints are read-only and do not accept write requests.
- Do not expose API keys or JWT tokens in client-side code, public repos, logs, or screenshots.
- Rotate API keys from the API key page or `POST /api-keys/{api_key_id}/rotate` if a key is exposed.
