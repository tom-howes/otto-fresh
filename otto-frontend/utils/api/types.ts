export interface User {
  id: string;
  github_username: string;
  email: string | null;
  avatar_url: string;
  installation_id: string | null;
}

export interface UserUpdate {
  github_username?: string;
  email?: string;
  avatar_url?: string;
}

export interface GitHubRepo {
  full_name: string;
  name: string;
  owner: string;
  description: string | null;
  private: boolean;
  default_branch: string;
  language: string | null;
  url: string;
}

export interface AskResponse {
  answer: string;
  sources: { file: string; lines: string }[];
  chunks_used: number;
}

export interface RepoHistory {
  repo: string;
  indexed: boolean;
  total_chunks: number;
  has_embeddings: boolean;
  ready_for_rag: boolean;
  last_updated: string | null;
}

export interface RepoWithStatus {
  full_name: string;
  name: string;
  owner: string;
  description: string | null;
  private: boolean;
  default_branch: string;
  language: string | null;
  url: string;
  indexed: boolean;
  total_chunks: number;
  has_embeddings: boolean;
  ready_for_rag: boolean;
}

export interface RepoStatus {
  indexed: boolean;
  total_chunks: number;
  has_embeddings: boolean;
  ready_for_rag: boolean;
  user_access?: {
    access_level: string;
    first_accessed: string | null;
    last_accessed: string | null;
    access_count: number;
  };
}

export interface IndexedRepo {
  repo: string;
  total_chunks: number;
  storage_path: string;
  last_commit: string | null;
  last_updated: string | null;
  last_author: string | null;
}

export interface RepoAccess {
  has_access: boolean;
  repo: string;
  permissions?: { admin: boolean; push: boolean; pull: boolean };
  private?: boolean;
  can_ingest: boolean;
  can_push: boolean;
  message: string;
}

export interface CommitHistoryEntry {
  commit_sha: string;
  author: string | null;
  processed_at: string | null;
}

export interface UserPreferences {
  preferred_doc_type: string;
  preferred_chunk_size: number;
  auto_push_prs: boolean;
  favorite: boolean;
  notifications: boolean;
}

export interface UserPreferencesRequest {
  repo_full_name: string;
  preferred_doc_type?: string;
  preferred_chunk_size?: number;
  auto_push_prs?: boolean;
  favorite?: boolean;
  notifications?: boolean;
}

export type DocType = "api" | "user_guide" | "technical" | "readme";

export interface CompleteCodeResponse {
  completion: string;
  language: string;
  confidence: number;
  detected_file: string | null;
  detection_confidence: string | null;
  github_pr: string | null;
  pushed_by: string | null;
}

export interface EditCodeResponse {
  modified_code: string;
  file: string;
  instruction: string;
  chunks_analyzed: number;
  detected_file: string | null;
  detection_confidence: string | null;
  github_pr: string | null;
  github_branch: string | null;
  pushed_by: string | null;
}

export interface GenerateDocsResponse {
  documentation: string;
  type: string;
  files_referenced: number;
  github_pr: string | null;
  github_branch: string | null;
  pushed_by: string | null;
}

export interface SearchCodeResponse {
  results: { file_path: string; content: string; lines: string; language: string; similarity?: number }[];
  total_found: number;
}

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
  priority: number; // 0=lowest … 4=highest
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

export interface SSEEvent {
  type: "token" | "complete" | "error";
  content?: string;
  sources?: { file: string; lines: string }[];
  message?: string;
}
