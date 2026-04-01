import { apiFetch } from "./client";
import { GitHubRepo } from "./types";

export const githubApi = {
  getRepos: () => apiFetch<GitHubRepo[]>("/github/repos"),
};
