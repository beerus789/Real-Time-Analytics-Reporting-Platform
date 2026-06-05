import { ReactNode } from "react";

import { AppShell } from "@/components/app/app-shell";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

