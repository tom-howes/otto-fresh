"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/use-auth-context";
import { FaGithub } from "react-icons/fa";

const API_BASE = "/api";

const InstallPage = () => {
  const { refetchUser, refetchWorkspaces, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Re-fetch user in case cookie just got set
    const init = async () => {
      await refetchUser();
      await refetchWorkspaces();
    };
    void init();
  }, []);

  const handleInstall = () => {
    window.location.href = `${API_BASE}/github/install`;
  };

  const handleSkip = () => {
    router.replace("/project/backlog");
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-6 flex flex-col items-center text-center">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 text-xl font-bold text-white">
            O
          </div>
          <h1 className="text-xl font-semibold text-gray-900">Connect your repositories</h1>
          <p className="mt-2 text-sm text-gray-500">
            Install the Otto GitHub App to let Otto index your repos and help you complete tickets.
          </p>
        </div>

        <button
          onClick={handleInstall}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gray-900 px-4 py-3 text-sm font-medium text-white hover:bg-gray-800"
        >
          <FaGithub className="text-lg" />
          Install GitHub App
        </button>

        <button
          onClick={handleSkip}
          className="mt-3 w-full rounded-lg px-4 py-2.5 text-sm text-gray-500 hover:bg-gray-50"
        >
          Skip for now
        </button>
      </div>
    </div>
  );
};

export default InstallPage;