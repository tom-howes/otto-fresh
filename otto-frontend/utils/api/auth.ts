import { apiFetch } from "./client";

const API_URL = "/api";

export const authApi = {
  loginUrl: () => `${API_URL}/auth/login`,
  logout: () => apiFetch("/auth/logout", { method: "POST" }),
};
