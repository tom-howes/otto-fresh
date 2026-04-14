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
  updateWorkspace: (id: string, updates: Partial<Workspace>) => void;
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
  updateWorkspace: () => {},
});

const API_BASE = "/api";
const TOKEN_KEY = "session_token";
const SESSION_MAX_AGE = 6 * 60 * 60; // 6 hours

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

function storeToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token);
  document.cookie = `session_token=${token}; path=/; max-age=${SESSION_MAX_AGE}; SameSite=Lax`;
}

function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getStoredToken();
  return fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  // Try to get a new session_token using the refresh_token cookie (httpOnly, sent automatically)
  const tryRefresh = useCallback(async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.token) storeToken(data.token);
      return true;
    } catch {
      return false;
    }
  }, []);

  const fetchUser = useCallback(async () => {
    const attempt = async () => {
      const res = await authFetch(`${API_BASE}/users/me`);
      if (res.ok) return res.json();
      if (res.status === 401) return null;
      return null;
    };

    try {
      let data = await attempt();

      // Session token expired — try refreshing once
      if (!data) {
        const refreshed = await tryRefresh();
        if (refreshed) {
          data = await attempt();
        }
      }

      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, [tryRefresh]);

  const fetchWorkspaces = useCallback(async (clearOnFailure = false) => {
    try {
      const res = await authFetch(`${API_BASE}/users/me/workspaces`);
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data);
        return data;
      }
      if (clearOnFailure) setWorkspaces([]);
      return [];
    } catch {
      if (clearOnFailure) setWorkspaces([]);
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
        storeToken(token);
        const url = new URL(window.location.href);
        url.searchParams.delete("token");
        window.history.replaceState({}, "", url.toString());
      }

      const userData = await fetchUser();
      if (userData) await fetchWorkspaces(true);

      setLoading(false);
    };
    init();
  }, [fetchUser, fetchWorkspaces]);

  const updateWorkspace = useCallback((id: string, updates: Partial<Workspace>) => {
    setWorkspaces(prev => prev.map(w => w.id === id ? { ...w, ...updates } : w));
  }, []);

  const login = () => {
    window.location.href = `${API_BASE}/auth/login`;
  };

  const logout = async () => {
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("otto-last-workspace");
    await authFetch(`${API_BASE}/auth/logout`, { method: "POST" });
    setUser(null);
    setWorkspaces([]);
    window.location.href = "/";
  };

  return (
    <AuthContext.Provider value={{
      user, workspaces, loading,
      isAuthenticated: !!user,
      login, logout, updateWorkspace,
      refetchUser: fetchUser,
      refetchWorkspaces: fetchWorkspaces,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
