// Consolidated types file - no more imports from deleted API routes

export type IssueCountType = {
  TODO: number;
  IN_PROGRESS: number;
  DONE: number;
};

export type MenuOptionType = {
  label: string;
  id: string;
};

export type IssueType = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  status: "TODO" | "IN_PROGRESS" | "DONE";
  type: "TASK" | "BUG" | "STORY" | "EPIC" | "SUBTASK";
  priority: "LOW" | "MEDIUM" | "HIGH";
  sprintPosition: number;
  boardPosition: number;
  reporterId: string | null;
  assigneeId: string | null;
  parentId: string | null;
  sprintId: string | null;
  sprintColor: string | null;
  createdAt: Date;
  updatedAt: Date;
  sprintIsActive?: boolean;
  parent: IssueType | null;
  assignee: {
    id: string;
    name: string | null;
    email: string;
    avatar: string | null;
  } | null;
  reporter: {
    id: string;
    name: string | null;
    email: string;
    avatar: string | null;
  } | null;
  children: IssueType[];
};

export type GetIssuesResponse = {
  issues: IssueType[];
};

export type GetIssueCommentsResponse = {
  comments: Array<{
    id: string;
    issueId: string;
    authorId: string | null;
    content: string | null;
    createdAt: Date;
    updatedAt: Date;
    isEdited: boolean;
    author: {
      id: string;
      name: string | null;
      avatar: string | null;
      email: string;
    } | null;
  }>;
};