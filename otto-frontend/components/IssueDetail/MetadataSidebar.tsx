"use client";

import { useState, useRef, useEffect } from "react";
import { Issue } from "@/types";
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

export default function MetadataSidebar({ issue, members, onUpdateIssue }: MetadataSidebarProps) {
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

  const priorityColor =
    issue.priority === "urgent" ? "#f87171" :
    issue.priority === "high"   ? "#fb923c" :
    issue.priority === "medium" ? "#facc15" : "#60a5fa";

  const STATUS_CONFIG_LABEL: Record<string, string> = {
    TODO: "To Do", IN_PROGRESS: "In Progress", DONE: "Done",
  };

  const assignedMember = members.find(m => m.id === assignee || m.github_username === assignee);

  return (
    <div className="w-56 shrink-0 p-5 space-y-5 bg-gray-50/50 dark:bg-gray-900/50">
      {[
        {
          label: "Section",
          el: <span className="text-xs text-gray-600 dark:text-gray-300">{issue.section_id ?? STATUS_CONFIG_LABEL[issue.status]}</span>,
        },
        {
          label: "Priority",
          el: <span className="text-xs font-medium capitalize" style={{ color: priorityColor }}>{issue.priority}</span>,
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
                    onClick={() => { setAssignee(null); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: "?" }); }}
                    className="flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <Avatar letter="?" />
                    <span className="text-xs text-gray-400 dark:text-gray-500">Unassigned</span>
                  </button>
                  {members.map(m => (
                    <button
                      key={m.id}
                      onClick={() => { setAssignee(m.id); setShowAssigneePicker(false); onUpdateIssue?.({ assignee: m.id }); }}
                      className={`flex w-full items-center gap-2.5 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${assignee === m.id ? "bg-violet-50 dark:bg-violet-900/30" : ""}`}
                    >
                      {m.avatar_url ? (
                        <img src={m.avatar_url} alt={m.github_username} className="h-6 w-6 rounded-full border border-gray-200 dark:border-gray-700" />
                      ) : (
                        <Avatar letter={m.github_username[0].toUpperCase()} />
                      )}
                      <span className="text-xs text-gray-700 dark:text-gray-300">{m.github_username}</span>
                      {assignee === m.id && <span className="ml-auto text-violet-500 text-xs">✓</span>}
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
