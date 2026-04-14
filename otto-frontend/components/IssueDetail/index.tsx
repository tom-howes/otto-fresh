"use client";

import { useState, useEffect, useRef } from "react";
import { Issue, IssueStatus, STATUS_CONFIG, TYPE_ICONS, TYPE_COLORS } from "@/types";
import CommentsSection from "./CommentsSection";
import OttoAIPanel from "./OttoAIPanel";
import MetadataSidebar from "./MetadataSidebar";

const SECTION_TO_STATUS: Record<string, IssueStatus> = {
  backlog: "TODO",
  todo: "TODO",
  in_progress: "IN_PROGRESS",
  done: "DONE",
};

interface Member {
  id: string;
  github_username: string;
  avatar_url: string;
}

interface IssueDetailProps {
  issue: Issue;
  workspaceId: string | null;
  members?: Member[];
  initialComments?: import("@/utils/api").BackendComment[];
  onBack: () => void;
  onUpdateIssue?: (update: Partial<Issue>) => void;
  onDeleteIssue?: () => Promise<void>;
}

export default function IssueDetail({ issue, workspaceId, members: membersProp, initialComments, onBack, onUpdateIssue, onDeleteIssue }: IssueDetailProps) {
  const derivedStatus = SECTION_TO_STATUS[issue.section_id ?? ""] ?? issue.status;
  const cfg = STATUS_CONFIG[derivedStatus];
  const [showOttoAI, setShowOttoAI] = useState(false);

  useEffect(() => {
    setShowOttoAI(localStorage.getItem("otto-ai-panel-open") === "true");
  }, []);
  const [members, setMembers] = useState<Member[]>(membersProp ?? []);

  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(issue.title);
  const titleInputRef = useRef<HTMLInputElement>(null);

  const [editingDesc, setEditingDesc] = useState(false);
  const [descDraft, setDescDraft] = useState(issue.description ?? "");

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Sync members when the prop updates (e.g. workspace changes)
  useEffect(() => {
    if (membersProp) setMembers(membersProp);
  }, [membersProp]);

  // Sync drafts when navigating to a different issue
  useEffect(() => {
    setTitleDraft(issue.title);
    setDescDraft(issue.description ?? "");
    setEditingTitle(false);
    setEditingDesc(false);
    setConfirmDelete(false);
  }, [issue.id]);

  useEffect(() => {
    if (editingTitle) titleInputRef.current?.focus();
  }, [editingTitle]);

  const saveTitle = () => {
    const trimmed = titleDraft.trim();
    if (trimmed && trimmed !== issue.title) {
      onUpdateIssue?.({ title: trimmed });
    } else {
      setTitleDraft(issue.title);
    }
    setEditingTitle(false);
  };

  const saveDesc = () => {
    const trimmed = descDraft.trim();
    const current = issue.description ?? "";
    if (trimmed !== current) {
      onUpdateIssue?.({ description: trimmed || undefined });
    }
    setEditingDesc(false);
  };

  const handleDelete = async () => {
    if (!onDeleteIssue) return;
    setDeleting(true);
    try {
      await onDeleteIssue();
    } finally {
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-6 border-r border-gray-100 dark:border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            ← Back
          </button>

          {onDeleteIssue && (
            confirmDelete ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-red-500">Delete this issue?</span>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="text-xs font-medium text-white bg-red-500 hover:bg-red-600 px-2.5 py-1 rounded-lg transition-colors disabled:opacity-50"
                >
                  {deleting ? "Deleting…" : "Confirm"}
                </button>
                <button
                  onClick={() => setConfirmDelete(false)}
                  className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="p-1.5 text-gray-300 dark:text-gray-600 hover:text-red-400 dark:hover:text-red-400 transition-colors"
                title="Delete issue"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )
          )}
        </div>

        <div className="flex items-center gap-2 mb-4">
          <span className={`text-sm ${TYPE_COLORS[issue.type]}`}>{TYPE_ICONS[issue.type]}</span>
          <span className="font-mono text-xs text-gray-300 dark:text-gray-600">{issue.id}</span>
          <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.badge}`}>
            <div className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </div>
          <div className="ml-auto">
            <button
              onClick={() => setShowOttoAI(prev => {
                const next = !prev;
                localStorage.setItem("otto-ai-panel-open", String(next));
                return next;
              })}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold text-white transition-opacity shadow-md shadow-violet-200 ${
                showOttoAI
                  ? "bg-violet-700 opacity-90"
                  : "bg-gradient-to-r from-violet-500 to-blue-500 hover:opacity-90"
              }`}
            >
              ✦ Otto AI
            </button>
          </div>
        </div>

        {/* Editable title */}
        {editingTitle ? (
          <input
            ref={titleInputRef}
            value={titleDraft}
            onChange={e => setTitleDraft(e.target.value)}
            onBlur={saveTitle}
            onKeyDown={e => {
              if (e.key === "Enter") saveTitle();
              if (e.key === "Escape") { setTitleDraft(issue.title); setEditingTitle(false); }
            }}
            className="w-full text-xl font-bold text-gray-900 dark:text-gray-100 bg-transparent border-b-2 border-violet-400 outline-none mb-4"
          />
        ) : (
          <h1
            onClick={() => setEditingTitle(true)}
            className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4 cursor-pointer hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
            title="Click to edit"
          >
            {issue.title}
          </h1>
        )}

        {/* Editable description */}
        {editingDesc ? (
          <textarea
            value={descDraft}
            onChange={e => setDescDraft(e.target.value)}
            onBlur={saveDesc}
            onKeyDown={e => {
              if (e.key === "Escape") { setDescDraft(issue.description ?? ""); setEditingDesc(false); }
            }}
            placeholder="Add a description…"
            rows={4}
            autoFocus
            className="w-full text-sm text-gray-500 dark:text-gray-400 bg-transparent border border-violet-300 dark:border-violet-500/50 rounded-lg p-2 outline-none resize-none mb-6"
          />
        ) : (
          <div
            onClick={() => setEditingDesc(true)}
            className="cursor-pointer mb-6"
            title="Click to edit"
          >
            {issue.description ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
                {issue.description}
              </p>
            ) : (
              <p className="text-sm text-gray-300 dark:text-gray-600 italic hover:text-gray-400 dark:hover:text-gray-500 transition-colors">
                Click to add a description…
              </p>
            )}
          </div>
        )}

        <CommentsSection workspaceId={workspaceId} issueId={issue.id} members={members} initialComments={initialComments} />

        {showOttoAI && <OttoAIPanel />}
      </div>

      <MetadataSidebar issue={issue} members={members} onUpdateIssue={onUpdateIssue} />
    </div>
  );
}
