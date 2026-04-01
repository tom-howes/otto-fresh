import { apiFetch, streamFetch } from "./client";

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

export interface CommitHistoryEntry {
  commit_sha: string;
  author: string | null;
  processed_at: string | null;
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

export interface IndexedRepo {
  repo: string;
  total_chunks: number;
  storage_path: string;
  last_commit: string | null;
  last_updated: string | null;
  last_author: string | null;
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

export const ragApi = {
  ask: (repo_full_name: string, question: string) =>
    apiFetch<AskResponse>("/rag/ask", {
      method: "POST",
      body: JSON.stringify({ repo_full_name, question }),
    }),
  askStream: (repo_full_name: string, question: string) =>
    streamFetch("/rag/ask/stream", { repo_full_name, question }),
  runPipeline: (repo_full_name: string) =>
    apiFetch("/rag/repos/pipeline", {
      method: "POST",
      body: JSON.stringify({ repo_full_name }),
    }),
  getUserRepoHistory: () =>
    apiFetch<RepoHistory[]>("/rag/repos/user/history"),
  getAllRepos: (indexedOnly = false) =>
    apiFetch<RepoWithStatus[]>(`/rag/repos/user/all${indexedOnly ? "?indexed_only=true" : ""}`),
  completeCode: (repo_full_name: string, code_context: string, language?: string, target_file?: string, push_to_github = false) =>
    apiFetch<CompleteCodeResponse>("/rag/code/complete", {
      method: "POST",
      body: JSON.stringify({ repo_full_name, code_context, language, target_file: target_file || null, push_to_github }),
    }),
  editCode: (repo_full_name: string, instruction: string, target_file?: string, push_to_github = false) =>
    apiFetch<EditCodeResponse>("/rag/code/edit", {
      method: "POST",
      body: JSON.stringify({ repo_full_name, instruction, target_file: target_file || null, push_to_github }),
    }),
  editCodeStream: (repo_full_name: string, instruction: string, target_file?: string, push_to_github = false) =>
    streamFetch("/rag/code/edit/stream", { repo_full_name, instruction, target_file: target_file || null, push_to_github }),
  generateDocs: (repo_full_name: string, doc_type: DocType, target?: string, push_to_github = false) =>
    apiFetch<GenerateDocsResponse>("/rag/docs/generate", {
      method: "POST",
      body: JSON.stringify({ repo_full_name, doc_type, target: target || null, push_to_github }),
    }),
  generateDocsStream: (repo_full_name: string, doc_type: DocType, target?: string, push_to_github = false) =>
    streamFetch("/rag/docs/generate/stream", { repo_full_name, doc_type, target: target || null, push_to_github }),
  search: (repo_full_name: string, query: string, language?: string, top_k = 10) =>
    apiFetch<SearchCodeResponse>("/rag/search", {
      method: "POST",
      body: JSON.stringify({ repo_full_name, query, language: language || null, top_k }),
    }),
  getRepoStatus: (owner: string, repo: string) =>
    apiFetch<RepoStatus>(`/rag/repos/${owner}/${repo}/status`),
  getCommitHistory: (owner: string, repo: string, limit = 10) =>
    apiFetch<CommitHistoryEntry[]>(`/rag/repos/${owner}/${repo}/commit-history?limit=${limit}`),
  checkRepoAccess: (owner: string, repo: string) =>
    apiFetch<RepoAccess>(`/rag/repos/${owner}/${repo}/access`),
  getIndexedRepos: () =>
    apiFetch<IndexedRepo[]>("/rag/repos/indexed"),
  savePreferences: (prefs: UserPreferencesRequest) =>
    apiFetch<{ success: boolean; message: string; repo: string }>("/rag/repos/user/preferences", {
      method: "POST",
      body: JSON.stringify(prefs),
    }),
  getPreferences: (owner: string, repo: string) =>
    apiFetch<{ repo: string; preferences: UserPreferences }>(`/rag/repos/${owner}/${repo}/preferences`),
};
