"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@/context/use-auth-context";
import { type IssueType } from "@/utils/types";

// ─── Types ────────────────────────────────────────────────────────────────────

type TicketMode = "qa" | "code" | "docs";
type DocType    = "api" | "technical" | "readme" | "user_guide";

type RepoEntry = {
  repo: string;           // "owner/repo"
  ready_for_rag: boolean;
  total_chunks: number;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  sources?: Array<{ file: string; lines: string; similarity: number }>;
  files_referenced?: string[];
  prUrl?: string;
};

// ─── Constants ────────────────────────────────────────────────────────────────

const API_BASE = "/api"; // adjust if your API is hosted elsewhere

const MODE_CONFIG: Record<TicketMode, { label: string; icon: string; placeholder: string }> = {
  qa:   { label: "Q&A",  icon: "💬", placeholder: "Ask anything about this ticket in the codebase…" },
  code: { label: "Code", icon: "⚡", placeholder: "Describe what code to generate or edit for this ticket…" },
  docs: { label: "Docs", icon: "📄", placeholder: "What do you want documented for this ticket?" },
};

const DOC_TYPES: { value: DocType; label: string }[] = [
  { value: "api",        label: "API"        },
  { value: "technical",  label: "Technical"  },
  { value: "readme",     label: "README"     },
  { value: "user_guide", label: "User Guide" },
];

const uid = () => Math.random().toString(36).slice(2);

// ─── OttoTicketPanel ──────────────────────────────────────────────────────────

