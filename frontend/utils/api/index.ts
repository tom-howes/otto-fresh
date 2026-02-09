// Mock API with local state management for testing
import { mockIssues, mockSprints, mockProject, mockComments, mockUsers } from '@/utils/mockData';

const mockDelay = () => new Promise(resolve => setTimeout(resolve, 300));

// Local state - stored in memory (will reset on page refresh)
let localIssues = [...mockIssues];
let localSprints = [...mockSprints];
let localComments = [...mockComments];

export const api = {
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
      console.log('Mock updateBatchIssues called:', body);
      
      if (body.issues && Array.isArray(body.issues)) {
        body.issues.forEach((update: any) => {
          const index = localIssues.findIndex(i => i.id === update.id);
          if (index !== -1) {
            localIssues[index] = { ...localIssues[index], ...update };
          }
        });
      }
      
      return localIssues;
    },
    getIssueDetails: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      return localIssues.find(i => i.id === issueId) || null;
    },
    postIssue: async (body: any) => {
      await mockDelay();
      console.log('Mock postIssue called:', body);
      
      // Create proper Lexical JSON format for description
      const description = body.description ? JSON.stringify({
        root: {
          children: [
            {
              children: [{ detail: 0, format: 0, mode: "normal", style: "", text: body.description, type: "text", version: 1 }],
              direction: "ltr",
              format: "",
              indent: 0,
              type: "paragraph",
              version: 1,
            },
          ],
          direction: "ltr",
          format: "",
          indent: 0,
          type: "root",
          version: 1,
        },
      }) : null;
      
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
        assignee: body.assigneeId ? mockUsers.find(u => u.id === body.assigneeId) || null : null,
        reporter: mockUsers.find(u => u.id === (body.reporterId || "user-1")) || null,
        children: [],
      };
      
      localIssues.push(newIssue);
      return newIssue;
    },
    patchIssue: async (data: any) => {
      await mockDelay();
      console.log('Mock patchIssue called:', data);
      
      const { issueId, ...updates } = data;
      const index = localIssues.findIndex(i => i.id === issueId);
      
      if (index !== -1) {
        localIssues[index] = {
          ...localIssues[index],
          ...updates,
          updatedAt: new Date(),
        };
        return localIssues[index];
      }
      
      return null;
    },
    deleteIssue: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      console.log('Mock deleteIssue called:', issueId);
      
      const index = localIssues.findIndex(i => i.id === issueId);
      if (index !== -1) {
        const deletedIssue = localIssues[index];
        localIssues = localIssues.filter(i => i.id !== issueId);
        return deletedIssue;
      }
      
      return null;
    },
    addCommentToIssue: async (payload: any) => {
      await mockDelay();
      console.log('Mock addCommentToIssue called:', payload);
      
      const newComment = {
        id: `comment-${Date.now()}`,
        issueId: payload.issueId,
        authorId: payload.authorId || "user-1",
        content: payload.content,
        createdAt: new Date(),
        updatedAt: new Date(),
        isEdited: false,
        author: mockUsers.find(u => u.id === (payload.authorId || "user-1")) || null,
      };
      
      localComments.push(newComment);
      return newComment;
    },
    getIssueComments: async ({ issueId }: { issueId: string }) => {
      await mockDelay();
      return localComments.filter(c => c.issueId === issueId);
    },
    updateIssueComment: async (data: any) => {
      await mockDelay();
      console.log('Mock updateIssueComment called:', data);
      
      const index = localComments.findIndex(c => c.id === data.commentId);
      if (index !== -1) {
        localComments[index] = {
          ...localComments[index],
          content: data.content,
          updatedAt: new Date(),
          isEdited: true,
        };
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
        endDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000), // 2 weeks
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
      console.log('Mock patchSprint called:', data);
      
      const { sprintId, ...updates } = data;
      const index = localSprints.findIndex(s => s.id === sprintId);
      
      if (index !== -1) {
        localSprints[index] = {
          ...localSprints[index],
          ...updates,
          updatedAt: new Date(),
        };
        return localSprints[index];
      }
      
      return null;
    },
    deleteSprint: async ({ sprintId }: { sprintId: string }) => {
      await mockDelay();
      console.log('Mock deleteSprint called:', sprintId);
      
      const index = localSprints.findIndex(s => s.id === sprintId);
      if (index !== -1) {
        const deletedSprint = localSprints[index];
        localSprints = localSprints.filter(s => s.id !== sprintId);
        return deletedSprint;
      }
      
      return null;
    },
  },
};

// Helper to reset data (useful for testing)
export const resetMockData = () => {
  localIssues = [...mockIssues];
  localSprints = [...mockSprints];
  localComments = [...mockComments];
};