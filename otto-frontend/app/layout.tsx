import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/context/AuthContext";
import { JobsProvider } from "@/context/JobsContext";

export const metadata: Metadata = {
  title: "Otto — AI-Powered Project Management",
  description: "Otto connects to your GitHub repositories and uses RAG to answer questions, generate docs, complete code, and edit files — all in plain English.",
  openGraph: {
    title: "Otto — AI-Powered Project Management",
    description: "Ask questions about your codebase, auto-generate docs, get intelligent code completions, and edit files with natural language. Built for software teams.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{if(localStorage.getItem('otto-theme')==='dark')document.documentElement.classList.add('dark')}catch(e){}` }} />
      </head>
      <body>
        <ThemeProvider>
          <AuthProvider>
            <JobsProvider>
              {children}
            </JobsProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}