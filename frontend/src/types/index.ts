export interface DocumentRead {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  content_hash: string;
  status: "processing" | "indexed" | "failed";
  total_chunks: number;
  total_tokens: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunkRead {
  id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  page_number?: number;
  original_text: string;
  token_count: number;
  created_at: string;
}

export interface DocumentDetail extends DocumentRead {
  chunks: DocumentChunkRead[];
}

export interface Citation {
  document_id: string;
  filename: string;
  chunk_id: string;
  page_number?: number;
  quoted_text: string;
}

export interface AnswerResponse {
  answer: string;
  citations: Citation[];
  confidence_label: "supported" | "partially_supported" | "insufficient_evidence";
  evidence_summary: string;
  warnings: string[];
}

export interface MessageRead {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  confidence_label: string;
  token_count: number;
  execution_id?: string;
  created_at: string;
}

export interface ConversationRead {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends ConversationRead {
  messages: MessageRead[];
}

export interface ChatResponse {
  conversation_id: string;
  message: MessageRead;
  answer_response: AnswerResponse;
  execution_id: string;
  trace_id: string;
  latency_ms: number;
  token_usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
}

export interface RetrievalResultRead {
  id: string;
  chunk_id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  page_number?: number;
  sparse_rank?: number;
  dense_rank?: number;
  rrf_score: number;
  rerank_score?: number;
  selected_for_context: boolean;
  chunk_text: string;
}

export interface QueryExecutionRead {
  id: string;
  conversation_id?: string;
  trace_id: string;
  original_query: string;
  rewritten_queries: string[];
  retrieval_method: string;
  bm25_count: number;
  dense_count: number;
  fused_count: number;
  reranked_count: number;
  evidence_sufficient: bool;
  selected_context_tokens: number;
  generation_attempts: number;
  faithfulness_score?: number;
  citation_valid: boolean;
  fallback_reason?: string;
  final_status: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  created_at: string;
  retrieval_results: RetrievalResultRead[];
}

export interface SystemMetrics {
  total_documents: number;
  total_chunks: number;
  total_queries: number;
  avg_latency_ms: number;
  total_tokens_consumed: number;
  estimated_total_cost_usd: number;
  avg_faithfulness?: number;
  avg_relevancy?: number;
  retrieval_distribution: Record<string, number>;
}

export interface EvaluationResultRead {
  id: string;
  run_id: string;
  question: string;
  ground_truth: string;
  generated_answer: string;
  retrieved_contexts: string[];
  faithfulness?: number;
  answer_relevancy?: number;
  context_precision?: number;
  context_recall?: number;
  created_at: string;
}

export interface EvaluationRunRead {
  id: string;
  name: string;
  description?: string;
  dataset_name: string;
  configuration_name: string;
  status: string;
  sample_count: number;
  avg_faithfulness?: number;
  avg_answer_relevancy?: number;
  avg_context_precision?: number;
  avg_context_recall?: number;
  total_duration_seconds?: number;
  created_at: string;
  results?: EvaluationResultRead[];
}
