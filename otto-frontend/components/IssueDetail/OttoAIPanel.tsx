"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import {
  ragApi, streamSSE,
  RepoWithStatus, DocType, CompleteCodeResponse, EditCodeResponse,
  RepoAccess,
} from "@/utils/api";
import { useJobs } from "@/context/JobsContext";

function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        h1: ({ children }) => <h1 className="text-base font-bold text-gray-800 dark:text-gray-100 mt-4 mb-2 first:mt-0">{children}</h1>,
        h2: ({ children }) => <h2 className="text-sm font-bold text-gray-800 dark:text-gray-100 mt-3 mb-1.5 first:mt-0">{children}</h2>,
        h3: ({ children }) => <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mt-3 mb-1 first:mt-0">{children}</h3>,
        p: ({ children }) => <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="space-y-1 mb-2 pl-4 last:mb-0">{children}</ul>,
        ol: ({ children }) => <ol className="space-y-1 mb-2 pl-4 list-decimal last:mb-0">{children}</ol>,
        li: ({ children }) => <li className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed list-disc marker:text-violet-400">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold text-gray-800 dark:text-gray-100">{children}</strong>,
        em: ({ children }) => <em className="italic text-gray-600 dark:text-gray-400">{children}</em>,
        code: ({ children, className }) => {
          const isBlock = className?.includes("language-");
          return isBlock ? (
            <code className="block w-full overflow-x-auto rounded-lg bg-gray-900 dark:bg-black/40 px-4 py-3 text-xs text-emerald-300 font-mono leading-relaxed whitespace-pre">{children}</code>
          ) : (
            <code className="rounded-md bg-gray-100 dark:bg-white/10 px-1.5 py-0.5 text-xs font-mono text-violet-600 dark:text-violet-300">{children}</code>
          );
        },
        pre: ({ children }) => <pre className="mb-2 last:mb-0">{children}</pre>,
        blockquote: ({ children }) => <blockquote className="border-l-2 border-violet-300 dark:border-violet-500/50 pl-3 my-2 text-sm text-gray-500 dark:text-gray-400 italic">{children}</blockquote>,
        hr: () => <hr className="my-3 border-gray-100 dark:border-white/10" />,
        a: ({ href, children }) => <a href={href} target="_blank" rel="noopener noreferrer" className="text-violet-600 dark:text-violet-400 underline underline-offset-2 hover:opacity-80">{children}</a>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export default function OttoAIPanel({ issueId, issueTitle }: { issueId: string; issueTitle: string }) {
  const [question, setQuestion] = useState("");
  const [activeTab, setActiveTab] = useState<"qa" | "code" | "docs" | "search">("qa");
  const [repoName, setRepoName] = useState("");
  const [repos, setRepos] = useState<RepoWithStatus[]>([]);
  const [reposLoading, setReposLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);

  const [codeMode, setCodeMode] = useState<"complete" | "edit">("complete");
  const [codeContext, setCodeContext] = useState("");
  const [targetFile, setTargetFile] = useState("");
  const [pushToGithub, setPushToGithub] = useState(false);
  const [completeResult, setCompleteResult] = useState<CompleteCodeResponse | null>(null);
  const [editResult, setEditResult] = useState<EditCodeResponse | null>(null);

  const [docType, setDocType] = useState<DocType>("readme");
  const [docTarget, setDocTarget] = useState("");
  const [docsResult, setDocsResult] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<{ file_path: string; content: string; lines: string; language: string }[]>([]);

  const [repoAccess, setRepoAccess] = useState<RepoAccess | null>(null);
  

  const { startJob, appendChunk, finishJob, getJob } = useJobs();
  const existingJob = getJob(issueId, "qa");
  const [answer, setAnswer] = useState(existingJob?.answer ?? "");
  const [asking, setAsking] = useState(existingJob?.status === "running");
  const [sources, setSources] = useState<{ file: string; lines: string }[]>([]);

  const codeJob = getJob(issueId, "code");
  const docsJob = getJob(issueId, "docs");
  const searchJob = getJob(issueId, "search");

  const [codeLoading, setCodeLoading] = useState(codeJob?.status === "running");
  const [docsLoading, setDocsLoading] = useState(docsJob?.status === "running");
  const [searching, setSearching] = useState(searchJob?.status === "running");

  useEffect(() => {
    const qaJob = getJob(issueId, "qa");
    if (qaJob) {
      setAnswer(qaJob.answer);
      setAsking(qaJob.status === "running");
    } else {
      setAnswer("");
      setAsking(false);
    }

    const searchJob = getJob(issueId, "search");
    setSearching(searchJob?.status === "running");
    if (searchJob?.searchResults) setSearchResults(searchJob.searchResults);

    const codeJob = getJob(issueId, "code");
    setCodeLoading(codeJob?.status === "running");
    if (codeJob?.codeResult) {
      const result = codeJob.codeResult as CompleteCodeResponse | EditCodeResponse;
      if ("completion" in result) {
        setCompleteResult(result as CompleteCodeResponse);
      } else {
        setEditResult(result as EditCodeResponse);
      }
    }

    const docsJob = getJob(issueId, "docs");
    setDocsLoading(docsJob?.status === "running");
    if (docsJob?.docsResult) setDocsResult(docsJob.docsResult);
  }, [issueId]);

  useEffect(() => {
    const loadRepos = async () => {
      setReposLoading(true);
      try {
        const data = await ragApi.getAllRepos();
        setRepos(data);
        if (data.length > 0) setRepoName(data[0].full_name);
      } catch { /* not fatal */ } finally {
        setReposLoading(false);
      }
    };
    loadRepos();
  }, []);

  useEffect(() => {
    if (!repoName || !repoName.includes("/")) return;
    const [owner, repo] = repoName.split("/");
    setRepoAccess(null);
    ragApi.checkRepoAccess(owner, repo).then(setRepoAccess).catch(() => {});
  }, [repoName]);

  const selectedRepo = repos.find(r => r.full_name === repoName);
  const isReady = selectedRepo?.ready_for_rag ?? false;

  const handleAsk = async () => {
    if (!question.trim() || !repoName.trim() || asking || indexing) return;
    setAnswer("");
    setSources([]);

    if (!isReady) {
      setIndexing(true);
      setAnswer("Indexing repo first, this may take a minute…");
      try {
        try {
          await ragApi.runPipeline(repoName);
        } catch {
          setAnswer("Indexing in progress, retrying…");
          await ragApi.runPipeline(repoName);
        }
        const data = await ragApi.getAllRepos();
        setRepos(data);
      } catch (err: unknown) {
        setAnswer(err instanceof Error ? `Indexing failed: ${err.message}` : "Indexing failed.");
        setIndexing(false);
        return;
      }
      setIndexing(false);
    }

    const jobId = startJob(issueId, issueTitle, question, "qa");
    setAsking(true);
    setAnswer("");
    try {
      const res = await ragApi.askStream(repoName, question);
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `Request failed: ${res.status}`);
      }
      for await (const event of streamSSE(res)) {
        if (event.type === "token") {
          setAnswer(prev => {
            const next = prev + (event.content ?? "");
            appendChunk(jobId, event.content ?? "");
            return next;
          });
        } else if (event.type === "complete") {
          setSources(event.sources || []);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
      finishJob(jobId, "done");
    } catch (err: unknown) {
      setAnswer(err instanceof Error ? `Error: ${err.message}` : "Something went wrong.");
      finishJob(jobId, "error");
    } finally {
      setAsking(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || !repoName || searching) return;
    setSearching(true);
    setSearchResults([]);
    const jobId = startJob(issueId, issueTitle, searchQuery, "search");
    try {
      const res = await ragApi.search(repoName, searchQuery);
      setSearchResults(res.results);
      finishJob(jobId, "done", { searchResults: res.results });
    } catch {
      finishJob(jobId, "error");
    } finally {
      setSearching(false);
    }
  };

  const handleCodeComplete = async () => {
    if (!codeContext.trim() || !repoName.trim() || codeLoading) return;
    setCodeLoading(true);
    setCompleteResult(null);
    const jobId = startJob(issueId, issueTitle, codeContext, "code");
    try {
      const detectedLang = selectedRepo?.language?.toLowerCase() || undefined;
      const res = await ragApi.completeCode(repoName, codeContext, detectedLang, targetFile || undefined, pushToGithub);
      setCompleteResult(res);
      finishJob(jobId, "done", { codeResult: res });
    } catch (err: unknown) {
      const errorResult = { completion: err instanceof Error ? `Error: ${err.message}` : "Something went wrong.", language: "", confidence: 0, detected_file: null, detection_confidence: null, github_pr: null, pushed_by: null };
      setCompleteResult(errorResult);
      finishJob(jobId, "error", { codeResult: errorResult });
    } finally {
      setCodeLoading(false);
    }
  };

  const handleCodeEdit = async () => {
    if (!codeContext.trim() || !repoName.trim() || codeLoading) return;
    setCodeLoading(true);
    setEditResult(null);
    const jobId = startJob(issueId, issueTitle, codeContext, "code");
    try {
      const res = await ragApi.editCodeStream(repoName, codeContext, targetFile || undefined, pushToGithub);
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `Request failed: ${res.status}`);
      }
      let content = "";
      for await (const event of streamSSE(res)) {
        if (event.type === "token") {
          content += event.content ?? "";
          const partial = { modified_code: content, file: targetFile || "", instruction: codeContext, chunks_analyzed: 0, detected_file: null, detection_confidence: null, github_pr: null, github_branch: null, pushed_by: null };
          setEditResult(partial);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
      const finalResult = { modified_code: content, file: targetFile || "", instruction: codeContext, chunks_analyzed: 0, detected_file: null, detection_confidence: null, github_pr: null, github_branch: null, pushed_by: null };
      finishJob(jobId, "done", { codeResult: finalResult });
    } catch (err: unknown) {
      const errorResult = { modified_code: err instanceof Error ? `Error: ${err.message}` : "Something went wrong.", file: "", instruction: codeContext, chunks_analyzed: 0, detected_file: null, detection_confidence: null, github_pr: null, github_branch: null, pushed_by: null };
      setEditResult(errorResult);
      finishJob(jobId, "error", { codeResult: errorResult });
    } finally {
      setCodeLoading(false);
    }
  };

  const handleGenerateDocs = async () => {
    if (!repoName.trim() || docsLoading) return;
    setDocsLoading(true);
    setDocsResult("");
    const jobId = startJob(issueId, issueTitle, docType, "docs");
    try {
      const res = await ragApi.generateDocsStream(repoName, docType, docTarget || undefined, pushToGithub);
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Unknown error" }));
        const detail = typeof error.detail === "string" ? error.detail : `Request failed: ${res.status}`;
        throw new Error(detail);
      }
      let content = "";
      for await (const event of streamSSE(res)) {
        if (event.type === "token") {
          content += event.content ?? "";
          setDocsResult(content);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
      finishJob(jobId, "done", { docsResult: content });
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? `Error: ${err.message}` : "Something went wrong.";
      setDocsResult(errorMsg);
      finishJob(jobId, "error", { docsResult: errorMsg });
    } finally {
      setDocsLoading(false);
    }
  };

  return (
    <div className="mt-8 border-t border-gray-100 dark:border-gray-800 pt-6">
      <div className="rounded-2xl p-px bg-gradient-to-br from-violet-400/30 via-blue-400/10 to-violet-400/20 dark:from-violet-500/40 dark:via-blue-500/10 dark:to-violet-500/30 shadow-lg shadow-violet-100/50 dark:shadow-violet-900/20">
        <div className="rounded-[15px] bg-white dark:bg-[#0f0f13] overflow-hidden">

          {/* Panel header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100/80 dark:border-white/5 bg-gradient-to-r from-violet-50/60 via-transparent to-blue-50/40 dark:from-violet-950/40 dark:via-transparent dark:to-blue-950/20">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 text-xs font-black text-white shadow-md shadow-violet-300/50 dark:shadow-violet-700/50 shrink-0">
              ✦
            </div>
            <span className="text-xs font-semibold text-gray-700 dark:text-gray-200 tracking-wide">Otto AI</span>
            <div className="h-3 w-px bg-gray-200 dark:bg-white/10" />
            <div className="flex items-center gap-0.5">
              {([["qa", "Q&A"], ["code", "Code"], ["docs", "Docs"], ["search", "Search"]] as const).map(([id, label]) => (
                <button key={id} onClick={() => setActiveTab(id)}
                  className={`relative px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                    activeTab === id
                      ? "bg-violet-100 dark:bg-violet-500/20 text-violet-700 dark:text-violet-300"
                      : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400 hover:bg-gray-100/60 dark:hover:bg-white/5"
                  }`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="ml-auto flex items-center gap-2 rounded-full border border-gray-200 dark:border-white/10 bg-white dark:bg-white/5 px-3 py-1 min-w-0 max-w-[220px]">
              <svg className="h-3 w-3 text-gray-300 dark:text-gray-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              {reposLoading ? (
                <div className="flex-1 h-2.5 rounded-full bg-gray-100 dark:bg-white/10 animate-pulse" />
              ) : repos.length > 0 ? (
                <select value={repoName} onChange={e => setRepoName(e.target.value)}
                  className="flex-1 bg-transparent text-xs text-gray-600 dark:text-gray-300 outline-none min-w-0 cursor-pointer truncate">
                  {repos.map(r => <option key={r.full_name} value={r.full_name}>{r.full_name}</option>)}
                </select>
              ) : (
                <input value={repoName} onChange={e => setRepoName(e.target.value)}
                  className="flex-1 bg-transparent text-xs text-gray-600 dark:text-gray-300 outline-none placeholder-gray-300 dark:placeholder-gray-600 min-w-0"
                  placeholder="owner/repo" />
              )}
              <div
                title={repoAccess ? (repoAccess.can_push ? "Push access" : "Read-only") : (isReady ? "Ready" : "Not indexed")}
                className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                  !isReady ? "bg-amber-400" :
                  repoAccess?.can_push ? "bg-emerald-400" :
                  repoAccess ? "bg-blue-400" : "bg-emerald-400"
                }`}
              />
            </div>
          </div>


          {/* Tab content */}
          <div className="p-5">

            {/* Q&A */}
            {activeTab === "qa" && (
              <div className="space-y-3">
                <div className="group rounded-2xl border border-gray-200 dark:border-white/8 bg-gray-50 dark:bg-white/[0.03] focus-within:border-violet-300 dark:focus-within:border-violet-500/50 focus-within:shadow-md focus-within:shadow-violet-100/50 dark:focus-within:shadow-violet-900/20 transition-all overflow-hidden">
                  <input value={question} onChange={e => setQuestion(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleAsk()}
                    className="w-full bg-transparent px-4 py-3.5 text-sm text-gray-700 dark:text-gray-200 outline-none placeholder-gray-300 dark:placeholder-gray-600"
                    placeholder="" />
                  <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 dark:border-white/5">
                    <span className="text-xs text-gray-300 dark:text-gray-600">Press Enter to send</span>
                    <button onClick={handleAsk} disabled={asking || indexing}
                      className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-500 to-blue-500 px-3.5 py-1.5 text-xs font-semibold text-white disabled:opacity-40 hover:opacity-90 transition-opacity shadow-sm shadow-violet-300/40 dark:shadow-violet-700/40">
                      {asking || indexing
                        ? <><span className="inline-block w-3 text-center animate-pulse">···</span> Thinking</>
                        : <>Ask ↑</>}
                    </button>
                  </div>
                </div>
                {answer && (
                  <div className="rounded-2xl border border-gray-100 dark:border-white/6 overflow-hidden">
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-50 to-transparent dark:from-violet-950/30 dark:to-transparent border-b border-gray-100 dark:border-white/5">
                      <div className="flex h-4 w-4 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-blue-500 text-white text-[9px] font-black">✦</div>
                      <span className="text-xs font-semibold text-violet-700 dark:text-violet-300">Answer</span>
                    </div>
                    <div className="p-4">
                      <MarkdownContent content={answer} />
                      {sources.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-white/5 space-y-1.5">
                          <p className="text-xs font-medium text-gray-400 dark:text-gray-500 mb-2">Sources</p>
                          {sources.map((s, i) => (
                            <div key={i} className="flex items-center gap-2 rounded-lg bg-gray-50 dark:bg-white/[0.03] px-2.5 py-1.5">
                              <svg className="h-3 w-3 text-gray-300 dark:text-gray-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              <span className="text-xs text-gray-500 dark:text-gray-400 font-mono truncate">{s.file}</span>
                              {s.lines && <span className="text-xs text-gray-300 dark:text-gray-600 shrink-0">:{s.lines}</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Code */}
            {activeTab === "code" && (
              <div className="space-y-3">
                <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-gray-100 dark:bg-white/5">
                  {(["complete", "edit"] as const).map(m => (
                    <button key={m}
                      onClick={() => { setCodeMode(m); setCompleteResult(null); setEditResult(null); }}
                      className={`flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-xs font-semibold transition-all ${
                        codeMode === m
                          ? "bg-white dark:bg-white/10 text-gray-800 dark:text-gray-100 shadow-sm"
                          : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400"
                      }`}>
                      {m === "complete" ? "Complete" : "Edit"}
                    </button>
                  ))}
                </div>

                <div className="rounded-2xl border border-gray-200 dark:border-white/8 bg-gray-50 dark:bg-white/[0.03] focus-within:border-violet-300 dark:focus-within:border-violet-500/50 focus-within:shadow-md focus-within:shadow-violet-100/50 dark:focus-within:shadow-violet-900/20 transition-all overflow-hidden">
                  <textarea
                    value={codeContext}
                    onChange={e => setCodeContext(e.target.value)}
                    rows={4}
                    className="w-full bg-transparent px-4 pt-4 pb-2 text-sm text-gray-700 dark:text-gray-200 outline-none resize-none placeholder-gray-300 dark:placeholder-gray-600 leading-relaxed"
                    placeholder=""
                  />
                  <div className="flex items-center gap-3 px-4 py-3 border-t border-gray-100 dark:border-white/5">
                    <svg className="h-3.5 w-3.5 text-gray-300 dark:text-gray-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <input value={targetFile} onChange={e => setTargetFile(e.target.value)}
                      className="flex-1 bg-transparent text-xs text-gray-500 dark:text-gray-400 font-mono outline-none placeholder-gray-300 dark:placeholder-gray-500"
                      placeholder="Target file (auto-detected if blank)" />
                    <button
                      onClick={codeMode === "complete" ? handleCodeComplete : handleCodeEdit}
                      disabled={codeLoading || !codeContext.trim()}
                      className="shrink-0 flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-violet-500 to-blue-500 px-4 py-2 text-xs font-bold text-white disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-violet-300/30 dark:shadow-violet-700/30">
                      {codeLoading
                        ? <span className="flex items-center gap-1.5"><span className="animate-spin inline-block w-3 h-3 border border-white/30 border-t-white rounded-full" /> Running…</span>
                        : codeMode === "complete" ? "Run" : "Apply"}
                    </button>
                  </div>
                </div>

                <button onClick={() => setPushToGithub(p => !p)}
                  className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-medium border transition-all ${
                    pushToGithub
                      ? "border-violet-300 dark:border-violet-500/50 bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-300 shadow-sm shadow-violet-100 dark:shadow-violet-900/20"
                      : "border-gray-200 dark:border-white/8 text-gray-400 dark:text-gray-500 hover:border-gray-300 dark:hover:border-white/15 hover:bg-gray-50 dark:hover:bg-white/[0.03]"
                  }`}>
                  <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  {pushToGithub ? "Will open a GitHub PR" : "Push to GitHub"}
                </button>

                {(completeResult || editResult) && (() => {
                  const code = completeResult ? completeResult.completion : editResult!.modified_code;
                  const file = completeResult?.detected_file ?? editResult?.detected_file ?? editResult?.file;
                  const conf = completeResult?.detection_confidence ?? editResult?.detection_confidence;
                  const pr = (completeResult ?? editResult)?.github_pr;
                  return (
                    <div className="rounded-2xl border border-gray-200 dark:border-white/8 overflow-hidden">
                      <div className="flex items-center gap-2.5 px-4 py-2.5 bg-gray-50 dark:bg-white/[0.03] border-b border-gray-100 dark:border-white/5">
                        <div className="flex h-4 w-4 items-center justify-center rounded bg-gradient-to-br from-violet-500 to-blue-500 text-white text-[9px] font-black shrink-0">✦</div>
                        <span className="text-xs font-mono text-gray-500 dark:text-gray-400 truncate flex-1">{file ?? "output"}</span>
                        {conf && (
                          <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${conf === "high" ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400"}`}>
                            {conf} confidence
                          </span>
                        )}
                        {pr && (
                          <a href={pr} target="_blank" rel="noopener noreferrer"
                            className="shrink-0 flex items-center gap-1 rounded-full bg-violet-500 px-2.5 py-0.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity">
                            ↗ View PR
                          </a>
                        )}
                      </div>
                      <pre className="p-4 text-xs text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap leading-relaxed max-h-[36rem] overflow-y-auto bg-[#fafafa] dark:bg-[#0a0a0e]">{code}</pre>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Docs */}
            {activeTab === "docs" && (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {([["readme", "README"], ["api", "API Docs"], ["technical", "Technical"], ["user_guide", "User Guide"]] as const).map(([t, label]) => (
                    <button key={t} onClick={() => setDocType(t)}
                      className={`rounded-xl px-3.5 py-1.5 text-xs font-semibold border transition-all ${
                        docType === t
                          ? "border-violet-300 dark:border-violet-500/50 bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-300 shadow-sm"
                          : "border-gray-200 dark:border-white/8 text-gray-400 dark:text-gray-500 hover:border-gray-300 dark:hover:border-white/15 hover:bg-gray-50 dark:hover:bg-white/[0.03]"
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-2.5 rounded-2xl border border-gray-200 dark:border-white/8 bg-gray-50 dark:bg-white/[0.03] px-4 py-3 focus-within:border-violet-300 dark:focus-within:border-violet-500/50 transition-all">
                  <svg className="h-3.5 w-3.5 text-gray-300 dark:text-gray-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                  <input value={docTarget} onChange={e => setDocTarget(e.target.value)}
                    className="flex-1 bg-transparent text-sm text-gray-600 dark:text-gray-300 outline-none placeholder-gray-300 dark:placeholder-gray-600"
                    placeholder="Target file or function (optional)" />
                </div>

                <div className="flex items-center gap-2">
                  <button onClick={() => setPushToGithub(p => !p)}
                    className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-medium border transition-all ${
                      pushToGithub
                        ? "border-violet-300 dark:border-violet-500/50 bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-300 shadow-sm"
                        : "border-gray-200 dark:border-white/8 text-gray-400 dark:text-gray-500 hover:border-gray-300 dark:hover:border-white/15"
                    }`}>
                    <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
                    </svg>
                    {pushToGithub ? "✓ Push to GitHub" : "Push to GitHub"}
                  </button>
                  <button onClick={handleGenerateDocs} disabled={docsLoading}
                    className="ml-auto flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-blue-500 px-5 py-2 text-xs font-bold text-white disabled:opacity-40 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-violet-300/30 dark:shadow-violet-700/30">
                    {docsLoading
                      ? <span className="flex items-center gap-1.5"><span className="animate-spin inline-block w-3 h-3 border border-white/30 border-t-white rounded-full" /> Generating…</span>
                      : <>📄 Generate</>}
                  </button>
                </div>

                {docsResult && (
                  <div className="rounded-2xl border border-gray-200 dark:border-white/8 overflow-hidden">
                    <div className="flex items-center gap-2.5 px-4 py-2.5 bg-gray-50 dark:bg-white/[0.03] border-b border-gray-100 dark:border-white/5">
                      <div className="flex h-4 w-4 items-center justify-center rounded bg-gradient-to-br from-violet-500 to-blue-500 text-white text-[9px] font-black shrink-0">✦</div>
                      <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 capitalize">{docType.replace("_", " ")}</span>
                      <span className="text-xs text-gray-300 dark:text-gray-600">·</span>
                      <span className="text-xs text-gray-400 dark:text-gray-500 font-mono truncate">{repoName.split("/")[1]}</span>
                    </div>
                    <div className="p-4 max-h-[36rem] overflow-y-auto">
                      <MarkdownContent content={docsResult} />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Search */}
            {activeTab === "search" && (
              <div className="space-y-3">
                <div className="group rounded-2xl border border-gray-200 dark:border-white/8 bg-gray-50 dark:bg-white/[0.03] focus-within:border-violet-300 dark:focus-within:border-violet-500/50 focus-within:shadow-md focus-within:shadow-violet-100/50 dark:focus-within:shadow-violet-900/20 transition-all overflow-hidden">
                  <input
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && void handleSearch()}
                    className="w-full bg-transparent px-4 py-3.5 text-sm text-gray-700 dark:text-gray-200 outline-none placeholder-gray-300 dark:placeholder-gray-600"
                    placeholder="Search codebase…"
                  />
                  <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 dark:border-white/5">
                    <span className="text-xs text-gray-300 dark:text-gray-600">Press Enter to search</span>
                    <button
                      onClick={() => void handleSearch()}
                      disabled={searching || !searchQuery.trim()}
                      className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-500 to-blue-500 px-3.5 py-1.5 text-xs font-semibold text-white disabled:opacity-40 hover:opacity-90 transition-opacity shadow-sm shadow-violet-300/40 dark:shadow-violet-700/40"
                    >
                      {searching
                        ? <><span className="inline-block w-3 text-center animate-pulse">···</span> Searching</>
                        : <>Search ↑</>}
                    </button>
                  </div>
                </div>

                {searchResults.length > 0 && (
                  <div className="rounded-2xl border border-gray-100 dark:border-white/6 overflow-hidden">
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-violet-50 to-transparent dark:from-violet-950/30 dark:to-transparent border-b border-gray-100 dark:border-white/5">
                      <div className="flex h-4 w-4 items-center justify-center rounded-md bg-gradient-to-br from-violet-500 to-blue-500 text-white text-[9px] font-black">✦</div>
                      <span className="text-xs font-semibold text-violet-700 dark:text-violet-300">{searchResults.length} result{searchResults.length !== 1 ? "s" : ""}</span>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-white/5 max-h-[36rem] overflow-y-auto">
                      {searchResults.map((r, i) => (
                        <div key={i} className="px-4 py-3">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-xs font-mono text-gray-500 dark:text-gray-400 truncate flex-1">{r.file_path}</span>
                            <span className="shrink-0 text-xs text-gray-300 dark:text-gray-600">:{r.lines}</span>
                            {r.language && (
                              <span className="shrink-0 rounded-full bg-gray-100 dark:bg-white/5 px-2 py-0.5 text-xs text-gray-400 dark:text-gray-500">{r.language}</span>
                            )}
                          </div>
                          <pre className="text-xs text-gray-500 dark:text-gray-400 font-mono whitespace-pre-wrap line-clamp-3 leading-relaxed">{r.content}</pre>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {!searching && searchQuery && searchResults.length === 0 && (
                  <p className="text-xs text-gray-300 dark:text-gray-600 text-center py-4">No results found.</p>
                )}
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
