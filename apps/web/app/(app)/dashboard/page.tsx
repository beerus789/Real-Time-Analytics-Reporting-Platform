"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3, DatabaseZap, KeyRound, UsersRound } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/app/page-header";
import { StatTile } from "@/components/app/stat-tile";
import { Badge } from "@/components/ui/badge";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { Table, Td, Th } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";
import type { ApiKeyRecord, Dashboard, Member } from "@/types/api";

export default function OverviewPage() {
  const dashboards = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => apiFetch<Dashboard[]>("/dashboards")
  });
  const apiKeys = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => apiFetch<ApiKeyRecord[]>("/api-keys")
  });
  const members = useQuery({
    queryKey: ["members"],
    queryFn: () => apiFetch<Member[]>("/organizations/members")
  });

  const activeKeys = apiKeys.data?.filter((item) => !item.revoked_at).length ?? 0;
  const widgetCount = dashboards.data?.reduce((sum, item) => sum + (item.widgets?.length ?? 0), 0) ?? 0;

  return (
    <div>
      <PageHeader
        title="Analytics overview"
        description="Operate ingestion, dashboards, sharing, and team access from a single workspace."
        actions={
          <Link
            href="/dashboards"
            className="inline-flex h-10 items-center justify-center rounded-md border border-primary bg-primary px-4 text-sm font-medium text-white transition hover:bg-primary/90"
          >
            Open dashboards
          </Link>
        }
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatTile
          label="Dashboards"
          value={String(dashboards.data?.length ?? 0)}
          helper={`${widgetCount} configured widgets`}
          icon={BarChart3}
        />
        <StatTile label="Active API keys" value={String(activeKeys)} helper="Ingestion access" icon={KeyRound} />
        <StatTile
          label="Team members"
          value={String(members.data?.length ?? 0)}
          helper="RBAC enabled"
          icon={UsersRound}
        />
        <StatTile label="Pipeline" value="Async" helper="Celery-backed normalization" icon={DatabaseZap} />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1.6fr_1fr]">
        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">Recent dashboards</h2>
          </PanelHeader>
          <PanelBody>
            {dashboards.isLoading ? <LoadingState /> : null}
            {dashboards.error ? <ErrorState message={(dashboards.error as Error).message} /> : null}
            {dashboards.data?.length === 0 ? (
              <EmptyState
                title="No dashboards yet"
                description="Create a dashboard and connect widgets to incoming analytics events."
              />
            ) : null}
            {dashboards.data?.length ? (
              <Table>
                <thead>
                  <tr>
                    <Th>Name</Th>
                    <Th>Sharing</Th>
                    <Th>Refresh</Th>
                    <Th>Updated</Th>
                  </tr>
                </thead>
                <tbody>
                  {dashboards.data.map((dashboard) => (
                    <tr key={dashboard.id}>
                      <Td>
                        <Link className="font-medium text-primary" href="/dashboards">
                          {dashboard.name}
                        </Link>
                      </Td>
                      <Td>
                        <Badge tone={dashboard.visibility === "public" ? "success" : "neutral"}>
                          {dashboard.visibility}
                        </Badge>
                      </Td>
                      <Td>{dashboard.auto_refresh_seconds}s</Td>
                      <Td>{new Date(dashboard.updated_at).toLocaleString()}</Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : null}
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">Operational checklist</h2>
          </PanelHeader>
          <PanelBody>
            <div className="space-y-3 text-sm">
              <div className="rounded-md border border-border p-3">
                <div className="font-medium">1. Create an API key</div>
                <div className="mt-1 text-muted-foreground">Use it from server-side ingestion clients.</div>
              </div>
              <div className="rounded-md border border-border p-3">
                <div className="font-medium">2. Send events or upload CSV</div>
                <div className="mt-1 text-muted-foreground">Valid rows continue even when CSV rows fail.</div>
              </div>
              <div className="rounded-md border border-border p-3">
                <div className="font-medium">3. Build dashboard widgets</div>
                <div className="mt-1 text-muted-foreground">Use the safe query builder with auto-refresh.</div>
              </div>
            </div>
          </PanelBody>
        </Panel>
      </div>
    </div>
  );
}
