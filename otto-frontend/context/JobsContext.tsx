"use client";
import { createContext, useContext, useState } from "react";

export type JobType = "qa" | "search" | "code" | "docs";

export type Job = {
  id: string;
  issueId: string;
  issueTitle: string;
  status: "running" | "done" | "error";
  type: JobType;
  question: string;
  answer: string;
  // Store results for each type so they survive navigation
  searchResults?: { file_path: string; content: string; lines: string; language: string }[];
  codeResult?: unknown;
  docsResult?: string;
};

type JobsContextType = {
  jobs: Job[];
  startJob: (issueId: string, issueTitle: string, question: string, type: JobType) => string;
  appendChunk: (id: string, chunk: string) => void;
  finishJob: (id: string, status: "done" | "error", result?: Partial<Job>) => void;
  getJob: (issueId: string, type: JobType) => Job | undefined;
};

const JobsContext = createContext<JobsContextType>(null!);

export function JobsProvider({ children }: { children: React.ReactNode }) {
  const [jobs, setJobs] = useState<Job[]>([]);

  const startJob = (issueId: string, issueTitle: string, question: string, type: JobType) => {
    const id = `${issueId}-${type}`;
    setJobs(prev => [
      ...prev.filter(j => !(j.issueId === issueId && j.type === type)),
      { id, issueId, issueTitle, status: "running", type, question, answer: "" }
    ]);
    return id;
  };

  const appendChunk = (id: string, chunk: string) => {
    setJobs(prev => prev.map(j => j.id === id ? { ...j, answer: j.answer + chunk } : j));
  };

  const finishJob = (id: string, status: "done" | "error", result?: Partial<Job>) => {
    setJobs(prev => prev.map(j => 
      j.id === id ? { ...j, status, ...result } : j
    ));
  };

  const getJob = (issueId: string, type: JobType) => 
    jobs.find(j => j.issueId === issueId && j.type === type);

  return (
    <JobsContext.Provider value={{ jobs, startJob, appendChunk, finishJob, getJob }}>
      {children}
    </JobsContext.Provider>
  );
}

export const useJobs = () => useContext(JobsContext);