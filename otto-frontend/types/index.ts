export type IssueStatus = "TODO" | "IN_PROGRESS" | "DONE";
export type IssuePriority = "urgent" | "high" | "medium" | "low";
export type IssueType = "task" | "story" | "bug" | "epic";

export interface Issue {
  id: string;
  title: string;
  status: IssueStatus;
  type: IssueType;
  priority: IssuePriority;
  assignee: string;
  // Fields populated from real backend data (absent in mock data)
  section_id?: string;
  description?: string | null;
  assignee_id?: string | null;
  reporter_id?: string;
  position?: number;
  created_at?: string;
  updated_at?: string;
}

export interface StatusConfig {
  label: string;
  dot: string;
  badge: string;
}

export const STATUS_CONFIG: Record<IssueStatus, StatusConfig> = {
  TODO:        { label: "To Do",       dot: "bg-gray-300",    badge: "bg-gray-100 text-gray-500"      },
  IN_PROGRESS: { label: "In Progress", dot: "bg-violet-400",  badge: "bg-violet-50 text-violet-600"   },
  DONE:        { label: "Done",        dot: "bg-emerald-400", badge: "bg-emerald-50 text-emerald-600" },
};

export const PRIORITY_COLORS: Record<IssuePriority, string> = {
  urgent: "bg-red-400",
  high:   "bg-orange-400",
  medium: "bg-yellow-300",
  low:    "bg-blue-400",
};

export const TYPE_ICONS: Record<IssueType, string> = {
  task:  "⬡",
  story: "⬢",
  bug:   "⬤",
  epic:  "⚡",
};

export const TYPE_COLORS: Record<IssueType, string> = {
  task:  "text-blue-400",
  story: "text-emerald-500",
  bug:   "text-red-400",
  epic:  "text-purple-400",
};