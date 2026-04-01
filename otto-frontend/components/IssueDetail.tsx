"use client";

import { useState, useRef, useEffect } from "react";
import { Issue, STATUS_CONFIG, TYPE_ICONS, TYPE_COLORS } from "@/types";
import Avatar from "@/components/ui/Avatar";
import CommentsSection from "./IssueDetail/CommentsSection";
import OttoAIPanel from "./IssueDetail/OttoAIPanel";

interface IssueDetailProps {
  issue: Issue;
  workspaceId: string | null;
  onBack: () => void;
  onUpdateIssue?: (updated: Partial<Issue>) => void;
}

const STATIC_MEMBERS = [
  { letter: "S", name: "Shloka" },
  { letter: "M", name: "Malav" },
  { letter: "P", name: "Paschal" },
  { letter: "T", name: "Tom" },
  { letter: "SC", name: "Sahil" },
  { letter: "A", name: "Ayushman" },
];

export default function IssueDetail({ issue, workspaceId, onBack, onUpdateIssue }: IssueDetailProps) {
  const cfg = STATUS_CONFIG[issue.status];
  const [showOttoAI, setShowOttoAI] = useState(false);
  const [assignee, setAssignee] = useState(issue.assignee === "?" ? null : issue.assignee);
  const [showAssigneePicker, setShowAssigneePicker] = useState(false);
  const assigneeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (assigneeRef.current && !assigneeRef.current.contains(e.target as Node)) {
        setShowAssigneePicker(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-6 border-r border-gray-100 dark:border-gray-800">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 mb-4 transition-colors"
        >
          ← Back
        </button>

        <div className="flex items-center gap-2 mb-4">
          <span className={`text-sm ${TYPE_COLORS[issue.type]}`}>{TYPE_ICONS[issue.type]}</span>
          <span className="font-mono text-xs text-gray-300 dark:text-gray-600">{issue.id}</span>
          <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.badge}`}>
            <div className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </div>
          <div className="ml-auto">
            <button
              onClick={() => setShowOttoAI(prev => !prev)}
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

        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">{issue.title}</h1>
        {issue.description ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-6">{issue.description}</p>
        ) : (
          <p className="text-sm text-gray-300 dark:text-gray-600 italic mb-6">No description.</p>
        )}

        <CommentsSection workspaceId={workspaceId} issueId={issue.id} />

        {showOttoAI && <OttoAIPanel />}
      </div>

      {/* Metadata sidebar */}
      <div className="w-56 shrink-0 p-5 space-y-5 bg-gray-50/50 dark:bg-gray-900/50">
        {[
          {
            label: "Section",
            el: <span className="text-xs text-gray-600 dark:text-gray-300">{issue.section_id ?? cfg.label}</span>,
          },
          {
            label: "Priority",
            el: <span className="text-xs font-medium capitalize" style={{ color: issue.priority === "urgent" ? "#f87171" : issue.priority === "high" ? "#fb923c" : issue.priority === "medium" ? "#facc15" : "#60a5fa" }}>{issue.priority}</span>,
          },
          {
            label: "Assignee",
            el: (
              <div className="relative" ref={assigneeRef}>
                <button
                  onClick={() => setShowAssigneePicker(p => !p)}
                  className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                >
                  <Avatar letter={assignee ?? "?"} />
                  <span className="text-xs text-gray-600 dark:text-gray-300 truncate">
                    {assignee
                      ? STATIC_MEMBERS.find(m => m.letter === assignee)?.name ?? assignee
                      : <span className="text-gray-400 dark:text-gray-500">Unassigned</span>}
                  </span>
                </button>
                {showAssigneePicker && (
                  <div className="absolute left-0 top-8 z-10 w-44 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg py-1 overflow-hidden">
                    <button
                      onClick={() => { setAssignee(null); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: "?" }); }}
                      className="flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <Avatar letter="?" />
                      <span className="text-xs text-gray-400 dark:text-gray-500">Unassigned</span>
                    </button>
                    {STATIC_MEMBERS.map(m => (
                      <button
                        key={m.letter}
                        onClick={() => { setAssignee(m.letter); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: m.letter }); }}
                        className={`flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${assignee === m.letter ? "bg-violet-50 dark:bg-violet-900/30" : ""}`}
                      >
                        <Avatar letter={m.letter} />
                        <span className="text-xs text-gray-700 dark:text-gray-300">{m.name}</span>
                        {assignee === m.letter && <span className="ml-auto text-violet-500 text-xs">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ),
          },
          {
            label: "Created",
            el: <span className="text-xs text-gray-400 dark:text-gray-500">{issue.created_at ? new Date(issue.created_at).toLocaleDateString() : "—"}</span>,
          },
        ].map(({ label, el }) => (
          <div key={label}>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-1.5">{label}</p>
            {el}
          </div>
        ))}
      </div>
    </div>
  );
}
