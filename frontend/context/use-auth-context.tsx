"use client";
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

// Types matching your FastAPI backend models
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
  repo_owner: string;
  repo_name: string;
  repo_full_name: string;
  repo_default_branch: string;
  member_ids: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
};

type AuthContextProps = {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  workspaces: Workspace[];
  login: () => void;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
  refetchWorkspaces: () => Promise<void>;
};

const AuthContext = createContext<AuthContextProps>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
  workspaces: [],
  login: () => {},
  logout: async () => {},
  refetchUser: async () => {},
  refetchWorkspaces: async () => {},
});

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://backend-service-484671782718.us-east1.run.app";

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        credentials: "include", // Important: sends cookies
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        return userData;
      } else {
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error("Failed to fetch user:", error);
      setUser(null);
      return null;
    }
  }, []);

  const fetchWorkspaces = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/users/me/workspaces`, {
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        setWorkspaces(data);
        return data;
      } else {
        setWorkspaces([]);
        return [];
      }
    } catch (error) {
      console.error("Failed to fetch workspaces:", error);
      setWorkspaces([]);
      return [];
    }
  }, []);

  // Initial auth check on mount
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      const userData = await fetchUser();
      if (userData) {
        await fetchWorkspaces();
      }
      setIsLoading(false);
    };
    initAuth();
  }, [fetchUser, fetchWorkspaces]);

  const login = () => {
    // Redirect to FastAPI GitHub OAuth endpoint
    window.location.href = `${API_BASE_URL}/auth/login`;
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      setUser(null);
      setWorkspaces([]);
      // Optionally redirect to home
      window.location.href = "/";
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        workspaces,
        login,
        logout,
        refetchUser: fetchUser,
        refetchWorkspaces: fetchWorkspaces,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

// Backward-compatible hook for existing code
export const useUser = () => {
  const { user, isLoading, isAuthenticated } = useAuth();
  
  return {
    user: user ? {
      id: user.id,
      firstName: user.github_username,
      lastName: "",
      fullName: user.github_username,
      emailAddresses: user.email ? [{ emailAddress: user.email }] : [],
      imageUrl: user.avatar_url,
    } : null,
    isLoaded: !isLoading,
    isSignedIn: isAuthenticated,
  };
};