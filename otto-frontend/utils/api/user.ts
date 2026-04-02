import { apiFetch } from "./client";
import { User, UserUpdate, BackendIssue } from "./types";

const PRIORITY_MAP: Record<number, "urgent" | "high" | "medium" | "low"> = {
  0: "low", 1: "low", 2: "medium", 3: "high", 4: "urgent",
};

export function adaptIssue(raw: BackendIssue): import("@/types").Issue {
  return {
    id: raw.id,
    title: raw.title,
    description: raw.description,
    section_id: raw.section_id,
    status: "TODO",
    type: "task",
    priority: PRIORITY_MAP[raw.priority] ?? "medium",
    assignee: raw.assignee_id ? raw.assignee_id.slice(0, 1).toUpperCase() : "?",
    assignee_id: raw.assignee_id,
    reporter_id: raw.reporter_id,
    position: raw.position,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}

export const userApi = {
  getMe: () => apiFetch<User>("/users/me"),

  updateMe: (update: UserUpdate) =>
    apiFetch<User>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(update),
    }),
};
