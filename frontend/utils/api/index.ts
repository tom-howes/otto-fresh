// API client connecting to FastAPI backend
import { apiClient } from "./client";

// Types
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
  name: string;
  repo_full_name: string;
  member_ids: string[];
};

export type GitHubRepo = {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  description: string | null;
  default_branch: string;
  html_url: string;
};

// Auth API
export const authApi = {
  login: () => {
    window.location.href = `${apiClient.defaults.baseURL}/auth/login`;
  },
  logout: async () => {
    const { data } = await apiClient.post("/auth/logout");
    return data;
  },
};

// User API
export const userApi = {
  getMe: async (): Promise<User> => {
    const { data } = await apiClient.get("/users/me");
    return data;
  },
  updateMe: async (updateData: Partial<User>): Promise<User> => {
    const { data } = await apiClient.patch("/users/me", updateData);
    return data;
  },
  getWorkspaces: async (): Promise<Workspace[]> => {
    const { data } = await apiClient.get("/users/me/workspaces");
    return data;
  },
};

// GitHub API
export const githubApi = {
  getRepos: async (): Promise<GitHubRepo[]> => {
    const { data } = await apiClient.get("/github/repos");
    return data;
  },
  installApp: () => {
    window.location.href = `${apiClient.defaults.baseURL}/github/install`;
  },
};

// RAG API
export const ragApi = {
  ingestRepo: async (repoFullName: string, branch?: string) => {
    const { data } = await apiClient.post("/rag/repos/ingest", {
      repo_full_name: repoFullName,
      branch,
    });
    return data;
  },
  askQuestion: async (repoFullName: string, question: string) => {
    const { data } = await apiClient.post("/rag/ask", {
      repo_full_name: repoFullName,
      question,
    });
    return data;
  },
  generateDocs: async (repoFullName: string, target: string, docType = "api") => {
    const { data } = await apiClient.post("/rag/docs/generate", {
      repo_full_name: repoFullName,
      target,
      doc_type: docType,
    });
    return data;
  },
  getRepoStatus: async (owner: string, repo: string) => {
    const { data } = await apiClient.get(`/rag/repos/${owner}/${repo}/status`);
    return data;
  },
};

// ============================================================
// MOCK DATA FOR UI (until backend task routes are implemented)
// ============================================================
import { mockIssues, mockSprints, mockProject, mockComments, mockUsers } from "@/utils/mockData";

const mockDelay = () => new Promise((resolve) => setTimeout(resolve, 300));

let localIssues = [...mockIssues];
let localSprints = [...mockSprints];
let localComments = [...mockComments];

