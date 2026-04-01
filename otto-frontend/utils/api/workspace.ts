import { apiFetch } from "./client";

export interface BackendWorkspace {
  id: string;
  name: string;
  join_code: string;
  member_ids: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BackendIssue {
  id: string;
  title: string;
  description: string | null;
  section_id: string;
  assignee_id: string | null;
  reporter_id: string;
  position: number;
  priority: number;
  branch: string | null;
  branch_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendIssueUpdate {
  title: string | null;
  description: string | null;
  section_id: string | null;
  position: number | null;
  assignee_id: string | null;
  priority: number | null;
}

export interface BackendComment {
  id: string;
  content: string;
  author_id: string;
  created_at: string;
  updated_at: string;
}

export const workspaceApi = {
  getIssues: (workspaceId: string) =>
    apiFetch<{ issues: BackendIssue[] }>(`/workspaces/${workspaceId}/issues`),
  createIssue: (workspaceId: string, title: string, section_id: string) =>
    apiFetch<BackendIssue>(`/workspaces/${workspaceId}/issues`, {
      method: "POST",
      body: JSON.stringify({ title, section_id }),
    }),
  updateIssue: (workspaceId: string, issueId: string, update: Partial<BackendIssueUpdate>) =>
    apiFetch<BackendIssue>(`/workspaces/${workspaceId}/issues/${issueId}`, {
      method: "PATCH",
      body: JSON.stringify(update),
    }),
  deleteIssue: (workspaceId: string, issueId: string) =>
    apiFetch<void>(`/workspaces/${workspaceId}/issues/${issueId}`, { method: "DELETE" }),
  getComments: (workspaceId: string, issueId: string) =>
    apiFetch<{ comments: BackendComment[] }>(`/workspaces/${workspaceId}/issues/${issueId}/comments`),
  addComment: (workspaceId: string, issueId: string, content: string) =>
    apiFetch<BackendComment>(`/workspaces/${workspaceId}/issues/${issueId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  deleteComment: (workspaceId: string, issueId: string, commentId: string) =>
    apiFetch<void>(`/workspaces/${workspaceId}/issues/${issueId}/comments/${commentId}`, { method: "DELETE" }),
  create: (name: string) =>
    apiFetch<BackendWorkspace>("/workspaces", {
      method: "POST",
      body: JSON.stringify({ name, repos: [] }),
    }),
  join: (join_code: string) =>
    apiFetch<BackendWorkspace>("/workspaces/join", {
      method: "POST",
      body: JSON.stringify({ join_code }),
    }),
  get: (workspaceId: string) =>
    apiFetch<BackendWorkspace>(`/workspaces/${workspaceId}`),
  update: (workspaceId: string, update: { name?: string; member_ids?: string[] }) =>
    apiFetch<BackendWorkspace>(`/workspaces/${workspaceId}`, {
      method: "PATCH",
      body: JSON.stringify(update),
    }),
  getIssue: (workspaceId: string, issueId: string) =>
    apiFetch<BackendIssue>(`/workspaces/${workspaceId}/issues/${issueId}`),
  getComment: (workspaceId: string, issueId: string, commentId: string) =>
    apiFetch<BackendComment>(`/workspaces/${workspaceId}/issues/${issueId}/comments/${commentId}`),
  updateComment: (workspaceId: string, issueId: string, commentId: string, content: string) =>
    apiFetch<BackendComment>(`/workspaces/${workspaceId}/issues/${issueId}/comments/${commentId}`, {
      method: "PATCH",
      body: JSON.stringify({ content }),
    }),
};
