"use client";

import { useState } from "react";
import { workspaceApi } from "@/utils/api";

interface WorkspaceSetupProps {
  onDone: () => Promise<void>;
}

export default function WorkspaceSetup({ onDone }: WorkspaceSetupProps) {
  const [tab, setTab] = useState<"create" | "join">("create");
  const [name, setName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      await workspaceApi.create(name.trim());
      await onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create workspace");
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!joinCode.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      await workspaceApi.join(joinCode.trim());
      await onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid join code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full items-center justify-center bg-[#fafafa] dark:bg-gray-950"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      <div className="w-full max-w-md rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">

        {/* Header */}
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-xl font-bold text-white shadow-md shadow-violet-200">
            O
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Set up your workspace
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Create a workspace for your team, or enter an invite code to join an existing one.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
          {(["create", "join"] as const).map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(null); }}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                tab === t
                  ? "bg-violet-50 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400"
                  : "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
              }`}
            >
              {t === "create" ? "Create new" : "Join with invite code"}
            </button>
          ))}
        </div>

        {/* Create tab */}
        {tab === "create" && (
          <div className="space-y-3">
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && void handleCreate()}
              placeholder="Workspace name (e.g. My Team)"
              className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 outline-none placeholder-gray-400 dark:placeholder-gray-500 focus:border-violet-400 dark:focus:border-violet-500 transition-colors"
            />
            {error && <p className="text-xs text-red-500">{error}</p>}
            <button
              onClick={() => void handleCreate()}
              disabled={loading || !name.trim()}
              className="w-full rounded-xl bg-gradient-to-r from-violet-500 to-blue-500 px-4 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? "Creating…" : "Create workspace"}
            </button>
          </div>
        )}

        {/* Join tab */}
        {tab === "join" && (
          <div className="space-y-3">
            <p className="text-xs text-gray-400 dark:text-gray-500">
              Ask your teammate to share the invite code from their workspace settings.
            </p>
            <input
              value={joinCode}
              onChange={e => setJoinCode(e.target.value)}
              onKeyDown={e => e.key === "Enter" && void handleJoin()}
              placeholder="Enter invite code"
              className="w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-sm text-gray-800 dark:text-gray-100 outline-none placeholder-gray-400 dark:placeholder-gray-500 focus:border-violet-400 dark:focus:border-violet-500 transition-colors font-mono tracking-widest"
            />
            {error && <p className="text-xs text-red-500">{error}</p>}
            <button
              onClick={() => void handleJoin()}
              disabled={loading || !joinCode.trim()}
              className="w-full rounded-xl bg-gradient-to-r from-violet-500 to-blue-500 px-4 py-3 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? "Joining…" : "Join workspace"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
