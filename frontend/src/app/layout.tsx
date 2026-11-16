import "./globals.css";
import { Navigation } from "@/components/Navigation";

export const metadata = {
  title: "Agentic RAG Intelligence Platform",
  description: "Enterprise Document Intelligence with Hybrid Retrieval, RRF, Cross-Encoder Reranking, and Bounded LangGraph Orchestration.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex h-screen overflow-hidden bg-[#090d16] text-slate-100 antialiased">
        <Navigation />
        <main className="flex-1 overflow-y-auto bg-[#090d16] relative flex flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
