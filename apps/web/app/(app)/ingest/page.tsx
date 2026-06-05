"use client";

import { useMutation } from "@tanstack/react-query";
import { UploadCloud, Zap } from "lucide-react";
import { FormEvent, useState } from "react";

import { PageHeader } from "@/components/app/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/ui/state";
import type { IngestResponse } from "@/types/api";

const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";

async function ingest(path: string, apiKey: string, init: RequestInit): Promise<IngestResponse> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      "X-API-Key": apiKey
    }
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Ingestion request failed");
  }
  return response.json();
}

export default function IngestPage() {
  const [apiKey, setApiKey] = useState("");
  const [eventName, setEventName] = useState("page_view");
  const [userId, setUserId] = useState("user-123");
  const [properties, setProperties] = useState('{"path":"/pricing","browser":"Chrome"}');
  const [csvFile, setCsvFile] = useState<File | null>(null);

  const eventMutation = useMutation({
    mutationFn: () =>
      ingest("/ingest/event", apiKey, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_name: eventName,
          timestamp: new Date().toISOString(),
          user_id: userId || null,
          properties: JSON.parse(properties || "{}")
        })
      })
  });

  const csvMutation = useMutation({
    mutationFn: () => {
      if (!csvFile) {
        throw new Error("Choose a CSV file first");
      }
      const form = new FormData();
      form.append("file", csvFile);
      return ingest("/ingest/csv", apiKey, {
        method: "POST",
        body: form
      });
    }
  });

  function submitEvent(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    eventMutation.mutate();
  }

  function submitCsv(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    csvMutation.mutate();
  }

  return (
    <div>
      <PageHeader
        title="Data ingestion"
        description="Send single events through the API key path or upload CSV files with row-level failure reporting."
      />
      <div className="grid gap-5 xl:grid-cols-2">
        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">Event tester</h2>
          </PanelHeader>
          <PanelBody>
            <form className="space-y-4" onSubmit={submitEvent}>
              <div className="space-y-2">
                <Label htmlFor="api-key">API key</Label>
                <Input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="pa_..."
                  required
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="event-name">Event name</Label>
                  <Input
                    id="event-name"
                    value={eventName}
                    onChange={(event) => setEventName(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="user-id">User ID</Label>
                  <Input id="user-id" value={userId} onChange={(event) => setUserId(event.target.value)} />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="properties">Properties JSON</Label>
                <Textarea
                  id="properties"
                  value={properties}
                  onChange={(event) => setProperties(event.target.value)}
                />
              </div>
              {eventMutation.error ? <ErrorState message={(eventMutation.error as Error).message} /> : null}
              {eventMutation.data ? (
                <div className="rounded-md border border-success/20 bg-success/5 p-4 text-sm text-success">
                  Accepted {eventMutation.data.accepted} event.
                </div>
              ) : null}
              <Button disabled={eventMutation.isPending}>
                <Zap className="h-4 w-4" aria-hidden />
                Send event
              </Button>
            </form>
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">CSV upload</h2>
          </PanelHeader>
          <PanelBody>
            <form className="space-y-4" onSubmit={submitCsv}>
              <div className="space-y-2">
                <Label htmlFor="csv-api-key">API key</Label>
                <Input
                  id="csv-api-key"
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="pa_..."
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="csv-file">CSV file</Label>
                <Input
                  id="csv-file"
                  type="file"
                  accept=".csv,text/csv"
                  onChange={(event) => setCsvFile(event.target.files?.[0] ?? null)}
                />
              </div>
              <div className="rounded-md border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
                Required columns: event_name, timestamp, user_id, properties.
              </div>
              {csvMutation.error ? <ErrorState message={(csvMutation.error as Error).message} /> : null}
              {csvMutation.data ? (
                <div className="rounded-md border border-border bg-panel p-4 text-sm">
                  <div>Accepted: {csvMutation.data.accepted}</div>
                  <div>Rejected: {csvMutation.data.rejected}</div>
                  {csvMutation.data.errors.length ? (
                    <pre className="mt-3 max-h-44 overflow-auto rounded-md bg-muted p-3 text-xs">
                      {JSON.stringify(csvMutation.data.errors, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ) : null}
              <Button disabled={csvMutation.isPending}>
                <UploadCloud className="h-4 w-4" aria-hidden />
                Upload CSV
              </Button>
            </form>
          </PanelBody>
        </Panel>
      </div>
    </div>
  );
}
