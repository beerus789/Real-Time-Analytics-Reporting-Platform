"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Share2 } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { Layout, Responsive, WidthProvider } from "react-grid-layout";

import { WidgetCard } from "@/components/dashboard/widget-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import type { Dashboard, Widget, WidgetKind, WidgetQuery } from "@/types/api";

const defaultQuery: WidgetQuery = {
  aggregate: "count",
  event_name: "page_view",
  group_by: null,
  time_bucket: "day",
  filters: []
};

const ResponsiveGridLayout = WidthProvider(Responsive);

export function DashboardBuilder({ dashboardId }: { dashboardId: string }) {
  const queryClient = useQueryClient();
  const [widgetTitle, setWidgetTitle] = useState("Page views");
  const [widgetKind, setWidgetKind] = useState<WidgetKind>("line");
  const [eventName, setEventName] = useState("page_view");

  const dashboardQuery = useQuery({
    queryKey: ["dashboard", dashboardId],
    queryFn: () => apiFetch<Dashboard>(`/dashboards/${dashboardId}`)
  });

  const widgets = dashboardQuery.data?.widgets ?? [];
  const refreshMs = (dashboardQuery.data?.auto_refresh_seconds ?? 60) * 1000;
  const layout = useMemo<Layout[]>(
    () =>
      widgets.map((widget) => ({
        i: widget.id,
        x: widget.layout.x,
        y: widget.layout.y,
        w: widget.layout.w,
        h: widget.layout.h,
        minW: 3,
        minH: 3
      })),
    [widgets]
  );

  const addWidget = useMutation({
    mutationFn: () =>
      apiFetch<Widget>(`/dashboards/${dashboardId}/widgets`, {
        method: "POST",
        body: JSON.stringify({
          title: widgetTitle,
          kind: widgetKind,
          query: { ...defaultQuery, event_name: eventName || null },
          layout: { x: 0, y: widgets.length * 4, w: widgetKind === "kpi" ? 4 : 6, h: 4 }
        })
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard", dashboardId] })
  });

  const updateLayout = useMutation({
    mutationFn: async (items: Layout[]) => {
      await Promise.all(
        items.map((item) =>
          apiFetch(`/dashboards/widgets/${item.i}`, {
            method: "PATCH",
            body: JSON.stringify({
              layout: { x: item.x, y: item.y, w: item.w, h: item.h }
            })
          })
        )
      );
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard", dashboardId] })
  });

  const share = useMutation({
    mutationFn: () =>
      apiFetch<{ public_url: string }>(`/dashboards/${dashboardId}/share`, {
        method: "POST"
      })
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    addWidget.mutate();
  }

  if (dashboardQuery.isLoading) {
    return <LoadingState label="Loading dashboard" />;
  }

  if (dashboardQuery.error || !dashboardQuery.data) {
    return <ErrorState message={(dashboardQuery.error as Error)?.message ?? "Dashboard not found"} />;
  }

  return (
    <div className="space-y-5">
      <Panel>
        <PanelHeader className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <h2 className="text-lg font-semibold">{dashboardQuery.data.name}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Auto-refresh every {dashboardQuery.data.auto_refresh_seconds}s
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => share.mutate()} disabled={share.isPending}>
              <Share2 className="h-4 w-4" aria-hidden />
              Share
            </Button>
            {share.data?.public_url ? (
              <Button
                variant="ghost"
                onClick={() => navigator.clipboard.writeText(share.data.public_url)}
              >
                <Copy className="h-4 w-4" aria-hidden />
                Copy link
              </Button>
            ) : null}
          </div>
        </PanelHeader>
        <PanelBody>
          <form className="grid gap-3 md:grid-cols-[1fr_160px_1fr_auto]" onSubmit={submit}>
            <div className="space-y-2">
              <Label htmlFor="widget-title">Widget title</Label>
              <Input
                id="widget-title"
                value={widgetTitle}
                onChange={(event) => setWidgetTitle(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="widget-kind">Type</Label>
              <Select
                id="widget-kind"
                value={widgetKind}
                onChange={(event) => setWidgetKind(event.target.value as WidgetKind)}
              >
                <option value="line">Line</option>
                <option value="bar">Bar</option>
                <option value="pie">Pie</option>
                <option value="kpi">KPI</option>
                <option value="table">Table</option>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-name">Event name</Label>
              <Input
                id="event-name"
                value={eventName}
                onChange={(event) => setEventName(event.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button disabled={addWidget.isPending}>
                <Plus className="h-4 w-4" aria-hidden />
                Add
              </Button>
            </div>
          </form>
          {addWidget.error ? (
            <div className="mt-4">
              <ErrorState message={(addWidget.error as Error).message} />
            </div>
          ) : null}
        </PanelBody>
      </Panel>

      {widgets.length === 0 ? (
        <EmptyState
          title="No widgets yet"
          description="Add a chart, KPI, or table widget to start shaping this dashboard."
        />
      ) : (
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: layout, md: layout, sm: layout, xs: layout, xxs: layout }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={96}
          margin={[16, 16]}
          onDragStop={(items: Layout[]) => updateLayout.mutate(items)}
          onResizeStop={(items: Layout[]) => updateLayout.mutate(items)}
        >
          {widgets.map((widget) => (
            <div key={widget.id}>
              <WidgetCard widget={widget} refreshMs={refreshMs} />
            </div>
          ))}
        </ResponsiveGridLayout>
      )}
    </div>
  );
}
