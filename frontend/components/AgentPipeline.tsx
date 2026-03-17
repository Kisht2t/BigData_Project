"use client";

import { FileText, Flame, GitBranch, CheckCircle2, Circle, Loader2 } from "lucide-react";

export type AgentStatus = "idle" | "searching" | "done" | "failed";

export interface AgentState {
  arxiv: AgentStatus;
  hackernews: AgentStatus;
  github: AgentStatus;
}

const AGENTS = [
  {
    key: "arxiv" as const,
    label: "arXiv",
    icon: FileText,
    color: "text-blue-600",
    bg: "bg-blue-50 border-blue-200",
  },
  {
    key: "hackernews" as const,
    label: "Hacker News",
    icon: Flame,
    color: "text-orange-600",
    bg: "bg-orange-50 border-orange-200",
  },
  {
    key: "github" as const,
    label: "GitHub",
    icon: GitBranch,
    color: "text-gray-700",
    bg: "bg-gray-50 border-gray-200",
  },
];

function StatusIcon({ status }: { status: AgentStatus }) {
  if (status === "searching") {
    return <Loader2 size={14} className="animate-spin text-blue-500" />;
  }
  if (status === "done") {
    return <CheckCircle2 size={14} className="text-green-500" />;
  }
  if (status === "failed") {
    return <Circle size={14} className="text-red-400" />;
  }
  return <Circle size={14} className="text-gray-300" />;
}

function statusLabel(status: AgentStatus): string {
  if (status === "searching") return "Searching...";
  if (status === "done") return "Done";
  if (status === "failed") return "Failed";
  return "Waiting";
}

export default function AgentPipeline({ agents }: { agents: AgentState }) {
  const allIdle = Object.values(agents).every((s) => s === "idle");
  if (allIdle) return null;

  return (
    <div className="flex items-center gap-3 py-3 px-4 bg-white border border-gray-200 rounded-xl mb-4">
      <span className="text-xs font-medium text-gray-500 shrink-0">Agents</span>
      <div className="flex items-center gap-2 flex-wrap">
        {AGENTS.map((agent) => {
          const status = agents[agent.key];
          const Icon = agent.icon;
          return (
            <div
              key={agent.key}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium transition-all duration-300 ${agent.bg}`}
            >
              <Icon size={12} className={agent.color} />
              <span className={agent.color}>{agent.label}</span>
              <StatusIcon status={status} />
              <span className="text-gray-400">{statusLabel(status)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
