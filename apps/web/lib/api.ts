import { useAuthStore } from "@/store/auth";
import type { ApiErrorEnvelope } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api/backend";

export class ApiError extends Error {
  code: string;
  requestId: string;
  status: number;
  details: Record<string, unknown>;

  constructor(status: number, envelope: ApiErrorEnvelope) {
    super(envelope.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = envelope.error.code;
    this.requestId = envelope.error.request_id;
    this.details = envelope.error.details;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const token = init.token ?? useAuthStore.getState().accessToken;
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
    const envelope = (await response.json().catch(() => ({
      error: {
        code: "network_error",
        message: "Request failed",
        details: {},
        request_id: "unknown"
      }
    }))) as ApiErrorEnvelope;
    throw new ApiError(response.status, envelope);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
