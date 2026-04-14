"use client";

import { useState, useRef, useEffect } from "react";
import { Issue, IssuePriority } from "@/types";
import Avatar from "@/components/ui/Avatar";

interface Member {
  id: string;
  github_username: string;
  avatar_url: string;
}

interface MetadataSidebarProps {
  issue: Issue;
  members: Member[];
  onUpdateIssue?: (update: Partial<Issue>) => void;
}

const PRIORITIES: IssuePriority[] = ["urgent", "high", "medium", "low"];

const PRIORITY_STYLE: Record<IssuePriority, { color: string; dot: string }> = {
  urgent: { color: "#f87171", dot: "bg-red-400" },
  high:   { color: "#fb923c", dot: "bg-orange-400" },
  medium: { color: "#facc15", dot: "bg-yellow-300" },
  low:    { color: "#60a5fa", dot: "bg-blue-400" },
};

export default function MetadataSidebar({ issue, members, onUpdateIssue }: MetadataSidebarProps) {
  const [assigneeId, setAssigneeId] = useState<string | null>(issue.assignee_id ?? null);
  const [showAssigneePicker, setShowAssigneePicker] = useState(false);
  const [showPriorityPicker, setShowPriorityPicker] = useState(false);
  const assigneeRef = useRef<HTMLDivElement>(null);
  const priorityRef = useRef<HTMLDivElement>(null);

  // Sync assigneeId when the issue prop changes (e.g. navigating between issues)
  useEffect(() => {
    setAssigneeId(issue.assignee_id ?? null);
  }, [issue.id, issue.assignee_id]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (assigneeRef.current && !assigneeRef.current.contains(e.target as Node)) {
        setShowAssigneePicker(false);
      }
      if (priorityRef.current && !priorityRef.current.contains(e.target as Node)) {
        setShowPriorityPicker(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const priorityColor = PRIORITY_STYLE[issue.priority]?.color ?? "#60a5fa";

  const STATUS_CONFIG_LABEL: Record<string, string> = {
    TODO: "To Do", IN_PROGRESS: "In Progress", DONE: "Done",
  };

  // Normalize IDs to strings since backend may return numeric GitHub user IDs
  const assignedMember = members.find(m => String(m.id) === String(assigneeId ?? ""));

  return (
    <div className="w-56 shrink-0 p-5 space-y-5 bg-gray-50/50 dark:bg-gray-900/50">
      {[
        {
          label: "Section",
          el: <span className="text-xs text-gray-600 dark:text-gray-300">{issue.section_id ?? STATUS_CONFIG_LABEL[issue.status]}</span>,
        },
        {
          label: "Priority",
          el: (
            <div className="relative" ref={priorityRef}>
              <button
                onClick={() => setShowPriorityPicker(p => !p)}
                className="flex items-center gap-1.5 hover:opacity-80 transition-opacity"
              >
                <div className={`h-1.5 w-1.5 rounded-full ${PRIORITY_STYLE[issue.priority]?.dot}`} />
                <span className="text-xs font-medium capitalize" style={{ color: priorityColor }}>{issue.priority}</span>
                <span className="text-gray-300 dark:text-gray-600 text-xs">▾</span>
              </button>
              {showPriorityPicker && (
                <div className="absolute left-0 top-7 z-10 w-36 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg py-1 overflow-hidden">
                  {PRIORITIES.map(p => (
                    <button
                      key={p}
                      onClick={() => { setShowPriorityPicker(false); onUpdateIssue?.({ priority: p }); }}
                      className={`flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${issue.priority === p ? "bg-gray-50 dark:bg-gray-800/60" : ""}`}
                    >
                      <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${PRIORITY_STYLE[p].dot}`} />
                      <span className="text-xs capitalize font-medium" style={{ color: PRIORITY_STYLE[p].color }}>{p}</span>
                      {issue.priority === p && <span className="ml-auto text-xs" style={{ color: PRIORITY_STYLE[p].color }}>✓</span>}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ),
        },
        {
          label: "Assignee",
          el: (
            <div className="relative" ref={assigneeRef}>
              <button
                onClick={() => setShowAssigneePicker(p => !p)}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
              >
                {assignedMember?.avatar_url ? (
                  <img src={assignedMember.avatar_url} alt={assignedMember.github_username} className="h-6 w-6 rounded-full border border-gray-200 dark:border-gray-700" />
                ) : (
                  <Avatar letter={assignedMember?.github_username?.[0]?.toUpperCase() ?? "?"} />
                )}
                <span className="text-xs text-gray-600 dark:text-gray-300 truncate">
                  {assignedMember
                    ? assignedMember.github_username
                    : <span className="text-gray-400 dark:text-gray-500">Unassigned</span>}
                </span>
              </button>
              {showAssigneePicker && (
                <div className="absolute left-0 top-8 z-10 w-48 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg py-1 overflow-hidden">
                  <button
                    onClick={() => { setAssigneeId(null); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: "?", assignee_id: null }); }}
                    className="flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <Avatar letter="?" />
                    <span className="text-xs text-gray-400 dark:text-gray-500">Unassigned</span>
                  </button>
                  {members.map(m => (
                    <button
                      key={m.id}
                      onClick={() => { setAssigneeId(m.id); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: m.github_username[0]?.toUpperCase() ?? "?", assignee_id: m.id }); }}
                      className={`flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${assigneeId === m.id ? "bg-violet-50 dark:bg-violet-900/30" : ""}`}
                    >
                      {m.avatar_url ? (
                        <img src={m.avatar_url} alt={m.github_username} className="h-6 w-6 rounded-full border border-gray-200 dark:border-gray-700" />
                      ) : (
                        <Avatar letter={m.github_username[0].toUpperCase()} />
                      )}
                      <span className="text-xs text-gray-700 dark:text-gray-300">{m.github_username}</span>
                      {assigneeId === m.id && <span className="ml-auto text-violet-500 text-xs">✓</span>}
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
  );
}
