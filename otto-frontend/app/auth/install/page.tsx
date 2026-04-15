"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function InstallPage() {
  const { refetchUser, refetchWorkspaces } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const init = async () => {
      await refetchUser();
      await refetchWorkspaces();
    };
    void init();
  }, []);

  const handleInstall = () => {
    window.location.href = "/api/github/install";
  };

  const handleSkip = () => {
    router.replace("/project/backlog");
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50 dark:bg-gray-950"
      style={{ fontFamily: "Inter, system-ui, sans-serif" }}>
      <div className="w-full max-w-md rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-8 shadow-sm">
        {/* Header */}
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-xl font-bold text-white shadow-md shadow-violet-200">
            O
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Connect your repositories
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Install the Otto GitHub App to let Otto index your repos and help you complete tickets.
          </p>
        </div>

        {/* Install button */}
        <button
          onClick={handleInstall}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-gray-900 dark:bg-gray-100 px-4 py-3 text-sm font-medium text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
        >
          {/* GitHub icon */}
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z" />
          </svg>
          Install GitHub App
        </button>

        {/* Skip button */}
        <button
          onClick={handleSkip}
          className="mt-3 w-full rounded-xl px-4 py-2.5 text-sm text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          Skip for now
        </button>
      </div>
    </div>
  );
}