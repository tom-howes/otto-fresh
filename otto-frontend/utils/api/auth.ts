import { apiFetch } from "./client";

export const authApi = {
  loginUrl: () => "/api/auth/login",

  logout: () =>
    apiFetch("/auth/logout", { method: "POST" }),
};
