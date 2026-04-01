"use client";

import { useState, useEffect } from "react";
import { Issue } from "@/types";
import { useTheme } from "@/components/ThemeProvider";
import { useAuth } from "@/context/AuthContext";
import Avatar from "@/components/ui/Avatar";
import BoardView from "@/components/BoardView";
import BacklogView from "@/components/BacklogView";
import IssueDetail from "@/components/IssueDetail";
import { workspaceApi, adaptIssue } from "@/utils/api";
import WorkspaceSetup from "@/components/WorkspaceSetup";
import WorkspaceSettings from "@/components/WorkspaceSettings";

type View = "Board" | "Issues" | "Roadmap";
const NAV: View[] = ["Board", "Issues", "Roadmap"];

export default function OttoPM({ defaultView = "Board" }: { defaultView?: View }) {
  const [view, setView] = useState<View>(defaultView);
  const [search, setSearch] = useState("");
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [issuesLoading, setIssuesLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const { theme, toggle } = useTheme();
  const { user, workspaces, loading, login, logout, refetchWorkspaces } = useAuth();

  const workspaceId = workspaces[0]?.id ?? null;

  useEffect(() => {
    if (!workspaceId) return;
    const load = async () => {
      setIssuesLoading(true);
      try {
        const res = await workspaceApi.getIssues(workspaceId);
        setIssues((res.issues ?? []).map(adaptIssue));
      } catch { /* silent */ } finally {
        setIssuesLoading(false);
      }
    };
    void load();
  }, [workspaceId]);

  const handleCreateIssue = async (sectionId: string, title: string) => {
    if (!workspaceId) throw new Error("No workspace found. Make sure you've created or joined a workspace.");
    const raw = await workspaceApi.createIssue(workspaceId, title.trim(), sectionId);
    setIssues(prev => [...prev, adaptIssue(raw)]);
  };

  const handleMoveIssue = async (issueId: string, sectionId: string) => {
    if (!workspaceId) return;
    const raw = await workspaceApi.updateIssue(workspaceId, issueId, { section_id: sectionId });
    setIssues(prev => prev.map(i => i.id === issueId ? { ...adaptIssue(raw), assignee: i.assignee } : i));
  };

  const handleNav = (n: View) => {
    setView(n);
    setSelectedIssue(null);
  };

  return (
    <div className="flex h-screen flex-col bg-[#fafafa] dark:bg-gray-950" style={{ fontFamily: "Inter, system-ui, sans-serif" }}>

      {/* ── Top Navbar ── */}
      <div className="flex h-12 shrink-0 items-center border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 shadow-sm">
        {/* Logo */}
        <div className="flex items-center gap-2 mr-5">
          <div className="h-7 w-7 rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-violet-200">
            O
          </div>
          <span className="text-sm font-bold text-gray-800 dark:text-gray-100">Otto PM</span>
        </div>

        <div className="h-4 w-px bg-gray-100 dark:bg-gray-700 mr-4" />

        {/* Nav tabs */}
        {NAV.map(n => (
          <button
            key={n}
            onClick={() => handleNav(n)}
            className={`relative px-3.5 h-12 text-xs font-medium transition-colors ${
              view === n
                ? "text-violet-600 dark:text-violet-400"
                : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            }`}
          >
            {n}
            {view === n && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 rounded-t-full bg-violet-500" />
            )}
          </button>
        ))}

        {/* Right side */}
        <div className="ml-auto flex items-center gap-2">
          {/* Search */}
          <div className="flex items-center gap-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-2.5 py-1.5 w-32 focus-within:border-violet-400 transition-colors">
            <svg className="h-3 w-3 text-gray-300 dark:text-gray-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
            </svg>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search..."
              className="bg-transparent text-xs text-gray-600 dark:text-gray-300 outline-none placeholder-gray-300 dark:placeholder-gray-600 w-full"
            />
          </div>

          {/* Team avatars */}
          <div className="flex -space-x-1.5">
            {["S", "M", "P", "A"].map(l => <Avatar key={l} letter={l} />)}
          </div>

          {/* Filters */}
          {["Epic ▾", "Type ▾"].map(f => (
            <button key={f} className="rounded-lg border border-gray-200 dark:border-gray-700 px-2 py-1.5 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              {f}
            </button>
          ))}

          <div className="h-4 w-px bg-gray-100 dark:bg-gray-700" />

          {/* Dark mode toggle */}
          <button
            onClick={toggle}
            className="rounded-lg border border-gray-200 dark:border-gray-700 p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              // Sun icon
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 7a5 5 0 1 0 0 10A5 5 0 0 0 12 7z" />
              </svg>
            ) : (
              // Moon icon
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            )}
          </button>

          <div className="h-4 w-px bg-gray-100 dark:bg-gray-700" />

          {/* Auth */}
          {loading ? (
            <div className="h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse" />
          ) : user ? (
            <div className="flex items-center gap-2">
              <img src={user.avatar_url} alt={user.github_username}
                className="h-7 w-7 rounded-full border border-gray-200 dark:border-gray-700" />
              <button onClick={logout}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                Sign out
              </button>
            </div>
          ) : (
            <button onClick={login}
              className="flex items-center gap-1.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-1.5 text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors shadow-sm">
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
              </svg>
              Sign in with GitHub
            </button>
          )}
        </div>
      </div>

      {/* ── Sub-header ── */}
      <div className="flex h-9 shrink-0 items-center border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 px-5">
        <button
          onClick={() => workspaces[0] && setShowSettings(true)}
          className="text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          {workspaces[0]?.name ?? "Sample Project"}
        </button>
        <span className="mx-1.5 text-xs text-gray-300 dark:text-gray-600">/</span>
        <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
          {selectedIssue
            ? `${selectedIssue.id} · ${selectedIssue.title}`
            : view === "Board" ? "Active sprints" : view === "Issues" ? "All issues" : view}
        </span>
        {workspaces[0] && (
          <button
            onClick={() => setShowSettings(true)}
            className="ml-auto text-gray-300 dark:text-gray-600 hover:text-gray-500 dark:hover:text-gray-400 transition-colors"
            title="Workspace settings"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        )}
      </div>

      {/* Workspace settings modal */}
      {showSettings && workspaces[0] && (
        <WorkspaceSettings
          workspace={workspaces[0]}
          onClose={() => setShowSettings(false)}
          onUpdated={() => { setShowSettings(false); void refetchWorkspaces(); }}
        />
      )}

      {/* ── Content ── */}
      <div className="flex-1 overflow-hidden">
        {/* No workspace yet — show setup screen */}
        {!loading && user && workspaces.length === 0 ? (
          <WorkspaceSetup onDone={refetchWorkspaces} />
        ) : selectedIssue ? (
          <IssueDetail
            issue={selectedIssue}
            workspaceId={workspaceId}
            onBack={() => setSelectedIssue(null)}
            onUpdateIssue={(updated) => {
              const merged = { ...selectedIssue, ...updated };
              setSelectedIssue(merged);
              setIssues(prev => prev.map(i => i.id === selectedIssue.id ? merged : i));
            }}
          />
        ) : workspaces.length > 0 ? (
          <>
            {view === "Board"  && <BoardView   issues={issues} loading={issuesLoading} search={search} onSelectIssue={setSelectedIssue} onCreateIssue={handleCreateIssue} onMoveIssue={handleMoveIssue} />}
            {view === "Issues" && <BacklogView issues={issues} loading={issuesLoading} search={search} onSelectIssue={setSelectedIssue} onCreateIssue={handleCreateIssue} />}
            {view === "Roadmap" && (
              <div className="flex items-center justify-center h-full text-gray-300 dark:text-gray-600 text-sm">
                Roadmap — coming soon
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}