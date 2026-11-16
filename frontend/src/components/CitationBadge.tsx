"use client";

import { Citation } from "@/types";
import { BookOpen } from "lucide-react";

interface CitationBadgeProps {
  citation: Citation;
  index: number;
  onClick: (citation: Citation) => void;
}

export function CitationBadge({ citation, index, onClick }: CitationBadgeProps) {
  return (
    <button
      onClick={() => onClick(citation)}
      className="inline-flex items-center gap-1 px-2 py-0.5 mx-1 text-xs font-medium rounded bg-blue-950/60 text-blue-300 border border-blue-800/60 hover:bg-blue-900/80 hover:text-white transition shadow-sm"
      title={`Source: ${citation.filename} (Page ${citation.page_number || 1})`}
    >
      <BookOpen className="h-3 w-3 shrink-0 text-blue-400" />
      <span>
        [{index + 1}] {citation.filename.slice(0, 16)}
        {citation.filename.length > 16 ? "..." : ""}
        {citation.page_number ? ` p.${citation.page_number}` : ""}
      </span>
    </button>
  );
}
