const BASE_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL ?? "http://localhost:8000";

export type SourceType = "arxiv" | "hackernews" | "github";

export interface SourceAttribution {
  source: SourceType;
  title: string;
  url: string;
  contribution: string;
}

export interface Contradiction {
  claim_a: string;
  claim_b: string;
  source_a: SourceType;
  source_b: SourceType;
}

export interface AskResponse {
  answer: string;
  sources: SourceAttribution[];
  contradictions: Contradiction[];
  confidence: "High" | "Medium" | "Low";
  session_id: string;
}

export interface IngestResponse {
  status: string;
  chunks_added: number;
  title: string;
}

export async function askQuestion(
  question: string,
  sessionId: string,
  context?: string
): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, session_id: sessionId, context: context ?? null }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API error ${res.status}: ${error}`);
  }

  return res.json();
}

export async function ingestSource(
  payload: { url?: string; arxiv_id?: string }
): Promise<IngestResponse> {
  const res = await fetch(`${BASE_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Ingestion failed ${res.status}: ${error}`);
  }

  return res.json();
}

export interface HistoryItem {
  id: string;
  session_id: string;
  question: string;
  answer: string;
  sources: SourceAttribution[];
  contradictions: Contradiction[];
  confidence: "High" | "Medium" | "Low";
  timestamp: string;
}

export async function getHistory(sessionId: string): Promise<HistoryItem[]> {
  try {
    const res = await fetch(`${BASE_URL}/history/${sessionId}`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}
