"use client";

import { Citation } from "@/types";
import { X, CheckCircle, FileText, Hash, Bookmark } from "lucide-react";

interface SourceViewerModalProps {
  citation: Citation | null;
  onClose: () => void;
}

export function SourceViewerModal({ citation, onClose }: SourceViewerModalProps) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl bg-[#0f172a] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#131d33]">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-blue-400" />
            <h3 className="font-semibold text-sm text-white">{citation.filename}</h3>
            {citation.page_number && (
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Page {citation.page_number}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-2">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Grounded Evidence Quote (Verified)</span>
            </div>
            <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-emerald-200 text-sm italic font-serif leading-relaxed">
              &ldquo;{citation.quoted_text}&rdquo;
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800/80 space-y-2 text-xs text-slate-400 font-mono">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1 text-slate-500">
                <Hash className="h-3.5 w-3.5" /> Chunk ID
              </span>
              <span className="text-slate-300">{citation.chunk_id}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1 text-slate-500">
                <Bookmark className="h-3.5 w-3.5" /> Document ID
              </span>
              <span className="text-slate-300">{citation.document_id}</span>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-[#1e293b] bg-[#0c1222] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition"
          >
            Close Source
          </button>
        </div>
      </div>
    </div>
  );
}
