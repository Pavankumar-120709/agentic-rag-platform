import {
  DocumentRead,
  DocumentDetail,
  ConversationRead,
  ConversationDetail,
  ChatResponse,
  SystemMetrics,
  QueryExecutionRead,
  EvaluationRunRead,
} from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchMetrics(): Promise<SystemMetrics> {
  const res = await fetch(`${BASE_URL}/metrics`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch system metrics");
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentRead[]> {
  const res = await fetch(`${BASE_URL}/documents`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function fetchDocumentDetail(id: string): Promise<DocumentDetail> {
  const res = await fetch(`${BASE_URL}/documents/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch document detail");
  return res.json();
}

export async function uploadDocument(file: File): Promise<DocumentRead> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || "Failed to upload document");
  }
  return res.json();
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/documents/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete document");
}

export async function fetchConversations(): Promise<ConversationRead[]> {
  const res = await fetch(`${BASE_URL}/conversations`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch conversations");
  return res.json();
}

export async function fetchConversation(id: string): Promise<ConversationDetail> {
  const res = await fetch(`${BASE_URL}/conversations/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch conversation");
  return res.json();
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/conversations/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
}

export async function sendChatMessage(
  query: string,
  conversationId?: string,
  retrievalMethod = "hybrid"
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      conversation_id: conversationId,
      retrieval_method: retrievalMethod,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute chat request");
  }
  return res.json();
}

export async function fetchExecutionTrace(id: string): Promise<QueryExecutionRead> {
  const res = await fetch(`${BASE_URL}/query-executions/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch execution trace");
  return res.json();
}

export async function fetchEvaluationRuns(): Promise<EvaluationRunRead[]> {
  const res = await fetch(`${BASE_URL}/evaluation/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch evaluation runs");
  return res.json();
}

export async function fetchEvaluationRun(id: string): Promise<EvaluationRunRead> {
  const res = await fetch(`${BASE_URL}/evaluation/runs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch evaluation run");
  return res.json();
}

export async function triggerEvaluation(
  configName = "hybrid_with_rerank"
): Promise<EvaluationRunRead> {
  const res = await fetch(`${BASE_URL}/evaluation/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      configuration_name: configName,
      name: `Benchmark - ${configName}`,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to trigger evaluation run");
  }
  return res.json();
}
