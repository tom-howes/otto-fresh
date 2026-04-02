import { apiFetch, streamFetch } from "./client";
import {
  AskResponse, RepoHistory, RepoWithStatus, CompleteCodeResponse, EditCodeResponse,
  GenerateDocsResponse, SearchCodeResponse, RepoStatus, CommitHistoryEntry,
  RepoAccess, IndexedRepo, UserPreferences, UserPreferencesRequest, DocType,
} from "./types";

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
