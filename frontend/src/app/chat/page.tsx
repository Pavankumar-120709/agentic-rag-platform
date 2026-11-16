"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  MessageSquare,
  Send,
  Plus,
  Bot,
  User,
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  Clock,
  Coins,
  ExternalLink,
  Loader2,
  Trash2,
  FileText
} from "lucide-react";
import { CitationBadge } from "@/components/CitationBadge";
import { SourceViewerModal } from "@/components/SourceViewerModal";
import {
  fetchConversations,
  fetchConversation,
  sendChatMessage,
  deleteConversation
} from "@/lib/api";
import { ConversationRead, ConversationDetail, MessageRead, Citation, ChatResponse } from "@/types";

function ChatContent() {
  const searchParams = useSearchParams();
  const initialId = searchParams.get("id");

  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(initialId);
  const [messages, setMessages] = useState<MessageRead[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [retrievalMethod, setRetrievalMethod] = useState<"hybrid" | "dense_only" | "sparse_only">("hybrid");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadConversations = async () => {
    try {
      const convs = await fetchConversations();
      setConversations(convs);
      if (!activeConversationId && convs.length > 0) {
        setActiveConversationId(convs[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadConversationMessages = async (id: string) => {
    try {
      const conv = await fetchConversation(id);
      setMessages(conv.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      loadConversationMessages(activeConversationId);
    } else {
      setMessages([]);
    }
  }, [activeConversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isLoading) return;

    const query = inputQuery.trim();
    setInputQuery("");
    setIsLoading(true);

    const tempUserMsg: MessageRead = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConversationId || "",
      role: "user",
      content: query,
      citations: [],
      confidence_label: "supported",
      token_count: 0,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await sendChatMessage(
        query,
        activeConversationId || undefined,
        retrievalMethod
      );

      setLatestResponse(response);
      setActiveConversationId(response.conversation_id);
      setMessages((prev) => [...prev, response.message]);
      await loadConversations();
    } catch (err: any) {
      const errorMsg: MessageRead = {
        id: `err-${Date.now()}`,
        conversation_id: activeConversationId || "",
        role: "assistant",
        content: `Error: ${err.message || "Failed to process request."}`,
        citations: [],
        confidence_label: "insufficient_evidence",
        token_count: 0,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    await deleteConversation(id);
    if (activeConversationId === id) {
      setActiveConversationId(null);
      setMessages([]);
    }
    await loadConversations();
  };

  return (
    <div className="flex h-screen bg-[#090d16] overflow-hidden">
      {/* Conversations Sidebar */}
      <div className="w-72 border-r border-[#1e293b] bg-[#0c1222] flex flex-col shrink-0">
        <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
          <h2 className="font-semibold text-xs text-slate-300 uppercase tracking-wider">
            Conversations
          </h2>
          <button
            onClick={() => {
              setActiveConversationId(null);
              setMessages([]);
              setLatestResponse(null);
            }}
            className="p-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition text-xs flex items-center gap-1 shadow-sm"
            title="New Chat"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>New</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No conversations yet.
            </div>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => setActiveConversationId(c.id)}
                className={`flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition group ${
                  activeConversationId === c.id
                    ? "bg-[#16213e] text-white border border-blue-500/30"
                    : "text-slate-400 hover:bg-slate-900/40 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 text-slate-400 group-hover:text-blue-400" />
                  <span className="truncate">{c.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 transition"
                  title="Delete"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Retrieval Strategy Selector */}
        <div className="p-3 border-t border-[#1e293b] bg-[#0a0f1d] text-xs">
          <label className="text-[11px] text-slate-400 block mb-1.5 font-medium">
            Retrieval Strategy
          </label>
          <select
            value={retrievalMethod}
            onChange={(e: any) => setRetrievalMethod(e.target.value)}
            className="w-full bg-[#131d33] border border-slate-700 rounded-lg p-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="hybrid">Hybrid (Dense + BM25 + RRF)</option>
            <option value="dense_only">Dense Only (pgvector)</option>
            <option value="sparse_only">Sparse Only (BM25)</option>
          </select>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-[#090d16] relative">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-lg mx-auto">
              <div className="h-12 w-12 rounded-2xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 mb-4 shadow-lg shadow-blue-500/10">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-base font-semibold text-white">Agentic Research Assistant</h3>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                Ask questions over uploaded knowledge assets. The bounded LangGraph pipeline will
                execute hybrid search, Reciprocal Rank Fusion, cross-encoder reranking, and
                deterministic citation verification.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-2 text-left w-full text-xs">
                <button
                  onClick={() => setInputQuery("What is the token budget constraint in context selection?")}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-blue-500/50 text-slate-300 transition"
                >
                  &ldquo;What is the token budget constraint?&rdquo;
                </button>
                <button
                  onClick={() => setInputQuery("How does RRF combine dense and sparse rankings?")}
                  className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-blue-500/50 text-slate-300 transition"
                >
                  &ldquo;How does RRF combine rankings?&rdquo;
                </button>
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 max-w-3xl ${
                  m.role === "user" ? "ml-auto justify-end" : "mr-auto"
                }`}
              >
                {m.role === "assistant" && (
                  <div className="h-7 w-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-1">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`rounded-xl p-4 text-xs leading-relaxed space-y-3 ${
                    m.role === "user"
                      ? "bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-600/10"
                      : "bg-[#0f172a] border border-[#1e293b] text-slate-200 rounded-bl-none shadow-sm"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>

                  {m.role === "assistant" && (
                    <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border ${
                          m.confidence_label === "supported"
                            ? "bg-emerald-950/60 text-emerald-300 border-emerald-800"
                            : m.confidence_label === "partially_supported"
                            ? "bg-amber-950/60 text-amber-300 border-amber-800"
                            : "bg-red-950/60 text-red-300 border-red-800"
                        }`}
                      >
                        {m.confidence_label === "supported" && <ShieldCheck className="h-3 w-3" />}
                        {m.confidence_label === "partially_supported" && <HelpCircle className="h-3 w-3" />}
                        {m.confidence_label === "insufficient_evidence" && <ShieldAlert className="h-3 w-3" />}
                        {m.confidence_label.replace("_", " ").toUpperCase()}
                      </span>

                      {m.citations && m.citations.length > 0 && (
                        <div className="inline-flex flex-wrap items-center">
                          {m.citations.map((cite, idx) => (
                            <CitationBadge
                              key={`${cite.chunk_id}-${idx}`}
                              citation={cite}
                              index={idx}
                              onClick={(c) => setSelectedCitation(c)}
                            />
                          ))}
                        </div>
                      )}

                      {m.execution_id && (
                        <Link
                          href={`/traces/${m.execution_id}`}
                          className="ml-auto inline-flex items-center gap-1 text-[10px] text-blue-400 hover:underline"
                        >
                          <ExternalLink className="h-3 w-3" /> View Execution Trace
                        </Link>
                      )}
                    </div>
                  )}
                </div>

                {m.role === "user" && (
                  <div className="h-7 w-7 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0 mt-1">
                    <User className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {isLoading && (
            <div className="flex gap-3 max-w-3xl mr-auto animate-pulse">
              <div className="h-7 w-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="p-3.5 rounded-xl bg-[#0f172a] border border-[#1e293b] text-xs text-slate-400 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                <span>Executing LangGraph workflow (hybrid retrieval, RRF, cross-encoder rerank)...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-[#1e293b] bg-[#0c1222]">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-2">
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask a question grounded in your documents..."
              className="flex-1 bg-[#131d33] border border-slate-700 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition shadow-inner"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isLoading}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl text-xs font-medium transition flex items-center gap-1.5 shadow-lg shadow-blue-600/20"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>

      <SourceViewerModal
        citation={selectedCitation}
        onClose={() => setSelectedCitation(null)}
      />
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-xs text-slate-400">Loading Chat Interface...</div>}>
      <ChatContent />
    </Suspense>
  );
}
