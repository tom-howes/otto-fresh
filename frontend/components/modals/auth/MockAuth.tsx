"use client";
import React from "react";

// Mock authentication components - replace with real auth when integrating backend

export const SignIn = () => {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg bg-white p-8 shadow-lg">
      <h2 className="mb-4 text-2xl font-bold">Sign In</h2>
      <p className="mb-6 text-center text-gray-600">
        Authentication is mocked for UI development
      </p>
      <div className="w-full max-w-sm space-y-4">
        <input
          type="email"
          placeholder="Email"
          disabled
          className="w-full rounded-md border border-gray-300 px-3 py-2"
        />
        <input
          type="password"
          placeholder="Password"
          disabled
          className="w-full rounded-md border border-gray-300 px-3 py-2"
        />
        <button
          disabled
          className="w-full rounded-md bg-blue-600 px-4 py-2 text-white"
        >
          Sign In (Disabled)
        </button>
      </div>
    </div>
  );
};

export const SignInButton = ({ children }: { children?: React.ReactNode }) => {
  return (
    <button className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
      {children || "Sign In"}
    </button>
  );
};

export const UserButton = () => {
  return (
    <div className="flex items-center gap-2">
      <img
        src="https://i.pravatar.cc/150?img=1"
        alt="User"
        className="h-8 w-8 rounded-full"
      />
    </div>
  );
};

export function useUser() {
  return {
    user: {
      id: "mock-user-123",
      firstName: "John",
      lastName: "Doe",
      fullName: "John Doe",
      emailAddresses: [{ emailAddress: "john@example.com" }],
      imageUrl: "https://i.pravatar.cc/150?img=1",
    },
    isLoaded: true,
    isSignedIn: true,
  };
}