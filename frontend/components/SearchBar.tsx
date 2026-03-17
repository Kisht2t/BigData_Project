"use client";

import { useState, useRef, type KeyboardEvent } from "react";
import { ArrowUp, Loader2, Plus, X } from "lucide-react";
import { ingestSource } from "@/lib/api";

interface SearchBarProps {
  onSubmit: (question: string) => void;
  loading: boolean;
  onIngest?: (title: string) => void;
}

export default function SearchBar({ onSubmit, loading, onIngest }: SearchBarProps) {
  const [value, setValue] = useState("");
  const [ingestValue, setIngestValue] = useState("");
  const [showIngest, setShowIngest] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMsg, setIngestMsg] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSubmit() {
    const q = value.trim();
    if (!q || loading) return;
    setValue("");
    onSubmit(q);
  }

  async function handleIngest() {
    const v = ingestValue.trim();
    if (!v || ingesting) return;

    setIngesting(true);
    setIngestMsg(null);
    try {
      const isArxivId = /^\d{4}\.\d{4,5}$/.test(v);
      const result = await ingestSource(
        isArxivId ? { arxiv_id: v } : { url: v }
      );
      setIngestMsg(`Added ${result.chunks_added} chunks: ${result.title}`);
      setIngestValue("");
      onIngest?.(result.title);
    } catch (e: unknown) {
      setIngestMsg(`Failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="border-t border-gray-100 bg-white px-4 py-4">
      {showIngest && (
        <div className="mb-3 p-3 bg-gray-50 border border-gray-200 rounded-xl">
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={ingestValue}
              onChange={(e) => setIngestValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleIngest()}
              placeholder="Paste a URL or arXiv ID (e.g. 2310.06825)"
              className="flex-1 text-sm bg-white border border-gray-200 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleIngest}
              disabled={ingesting || !ingestValue.trim()}
              className="px-3 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {ingesting ? <Loader2 size={14} className="animate-spin" /> : "Add"}
            </button>
          </div>
          {ingestMsg && (
            <p className="text-xs text-gray-600 mt-2">{ingestMsg}</p>
          )}
        </div>
      )}

      <div className="flex items-end gap-2">
        <button
          onClick={() => setShowIngest((s) => !s)}
          className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors shrink-0"
          title={showIngest ? "Close ingest panel" : "Add a source"}
        >
          {showIngest ? <X size={16} /> : <Plus size={16} />}
        </button>

        <div className="flex-1 flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent focus-within:bg-white transition-all">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
            }}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Ask a tech or science question..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-gray-800 placeholder-gray-400 outline-none resize-none"
          />
          <button
            onClick={handleSubmit}
            disabled={!value.trim() || loading}
            className="shrink-0 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <ArrowUp size={14} />
            )}
          </button>
        </div>
      </div>

      <p className="text-xs text-gray-400 text-center mt-2">
        Press Enter to search. Shift+Enter for new line.
      </p>
    </div>
  );
}
