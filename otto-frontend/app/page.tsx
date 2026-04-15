"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/components/ThemeProvider";

/* ─── Data ─────────────────────────────────────────────────────────────── */

const features = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
      </svg>
    ),
    tag: "Ask anything",
    title: "Codebase Q&A",
    description: "Ask questions about your code in plain English and get accurate, sourced answers instantly. No more digging through stale docs or pinging teammates.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
    ),
    tag: "Always up to date",
    title: "Docs Generator",
    description: "Auto-generate API references, READMEs, and guides straight from your code. Otto keeps documentation in sync with every push. No manual effort required.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
      </svg>
    ),
    tag: "Context-aware",
    title: "Code Completion",
    description: "Suggestions that actually match your architecture. Otto learns your patterns, naming conventions, and stack so completions feel like they were written by a senior on your team.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
      </svg>
    ),
    tag: "One click to ship",
    title: "AI Code Editor",
    description: "Describe a change in plain English. Otto makes the edit and opens a pull request automatically. From idea to PR without touching the terminal.",
  },
];

const steps = [
  {
    number: "01",
    title: "Connect your repo",
    description: "Sign in with GitHub and install the Otto App on any repo, public or private. Done in under two minutes.",
  },
  {
    number: "02",
    title: "Otto learns your code",
    description: "Otto indexes your entire codebase and keeps it fresh on every push. No setup, no configuration.",
  },
  {
    number: "03",
    title: "Ask, generate, ship",
    description: "Query code, write docs, get completions, open PRs. All from one place, all in plain English.",
  },
];

const benefits = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
      </svg>
    ),
    title: "Instant answers",
    description: "No more Slack pings asking who owns what file. Otto knows your entire codebase and answers in seconds.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
      </svg>
    ),
    title: "Always in sync",
    description: "Webhooks update your embeddings on every push. Your team always queries the latest version of your code.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6">
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
      </svg>
    ),
    title: "Built for teams",
    description: "Shared workspaces, per-user tracking, and multi-repo support. Otto scales with your team from 2 to 200.",
  },
];

const faqs = [
  {
    q: "How does Otto understand my codebase?",
    a: "Otto uses Retrieval-Augmented Generation (RAG). When you connect a repo, it ingests your code, splits it into semantic chunks, and generates vector embeddings using Vertex AI. When you ask a question, Otto searches those embeddings and feeds the most relevant context to Gemini to generate an accurate, grounded answer.",
  },
  {
    q: "Does it work with private repositories?",
    a: "Yes. Otto authenticates via GitHub OAuth and a GitHub App installation, which gives it access to both public and private repos. Your code is indexed securely and is only accessible to members of your workspace.",
  },
  {
    q: "How do I get started?",
    a: "Click \"Get started free\", sign in with GitHub, install the Otto App on your repository, and Otto will begin indexing your code automatically. The whole process takes under two minutes.",
  },
  {
    q: "What happens when I push new code?",
    a: "Otto uses GitHub webhooks to detect pushes to your tracked branch. It automatically re-indexes only the changed files, so your embeddings stay fresh without any manual action.",
  },
];


/* ─── Component ─────────────────────────────────────────────────────────── */

