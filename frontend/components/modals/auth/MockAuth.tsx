"use client";
import React from "react";
import { useAuth, useUser as useAuthUser } from "@/context/use-auth-context";
import { FaGithub } from "react-icons/fa";

// Real authentication components using FastAPI backend

export const SignIn = () => {
  const { login, isLoading } = useAuth();

  return (
    <div className="flex flex-col items-center justify-center rounded-lg bg-white p-8 shadow-lg">
      <h2 className="mb-4 text-2xl font-bold">Sign In</h2>
      <p className="mb-6 text-center text-gray-600">
        Sign in with your GitHub account to continue
      </p>
      <button
        onClick={login}
        disabled={isLoading}
        className="flex w-full max-w-sm items-center justify-center gap-2 rounded-md bg-gray-900 px-4 py-3 text-white hover:bg-gray-800 disabled:opacity-50"
      >
        <FaGithub className="text-xl" />
        <span>Continue with GitHub</span>
      </button>
    </div>
  );
};

export const SignInButton = ({ children }: { children?: React.ReactNode }) => {
  const { login, isLoading } = useAuth();

  return (
    <button
      onClick={login}
      disabled={isLoading}
      className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
    >
      <FaGithub />
      {children || "Sign In with GitHub"}
    </button>
  );
};

export const UserButton = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="relative group">
      <button className="flex items-center gap-2">
        <img
          src={user.avatar_url}
          alt={user.github_username}
          className="h-8 w-8 rounded-full"
        />
      </button>
      {/* Dropdown menu */}
      <div className="absolute right-0 top-full mt-1 hidden w-48 rounded-md border bg-white py-1 shadow-lg group-hover:block">
        <div className="border-b px-4 py-2">
          <p className="text-sm font-medium">{user.github_username}</p>
          <p className="text-xs text-gray-500">{user.email}</p>
        </div>
        <button
          onClick={logout}
          className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100"
        >
          Sign out
        </button>
      </div>
    </div>
  );
};

// Re-export useUser for backward compatibility
export { useAuthUser as useUser };