"use client";

import { useState, useRef, useEffect } from "react";
import { Issue, PRIORITY_COLORS, TYPE_ICONS, TYPE_COLORS } from "@/types";
import Avatar from "@/components/ui/Avatar";

interface Member {
  id: string;
  github_username: string;
  avatar_url: string;
}

interface BoardViewProps {
  issues: Issue[];
  loading: boolean;
  search: string;
  members?: Member[];
  onSelectIssue: (issue: Issue) => void;
  onCreateIssue: (sectionId: string, title: string) => Promise<void>;
  onMoveIssue: (issueId: string, sectionId: string) => Promise<void>;
  onDeleteIssue: (issueId: string) => Promise<void>;
}

const SECTION_STYLES: Record<string, { dot: string; badge: string; label: string }> = {
  backlog:     { dot: "bg-gray-400",    badge: "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400",                   label: "text-gray-500 dark:text-gray-400" },
  todo:        { dot: "bg-blue-400",    badge: "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",                 label: "text-blue-600 dark:text-blue-400" },
  in_progress: { dot: "bg-violet-400",  badge: "bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400",         label: "text-violet-600 dark:text-violet-400" },
  done:        { dot: "bg-emerald-400", badge: "bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400",     label: "text-emerald-600 dark:text-emerald-400" },
};

const FALLBACK_STYLES = [
  { dot: "bg-blue-400",   badge: "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400",       label: "text-blue-600 dark:text-blue-400" },
  { dot: "bg-orange-400", badge: "bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400", label: "text-orange-600 dark:text-orange-400" },
];

const PRIORITY_ORDER: Record<string, number> = { urgent: 4, high: 3, medium: 2, low: 1 };

function getSectionStyle(sectionId: string, fallbackIdx: number) {
  return SECTION_STYLES[sectionId] ?? FALLBACK_STYLES[fallbackIdx % FALLBACK_STYLES.length];
}

