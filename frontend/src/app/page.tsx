"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Layers,
  MessageSquare,
  Clock,
  Coins,
  ShieldCheck,
  ArrowRight,
  Upload,
  RefreshCw,
  Cpu,
  CheckCircle2,
  AlertTriangle
} from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { DocumentUploadModal } from "@/components/DocumentUploadModal";
import { fetchMetrics, fetchDocuments, fetchConversations } from "@/lib/api";
import { SystemMetrics, DocumentRead, ConversationRead } from "@/types";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [m, docs, convs] = await Promise.all([
        fetchMetrics().catch(() => null),
        fetchDocuments().catch(() => []),
        fetchConversations().catch(() => []),
      ]);
      setMetrics(m);
      setDocuments(docs);
      setConversations(convs);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time hybrid retrieval telemetry, vector index state, and bounded agent metrics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="p-2.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 transition text-xs flex items-center gap-1.5"
            title="Refresh Data"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-2 shadow-lg shadow-blue-600/20"
          >
            <Upload className="h-4 w-4" />
            <span>Ingest Document</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Indexed Documents"
          value={metrics ? metrics.total_documents : "0"}
          subtitle={`${metrics ? metrics.total_chunks : 0} chunks embedded`}
          icon={FileText}
          badge="pgvector"
        />
        <MetricCard
          title="Total Queries Executed"
          value={metrics ? metrics.total_queries : "0"}
          subtitle="Agentic bounded flows"
          icon={MessageSquare}
          badge="LangGraph"
        />
        <MetricCard
          title="Average Latency"
          value={metrics ? `${metrics.avg_latency_ms} ms` : "0 ms"}
          subtitle="RRF + Cross-Encoder"
          icon={Clock}
        />
        <MetricCard
          title="Tokens Consumed"
          value={metrics ? metrics.total_tokens_consumed.toLocaleString() : "0"}
          subtitle={metrics ? `~$${metrics.estimated_total_cost_usd.toFixed(4)} USD` : "$0.00"}
          icon={Coins}
        />
      </div>

      {/* Evaluation Metrics & Architecture Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="font-semibold text-sm text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              Offline Quality Metrics (RAGAS)
            </h2>
            <Link
              href="/evaluation"
              className="text-xs text-blue-400 hover:underline flex items-center gap-1"
            >
              Details <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-xs text-slate-400">Faithfulness</span>
              <p className="text-xl font-bold text-emerald-400 mt-1">
                {metrics?.avg_faithfulness ? `${(metrics.avg_faithfulness * 100).toFixed(1)}%` : "N/A"}
              </p>
              <span className="text-[10px] text-slate-500">Claim-grounded</span>
            </div>
            <div className="p-4 rounded-lg bg-slate-900/60 border border-slate-800">
              <span className="text-xs text-slate-400">Answer Relevancy</span>
              <p className="text-xl font-bold text-blue-400 mt-1">
                {metrics?.avg_relevancy ? `${(metrics.avg_relevancy * 100).toFixed(1)}%` : "N/A"}
              </p>
              <span className="text-[10px] text-slate-500">Query intent</span>
            </div>
          </div>

          <div className="pt-2 text-xs text-slate-400 space-y-1">
            <p className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Deterministic citation verification enabled
            </p>
            <p className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Token budget: 2500 max tokens/context
            </p>
          </div>
        </div>

        {/* Dual-Index & Architecture Specs */}
        <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4 lg:col-span-2">
          <h2 className="font-semibold text-sm text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <Cpu className="h-4 w-4 text-blue-400" />
            Active Retrieval & Bounded Agent Pipeline
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
              <div className="font-semibold text-slate-200">1. Hybrid Retrieval</div>
              <p className="text-slate-400 text-[11px]">
                Dense pgvector cosine search + sparse BM25 keyword matching with technical entity retention.
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
              <div className="font-semibold text-slate-200">2. RRF & Cross-Encoder</div>
              <p className="text-slate-400 text-[11px]">
                Scale-invariant Reciprocal Rank Fusion (k=60) + cross-encoder pairwise reranking.
              </p>
            </div>
            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
              <div className="font-semibold text-slate-200">3. Verification & Guardrails</div>
              <p className="text-slate-400 text-[11px]">
                Bounded query rewriting (max 2), exact quotation validation, and automated abstention.
              </p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-blue-950/20 border border-blue-900/30 flex items-center justify-between text-xs text-blue-300">
            <span className="font-medium">Ready to inspect domain documents or evaluate knowledge answers?</span>
            <Link
              href="/chat"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded font-medium transition flex items-center gap-1"
            >
              Start Chat <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Documents & Conversations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Ingested Documents */}
        <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="font-semibold text-sm text-white flex items-center gap-2">
              <FileText className="h-4 w-4 text-slate-400" />
              Indexed Documents ({documents.length})
            </h2>
            <Link href="/documents" className="text-xs text-blue-400 hover:underline">
              Manage All
            </Link>
          </div>

          {documents.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No documents indexed yet. Click &quot;Ingest Document&quot; above to begin.
            </div>
          ) : (
            <div className="space-y-2">
              {documents.slice(0, 5).map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-xs"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <FileText className="h-4 w-4 text-blue-400 shrink-0" />
                    <span className="font-medium text-slate-200 truncate">{doc.filename}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 text-slate-400">
                    <span>{doc.total_chunks} chunks</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-900 text-[10px]">
                      {doc.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="font-semibold text-sm text-white flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-slate-400" />
              Recent Conversations ({conversations.length})
            </h2>
            <Link href="/chat" className="text-xs text-blue-400 hover:underline">
              Open Chat
            </Link>
          </div>

          {conversations.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              No query conversations yet. Start asking questions in the Agentic Chat.
            </div>
          ) : (
            <div className="space-y-2">
              {conversations.slice(0, 5).map((conv) => (
                <Link
                  key={conv.id}
                  href={`/chat?id=${conv.id}`}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-900/40 border border-slate-800 text-xs hover:border-slate-700 transition"
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <MessageSquare className="h-4 w-4 text-purple-400 shrink-0" />
                    <span className="font-medium text-slate-200 truncate">{conv.title}</span>
                  </div>
                  <span className="text-[11px] text-slate-500 shrink-0">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
