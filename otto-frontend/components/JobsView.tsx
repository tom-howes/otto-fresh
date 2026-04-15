// components/JobsView.tsx
"use client";
import { useJobs, Job, JobType } from "@/context/JobsContext";

const TYPE_LABEL: Record<JobType, string> = {
  qa: "Q&A",
  search: "Search",
  code: "Code",
  docs: "Docs",
};

const STATUS_STYLES = {
  running: "bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400",
  done: "bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400",
  error: "bg-red-50 dark:bg-red-900/30 text-red-400",
};

export default function JobsView({ onSelectIssueById }: { onSelectIssueById: (issueId: string) => void }) {
  const { jobs } = useJobs();

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-4">All Jobs</h2>
      {jobs.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500">No jobs have been run yet.</p>
      ) : (
        <div className="space-y-2">
          {[...jobs].reverse().map(job => (
            <button
              key={job.id}
              onClick={() => onSelectIssueById(job.issueId)}
              className="flex w-full items-center gap-3 rounded-xl border border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3 text-left hover:border-violet-200 dark:hover:border-violet-700 transition-colors"
            >
              <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                job.status === "running" ? "bg-violet-500 animate-pulse" :
                job.status === "done" ? "bg-green-500" : "bg-red-400"
              }`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{job.issueTitle}</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{job.question}</p>
              </div>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[job.status]}`}>
                {job.status}
              </span>
              <span className="shrink-0 rounded-full bg-gray-100 dark:bg-gray-800 px-2 py-0.5 text-xs text-gray-400 dark:text-gray-500">
                {TYPE_LABEL[job.type]}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}