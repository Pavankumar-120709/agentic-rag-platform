"use client";

import { useState, useRef } from "react";
import { UploadCloud, X, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { uploadDocument } from "@/lib/api";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function DocumentUploadModal({
  isOpen,
  onClose,
  onSuccess,
}: DocumentUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        onClose();
        setSuccess(false);
        setFile(null);
      }, 1000);
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-[#0f172a] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 border-b border-[#1e293b] flex items-center justify-between bg-[#131d33]">
          <h3 className="font-semibold text-sm text-white">Ingest New Document</h3>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition bg-slate-900/40 text-center"
          >
            <UploadCloud className="h-10 w-10 text-blue-400 mb-3" />
            <p className="text-sm font-medium text-slate-200">
              {file ? file.name : "Drag & drop your file here, or click to browse"}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports PDF, TXT, and Markdown up to 25MB
            </p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setFile(e.target.files[0]);
                  setError(null);
                }
              }}
            />
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/60 flex items-center gap-2 text-xs text-red-300">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/60 flex items-center gap-2 text-xs text-emerald-300">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span>Document indexed successfully!</span>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[#1e293b] bg-[#0c1222] flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={isUploading}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5 shadow-md shadow-blue-600/20"
          >
            {isUploading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            <span>{isUploading ? "Chunking & Indexing..." : "Upload & Ingest"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
