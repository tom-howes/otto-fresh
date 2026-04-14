"use client";

import { Workspace } from "@/context/AuthContext";

interface WorkspacePickerProps {
  workspaces: Workspace[];
  onSelect: (id: string) => void;
}

export default function WorkspacePicker({ workspaces, onSelect }: WorkspacePickerProps) {
  return (
    <div className="flex h-full items-center justify-center bg-[#fafafa] dark:bg-gray-950"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      <div className="w-full max-w-md rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">

        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-xl font-bold text-white shadow-md shadow-violet-200">
            O
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Choose a workspace
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Select the workspace you want to open.
          </p>
        </div>

        <div className="space-y-2">
          {workspaces.map(w => (
            <button
              key={w.id}
              onClick={() => onSelect(w.id)}
              className="flex w-full items-center gap-3 rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3 text-left hover:border-violet-300 dark:hover:border-violet-500/50 hover:bg-violet-50/50 dark:hover:bg-violet-900/10 transition-all group"
            >
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-blue-500 text-xs font-bold text-white">
                {w.name[0].toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{w.name}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">{(w.member_ids ?? []).length} member{(w.member_ids ?? []).length !== 1 ? "s" : ""}</p>
              </div>
              <svg className="h-4 w-4 text-gray-300 dark:text-gray-600 group-hover:text-violet-400 transition-colors shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
