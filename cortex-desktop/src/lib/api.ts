/**
 * Unified API Client for Cortex Desktop
 */
import { appState } from "$lib/state.svelte";

const getCortexApiBase = () => appState.apiUrl;
const getRagApiBase = () => appState.apiUrl;

export interface ProcessDocumentRequest {
  file: File;
  chunkStrategy?: "recursive" | "sliding" | "simple";
  chunkSize?: number;
}

export interface ProcessDocumentResponse {
  filename: string;
  insights: any;
  processing_time: number;
}

export async function processDocument(req: ProcessDocumentRequest): Promise<ProcessDocumentResponse> {
  const formData = new FormData();
  formData.append("file", req.file);

  const url = new URL(`${getCortexApiBase()}/process`);
  if (req.chunkStrategy) url.searchParams.set("chunk_strategy", req.chunkStrategy);
  if (req.chunkSize) url.searchParams.set("chunk_size", req.chunkSize.toString());

  const response = await fetch(url.toString(), { method: "POST", body: formData });
  if (!response.ok) throw new Error(`Processing failed: ${response.statusText}`);
  return response.json();
}

export async function checkHealth(): Promise<{ cortex: boolean; rag: boolean }> {
  try {
    const [cortexRes, ragRes] = await Promise.all([
      fetch(`${getCortexApiBase()}/health`),
      fetch(`${getRagApiBase()}/health`),
    ]);
    return { cortex: cortexRes.ok, rag: ragRes.ok };
  } catch {
    return { cortex: false, rag: false };
  }
}

// Vector Search
export interface VectorSearchRequest {
  query: string;
  topK?: number;
}

export interface VectorSearchResult {
  text: string;
  score: number;
  metadata?: any;
}

export interface VectorSearchResponse {
  results: VectorSearchResult[];
  query: string;
  total_results: number;
}

export async function searchVectors(req: VectorSearchRequest): Promise<VectorSearchResponse> {
  const response = await fetch(`${getCortexApiBase()}/vectors/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: req.query,
      top_k: req.topK || 5,
    }),
  });

  if (!response.ok) throw new Error(`Vector search failed: ${response.statusText}`);
  return response.json();
}

export async function indexDocument(file: File): Promise<{ status: string; chunks_indexed: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getCortexApiBase()}/vectors/index`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(`Indexing failed: ${response.statusText}`);
  return response.json();
}
