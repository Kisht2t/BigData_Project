"use client";

import { FileText, Flame, GitBranch, ExternalLink } from "lucide-react";
import type { SourceAttribution, SourceType } from "@/lib/api";

const SOURCE_CONFIG: Record<
  SourceType,
  { label: string; icon: typeof FileText; badge: string; border: string }
> = {
  arxiv: {
    label: "arXiv",
    icon: FileText,
    badge: "badge-arxiv",
    border: "border-l-blue-400",
  },
  hackernews: {
    label: "Hacker News",
    icon: Flame,
    badge: "badge-hackernews",
    border: "border-l-orange-400",
  },
  github: {
    label: "GitHub",
    icon: GitBranch,
    badge: "badge-github",
    border: "border-l-gray-400",
  },
};

function SourceCard({ source }: { source: SourceAttribution }) {
  const config = SOURCE_CONFIG[source.source];
  const Icon = config.icon;

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`block card px-4 py-3 border-l-4 ${config.border} hover:shadow-md transition-shadow group`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={config.badge}>
              <Icon size={10} />
              {config.label}
            </span>
          </div>
          <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600 transition-colors">
            {source.title}
          </p>
          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
            {source.contribution}
          </p>
        </div>
        <ExternalLink
          size={14}
          className="text-gray-300 group-hover:text-blue-400 shrink-0 mt-1 transition-colors"
        />
      </div>
    </a>
  );
}

export default function SourceCards({ sources }: { sources: SourceAttribution[] }) {
  if (!sources.length) return null;

  const grouped = sources.reduce<Record<SourceType, SourceAttribution[]>>(
    (acc, s) => {
      (acc[s.source] ??= []).push(s);
      return acc;
    },
    {} as Record<SourceType, SourceAttribution[]>
  );

  const order: SourceType[] = ["arxiv", "hackernews", "github"];

  return (
    <div className="mt-4">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Sources
      </h2>
      <div className="space-y-2">
        {order
          .filter((src) => grouped[src]?.length)
          .flatMap((src) => grouped[src].map((s, i) => (
            <SourceCard key={`${src}-${i}`} source={s} />
          )))}
      </div>
    </div>
  );
}
