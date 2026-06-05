"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

import { PageHeader } from "@/components/app/page-header";
import { DashboardBuilder } from "@/components/dashboard/dashboard-builder";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import type { Dashboard } from "@/types/api";

export default function DashboardsPage() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [name, setName] = useState("Growth Overview");
  const [refresh, setRefresh] = useState("60");
  const dashboards = useQuery({
    queryKey: ["dashboards"],
    queryFn: () => apiFetch<Dashboard[]>("/dashboards")
  });

  useEffect(() => {
    if (!selectedId && dashboards.data?.[0]) {
      setSelectedId(dashboards.data[0].id);
    }
  }, [dashboards.data, selectedId]);

  const createDashboard = useMutation({
    mutationFn: () =>
      apiFetch<Dashboard>("/dashboards", {
        method: "POST",
        body: JSON.stringify({
          name,
          auto_refresh_seconds: Number(refresh)
        })
      }),
    onSuccess: (dashboard) => {
      setSelectedId(dashboard.id);
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
    }
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createDashboard.mutate();
  }

  return (
    <div>
      <PageHeader
        title="Dashboard builder"
        description="Create dashboards, arrange widgets, share read-only public links, and auto-refresh metrics."
      />
      <Panel className="mb-5">
        <PanelBody>
          <form className="grid gap-3 md:grid-cols-[1fr_180px_auto]" onSubmit={submit}>
            <div className="space-y-2">
              <Label htmlFor="dashboard-name">Dashboard name</Label>
              <Input id="dashboard-name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="refresh">Auto-refresh</Label>
              <Select id="refresh" value={refresh} onChange={(event) => setRefresh(event.target.value)}>
                <option value="30">30s</option>
                <option value="60">1m</option>
                <option value="300">5m</option>
              </Select>
            </div>
            <div className="flex items-end">
              <Button disabled={createDashboard.isPending}>
                <Plus className="h-4 w-4" aria-hidden />
                Create
              </Button>
            </div>
          </form>
          {createDashboard.error ? (
            <div className="mt-4">
              <ErrorState message={(createDashboard.error as Error).message} />
            </div>
          ) : null}
        </PanelBody>
      </Panel>

      {dashboards.isLoading ? <LoadingState label="Loading dashboards" /> : null}
      {dashboards.error ? <ErrorState message={(dashboards.error as Error).message} /> : null}
      {dashboards.data?.length ? (
        <div className="mb-5 flex gap-2 overflow-x-auto">
          {dashboards.data.map((dashboard) => (
            <button
              key={dashboard.id}
              className={`flex h-10 shrink-0 items-center gap-2 rounded-md border px-3 text-sm ${
                selectedId === dashboard.id
                  ? "border-primary bg-primary text-white"
                  : "border-border bg-panel text-foreground"
              }`}
              onClick={() => setSelectedId(dashboard.id)}
            >
              {dashboard.name}
              <Badge tone={dashboard.visibility === "public" ? "success" : "neutral"}>
                {dashboard.visibility}
              </Badge>
            </button>
          ))}
        </div>
      ) : null}

      {dashboards.data?.length === 0 ? (
        <EmptyState
          title="No dashboards yet"
          description="Create your first dashboard, then add widgets connected to event metrics."
        />
      ) : null}

      {selectedId ? <DashboardBuilder dashboardId={selectedId} /> : null}
    </div>
  );
}

