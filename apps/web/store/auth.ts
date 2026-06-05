"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { UserProfile } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  profile: UserProfile | null;
  setSession: (token: string, profile?: UserProfile | null) => void;
  setProfile: (profile: UserProfile | null) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      profile: null,
      setSession: (token, profile = null) => set({ accessToken: token, profile }),
      setProfile: (profile) => set({ profile }),
      clear: () => set({ accessToken: null, profile: null })
    }),
    { name: "pulseboard-auth" }
  )
);

