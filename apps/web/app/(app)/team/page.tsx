"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, MailPlus } from "lucide-react";
import { FormEvent, useState } from "react";

import { PageHeader } from "@/components/app/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody, PanelHeader } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/state";
import { Table, Td, Th } from "@/components/ui/table";
import { apiFetch } from "@/lib/api";
import type { Invitation, Member, OutboxMessage, Role } from "@/types/api";

export default function TeamPage() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("analyst@example.com");
  const [role, setRole] = useState<Role>("Analyst");

  const members = useQuery({
    queryKey: ["members"],
    queryFn: () => apiFetch<Member[]>("/organizations/members")
  });
  const invites = useQuery({
    queryKey: ["invites"],
    queryFn: () => apiFetch<Invitation[]>("/organizations/invites")
  });
  const outbox = useQuery({
    queryKey: ["dev-outbox"],
    queryFn: () => apiFetch<OutboxMessage[]>("/organizations/dev-outbox")
  });

  const createInvite = useMutation({
    mutationFn: () =>
      apiFetch<Invitation>("/organizations/invites", {
        method: "POST",
        body: JSON.stringify({ email, role })
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invites"] });
      queryClient.invalidateQueries({ queryKey: ["dev-outbox"] });
    }
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createInvite.mutate();
  }

  return (
    <div>
      <PageHeader
        title="Team access"
        description="Manage organization membership, invite roles, and local dev outbox tokens."
      />
      <Panel className="mb-5">
        <PanelBody>
          <form className="grid gap-3 md:grid-cols-[1fr_180px_auto]" onSubmit={submit}>
            <div className="space-y-2">
              <Label htmlFor="invite-email">Invite email</Label>
              <Input
                id="invite-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">Role</Label>
              <Select id="invite-role" value={role} onChange={(event) => setRole(event.target.value as Role)}>
                <option value="Admin">Admin</option>
                <option value="Analyst">Analyst</option>
                <option value="Viewer">Viewer</option>
              </Select>
            </div>
            <div className="flex items-end">
              <Button disabled={createInvite.isPending}>
                <MailPlus className="h-4 w-4" aria-hidden />
                Invite
              </Button>
            </div>
          </form>
          {createInvite.error ? (
            <div className="mt-4">
              <ErrorState message={(createInvite.error as Error).message} />
            </div>
          ) : null}
        </PanelBody>
      </Panel>

      <div className="grid gap-5 xl:grid-cols-2">
        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">Members</h2>
          </PanelHeader>
          <PanelBody>
            {members.isLoading ? <LoadingState /> : null}
            {members.error ? <ErrorState message={(members.error as Error).message} /> : null}
            {members.data?.length ? (
              <Table>
                <thead>
                  <tr>
                    <Th>Name</Th>
                    <Th>Email</Th>
                    <Th>Role</Th>
                  </tr>
                </thead>
                <tbody>
                  {members.data.map((member) => (
                    <tr key={member.id}>
                      <Td className="font-medium">{member.full_name}</Td>
                      <Td>{member.email}</Td>
                      <Td>
                        <Badge tone={member.role === "Owner" ? "success" : "neutral"}>{member.role}</Badge>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            ) : null}
          </PanelBody>
        </Panel>

        <Panel>
          <PanelHeader>
            <h2 className="text-base font-semibold">Dev outbox</h2>
          </PanelHeader>
          <PanelBody>
            {outbox.isLoading ? <LoadingState /> : null}
            {outbox.error ? <ErrorState message={(outbox.error as Error).message} /> : null}
            {outbox.data?.length === 0 ? (
              <EmptyState title="No invite emails" description="Invite a teammate to generate a local token." />
            ) : null}
            <div className="space-y-3">
              {outbox.data?.map((message) => (
                <div key={message.id} className="rounded-md border border-border p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium">{message.recipient_email}</div>
                      <div className="mt-1 text-xs text-muted-foreground">{message.subject}</div>
                    </div>
                    {message.payload.token ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => navigator.clipboard.writeText(message.payload.token ?? "")}
                      >
                        <Copy className="h-4 w-4" aria-hidden />
                        Copy token
                      </Button>
                    ) : null}
                  </div>
                  {message.payload.token ? (
                    <code className="mt-3 block break-all rounded-md bg-muted p-3 text-xs">
                      {message.payload.token}
                    </code>
                  ) : null}
                </div>
              ))}
            </div>
          </PanelBody>
        </Panel>
      </div>

      <Panel className="mt-5">
        <PanelHeader>
          <h2 className="text-base font-semibold">Pending invites</h2>
        </PanelHeader>
        <PanelBody>
          {invites.data?.length ? (
            <Table>
              <thead>
                <tr>
                  <Th>Email</Th>
                  <Th>Role</Th>
                  <Th>Status</Th>
                  <Th>Expires</Th>
                </tr>
              </thead>
              <tbody>
                {invites.data.map((invite) => (
                  <tr key={invite.id}>
                    <Td>{invite.email}</Td>
                    <Td>{invite.role}</Td>
                    <Td>
                      <Badge tone={invite.accepted_at ? "success" : "warning"}>
                        {invite.accepted_at ? "accepted" : "pending"}
                      </Badge>
                    </Td>
                    <Td>{new Date(invite.expires_at).toLocaleString()}</Td>
                  </tr>
                ))}
              </tbody>
            </Table>
          ) : (
            <EmptyState title="No invites yet" description="Pending invites appear here after creation." />
          )}
        </PanelBody>
      </Panel>
    </div>
  );
}

