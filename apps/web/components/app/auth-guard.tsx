"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";

import { LoadingState } from "@/components/ui/state";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import type { UserProfile } from "@/types/api";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, setProfile, clear } = useAuthStore();

  const profileQuery = useQuery({
    queryKey: ["me", accessToken],
    queryFn: () => apiFetch<UserProfile>("/auth/me"),
    enabled: Boolean(accessToken)
  });

  useEffect(() => {
    if (!accessToken) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    if (profileQuery.data) {
      setProfile(profileQuery.data);
    }
    if (profileQuery.error) {
      clear();
      router.replace("/login");
    }
  }, [accessToken, clear, pathname, profileQuery.data, profileQuery.error, router, setProfile]);

  if (!accessToken || profileQuery.isLoading) {
    return <LoadingState label="Securing workspace" />;
  }

  return <>{children}</>;
}

