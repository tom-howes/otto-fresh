import { SSEEvent } from "./types";

const API_URL = "/api";

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = sessionStorage.getItem("session_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    const detail = typeof error.detail === "string"
      ? error.detail
      : Array.isArray(error.detail)
        ? error.detail.map((e: { msg: string }) => e.msg).join(", ")
        : `Request failed: ${res.status}`;
    throw new Error(detail);
  }

  // 204 No Content (e.g. DELETE) — no body to parse
  if (res.status === 204) return undefined as T;

  return res.json();
}

export function streamFetch(path: string, body: object): Promise<Response> {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "https://backend-service-484671782718.us-east1.run.app";
  return fetch(`${backendUrl}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(body),
  });
}

export async function* streamSSE(response: Response): AsyncGenerator<SSEEvent> {
  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try { yield JSON.parse(line.slice(6)); } catch { /* skip malformed */ }
      }
    }
  }
}
