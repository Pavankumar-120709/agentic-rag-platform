"use client";

import { useEffect, useState } from "react";
import {
  FileText,
  Upload,
  Trash2,
  RefreshCw,
  Search,
  Layers,
  Clock,
  Eye,
  AlertCircle,
  X,
  FileCode,
  Hash
} from "lucide-react";
import { DocumentUploadModal } from "@/components/DocumentUploadModal";
import { fetchDocuments, deleteDocument, fetchDocumentDetail } from "@/lib/api";
import { DocumentRead, DocumentDetail } from "@/types";
import { formatBytes } from "@/lib/utils";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocumentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document and all its indexed chunks?")) return;
    setDeletingId(id);
    try {
      await deleteDocument(id);
      await loadDocuments();
      if (selectedDoc?.id === id) {
        setSelectedDoc(null);
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleInspect = async (id: string) => {
    setLoadingDetail(true);
    try {
      const detail = await fetchDocumentDetail(id);
      setSelectedDoc(detail);
    } finally {
      setLoadingDetail(false);
    }
  };

  const filtered = documents.filter((d) =>
    d.filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-400" />
            Document Knowledge Base
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage ingested documents, view chunking breakdown, and inspect token-aware partitions.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadDocuments}
            className="p-2.5 rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-300 transition text-xs flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-2 shadow-lg shadow-blue-600/20"
          >
            <Upload className="h-4 w-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex items-center gap-3 bg-[#0f172a] p-3 rounded-xl border border-[#1e293b]">
        <Search className="h-4 w-4 text-slate-500 ml-2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter documents by filename..."
          className="bg-transparent border-none text-xs text-slate-200 placeholder-slate-500 focus:outline-none w-full"
        />
      </div>

      {/* Document Table */}
      <div className="rounded-xl border border-[#1e293b] bg-[#0f172a] overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#131d33] border-b border-[#1e293b] text-slate-400 uppercase tracking-wider font-semibold">
            <tr>
              <th className="py-3.5 px-4">Filename</th>
              <th className="py-3.5 px-4">Format</th>
              <th className="py-3.5 px-4">Size</th>
              <th className="py-3.5 px-4">Chunks</th>
              <th className="py-3.5 px-4">Tokens</th>
              <th className="py-3.5 px-4">Status</th>
              <th className="py-3.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1e293b] text-slate-300">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-slate-500">
                  {loading ? "Loading documents..." : "No documents found. Ingest your first document to begin."}
                </td>
              </tr>
            ) : (
              filtered.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-4 font-medium text-slate-200 flex items-center gap-2.5">
                    <FileText className="h-4 w-4 text-blue-400 shrink-0" />
                    <span className="truncate max-w-xs">{doc.filename}</span>
                  </td>
                  <td className="py-3 px-4 uppercase text-[11px] font-mono text-slate-400">
                    {doc.file_type}
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {formatBytes(doc.file_size_bytes)}
                  </td>
                  <td className="py-3 px-4">
                    <span className="font-semibold text-white">{doc.total_chunks}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400">
                    {doc.total_tokens.toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                        doc.status === "indexed"
                          ? "bg-emerald-950/60 text-emerald-400 border-emerald-900"
                          : doc.status === "processing"
                          ? "bg-amber-950/60 text-amber-400 border-amber-900 animate-pulse"
                          : "bg-red-950/60 text-red-400 border-red-900"
                      }`}
                    >
                      {doc.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      onClick={() => handleInspect(doc.id)}
                      className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-blue-400 transition"
                      title="Inspect Chunks"
                    >
                      <Eye className="h-4 w-4 inline" />
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={deletingId === doc.id}
                      className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-red-400 transition disabled:opacity-50"
                      title="Delete Document"
                    >
                      <Trash2 className="h-4 w-4 inline" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Chunk Inspector Drawer / Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-4xl bg-[#0f172a] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#131d33]">
              <div className="flex items-center gap-2">
                <FileCode className="h-5 w-5 text-blue-400" />
                <div>
                  <h3 className="font-semibold text-sm text-white">{selectedDoc.filename}</h3>
                  <p className="text-xs text-slate-400 font-mono">
                    {selectedDoc.total_chunks} chunks &bull; {selectedDoc.total_tokens} total tokens
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers className="h-4 w-4 text-blue-400" />
                Token-Aware Partitions
              </h4>

              <div className="space-y-3">
                {selectedDoc.chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
                      <span className="font-mono text-blue-400 font-medium">
                        Chunk #{chunk.chunk_index + 1}
                      </span>
                      <div className="flex items-center gap-3">
                        {chunk.page_number && (
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                            Page {chunk.page_number}
                          </span>
                        )}
                        <span className="text-slate-400 font-mono">
                          {chunk.token_count} tokens
                        </span>
                      </div>
                    </div>
                    <p className="text-xs text-slate-300 font-serif leading-relaxed whitespace-pre-wrap">
                      {chunk.original_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 border-t border-[#1e293b] bg-[#0c1222] flex justify-end">
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadDocuments}
      />
    </div>
  );
}
