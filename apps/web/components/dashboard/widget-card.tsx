"use client";

import { useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { WidgetChart } from "@/components/dashboard/widget-chart";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import type { Widget, WidgetData } from "@/types/api";

export function WidgetCard({
  widget,
  refreshMs,
  shareToken
}: {
  widget: Widget;
  refreshMs: number;
  shareToken?: string;
}) {
  const path = shareToken
    ? `/public/dashboards/${shareToken}/widgets/${widget.id}/data`
    : `/dashboards/widgets/${widget.id}/data`;
  const dataQuery = useQuery({
    queryKey: ["widget-data", widget.id, shareToken],
    queryFn: () => apiFetch<WidgetData>(path),
    refetchInterval: refreshMs
  });

  return (
    <Panel className="h-full overflow-hidden">
      <PanelHeader className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold">{widget.title}</div>
          <div className="mt-1 flex flex-wrap gap-2">
            <Badge>{widget.kind}</Badge>
            {widget.query.time_bucket ? <Badge tone="success">{widget.query.time_bucket}</Badge> : null}
          </div>
        </div>
        <Button
          size="icon"
          variant="ghost"
          title="Refresh data"
          onClick={() => dataQuery.refetch()}
        >
          <RefreshCw className="h-4 w-4" aria-hidden />
        </Button>
      </PanelHeader>
      <PanelBody className="h-[calc(100%-78px)]">
        {dataQuery.isLoading ? <LoadingState label="Loading widget" /> : null}
        {dataQuery.error ? <ErrorState message={(dataQuery.error as Error).message} /> : null}
        {dataQuery.data ? <WidgetChart widget={widget} data={dataQuery.data} /> : null}
      </PanelBody>
    </Panel>
  );
}
