"use client";
import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/use-auth-context";

// Inner component that uses useSearchParams (must be wrapped in Suspense)
const CallbackInner = () => {
  const { refetchUser, refetchWorkspaces } = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const finishAuth = async () => {
      // Backend passes session_token as query param to avoid cross-origin cookie issues.
      // We set it as a cookie on localhost so all proxied /api/* requests include it.
      const token = params.get("token");
      if (token) {
        document.cookie = `session_token=${token}; path=/; max-age=${
          60 * 60 * 24 * 7
        }; SameSite=Lax`;
      }

      await refetchUser();
      await refetchWorkspaces();
      router.replace("/project/backlog");
    };

    void finishAuth();
  }, []);

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
        <p className="text-sm text-gray-500">Signing you in…</p>
      </div>
    </div>
  );
};

const AuthCallbackPage = () => (
  <Suspense fallback={
    <div className="flex h-screen items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
    </div>
  }>
    <CallbackInner />
  </Suspense>
);

export default AuthCallbackPage;