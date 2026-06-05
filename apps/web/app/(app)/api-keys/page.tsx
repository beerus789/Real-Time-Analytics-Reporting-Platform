"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, KeyRound, RefreshCw, Trash2 } from "lucide-react";
import { FormEvent, useState } from "react";

import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { Table, Td, Th } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";
import type { ApiKeyCreated, ApiKeyRecord } from "@/types/api";

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("Production ingestion");
  const [latestKey, setLatestKey] = useState<string | null>(null);
  const keys = useQuery({
    queryKey: ["api-keys"],
    queryFn: () => apiFetch<ApiKeyRecord[]>("/api-keys")
  });

  const createKey = useMutation({
    mutationFn: () =>
      apiFetch<ApiKeyCreated>("/api-keys", {
        method: "POST",
        body: JSON.stringify({ name })
      }),
    onSuccess: (data) => {
      setLatestKey(data.key);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    }
  });

  const revokeKey = useMutation({
    mutationFn: (id: string) => apiFetch(`/api-keys/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] })
  });

  const rotateKey = useMutation({
    mutationFn: (id: string) => apiFetch<ApiKeyCreated>(`/api-keys/${id}/rotate`, { method: "POST" }),
    onSuccess: (data) => {
      setLatestKey(data.key);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    }
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createKey.mutate();
  }

  return (
    <div>
      <PageHeader
        title="API keys"
        description="Generate, rotate, and revoke organization-scoped ingestion keys. Secret values are shown once."
      />
      <Panel className="mb-5">
        <PanelBody>
          <form className="flex flex-col gap-3 md:flex-row md:items-end" onSubmit={submit}>
            <div className="w-full space-y-2">
              <Label htmlFor="key-name">Key name</Label>
              <Input id="key-name" value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <Button disabled={createKey.isPending}>
              <KeyRound className="h-4 w-4" aria-hidden />
              Generate
            </Button>
          </form>
          {latestKey ? (
            <div className="mt-4 flex flex-col gap-3 rounded-md border border-success/20 bg-success/5 p-4 md:flex-row md:items-center md:justify-between">
              <code className="break-all text-sm">{latestKey}</code>
              <Button variant="secondary" size="sm" onClick={() => navigator.clipboard.writeText(latestKey)}>
                <Copy className="h-4 w-4" aria-hidden />
                Copy
              </Button>
            </div>
          ) : null}
          {createKey.error ? (
            <div className="mt-4">
              <ErrorState message={(createKey.error as Error).message} />
            </div>
          ) : null}
        </PanelBody>
      </Panel>
      <Panel>
        <PanelHeader>
          <h2 className="text-base font-semibold">Keys</h2>
        </PanelHeader>
        <PanelBody>
          {keys.isLoading ? <LoadingState /> : null}
          {keys.error ? <ErrorState message={(keys.error as Error).message} /> : null}
          {keys.data?.length === 0 ? (
            <EmptyState title="No keys yet" description="Create an API key before sending events." />
          ) : null}
          {keys.data?.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Name</Th>
                  <Th>Prefix</Th>
                  <Th>Status</Th>
                  <Th>Last used</Th>
                  <Th>Actions</Th>
                </tr>
              </thead>
              <tbody>
                {keys.data.map((key) => (
                  <tr key={key.id}>
                    <Td className="font-medium">{key.name}</Td>
                    <Td>{key.prefix}</Td>
                    <Td>
                      <Badge tone={key.revoked_at ? "danger" : "success"}>
                        {key.revoked_at ? "revoked" : "active"}
                      </Badge>
                    </Td>
                    <Td>{key.last_used_at ? new Date(key.last_used_at).toLocaleString() : "Never"}</Td>
                    <Td>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm" onClick={() => rotateKey.mutate(key.id)}>
                          <RefreshCw className="h-4 w-4" aria-hidden />
                          Rotate
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => revokeKey.mutate(key.id)}>
                          <Trash2 className="h-4 w-4" aria-hidden />
                          Revoke
                        </Button>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : null}
        </PanelBody>
      </Panel>
    </div>
  );
}

