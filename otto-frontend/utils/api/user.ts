import { apiFetch } from "./client";

export interface User {
  id: string;
  github_username: string;
  email: string | null;
  avatar_url: string;
  installation_id: string | null;
}

export interface UserUpdate {
  github_username?: string;
  email?: string;
  avatar_url?: string;
}

export const userApi = {
  getMe: () => apiFetch<User>("/users/me"),
  updateMe: (update: UserUpdate) =>
    apiFetch<User>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(update),
    }),
};
