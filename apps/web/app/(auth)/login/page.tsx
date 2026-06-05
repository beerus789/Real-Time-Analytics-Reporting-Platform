"use client";

import { useMutation } from "@tanstack/react-query";
import { Eye, LogIn } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Panel, PanelBody } from "@/components/ui/panel";
import { ErrorState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { UserProfile } from "@/types/api";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") ?? "/dashboard";
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("owner@example.com");
  const [password, setPassword] = useState("Password123!");

  const mutation = useMutation({
    mutationFn: async () => {
      const token = await apiFetch<{ access_token: string }>("/auth/signin", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      setSession(token.access_token);
      const profile = await apiFetch<UserProfile>("/auth/me", { token: token.access_token });
      setSession(token.access_token, profile);
      return profile;
    },
    onSuccess: () => router.replace(next)
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8">
          <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-md bg-primary text-white">
            <Eye className="h-5 w-5" aria-hidden />
          </div>
          <h1 className="text-2xl font-semibold tracking-normal">Sign in to Pulseboard</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Continue into your analytics workspace.
          </p>
        </div>
        <Panel>
          <PanelBody>
            <form className="space-y-4" onSubmit={submit}>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
              {mutation.error ? <ErrorState message={(mutation.error as Error).message} /> : null}
              <Button className="w-full" disabled={mutation.isPending}>
                <LogIn className="h-4 w-4" aria-hidden />
                Sign in
              </Button>
            </form>
          </PanelBody>
        </Panel>
        <p className="mt-5 text-sm text-muted-foreground">
          New workspace?{" "}
          <Link href="/signup" className="font-medium text-primary">
            Create an organization
          </Link>
        </p>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginForm />
    </Suspense>
  );
}
