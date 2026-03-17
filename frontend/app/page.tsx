"use client";

import { useState, useEffect } from "react";
import ChatHistory, { type HistoryEntry } from "@/components/ChatHistory";
import AgentPipeline, { type AgentState } from "@/components/AgentPipeline";
import AnswerPanel from "@/components/AnswerPanel";
import SourceCards from "@/components/SourceCards";
import Contradiction from "@/components/Contradiction";
import SearchBar from "@/components/SearchBar";
import { askQuestion, getHistory, type AskResponse } from "@/lib/api";

const IDLE_AGENTS: AgentState = {
  arxiv: "idle",
  hackernews: "idle",
  github: "idle",
};

const SEARCHING_AGENTS: AgentState = {
  arxiv: "searching",
  hackernews: "searching",
  github: "searching",
};

function generateUUID(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  // Fallback for HTTP (non-secure) contexts
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export default function Page() {
  const [sessionId] = useState<string>(() => {
    if (typeof window === "undefined") return generateUUID();
    const stored = localStorage.getItem("mars_session_id");
    if (stored) return stored;
    const newId = generateUUID();
    localStorage.setItem("mars_session_id", newId);
    return newId;
  });
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [activeEntry, setActiveEntry] = useState<HistoryEntry | null>(null);
  const [agents, setAgents] = useState<AgentState>(IDLE_AGENTS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastIngested, setLastIngested] = useState<string | null>(null);

  // Load history from DynamoDB on mount
  useEffect(() => {
    getHistory(sessionId).then((items) => {
      if (items.length === 0) return;
      const entries: HistoryEntry[] = items.map((item) => ({
        id: item.id,
        question: item.question,
        response: {
          answer: item.answer,
          sources: item.sources,
          contradictions: item.contradictions,
          confidence: item.confidence,
          session_id: item.session_id,
        },
        timestamp: new Date(item.timestamp),
      }));
      setHistory(entries);
      setActiveEntry(entries[0]);
    });
  }, [sessionId]);

  async function handleQuestion(question: string) {
    setLoading(true);
    setError(null);
    setActiveEntry(null);
    setAgents(SEARCHING_AGENTS);

    // Capture and clear context before the async call
    const context = lastIngested ?? undefined;
    setLastIngested(null);

    try {
      const response: AskResponse = await askQuestion(question, sessionId, context);

      setAgents({ arxiv: "done", hackernews: "done", github: "done" });

      const entry: HistoryEntry = {
        id: crypto.randomUUID(),
        question,
        response,
        timestamp: new Date(),
      };

      setHistory((h) => [entry, ...h]);
      setActiveEntry(entry);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong. Is the API running?");
      setAgents({ arxiv: "failed", hackernews: "failed", github: "failed" });
    } finally {
      setLoading(false);
    }
  }

  function handleNew() {
    const newId = crypto.randomUUID();
    localStorage.setItem("mars_session_id", newId);
    // Force page reload to reinitialize sessionId state from localStorage
    window.location.reload();
  }

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <ChatHistory
        entries={history}
        activeId={activeEntry?.id ?? null}
        onSelect={setActiveEntry}
        onNew={handleNew}
      />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="px-6 py-4 border-b border-gray-100 bg-white shrink-0">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-base font-semibold text-gray-900">
              Research Synthesizer
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              arXiv · Hacker News · GitHub — cross-validated answers with source attribution
            </p>
          </div>
        </header>

        {/* Main content */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-6">

            {/* Empty state */}
            {!activeEntry && !loading && !error && (
              <div className="flex flex-col items-center justify-center h-full py-24 text-center">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="1.5">
                    <circle cx="11" cy="11" r="8" />
                    <path d="m21 21-4.35-4.35" />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-gray-800 mb-2">
                  Ask a research question
                </h2>
                <p className="text-sm text-gray-500 max-w-sm">
                  Three specialized agents will search academic papers, tech news, and open-source projects to synthesize a cross-validated answer.
                </p>
                <div className="mt-6 grid grid-cols-1 gap-2 w-full max-w-sm">
                  {[
                    "How does RAG differ from fine-tuning for LLMs?",
                    "What is the current state of Rust async runtimes?",
                    "How are vector databases different from traditional search?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => handleQuestion(q)}
                      className="text-left text-sm text-gray-600 hover:text-blue-600 hover:bg-blue-50 border border-gray-200 hover:border-blue-200 px-4 py-2.5 rounded-xl transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Agent pipeline status */}
            <AgentPipeline agents={agents} />

            {/* Error */}
            {error && (
              <div className="card px-4 py-3 border-red-200 bg-red-50 text-sm text-red-700">
                {error}
              </div>
            )}

            {/* Loading skeleton */}
            {loading && !activeEntry && (
              <div className="card p-5 animate-pulse space-y-3">
                <div className="h-4 bg-gray-100 rounded w-3/4" />
                <div className="h-4 bg-gray-100 rounded w-full" />
                <div className="h-4 bg-gray-100 rounded w-5/6" />
                <div className="h-4 bg-gray-100 rounded w-2/3" />
              </div>
            )}

            {/* Results */}
            {activeEntry && (
              <>
                <div className="mb-4">
                  <p className="text-xs text-gray-400 mb-1">Question</p>
                  <p className="text-base font-semibold text-gray-900">
                    {activeEntry.question}
                  </p>
                </div>

                <AnswerPanel response={activeEntry.response} />

                <Contradiction contradictions={activeEntry.response.contradictions} />

                <SourceCards sources={activeEntry.response.sources} />
              </>
            )}
          </div>
        </div>

        {/* Search bar pinned to bottom */}
        <div className="shrink-0 max-w-3xl mx-auto w-full">
          {lastIngested && (
            <div className="mx-4 mb-1 flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-700">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                <polyline points="13 2 13 9 20 9"/>
              </svg>
              <span>Context: <strong>{lastIngested}</strong></span>
              <button onClick={() => setLastIngested(null)} className="ml-auto text-blue-400 hover:text-blue-600">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          )}
          <SearchBar onSubmit={handleQuestion} loading={loading} onIngest={setLastIngested} />
        </div>
      </main>
    </div>
  );
}
