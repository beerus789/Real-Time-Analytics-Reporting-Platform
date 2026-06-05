"use client";

import {
  BarChart3,
  DatabaseZap,
  Gauge,
  KeyRound,
  LogOut,
  UsersRound
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";

import { AuthGuard } from "@/components/app/auth-guard";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

const navigation = [
  { href: "/dashboard", label: "Overview", icon: Gauge },
  { href: "/dashboards", label: "Dashboards", icon: BarChart3 },
  { href: "/ingest", label: "Ingestion", icon: DatabaseZap },
  { href: "/api-keys", label: "API Keys", icon: KeyRound },
  { href: "/team", label: "Team", icon: UsersRound }
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, clear } = useAuthStore();

  return (
    <AuthGuard>
      <div className="min-h-screen">
        <aside className="fixed inset-y-0 left-0 z-20 hidden w-72 border-r border-border bg-panel lg:block">
          <div className="flex h-16 items-center gap-3 border-b border-border px-6">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <BarChart3 className="h-5 w-5" aria-hidden />
            </div>
            <div>
              <div className="text-sm font-semibold">Pulseboard</div>
              <div className="text-xs text-muted-foreground">Analytics Ops</div>
            </div>
          </div>
          <nav className="space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const active = pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium transition",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="lg:pl-72">
          <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
            <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">
                  {profile?.organization_name ?? "Workspace"}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {profile?.email} / {profile?.role}
                </div>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  clear();
                  router.replace("/login");
                }}
              >
                <LogOut className="h-4 w-4" aria-hidden />
                Sign out
              </Button>
            </div>
            <div className="flex gap-2 overflow-x-auto px-4 pb-3 lg:hidden">
              {navigation.map((item) => {
                const active = pathname.startsWith(item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex h-9 shrink-0 items-center gap-2 rounded-md border px-3 text-sm",
                      active ? "border-primary bg-primary text-white" : "border-border bg-panel"
                    )}
                  >
                    <Icon className="h-4 w-4" aria-hidden />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </header>
          <main className="px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>
    </AuthGuard>
  );
}