export const OttoTicketPanel: React.FC<{ issue: IssueType }> = ({ issue }) => {
  const { workspaces } = useAuth();

  // Repo state — seeded from first workspace, switchable by user
  const [selectedRepo,  setSelectedRepo]  = useState<string>(
    () => workspaces[0]?.repo_full_name ?? ""
  );
  const [repos,         setRepos]         = useState<RepoEntry[]>([]);
  const [repoMenuOpen,  setRepoMenuOpen]  = useState(false);
  const [reposLoading,  setReposLoading]  = useState(false);

  const [indexingRepo,  setIndexingRepo]  = useState<string | null>(null);
  const [isOpen,        setIsOpen]        = useState(false);
  const [mode,          setMode]          = useState<TicketMode>("qa");
  const [docType,       setDocType]       = useState<DocType>("technical");
  const [pushToGitHub,  setPushToGitHub]  = useState(false);
  const [input,         setInput]         = useState("");
  const [messages,      setMessages]      = useState<Message[]>([]);
  const [isLoading,     setIsLoading]     = useState(false);

  const bottomRef   = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Ticket context injected into every prompt
  const ticketContext = [
    `Ticket: ${issue.key} — ${issue.name}`,
    issue.description ? `Description: ${issue.description}` : null,
    `Status: ${issue.status}`,
    `Type: ${issue.type}`,
    `Priority: ${issue.priority}`,
  ].filter(Boolean).join("\n");

  // Fetch ALL GitHub repos (including unindexed) when user clicks "Find my repos"
  const fetchAllRepos = async () => {
    setReposLoading(true);
    try {
      const res = await fetch(`${API_BASE}/rag/repos/user/all?indexed_only=false`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        // Map to RepoEntry shape — unindexed repos have ready_for_rag: false
        const mapped: RepoEntry[] = (data ?? []).map((r: any) => ({
          repo: r.full_name,
          ready_for_rag: r.ready_for_rag ?? false,
          total_chunks: r.total_chunks ?? 0,
        }));
        setRepos(mapped);
        setRepoMenuOpen(true);
      }
    } catch {
      // silently fail
    } finally {
      setReposLoading(false);
    }
  };

  // Run indexing pipeline for a not-yet-indexed repo
  const runPipeline = async (repoFullName: string) => {
    try {
      const res = await fetch(`${API_BASE}/rag/repos/pipeline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ repo_full_name: repoFullName, branch: "main" }),
      });
      if (res.ok) {
        // Refresh repo list so it shows as ready
        const updated = await fetch(`${API_BASE}/rag/repos/user/history`, {
          credentials: "include",
        });
        if (updated.ok) {
          const data: RepoEntry[] = await updated.json();
          setRepos(data ?? []);
          const indexed = data.find(r => r.repo === repoFullName && r.ready_for_rag);
          if (indexed) setSelectedRepo(repoFullName);
        }
      }
    } catch {
      // silently fail — user can retry
    } finally {
      setIndexingRepo(null);
    }
  };

  // Fetch user's indexed repos when panel opens
  useEffect(() => {
    if (!isOpen || repos.length > 0) return;
    setReposLoading(true);
    fetch(`${API_BASE}/rag/repos/user/history`, { credentials: "include" })
      .then(r => r.ok ? r.json() : [])
      .then((data: RepoEntry[]) => {
        setRepos(data ?? []);
        const ready = (data ?? []).filter((r: RepoEntry) => r.ready_for_rag);
        if (ready.length && !ready.find((r: RepoEntry) => r.repo === selectedRepo)) {
          setSelectedRepo(ready[0].repo);
        }
      })
      .catch(() => setRepos([]))
      .finally(() => setReposLoading(false));
  }, [isOpen]);

  // Reset on ticket change
  useEffect(() => {
    setMessages([]);
    setInput("");
  }, [issue.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = "auto";
    textareaRef.current.style.height =
      Math.min(textareaRef.current.scrollHeight, 100) + "px";
  }, [input]);

  // ─── Message helpers ────────────────────────────────────────────────────────

  const pushUser = (content: string) =>
    setMessages(prev => [...prev, { id: uid(), role: "user", content }]);

  const pushAssistant = (partial: Partial<Message>) =>
    setMessages(prev => [...prev, { id: uid(), role: "assistant", content: "", ...partial }]);

  const updateLast = (updates: Partial<Message>) =>
    setMessages(prev => {
      const copy = [...prev];
      const idx  = copy.map(m => m.role).lastIndexOf("assistant");
      if (idx !== -1) copy[idx] = { ...copy[idx], ...updates };
      return copy;
    });

  // ─── SSE stream parser ──────────────────────────────────────────────────────
  // Real SSE format: data: {"type": "token", "content": "..."}
  //                  data: {"type": "complete", "sources": [...]}

  const fetchStream = useCallback(async (endpoint: string, body: object) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    if (!res.ok || !res.body) throw new Error(await res.text());

    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let full    = "";
    let sources: Message["sources"] = [];
    pushAssistant({ streaming: true });

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      for (const line of decoder.decode(value, { stream: true }).split("\n")) {
        if (!line.startsWith("data: ")) continue;
        try {
              const raw = line.slice(6);
          if (raw === "[DONE]") break;
          // Try JSON format: {"type":"token","content":"..."}
          try {
            const evt = JSON.parse(raw);
            if (evt.type === "token") {
              full += evt.content ?? "";
              updateLast({ content: full, streaming: true });
            } else if (evt.type === "complete") {
              sources = evt.sources ?? [];
            } else if (evt.content) {
              // Fallback: any object with content field
              full += evt.content;
              updateLast({ content: full, streaming: true });
            }
          } catch {
            // Plain text format: just append the raw chunk
            if (raw.trim()) {
              full += raw;
              updateLast({ content: full, streaming: true });
            }
          }
        } catch {
          // skip malformed
        }
      }
    }
    updateLast({ content: full, streaming: false, sources });
  }, []);

  const fetchJson = useCallback(async (endpoint: string, body: object) => {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }, []);

  // ─── Submit ─────────────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || !selectedRepo) return;
    setInput("");
    setIsLoading(true);
    pushUser(trimmed);

    try {
      if (mode === "qa") {
        await fetchStream("/rag/ask/stream", {
          repo_full_name: selectedRepo,
          question: `${ticketContext}\n\nQuestion: ${trimmed}`,
        });

      } else if (mode === "code") {
        const instruction = `${ticketContext}\n\nTask: ${trimmed}`;
        if (pushToGitHub) {
          const data = await fetchJson("/rag/code/edit", {
            repo_full_name: selectedRepo,
            instruction,               // ← correct field name per API docs
            push_to_github: true,
          });
          pushAssistant({
            content: `✅ Code pushed as PR!\n\n${data.github?.pr_url ? `PR: ${data.github.pr_url}` : "Check your repository for the new branch."}`,
            prUrl: data.github?.pr_url,
          });
        } else {
          await fetchStream("/rag/code/edit/stream", {
            repo_full_name: selectedRepo,
            instruction,
            push_to_github: false,
          });
        }

      } else if (mode === "docs") {
        const target = `${issue.key} — ${issue.name}: ${trimmed}`;
        if (pushToGitHub) {
          const data = await fetchJson("/rag/docs/generate", {
            repo_full_name: selectedRepo,
            target,
            doc_type: docType,
            push_to_github: true,
          });
          pushAssistant({
            content: `✅ Docs pushed to GitHub!\n\nType: ${data.type ?? docType}${data.github_pr ? `\nPR: ${data.github_pr}` : ""}`,
            prUrl: data.github_pr,
          });
        } else {
          await fetchStream("/rag/docs/generate/stream", {
            repo_full_name: selectedRepo,
            target,
            doc_type: docType,
            push_to_github: false,
          });
        }
      }
    } catch (err: unknown) {
      pushAssistant({
        content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong."}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit();
    }
  };

  const readyRepos  = repos.filter(r => r.ready_for_rag);
  const allRepos    = repos; // includes not-yet-indexed
  const currentRepo = repos.find(r => r.repo === selectedRepo);
  const isReady     = currentRepo?.ready_for_rag ?? false;
  const hasAnyRepos = repos.length > 0;

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="mt-6 border-t border-gray-200">
      {/* Collapsible trigger */}
      <button
        onClick={() => setIsOpen(o => !o)}
        className="flex w-full items-center justify-between px-1 py-3 text-left"
      >
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 items-center justify-center rounded bg-gradient-to-br from-blue-500 to-violet-600 text-xs font-bold text-white">
            O
          </span>
          <span className="text-sm font-medium text-gray-700">Otto AI</span>
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
            {issue.key}
          </span>
          {selectedRepo && (
            <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-500 font-mono">
              {selectedRepo}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">{isOpen ? "▲ collapse" : "▼ expand"}</span>
      </button>

      {isOpen && (
        <div className="flex flex-col rounded-lg border border-gray-200 bg-gray-50 overflow-hidden">

          {/* ── Repo selector bar ── */}
          <div className="relative flex items-center justify-between border-b border-gray-200 bg-white px-3 py-2">
            <span className="text-xs text-gray-400">Repo</span>
            <div className="relative">
              <button
                onClick={() => setRepoMenuOpen(o => !o)}
                disabled={reposLoading}
                className="flex items-center gap-1.5 rounded-md border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
              >
                {reposLoading ? (
                  <span className="text-gray-400">Loading…</span>
                ) : (
                  <>
                    <span className={`h-1.5 w-1.5 rounded-full ${isReady ? "bg-green-500" : "bg-yellow-400"}`} />
                    <span className="max-w-[180px] truncate font-mono">
                      {selectedRepo || "Select repo"}
                    </span>
                    <span className="text-gray-400">▾</span>
                  </>
                )}
              </button>

              {repoMenuOpen && (
                <div className="absolute right-0 top-full z-20 mt-1 w-72 rounded-lg border border-gray-200 bg-white shadow-lg">
                  {/* Ready repos */}
                  {readyRepos.length > 0 && (
                    <>
                      <div className="border-b border-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
                        Ready ({readyRepos.length})
                      </div>
                      {readyRepos.map(r => (
                        <button
                          key={r.repo}
                          onClick={() => { setSelectedRepo(r.repo); setRepoMenuOpen(false); }}
                          className={`flex w-full items-center justify-between px-3 py-2 text-left text-xs hover:bg-gray-50 ${
                            r.repo === selectedRepo ? "bg-blue-50 text-blue-700" : "text-gray-700"
                          }`}
                        >
                          <div className="flex items-center gap-1.5 truncate">
                            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-green-500" />
                            <span className="truncate font-mono">{r.repo}</span>
                          </div>
                          <span className="ml-2 shrink-0 text-gray-400">{r.total_chunks} chunks</span>
                        </button>
                      ))}
                    </>
                  )}

                  {/* Not-yet-indexed repos */}
                  {allRepos.filter(r => !r.ready_for_rag).length > 0 && (
                    <>
                      <div className="border-b border-t border-gray-100 px-3 py-1.5 text-xs font-medium text-gray-500">
                        Not indexed
                      </div>
                      {allRepos.filter(r => !r.ready_for_rag).map(r => (
                        <div
                          key={r.repo}
                          className="flex w-full items-center justify-between px-3 py-2 text-xs text-gray-400"
                        >
                          <div className="flex items-center gap-1.5 truncate">
                            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-yellow-400" />
                            <span className="truncate font-mono">{r.repo}</span>
                          </div>
                          <button
                            onClick={() => {
                              setIndexingRepo(r.repo);
                              setRepoMenuOpen(false);
                              void runPipeline(r.repo);
                            }}
                            disabled={indexingRepo === r.repo}
                            className="ml-2 shrink-0 rounded bg-blue-600 px-2 py-0.5 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                          >
                            {indexingRepo === r.repo ? "Indexing…" : "Index"}
                          </button>
                        </div>
                      ))}
                    </>
                  )}

                  {/* No repos at all */}
                  {!hasAnyRepos && (
                    <div className="px-3 py-4 text-center space-y-2">
                      <p className="text-xs text-gray-500">No indexed repositories found.</p>
                      {/* Try fetching all GitHub repos first before installing */}
                      <button
                        onClick={() => { setRepoMenuOpen(false); void fetchAllRepos(); }}
                        className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700"
                      >
                        <span>🔍</span>
                        <span>Find my repos</span>
                      </button>
                      <div className="text-xs text-gray-400">or</div>
                      <a
                        href="https://github.com/apps/otto-pm/installations/new"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-md bg-gray-900 px-3 py-1.5 text-xs text-white hover:bg-gray-800"
                      >
                        <span>🐙</span>
                        <span>Install GitHub App</span>
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Mode tabs */}
          <div className="flex items-center gap-1 border-b border-gray-200 bg-white px-3 py-2">
            {(["qa", "code", "docs"] as TicketMode[]).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                  mode === m
                    ? m === "qa"   ? "bg-violet-100 text-violet-700"
                    : m === "code" ? "bg-amber-100 text-amber-700"
                    :                "bg-emerald-100 text-emerald-700"
                    : "text-gray-500 hover:bg-gray-100"
                }`}
              >
                <span>{MODE_CONFIG[m].icon}</span>
                <span>{MODE_CONFIG[m].label}</span>
              </button>
            ))}

            {mode === "docs" && (
              <div className="ml-auto flex gap-1">
                {DOC_TYPES.map(dt => (
                  <button
                    key={dt.value}
                    onClick={() => setDocType(dt.value)}
                    className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
                      docType === dt.value
                        ? "bg-emerald-100 text-emerald-700"
                        : "text-gray-400 hover:bg-gray-100"
                    }`}
                  >
                    {dt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Messages */}
          {messages.length > 0 && (
            <div className="max-h-80 overflow-y-auto px-3 py-3 space-y-3">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  {msg.role === "assistant" && (
                    <div className="mr-2 mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-gradient-to-br from-blue-500 to-violet-600 text-xs font-bold text-white">
                      O
                    </div>
                  )}
                  <div className="max-w-[88%] space-y-1">
                    {msg.role === "user" ? (
                      <div className="rounded-2xl rounded-tr-sm bg-blue-600 px-3 py-2 text-xs text-white">
                        {msg.content}
                      </div>
                    ) : (
                      <div className={`rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-3 py-2 text-xs text-gray-800 shadow-sm ${msg.streaming ? "animate-pulse" : ""}`}>
                        <pre className="whitespace-pre-wrap font-sans leading-relaxed">
                          {msg.content}{msg.streaming ? "▋" : ""}
                        </pre>
                        {/* Sources from Q&A */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-2 space-y-0.5 border-t border-gray-100 pt-2">
                            <p className="text-xs font-medium text-gray-400">Sources</p>
                            {msg.sources.map((s, i) => (
                              <div key={i} className="flex items-center gap-1.5 text-xs text-gray-500">
                                <span className="font-mono truncate">{s.file.split("/").pop()}</span>
                                <span className="text-gray-300">·</span>
                                <span>L{s.lines}</span>
                                <span className="ml-auto text-emerald-600">{Math.round(s.similarity * 100)}%</span>
                              </div>
                            ))}
                          </div>
                        )}
                        {msg.prUrl && (
                          <a href={msg.prUrl} target="_blank" rel="noopener noreferrer"
                            className="mt-2 block text-xs text-blue-600 underline">
                            View PR →
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
                <div className="flex items-center gap-1.5 text-xs text-gray-400">
                  <div className="flex gap-0.5">
                    {[0, 150, 300].map(d => (
                      <span key={d} className="animate-bounce" style={{ animationDelay: `${d}ms` }}>●</span>
                    ))}
                  </div>
                  <span>Otto is thinking…</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}

          {/* Push to GitHub toggle */}
          {(mode === "code" || mode === "docs") && (
            <div className="flex items-center justify-between border-t border-gray-200 bg-white px-3 py-2">
              <span className="text-xs text-gray-500">Push to GitHub as PR</span>
              <button
                onClick={() => setPushToGitHub(v => !v)}
                className={`relative h-5 w-9 rounded-full transition-colors ${pushToGitHub ? "bg-blue-600" : "bg-gray-300"}`}
              >
                <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${pushToGitHub ? "translate-x-4" : "translate-x-0.5"}`} />
              </button>
            </div>
          )}

          {/* Input */}
          <div className="border-t border-gray-200 bg-white p-3">
            <div className="flex items-end gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={MODE_CONFIG[mode].placeholder}
                rows={1}
                disabled={isLoading || !isReady}
                className="flex-1 resize-none bg-transparent text-xs text-gray-800 placeholder-gray-400 outline-none disabled:opacity-50"
              />
              <button
                onClick={() => void handleSubmit()}
                disabled={!input.trim() || isLoading || !isReady}
                className="mb-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-blue-600 text-white transition-colors hover:bg-blue-700 disabled:opacity-40"
              >
                ↑
              </button>
            </div>
            {!isReady && selectedRepo && (
              <p className="mt-1 text-xs text-amber-600">
                ⚠️ This repo isn't indexed yet. Run the pipeline first.
              </p>
            )}
            {!selectedRepo && (
              <p className="mt-1 text-xs text-red-500">
                No repository selected. Connect a GitHub repo first.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};