export default function Home() {
  const { isAuthenticated, loading, login } = useAuth();
  const { theme, toggle } = useTheme();
  const router = useRouter();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace("/project/board");
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-[#0d0d0f]">
        <div className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-white dark:bg-[#0d0d0f] text-neutral-900 dark:text-neutral-100 antialiased">

      {/* ── Navbar ─────────────────────────────────────────────────────── */}
      <header className="fixed inset-x-0 top-0 z-50 border-b border-neutral-200/80 dark:border-white/[0.06] bg-white/90 dark:bg-[#0d0d0f]/90 backdrop-blur-lg">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Image src="/otto-logo.png" alt="Otto" width={72} height={36}
            className="h-8 w-auto dark:invert object-contain" priority />

          <div className="flex items-center gap-3">
            <button onClick={toggle} aria-label="Toggle theme"
              className="p-2 rounded-lg text-neutral-400 hover:text-neutral-700 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-white/[0.06] transition-colors">
              {theme === "dark" ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-4.5 h-4.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-4.5 h-4.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
                </svg>
              )}
            </button>
            <button onClick={login}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-sm font-semibold transition-colors">
              <GitHubIcon className="w-4 h-4" />
              Sign in
            </button>
          </div>
        </div>
      </header>

      <main>

        {/* ── Hero ───────────────────────────────────────────────────────── */}
        <section className="relative pt-36 pb-28 px-6 text-center overflow-hidden">
          <div className="pointer-events-none absolute inset-0 flex items-start justify-center" aria-hidden>
            <div className="w-[700px] h-[500px] rounded-full bg-violet-500/10 dark:bg-violet-600/[0.08] blur-[140px] mt-4" />
          </div>

          <div className="relative max-w-3xl mx-auto">
            <div className="flex justify-center mb-10">
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-violet-400/20 blur-2xl scale-150" aria-hidden />
                <Image src="/otto-logo.png" alt="Otto" width={80} height={80}
                  className="relative h-16 w-auto dark:invert object-contain" priority />
              </div>
            </div>

            <h1 className="text-5xl sm:text-[4.5rem] font-black tracking-tight leading-[1.08] mb-6 text-neutral-900 dark:text-white">
              Your team&apos;s AI
              <br />
              <span className="text-violet-500">project co-pilot</span>
            </h1>

            <p className="text-lg sm:text-xl text-neutral-500 dark:text-neutral-400 leading-relaxed mb-10 max-w-xl mx-auto">
              Otto plugs into your GitHub workflow and helps your team move faster: answering code questions, generating docs, and shipping changes without the usual friction.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button onClick={login}
                className="flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-sm transition-colors shadow-lg shadow-violet-500/20">
                <GitHubIcon className="w-4 h-4" />
                Get started free
              </button>
              <a href="#demo"
                className="flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl border border-neutral-200 dark:border-white/[0.1] text-neutral-600 dark:text-neutral-300 font-bold text-sm hover:bg-neutral-50 dark:hover:bg-white/[0.04] transition-colors">
                <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 text-violet-500">
                  <path fillRule="evenodd" d="M4.5 5.653c0-1.427 1.529-2.33 2.779-1.643l11.54 6.347c1.295.712 1.295 2.573 0 3.286L7.28 19.99c-1.25.687-2.779-.217-2.779-1.643V5.653Z" clipRule="evenodd" />
                </svg>
                Watch the demo
              </a>
            </div>
          </div>
        </section>


        {/* ── Features ───────────────────────────────────────────────────── */}
        <section className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06]">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-500 mb-4">Capabilities</p>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-neutral-900 dark:text-white mb-4">
                What Otto can do for your team
              </h2>
              <p className="text-neutral-500 dark:text-neutral-400 text-lg">
                Four AI tools, all powered by your real codebase, not generic training data.
              </p>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              {features.map((f) => (
                <div key={f.title}
                  className="group p-7 rounded-2xl border border-neutral-200 dark:border-white/[0.07] bg-neutral-50 dark:bg-white/[0.03] hover:border-violet-300 dark:hover:border-violet-500/40 hover:bg-white dark:hover:bg-white/[0.05] transition-all duration-200">
                  <div className="flex items-start gap-5">
                    <div className="shrink-0 w-10 h-10 rounded-xl bg-violet-100 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center mt-0.5 group-hover:bg-violet-200 dark:group-hover:bg-violet-500/20 transition-colors">
                      {f.icon}
                    </div>
                    <div>
                      <p className="text-[11px] font-bold uppercase tracking-widest text-violet-500 mb-1.5">{f.tag}</p>
                      <h3 className="text-base font-bold text-neutral-900 dark:text-white mb-2">{f.title}</h3>
                      <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">{f.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Why Otto ───────────────────────────────────────────────────── */}
        <section className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06] bg-neutral-50 dark:bg-white/[0.015]">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-500 mb-4">Why Otto</p>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-neutral-900 dark:text-white mb-4">
                Built for how teams actually work
              </h2>
              <p className="text-neutral-500 dark:text-neutral-400 text-lg">
                Otto isn&apos;t another chatbot. It&apos;s a workspace built around your code.
              </p>
            </div>

            <div className="grid sm:grid-cols-3 gap-5">
              {benefits.map((b) => (
                <div key={b.title}
                  className="p-8 rounded-2xl border border-neutral-200 dark:border-white/[0.07] bg-white dark:bg-white/[0.04] text-center">
                  <div className="w-12 h-12 rounded-2xl bg-violet-100 dark:bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center mx-auto mb-5">
                    {b.icon}
                  </div>
                  <h3 className="text-base font-bold text-neutral-900 dark:text-white mb-2">{b.title}</h3>
                  <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">{b.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Demo Video ─────────────────────────────────────────────────── */}
        <section id="demo" className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06]">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-500 mb-4">Demo</p>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-neutral-900 dark:text-white mb-4">
                See it in action
              </h2>
              <p className="text-neutral-500 dark:text-neutral-400 text-lg max-w-md mx-auto">
                Watch how Otto helps software teams move faster without the usual chaos.
              </p>
            </div>

            <div className="rounded-2xl overflow-hidden border border-neutral-200 dark:border-white/[0.08] shadow-2xl shadow-black/5 dark:shadow-black/50 aspect-video">
              <iframe src="https://www.youtube.com/embed/ICIZRLIUMQ4"
                className="w-full h-full" allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                title="Otto product demo" />
            </div>
          </div>
        </section>

        {/* ── How it works ───────────────────────────────────────────────── */}
        <section className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06] bg-neutral-50 dark:bg-white/[0.015]">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-500 mb-4">Setup</p>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-neutral-900 dark:text-white mb-4">
                Up and running in minutes
              </h2>
              <p className="text-neutral-500 dark:text-neutral-400 text-lg">
                No config files, no infra to manage. Just connect and go.
              </p>
            </div>

            <div className="grid sm:grid-cols-3 gap-5">
              {steps.map((s) => (
                <div key={s.number}
                  className="relative p-7 rounded-2xl border border-neutral-200 dark:border-white/[0.07] bg-white dark:bg-white/[0.04]">
                  <div className="text-4xl font-black text-violet-400/25 dark:text-violet-400/20 mb-5 leading-none tabular-nums">
                    {s.number}
                  </div>
                  <h3 className="text-base font-bold text-neutral-900 dark:text-white mb-2">{s.title}</h3>
                  <p className="text-neutral-500 dark:text-neutral-400 text-sm leading-relaxed">{s.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── GitHub callout ─────────────────────────────────────────────── */}
        <section className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06]">
          <div className="max-w-5xl mx-auto">
            <div className="rounded-2xl border border-neutral-200 dark:border-white/[0.08] bg-neutral-50 dark:bg-white/[0.03] p-10 sm:p-14 flex flex-col sm:flex-row items-center gap-8 sm:gap-12">
              <div className="shrink-0 w-14 h-14 rounded-xl bg-neutral-900 dark:bg-white flex items-center justify-center">
                <GitHubIcon className="w-7 h-7 text-white dark:text-neutral-900" />
              </div>
              <div className="flex-1 text-center sm:text-left">
                <h3 className="text-xl font-black text-neutral-900 dark:text-white mb-3">
                  Built natively on GitHub
                </h3>
                <ul className="space-y-1.5">
                  {[
                    "OAuth login and GitHub App installation",
                    "Webhook-driven automatic re-indexing on every push",
                    "AI code edits create pull requests automatically",
                    "Works with public and private repositories",
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-sm text-neutral-500 dark:text-neutral-400">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}
                        className="w-4 h-4 text-violet-500 shrink-0 mt-0.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <button onClick={login}
                className="shrink-0 flex items-center gap-2 px-6 py-3 rounded-xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-bold text-sm hover:bg-neutral-700 dark:hover:bg-neutral-100 transition-colors whitespace-nowrap">
                Connect a repo
              </button>
            </div>
          </div>
        </section>

        {/* ── FAQ ────────────────────────────────────────────────────────── */}
        <section className="py-24 px-6 border-t border-neutral-100 dark:border-white/[0.06] bg-neutral-50 dark:bg-white/[0.015]">
          <div className="max-w-3xl mx-auto">
            <div className="text-center mb-14">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-500 mb-4">FAQ</p>
              <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-neutral-900 dark:text-white mb-4">
                Common questions
              </h2>
            </div>

            <div className="space-y-3">
              {faqs.map((faq, i) => (
                <div key={i}
                  className="rounded-2xl border border-neutral-200 dark:border-white/[0.07] bg-white dark:bg-white/[0.04] overflow-hidden">
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left"
                  >
                    <span className="text-sm font-bold text-neutral-900 dark:text-white">{faq.q}</span>
                    <svg
                      viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
                      className={`w-4 h-4 shrink-0 text-neutral-400 transition-transform duration-200 ${openFaq === i ? "rotate-180" : ""}`}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="m19 9-7 7-7-7" />
                    </svg>
                  </button>
                  {openFaq === i && (
                    <div className="px-6 pb-5 text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed border-t border-neutral-100 dark:border-white/[0.06] pt-4">
                      {faq.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Final CTA ──────────────────────────────────────────────────── */}
        <section className="py-32 px-6 border-t border-neutral-100 dark:border-white/[0.06] text-center relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center" aria-hidden>
            <div className="w-[500px] h-[300px] rounded-full bg-violet-500/10 dark:bg-violet-600/[0.07] blur-[100px]" />
          </div>
          <div className="relative max-w-2xl mx-auto">
            <div className="flex justify-center mb-10">
              <Image src="/otto-logo.png" alt="Otto" width={56} height={56}
                className="h-12 w-auto dark:invert object-contain opacity-60" />
            </div>

            <h2 className="text-4xl sm:text-5xl font-black tracking-tight mb-5 text-neutral-900 dark:text-white">
              Ready to work smarter?
            </h2>
            <p className="text-lg text-neutral-500 dark:text-neutral-400 mb-10 leading-relaxed max-w-md mx-auto">
              Join teams using Otto to stay on top of their codebase, ship faster, and spend less time searching for answers.
            </p>

            <button onClick={login}
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-base transition-colors shadow-xl shadow-violet-500/20">
              <GitHubIcon className="w-5 h-5" />
              Continue with GitHub, it&apos;s free
            </button>
          </div>
        </section>

      </main>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-neutral-200 dark:border-white/[0.06] py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <Image src="/otto-logo.png" alt="Otto" width={56} height={24}
            className="h-6 w-auto dark:invert object-contain opacity-60" />
          <p className="text-sm text-neutral-400 dark:text-neutral-500">
            AI-powered project management for software teams
          </p>
          <p className="text-sm text-neutral-400 dark:text-neutral-500">
            Built on GitHub, Vertex AI and Gemini
          </p>
        </div>
      </footer>

    </div>
  );
}

/* ─── Icons ─────────────────────────────────────────────────────────────── */

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0 0 22 12.017C22 6.484 17.522 2 12 2Z" />
    </svg>
  );
}
