"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";

export type User = {
  id: string;
  github_username: string;
  email: string | null;
  avatar_url: string;
  workspace_ids: string[];
  created_at: string;
  updated_at: string;
};

export type Workspace = {
  id: string;
  installation_id: string;
  name: string;
  join_code: string;
  repo_full_name: string;
  member_ids: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
};

interface AuthContextType {
  user: User | null;
  workspaces: Workspace[];
  loading: boolean;
  isAuthenticated: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
  refetchWorkspaces: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  workspaces: [],
  loading: true,
  isAuthenticated: false,
  login: () => {},
  logout: async () => {},
  refetchUser: async () => {},
  refetchWorkspaces: async () => {},
});

const API_BASE = "/api";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/users/me`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        return data;
      }
      setUser(null);
      return null;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  const fetchWorkspaces = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/users/me/workspaces`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data);
        return data;
      }
      setWorkspaces([]);
      return [];
    } catch {
      setWorkspaces([]);
      return [];
    }
  }, []);

  // Check if already logged in via session cookie
  // Also handle token from URL (post-OAuth redirect)
  useEffect(() => {
    const init = async () => {
      setLoading(true);

      // Handle post-OAuth token handoff from backend redirect.
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get("token");
      if (token) {
        document.cookie = `session_token=${token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`;
        const url = new URL(window.location.href);
        url.searchParams.delete("token");
        window.history.replaceState({}, "", url.toString());
      }

      const userData = await fetchUser();
      if (userData) await fetchWorkspaces();

      setLoading(false);
    };
    init();
  }, [fetchUser, fetchWorkspaces]);

  const login = () => {
    window.location.href = `${API_BASE}/auth/login`;
  };

  const logout = async () => {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    setWorkspaces([]);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{
      user, workspaces, loading,
      isAuthenticated: !!user,
      login, logout,
      refetchUser: fetchUser,
      refetchWorkspaces: fetchWorkspaces,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);