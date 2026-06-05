"use client";

import { useQuery } from "@tanstack/react-query";
import { BarChart3 } from "lucide-react";
import Link from "next/link";

import { WidgetCard } from "@/components/dashboard/widget-card";
import { Badge } from "@/components/ui/badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import type { Dashboard } from "@/types/api";

export default function PublicDashboardPage({ params }: { params: { token: string } }) {
  const dashboard = useQuery({
    queryKey: ["public-dashboard", params.token],
    queryFn: () => apiFetch<Dashboard>(`/public/dashboards/${params.token}`)
  });

  return (
    <main className="min-h-screen bg-background px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-6 flex flex-col justify-between gap-4 border-b border-border pb-5 md:flex-row md:items-end">
          <div>
            <Link href="/login" className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary">
              <BarChart3 className="h-4 w-4" aria-hidden />
              Pulseboard
            </Link>
            <h1 className="text-2xl font-semibold tracking-normal">
              {dashboard.data?.name ?? "Shared dashboard"}
            </h1>
            {dashboard.data?.description ? (
              <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
                {dashboard.data.description}
              </p>
            ) : null}
          </div>
          <Badge tone="success">read-only public link</Badge>
        </header>
        {dashboard.isLoading ? <LoadingState label="Loading shared dashboard" /> : null}
        {dashboard.error ? <ErrorState message={(dashboard.error as Error).message} /> : null}
        {dashboard.data?.widgets?.length === 0 ? (
          <EmptyState title="No public widgets" description="This dashboard has not published widgets yet." />
        ) : null}
        <div className="grid gap-4 lg:grid-cols-2">
          {dashboard.data?.widgets?.map((widget) => (
            <div key={widget.id} className={widget.kind === "kpi" ? "" : "lg:col-span-1"}>
              <WidgetCard
                widget={widget}
                refreshMs={dashboard.data.auto_refresh_seconds * 1000}
                shareToken={params.token}
              />
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

