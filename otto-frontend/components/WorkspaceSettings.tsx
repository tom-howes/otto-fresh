"use client";

import { useState } from "react";
import { workspaceApi } from "@/utils/api";
import { Workspace } from "@/context/AuthContext";

interface Props {
  workspace: Workspace;
  onClose: () => void;
  onUpdated: (newName: string) => void;
}

export default function WorkspaceSettings({ workspace, onClose, onUpdated }: Props) {
  const [name, setName] = useState(workspace.name);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSaveName = async () => {
    if (!name.trim()) return;
    if (name.trim() === workspace.name) { setEditing(false); return; }
    setSaving(true);
    setError(null);
    try {
      await workspaceApi.update(workspace.id, { name: name.trim() });
      onUpdated(name.trim());
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(workspace.join_code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-sm rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xl p-6">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 text-lg leading-none"
        >
          ×
        </button>

        <h2 className="text-sm font-bold text-gray-800 dark:text-gray-100 mb-6">Workspace Settings</h2>

        {/* Name */}
        <div className="mb-5">
          <label className="block text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            Name
          </label>
          {editing ? (
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  value={name}
                  onChange={e => setName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter") void handleSaveName();
                    if (e.key === "Escape") { setName(workspace.name); setEditing(false); }
                  }}
                  autoFocus
                  className="flex-1 rounded-lg border border-violet-300 dark:border-violet-500/50 bg-gray-50 dark:bg-gray-800 px-3 py-2 text-sm text-gray-800 dark:text-gray-100 outline-none"
                />
                <button
                  onClick={() => void handleSaveName()}
                  disabled={saving || !name.trim()}
                  className="rounded-lg bg-violet-500 px-3 py-2 text-xs font-medium text-white disabled:opacity-50 hover:bg-violet-600 transition-colors"
                >
                  {saving ? "…" : "Save"}
                </button>
                <button
                  onClick={() => { setName(workspace.name); setEditing(false); setError(null); }}
                  className="rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 text-xs text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  Cancel
                </button>
              </div>
              {error && <p className="text-xs text-red-500">{error}</p>}
            </div>
          ) : (
            <button
              onClick={() => setEditing(true)}
              className="group flex items-center gap-2 w-full text-left rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2 hover:border-gray-300 dark:hover:border-gray-600 transition-colors"
            >
              <span className="flex-1 text-sm text-gray-700 dark:text-gray-200">{name}</span>
              <svg className="h-3.5 w-3.5 text-gray-300 dark:text-gray-600 group-hover:text-gray-400 transition-colors shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
          )}
        </div>

        {/* Invite code */}
        <div className="mb-5">
          <label className="block text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            Invite Code
          </label>
          <div className="flex items-center gap-2">
            <div className="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-3 py-2">
              <span className="text-sm font-mono tracking-widest text-gray-700 dark:text-gray-200">
                {workspace.join_code}
              </span>
            </div>
            <button
              onClick={handleCopy}
              className={`rounded-lg border px-3 py-2 text-xs font-medium transition-all ${
                copied
                  ? "border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                  : "border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600"
              }`}
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <p className="mt-1.5 text-xs text-gray-400 dark:text-gray-500">
            Share this code with teammates to invite them.
          </p>
        </div>

        {/* Members */}
        <div>
          <label className="block text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            Members
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {workspace.member_ids.length} member{workspace.member_ids.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>
    </div>
  );
}
