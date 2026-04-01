import { apiFetch } from "./client";

export interface GitHubRepo {
  full_name: string;
  name: string;
  owner: string;
  description: string | null;
  private: boolean;
  default_branch: string;
  language: string | null;
  url: string;
}

export const githubApi = {
  getRepos: () => apiFetch<GitHubRepo[]>("/github/repos"),
};
