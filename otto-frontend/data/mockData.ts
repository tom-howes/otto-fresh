import { Issue } from "@/types";

export const MOCK_ISSUES: Issue[] = [
  { id: "SAMP-1", title: "Set up project repository",   status: "DONE",        type: "task",  priority: "medium", assignee: "S" },
  { id: "SAMP-2", title: "Design database schema",      status: "IN_PROGRESS", type: "story", priority: "high",   assignee: "M" },
  { id: "SAMP-3", title: "Build authentication system", status: "TODO",        type: "bug",   priority: "urgent", assignee: "P" },
  { id: "SAMP-4", title: "Fix navigation bug",          status: "TODO",        type: "bug",   priority: "high",   assignee: "A" },
  { id: "SAMP-5", title: "Add dark mode support",       status: "IN_PROGRESS", type: "task",  priority: "medium", assignee: "S" },
];

export const MOCK_SPRINTS = [
  { key: "sprint1", label: "Sprint 1", dates: "Dec 31 – Jan 13", issueIds: ["SAMP-1", "SAMP-2", "SAMP-3"], active: true  },
  { key: "sprint2", label: "Sprint 2", dates: "Jan 14 – Jan 27", issueIds: [],                              active: false },
  { key: "backlog", label: "Backlog",  dates: null,               issueIds: ["SAMP-4", "SAMP-5"],           active: false },
];