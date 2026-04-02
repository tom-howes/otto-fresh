"use client";

import { useState } from "react";
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

interface IssueDetailProps {
  issue: Issue;
  workspaceId: string | null;
  onBack: () => void;
  onUpdateIssue?: (update: Partial<Issue>) => void;
}

export default function IssueDetail({ issue, workspaceId, onBack, onUpdateIssue }: IssueDetailProps) {
  const derivedStatus = SECTION_TO_STATUS[issue.section_id ?? ""] ?? issue.status;
  const cfg = STATUS_CONFIG[derivedStatus];
  const [showOttoAI, setShowOttoAI] = useState(false);

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

      <MetadataSidebar issue={issue} onUpdateIssue={onUpdateIssue} />
    </div>
  );
}