function sectionLabel(id: string) {
  return id.replace(/[_-]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export default function BoardView({ issues, loading, search, members = [], onSelectIssue, onCreateIssue, onMoveIssue, onDeleteIssue }: BoardViewProps) {
  const [creatingIn, setCreatingIn] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [movingIssue, setMovingIssue] = useState<string | null>(null); // issueId showing section picker
  const [dragOverSection, setDragOverSection] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const pickerRef = useRef<HTMLDivElement>(null);

  const ORDERED_SECTIONS = ["backlog", "todo", "in_progress", "done"];
  const extraSections = issues.map(i => i.section_id ?? "").filter(s => s && !ORDERED_SECTIONS.includes(s));
  const sectionIds = [...new Set([...ORDERED_SECTIONS, ...extraSections])];
  const filtered = issues.filter(i =>
    !search ||
    i.title.toLowerCase().includes(search.toLowerCase()) ||
    i.id.toLowerCase().includes(search.toLowerCase())
  );
  const cols = sectionIds.length > 0 ? sectionIds : ["all"];

  useEffect(() => {
    if (creatingIn) setTimeout(() => inputRef.current?.focus(), 0);
  }, [creatingIn]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setMovingIssue(null);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const submitCreate = async (sectionId: string) => {
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    try {
      await onCreateIssue(sectionId, newTitle.trim());
      setNewTitle("");
      setCreatingIn(null);
    } finally {
      setCreating(false);
    }
  };

  const handleMove = async (issueId: string, targetSection: string) => {
    setMovingIssue(null);
    await onMoveIssue(issueId, targetSection);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-3 p-4 h-full overflow-auto content-start">
        {[0, 1, 2].map(i => (
          <div key={i}>
            <div className="mb-3 h-4 w-24 rounded bg-gray-100 dark:bg-gray-800 animate-pulse" />
            <div className="space-y-2">
              {[0, 1].map(j => (
                <div key={j} className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div
      className="grid gap-3 p-4 h-full overflow-auto content-start"
      style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(200px, 1fr))` }}
    >
      {cols.map((sectionId, idx) => {
        const style = getSectionStyle(sectionId, idx);
        const col = (sectionId === "all" ? filtered : filtered.filter(i => i.section_id === sectionId))
          .slice().sort((a, b) => (PRIORITY_ORDER[b.priority] ?? 0) - (PRIORITY_ORDER[a.priority] ?? 0));
        const otherSections = sectionIds.filter(s => s !== sectionId);

        return (
          <div
            key={sectionId}
            className={`flex flex-col rounded-2xl border transition-colors ${dragOverSection === sectionId ? "bg-violet-50/40 dark:bg-violet-900/10 border-violet-200 dark:border-violet-800 ring-2 ring-violet-200 dark:ring-violet-800" : "border-gray-100 dark:border-gray-800"}`}
            onDragEnter={e => { e.preventDefault(); setDragOverSection(sectionId); }}
            onDragOver={e => e.preventDefault()}
            onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragOverSection(null); }}
            onDrop={e => {
              e.preventDefault();
              setDragOverSection(null);
              const issueId = e.dataTransfer.getData("issueId");
              const fromSection = e.dataTransfer.getData("fromSection");
              if (issueId && fromSection !== sectionId) void handleMove(issueId, sectionId);
            }}
          >
            {/* Column header */}
            <div className="mb-3 flex items-center gap-2 px-3 pt-3">
              <div className={`h-2 w-2 rounded-full ${style.dot}`} />
              <span className={`text-xs font-semibold ${style.label}`}>
                {sectionId === "all" ? "All Issues" : sectionLabel(sectionId)}
              </span>
              <span className="ml-auto text-xs text-gray-300 dark:text-gray-600">{col.length}</span>
            </div>

            <div className="space-y-2 flex-1 px-3 pb-3">
              {col.map(issue => (
                <div
                  key={issue.id}
                  draggable={confirmDeleteId !== issue.id}
                  onDragStart={e => {
                    e.dataTransfer.effectAllowed = "move";
                    e.dataTransfer.setData("issueId", issue.id);
                    e.dataTransfer.setData("fromSection", sectionId);
                  }}
                  onClick={() => confirmDeleteId !== issue.id && onSelectIssue(issue)}
                  className="group rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 p-4 shadow-sm hover:shadow-md cursor-grab active:cursor-grabbing transition-shadow"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-xs ${TYPE_COLORS[issue.type]}`}>{TYPE_ICONS[issue.type]}</span>
                    <span className="font-mono text-xs text-gray-300 dark:text-gray-500 truncate max-w-[7rem]">{issue.id.slice(0, 8)}</span>
                    <div className={`ml-auto h-1.5 w-1.5 rounded-full ${PRIORITY_COLORS[issue.priority]}`} />
                    {/* Delete button */}
                    {confirmDeleteId === issue.id ? (
                      <div className="flex items-center gap-1.5 ml-1" onClick={e => e.stopPropagation()}>
                        <span className="text-xs text-red-400">Delete?</span>
                        <button
                          onClick={async () => {
                            setDeleting(true);
                            try { await onDeleteIssue(issue.id); } finally { setDeleting(false); setConfirmDeleteId(null); }
                          }}
                          disabled={deleting}
                          className="text-xs font-medium text-white bg-red-500 hover:bg-red-600 px-2 py-0.5 rounded-md transition-colors disabled:opacity-50"
                        >
                          {deleting ? "…" : "Yes"}
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        >
                          No
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={e => { e.stopPropagation(); setConfirmDeleteId(issue.id); }}
                        className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-300 dark:text-gray-600 hover:text-red-400 dark:hover:text-red-400 transition-all"
                        title="Delete issue"
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    )}
                  </div>
                  <p className="text-sm font-medium leading-snug mb-3 text-gray-800 dark:text-gray-100">
                    {issue.title}
                  </p>
                  <div className="flex items-center justify-between">
                    {/* Clickable section badge — move to another column */}
                    <div className="relative" ref={movingIssue === issue.id ? pickerRef : null}>
                      <button
                        onClick={e => {
                          e.stopPropagation();
                          setMovingIssue(movingIssue === issue.id ? null : issue.id);
                        }}
                        className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium hover:opacity-80 transition-opacity ${style.badge}`}
                      >
                        <div className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
                        {sectionId === "all" ? "Issue" : sectionLabel(sectionId)}
                        {otherSections.length > 0 && <span className="opacity-50">▾</span>}
                      </button>
                      {movingIssue === issue.id && otherSections.length > 0 && (
                        <div className="absolute left-0 top-7 z-20 w-44 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg py-1 overflow-hidden">
                          <p className="px-3 py-1.5 text-xs text-gray-400 dark:text-gray-500 font-medium">Move to…</p>
                          {otherSections.map((s) => {
                            const st = getSectionStyle(s, sectionIds.indexOf(s));
                            return (
                              <button
                                key={s}
                                onClick={e => { e.stopPropagation(); void handleMove(issue.id, s); }}
                                className="flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                              >
                                <div className={`h-2 w-2 rounded-full shrink-0 ${st.dot}`} />
                                <span className="text-xs text-gray-700 dark:text-gray-300">{sectionLabel(s)}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                    {(() => {
                      const m = members.find(m => String(m.id) === String(issue.assignee_id ?? ""));
                      return m?.avatar_url
                        ? <img src={m.avatar_url} alt={m.github_username} className="h-6 w-6 rounded-full border border-gray-200 dark:border-gray-700 shrink-0" />
                        : <Avatar letter={m?.github_username?.[0]?.toUpperCase() ?? issue.assignee} />;
                    })()}
                  </div>
                </div>
              ))}

              {/* Inline create */}
              {creatingIn === sectionId ? (
                <div className="rounded-2xl bg-white dark:bg-gray-800 border border-violet-300 dark:border-violet-600 p-3 shadow-sm space-y-2">
                  <input
                    ref={inputRef}
                    value={newTitle}
                    onChange={e => setNewTitle(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === "Enter") void submitCreate(sectionId);
                      if (e.key === "Escape") { setCreatingIn(null); setNewTitle(""); }
                    }}
                    placeholder="Issue title…"
                    className="w-full bg-transparent text-sm text-gray-700 dark:text-gray-200 outline-none placeholder-gray-300 dark:placeholder-gray-600"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => void submitCreate(sectionId)}
                      disabled={creating || !newTitle.trim()}
                      className="rounded-lg bg-violet-500 hover:bg-violet-600 disabled:opacity-50 px-3 py-1 text-xs font-medium text-white transition-colors"
                    >
                      {creating ? "…" : "Add"}
                    </button>
                    <button
                      onClick={() => { setCreatingIn(null); setNewTitle(""); }}
                      className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => { setCreatingIn(sectionId); setNewTitle(""); }}
                  className="w-full rounded-2xl border-2 border-dashed border-gray-200 dark:border-gray-700 py-3 text-xs text-gray-300 dark:text-gray-600 hover:border-violet-300 dark:hover:border-violet-700 hover:text-violet-400 dark:hover:text-violet-500 transition-colors"
                >
                  + Add issue
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
