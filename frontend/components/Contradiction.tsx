"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp } from "lucide-react";
import type { Contradiction as ContradictionType } from "@/lib/api";

const SOURCE_LABELS: Record<string, string> = {
  arxiv: "arXiv",
  hackernews: "Hacker News",
  github: "GitHub",
};

export default function Contradiction({
  contradictions,
}: {
  contradictions: ContradictionType[];
}) {
  const [expanded, setExpanded] = useState(false);

  if (!contradictions.length) return null;

  return (
    <div className="border border-amber-200 bg-amber-50 rounded-xl overflow-hidden mt-4">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-amber-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle size={15} className="text-amber-600 shrink-0" />
          <span className="text-sm font-medium text-amber-800">
            {contradictions.length === 1
              ? "Sources disagree on 1 claim"
              : `Sources disagree on ${contradictions.length} claims`}
          </span>
        </div>
        {expanded ? (
          <ChevronUp size={15} className="text-amber-500" />
        ) : (
          <ChevronDown size={15} className="text-amber-500" />
        )}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-amber-200">
          {contradictions.map((c, i) => (
            <div key={i} className="mt-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-lg border border-amber-200 p-3">
                  <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
                    {SOURCE_LABELS[c.source_a] ?? c.source_a}
                  </span>
                  <p className="text-sm text-gray-700 mt-1">{c.claim_a}</p>
                </div>
                <div className="bg-white rounded-lg border border-amber-200 p-3">
                  <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
                    {SOURCE_LABELS[c.source_b] ?? c.source_b}
                  </span>
                  <p className="text-sm text-gray-700 mt-1">{c.claim_b}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
