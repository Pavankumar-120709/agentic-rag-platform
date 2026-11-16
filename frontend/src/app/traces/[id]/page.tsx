"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Cpu,
  Clock,
  Coins,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Search,
  Sparkles,
  GitBranch,
  FileText,
  ShieldCheck,
  ShieldAlert
} from "lucide-react";
import { fetchExecutionTrace } from "@/lib/api";
import { QueryExecutionRead } from "@/types";

export default function ExecutionTracePage() {
  const params = useParams();
  const id = params?.id as string;

  const [trace, setTrace] = useState<QueryExecutionRead | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchExecutionTrace(id)
        .then(setTrace)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Loading execution trace details...
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="p-8 text-center text-xs text-red-400">
        Trace record not found.
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/chat"
            className="p-2 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <Cpu className="h-5 w-5 text-blue-400" />
              Query Execution Trace
            </h1>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Trace ID: {trace.trace_id} &bull; Execution ID: {trace.id}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${
              trace.final_status === "success"
                ? "bg-emerald-950/60 text-emerald-400 border-emerald-800"
                : "bg-amber-950/60 text-amber-400 border-amber-800"
            }`}
          >
            {trace.final_status.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Query & Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Latency</span>
          <p className="text-xl font-bold text-white flex items-center gap-1.5">
            <Clock className="h-4 w-4 text-blue-400" />
            {trace.latency_ms} ms
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Token Usage</span>
          <p className="text-xl font-bold text-white flex items-center gap-1.5">
            <Coins className="h-4 w-4 text-amber-400" />
            {trace.total_tokens} tokens
          </p>
          <span className="text-[10px] text-slate-500 font-mono">
            {trace.prompt_tokens} in / {trace.completion_tokens} out
          </span>
        </div>
        <div className="p-4 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Faithfulness</span>
          <p className="text-xl font-bold text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            {trace.faithfulness_score !== null ? `${(trace.faithfulness_score * 100).toFixed(0)}%` : "N/A"}
          </p>
        </div>
        <div className="p-4 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-1">
          <span className="text-[10px] text-slate-400 uppercase font-semibold">Citations Valid</span>
          <p className="text-xl font-bold text-white flex items-center gap-1.5">
            {trace.citation_valid ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            ) : (
              <ShieldAlert className="h-4 w-4 text-red-400" />
            )}
            {trace.citation_valid ? "Verified" : "Failed"}
          </p>
        </div>
      </div>

      {/* Query Evolution & Rewriting Timeline */}
      <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4">
        <h2 className="font-semibold text-sm text-white flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-purple-400" />
          Query Formulations & Agent Rewriting Lineage
        </h2>

        <div className="space-y-2 text-xs">
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="text-slate-400 block font-semibold mb-1">Original User Query:</span>
            <p className="text-slate-200 font-medium">{trace.original_query}</p>
          </div>

          {trace.rewritten_queries && trace.rewritten_queries.length > 0 && (
            <div className="p-3 rounded-lg bg-purple-950/20 border border-purple-900/40 text-purple-200 space-y-1.5">
              <span className="font-semibold block text-purple-300">
                Agentic Rewritten Formulations ({trace.rewritten_queries.length}):
              </span>
              {trace.rewritten_queries.map((rw, idx) => (
                <div key={idx} className="flex items-center gap-2 font-mono text-[11px]">
                  <span className="text-purple-400">Step {idx + 1}:</span>
                  <span>{rw}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Retrieved Candidates & Reranking Scores */}
      <div className="p-6 rounded-xl bg-[#0f172a] border border-[#1e293b] space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm text-white flex items-center gap-2">
            <Layers className="h-4 w-4 text-blue-400" />
            Rank Fusion & Cross-Encoder Scored Chunks ({trace.retrieval_results?.length || 0})
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            RRF Formula: Σ 1 / (60 + rank)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#131d33] border-b border-[#1e293b] text-slate-400 uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">Chunk ID</th>
                <th className="py-2.5 px-3">Document</th>
                <th className="py-2.5 px-3">Dense Rank</th>
                <th className="py-2.5 px-3">BM25 Rank</th>
                <th className="py-2.5 px-3">RRF Score</th>
                <th className="py-2.5 px-3">Rerank Score</th>
                <th className="py-2.5 px-3">Context Selected</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e293b] text-slate-300 font-mono">
              {trace.retrieval_results?.map((res) => (
                <tr key={res.id} className="hover:bg-slate-900/40">
                  <td className="py-2.5 px-3 text-blue-400 font-medium">{res.chunk_id}</td>
                  <td className="py-2.5 px-3 text-slate-300 truncate max-w-xs">{res.filename}</td>
                  <td className="py-2.5 px-3">{res.dense_rank ? `#${res.dense_rank}` : "-"}</td>
                  <td className="py-2.5 px-3">{res.sparse_rank ? `#${res.sparse_rank}` : "-"}</td>
                  <td className="py-2.5 px-3 text-purple-400 font-semibold">{res.rrf_score.toFixed(6)}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-semibold">
                    {res.rerank_score !== null ? res.rerank_score.toFixed(4) : "-"}
                  </td>
                  <td className="py-2.5 px-3">
                    {res.selected_for_context ? (
                      <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900 text-[10px]">
                        Selected
                      </span>
                    ) : (
                      <span className="text-slate-600 text-[10px]">Filtered</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
