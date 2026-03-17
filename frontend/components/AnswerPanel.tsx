"use client";

import ReactMarkdown from "react-markdown";
import type { AskResponse } from "@/lib/api";

const CONFIDENCE_STYLES = {
  High: "badge-high",
  Medium: "badge-medium",
  Low: "badge-low",
};

export default function AnswerPanel({ response }: { response: AskResponse }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-4">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
          Answer
        </h2>
        <span className={CONFIDENCE_STYLES[response.confidence]}>
          {response.confidence} confidence
        </span>
      </div>

      <div className="prose max-w-none text-gray-800 text-sm leading-relaxed">
        <ReactMarkdown
          components={{
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {children}
              </a>
            ),
            code: ({ children }) => (
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">
                {children}
              </code>
            ),
          }}
        >
          {response.answer}
        </ReactMarkdown>
      </div>
    </div>
  );
}
