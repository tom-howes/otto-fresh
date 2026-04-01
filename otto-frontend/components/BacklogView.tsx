"use client";

import { useState, useRef } from "react";
import { Issue, STATUS_CONFIG, PRIORITY_COLORS, TYPE_ICONS, TYPE_COLORS } from "@/types";
import Avatar from "@/components/ui/Avatar";

interface BacklogViewProps {
  issues: Issue[];
  loading: boolean;
  search: string;
  onSelectIssue: (issue: Issue) => void;
  onCreateIssue: (sectionId: string, title: string) => Promise<void>;
}

function sectionLabel(section_id: string) {
  return section_id.replace(/[_-]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

export default function BacklogView({ issues, loading, search, onSelectIssue, onCreateIssue }: BacklogViewProps) {
  const PRESET_SECTIONS = ["backlog", "todo", "in_progress", "in_review", "done"];

  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [creatingIn, setCreatingIn] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newSection, setNewSection] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const toggle = (key: string) => setOpen(o => ({ ...o, [key]: !o[key] }));

  const startCreate = () => {
    setCreatingIn("global");
    setNewTitle("");
    setNewSection(sectionIds[0] || PRESET_SECTIONS[0]);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const submitCreate = async () => {
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    setCreateError(null);
    try {
      await onCreateIssue(newSection, newTitle.trim());
      setNewTitle("");
      setCreatingIn(null);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create issue");
    } finally {
      setCreating(false);
    }
  };

  const filtered = issues.filter(i =>
    !search ||
    i.title.toLowerCase().includes(search.toLowerCase()) ||
    i.id.toLowerCase().includes(search.toLowerCase())
  );

  // Group by section_id; fall back to single "Backlog" group if none
  const sectionIds = [...new Set(filtered.map(i => i.section_id ?? ""))].filter(Boolean);
  const groups: { key: string; label: string; issues: Issue[] }[] =
    sectionIds.length > 0
      ? sectionIds.map(id => ({ key: id, label: sectionLabel(id), issues: filtered.filter(i => i.section_id === id) }))
      : [{ key: "backlog", label: "Backlog", issues: filtered }];

  // Default all groups open
  const isOpen = (key: string) => key in open ? open[key] : true;

  if (loading) {
    return (
      <div className="p-6 space-y-3 overflow-auto h-full">
        {[0, 1].map(i => (
          <div key={i} className="h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
        ))}
      </div>
    );
  }

  const allSectionOptions = [...new Set([...sectionIds, ...PRESET_SECTIONS])];

  return (
    <div className="p-6 space-y-3 overflow-auto h-full">
      {/* Global create */}
      <div className="flex items-center gap-2 mb-1">
        {creatingIn === "global" ? (
          <div className="flex flex-1 flex-col gap-1.5">
            {createError && <p className="text-xs text-red-500">{createError}</p>}
            <div className="flex items-center gap-2">
              <input
                ref={inputRef}
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                onKeyDown={e => {
                  if (e.key === "Enter") void submitCreate();
                  if (e.key === "Escape") { setCreatingIn(null); setCreateError(null); }
                }}
                placeholder="Issue title…"
                className="flex-1 rounded-lg border border-violet-300 dark:border-violet-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-xs text-gray-700 dark:text-gray-200 outline-none"
              />
              <select
                value={newSection}
                onChange={e => setNewSection(e.target.value)}
                className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-2 py-1.5 text-xs text-gray-600 dark:text-gray-300 outline-none cursor-pointer"
              >
                {allSectionOptions.map(s => (
                  <option key={s} value={s}>{sectionLabel(s)}</option>
                ))}
              </select>
              <button
                onClick={() => void submitCreate()}
                disabled={creating || !newTitle.trim()}
                className="rounded-lg bg-violet-500 hover:bg-violet-600 disabled:opacity-50 px-3 py-1.5 text-xs font-medium text-white transition-colors"
              >
                {creating ? "…" : "Add"}
              </button>
              <button
                onClick={() => { setCreatingIn(null); setCreateError(null); }}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={startCreate}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 hover:border-violet-300 dark:hover:border-violet-700 hover:text-violet-500 dark:hover:text-violet-400 transition-colors shadow-sm"
          >
            <span className="text-base leading-none">+</span> New Issue
          </button>
        )}
      </div>

      {groups.map(group => (
        <div key={group.key} className="rounded-2xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 shadow-sm overflow-hidden">
          {/* Group header */}
          <div
            className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            onClick={() => toggle(group.key)}
          >
            <span className="text-gray-300 dark:text-gray-500 text-xs">{isOpen(group.key) ? "▼" : "▶"}</span>
            <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">{group.label}</span>
            <span className="ml-auto text-xs text-gray-300 dark:text-gray-600">{group.issues.length} issues</span>
          </div>

          {/* Issues */}
          {isOpen(group.key) && (
            <div className="border-t border-gray-100 dark:border-gray-700">
              {group.issues.length === 0 && (
                <p className="px-4 py-4 text-xs text-gray-300 dark:text-gray-600 text-center">No issues</p>
              )}
              {group.issues.map((issue, i) => (
                <div
                  key={issue.id}
                  onClick={() => onSelectIssue(issue)}
                  className={`flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors ${i !== 0 ? "border-t border-gray-50 dark:border-gray-700" : ""}`}
                >
                  <span className={`text-xs ${TYPE_COLORS[issue.type]}`}>{TYPE_ICONS[issue.type]}</span>
                  <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${PRIORITY_COLORS[issue.priority]}`} />
                  <span className="font-mono text-xs text-gray-300 dark:text-gray-500 w-16 shrink-0 truncate">{issue.id.slice(0, 8)}</span>
                  <span className="flex-1 text-sm text-gray-700 dark:text-gray-200">{issue.title}</span>
                  <div className={`rounded-full px-2.5 py-0.5 text-xs font-medium shrink-0 ${STATUS_CONFIG[issue.status].badge}`}>
                    {group.label}
                  </div>
                  <Avatar letter={issue.assignee} />
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
