"use client";

import { MessageSquare, Plus } from "lucide-react";
import type { AskResponse } from "@/lib/api";

export interface HistoryEntry {
  id: string;
  question: string;
  response: AskResponse;
  timestamp: Date;
}

interface ChatHistoryProps {
  entries: HistoryEntry[];
  activeId: string | null;
  onSelect: (entry: HistoryEntry) => void;
  onNew: () => void;
}

export default function ChatHistory({
  entries,
  activeId,
  onSelect,
  onNew,
}: ChatHistoryProps) {
  return (
    <aside className="w-64 shrink-0 flex flex-col h-full border-r border-gray-200 bg-white">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
            MARS
          </span>
        </div>
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors"
        >
          <Plus size={14} />
          New research
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        {entries.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-8 px-4">
            Your research history will appear here
          </p>
        )}
        <ul className="space-y-0.5">
          {entries.map((entry) => (
            <li key={entry.id}>
              <button
                onClick={() => onSelect(entry)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors group flex items-start gap-2.5 ${
                  activeId === entry.id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <MessageSquare
                  size={13}
                  className={`shrink-0 mt-0.5 ${
                    activeId === entry.id ? "text-blue-500" : "text-gray-300 group-hover:text-gray-400"
                  }`}
                />
                <span className="line-clamp-2 leading-snug">{entry.question}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-100">
        <p className="text-xs text-gray-400 text-center">
          Multi-Agent Research Synthesizer
        </p>
      </div>
    </aside>
  );
}
