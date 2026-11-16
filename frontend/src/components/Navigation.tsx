"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  BarChart3,
  Cpu,
  Layers
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "Agentic Chat", icon: MessageSquare },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/evaluation", label: "RAGAS Evaluation", icon: BarChart3 },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-[#1e293b] bg-[#0c1222] flex flex-col shrink-0 h-screen sticky top-0">
      <div className="p-6 border-b border-[#1e293b] flex items-center gap-3">
        <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
          <Cpu className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
            Agentic RAG
            <span className="text-[10px] bg-blue-500/10 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/20 font-mono">
              v1.0
            </span>
          </h1>
          <p className="text-xs text-slate-400">Intelligence Platform</p>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all",
                isActive
                  ? "bg-blue-600 text-white shadow-md shadow-blue-600/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#131d33]"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[#1e293b] bg-[#0a0f1d]">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>PostgreSQL + pgvector Active</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1 font-mono">BM25 + RRF + LangGraph</p>
      </div>
    </aside>
  );
}
