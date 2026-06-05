"use client";

import { useMutation } from "@tanstack/react-query";
import { Building2, UserPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody } from "@/components/ui/panel";
import { ErrorState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { UserProfile } from "@/types/api";

export default function SignupPage() {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const [form, setForm] = useState({
    organization_name: "Acme Analytics",
    full_name: "Acme Owner",
    email: "owner@example.com",
    password: "Password123!"
  });

  const mutation = useMutation({
    mutationFn: async () => {
      const token = await apiFetch<{ access_token: string }>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(form)
      });
      setSession(token.access_token);
      const profile = await apiFetch<UserProfile>("/auth/me", { token: token.access_token });
      setSession(token.access_token, profile);
      return profile;
    },
    onSuccess: () => router.replace("/dashboard")
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-xl">
        <div className="mb-8">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-md bg-accent text-white">
            <Building2 className="h-5 w-5" aria-hidden />
          </div>
          <h1 className="text-2xl font-semibold tracking-normal">Create your analytics workspace</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Signup creates the organization and assigns you the Owner role.
          </p>
        </div>
        <Panel>
          <PanelBody>
            <form className="grid gap-4 md:grid-cols-2" onSubmit={submit}>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="organization">Organization</Label>
                <Input
                  id="organization"
                  value={form.organization_name}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, organization_name: event.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Full name</Label>
                <Input
                  id="name"
                  value={form.full_name}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, full_name: event.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, email: event.target.value }))
                  }
                  required
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={form.password}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, password: event.target.value }))
                  }
                  required
                />
              </div>
              {mutation.error ? (
                <div className="md:col-span-2">
                  <ErrorState message={(mutation.error as Error).message} />
                </div>
              ) : null}
              <div className="md:col-span-2">
                <Button className="w-full" disabled={mutation.isPending}>
                  <UserPlus className="h-4 w-4" aria-hidden />
                  Create workspace
                </Button>
              </div>
            </form>
          </PanelBody>
        </Panel>
        <p className="mt-5 text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-primary">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}