// Combined API export (real + mock)
export const api = {
  // Real APIs
  auth: authApi,
  user: userApi,
  github: githubApi,
  rag: ragApi,

  // Mock APIs (until backend implements these)
  project: {
    getProject: async () => {
      await mockDelay();
      return mockProject;
    },
    getMembers: async () => {
      await mockDelay();
      return mockUsers;
    },
  },
  issues: {
    getIssues: async () => {
      await mockDelay();
      return localIssues;
    },
    updateBatchIssues: async (body: any) => {
      await mockDelay();
      if (body.issues && Array.isArray(body.issues)) {
        body.issues.forEach((update: any) => {
          const index = localIssues.findIndex((i) => i.id === update.id);
          if (index !== -1) {
            localIssues[index] = { ...localIssues[index], ...update };
          }
        });
      }
      return localIssues;
    },
    getIssueDetails: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      return localIssues.find((i) => i.id === issueId) || null;
    },
    postIssue: async (body: any) => {
      await mockDelay();
      const description = body.description
        ? JSON.stringify({
            root: {
              children: [
                {
                  children: [{ detail: 0, format: 0, mode: "normal", style: "", text: body.description, type: "text", version: 1 }],
                  direction: "ltr", format: "", indent: 0, type: "paragraph", version: 1,
                },
              ],
              direction: "ltr", format: "", indent: 0, type: "root", version: 1,
            },
          })
        : null;

      const newIssue = {
        id: `issue-${Date.now()}`,
        key: `SAMP-${localIssues.length + 1}`,
        name: body.name || "New Issue",
        description,
        status: "TODO",
        type: body.type || "TASK",
        priority: body.priority || "MEDIUM",
        sprintPosition: localIssues.length,
        boardPosition: localIssues.length,
        reporterId: body.reporterId || "user-1",
        assigneeId: body.assigneeId || null,
        parentId: body.parentId || null,
        sprintId: body.sprintId || null,
        sprintColor: body.sprintId ? "#4CAF50" : null,
        createdAt: new Date(),
        updatedAt: new Date(),
        sprintIsActive: !!body.sprintId,
        parent: null,
        assignee: body.assigneeId ? mockUsers.find((u) => u.id === body.assigneeId) || null : null,
        reporter: mockUsers.find((u) => u.id === (body.reporterId || "user-1")) || null,
        children: [],
      };

      localIssues.push(newIssue);
      return newIssue;
    },
    patchIssue: async (data: any) => {
      await mockDelay();
      const { issueId, ...updates } = data;
      const index = localIssues.findIndex((i) => i.id === issueId);
      if (index !== -1) {
        localIssues[index] = { ...localIssues[index], ...updates, updatedAt: new Date() };
        return localIssues[index];
      }
      return null;
    },
    deleteIssue: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      const index = localIssues.findIndex((i) => i.id === issueId);
      if (index !== -1) {
        const deleted = localIssues[index];
        localIssues = localIssues.filter((i) => i.id !== issueId);
        return deleted;
      }
      return null;
    },
    addCommentToIssue: async (payload: any) => {
      await mockDelay();
      const newComment = {
        id: `comment-${Date.now()}`,
        issueId: payload.issueId,
        authorId: payload.authorId || "user-1",
        content: payload.content,
        createdAt: new Date(),
        updatedAt: new Date(),
        isEdited: false,
        author: mockUsers.find((u) => u.id === (payload.authorId || "user-1")) || null,
      };
      localComments.push(newComment);
      return newComment;
    },
    getIssueComments: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      return localComments.filter((c) => c.issueId === issueId);
    },
    updateIssueComment: async (data: any) => {
      await mockDelay();
      const index = localComments.findIndex((c) => c.id === data.commentId);
      if (index !== -1) {
        localComments[index] = { ...localComments[index], content: data.content, updatedAt: new Date(), isEdited: true };
        return localComments[index];
      }
      return null;
    },
  },
  sprints: {
    postSprint: async () => {
      await mockDelay();
      const newSprint = {
        id: `sprint-${Date.now()}`,
        name: `Sprint ${localSprints.length + 1}`,
        startDate: new Date(),
        endDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000),
        status: "PLANNED",
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      localSprints.push(newSprint);
      return newSprint;
    },
    getSprints: async () => {
      await mockDelay();
      return localSprints;
    },
    patchSprint: async (data: any) => {
      await mockDelay();
      const { sprintId, ...updates } = data;
      const index = localSprints.findIndex((s) => s.id === sprintId);
      if (index !== -1) {
        localSprints[index] = { ...localSprints[index], ...updates, updatedAt: new Date() };
        return localSprints[index];
      }
      return null;
    },
    deleteSprint: async ({ sprintId }: { sprintId: string }) => {
      await mockDelay();
      const index = localSprints.findIndex((s) => s.id === sprintId);
      if (index !== -1) {
        const deleted = localSprints[index];
        localSprints = localSprints.filter((s) => s.id !== sprintId);
        return deleted;
      }
      return null;
    },
  },
};

// Reset mock data helper
export const resetMockData = () => {
  localIssues = [...mockIssues];
  localSprints = [...mockSprints];
  localComments = [...mockComments];
};