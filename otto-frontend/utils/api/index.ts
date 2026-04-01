export { apiFetch, streamSSE, streamFetch } from "./client";
export type { SSEEvent } from "./client";

export { authApi } from "./auth";

export { userApi } from "./user";
export type { User, UserUpdate } from "./user";

export { githubApi } from "./github";
export type { GitHubRepo } from "./github";

export { workspaceApi } from "./workspace";
export type {
  BackendWorkspace,
  BackendIssue,
  BackendIssueUpdate,
  BackendComment,
} from "./workspace";

export { ragApi } from "./rag";
export type {
  AskResponse,
  RepoHistory,
  RepoWithStatus,
  DocType,
  CompleteCodeResponse,
  EditCodeResponse,
  GenerateDocsResponse,
  SearchCodeResponse,
  RepoStatus,
  CommitHistoryEntry,
  RepoAccess,
  IndexedRepo,
  UserPreferences,
  UserPreferencesRequest,
} from "./rag";

import type { BackendIssue } from "./workspace";

const PRIORITY_MAP: Record<number, "urgent" | "high" | "medium" | "low"> = {
  0: "low", 1: "low", 2: "medium", 3: "high", 4: "urgent",
};

export { PRIORITY_MAP };

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
