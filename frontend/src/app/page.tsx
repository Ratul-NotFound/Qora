"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Sidebar";
import SearchBox from "@/components/SearchBox";
import { 
  ArrowUpRight, BookOpen, GitMerge, FileCheck2, 
  Terminal, CheckCircle2, AlertCircle, ExternalLink, ChevronDown, ChevronUp, FileText, Compass, Sparkles
} from "lucide-react";
import axios from "axios";

interface Paper {
  id: str;
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  source: string;
  url: string;
  pdf_url: string;
  citations: number;
  summary?: string;
  key_findings?: string[];
  methods?: string[];
  datasets?: string[];
  research_gaps?: string[];
  relevance_score?: number;
}

interface Gap {
  gap: string;
  description: string;
  severity: string;
  related_papers: number;
}

interface Hypothesis {
  hypothesis: string;
  rationale: string;
  approach: string;
  novelty: string;
  feasibility: string;
  impact: string;
}

interface SessionData {
  papers: Paper[];
  report: string;
  intelligence: {
    gaps?: Gap[];
    hypotheses?: Hypothesis[];
    trends?: any;
    graph_data?: any;
  };
}

export default function Home() {
  const [isSearching, setIsSearching] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  
  // Results states
  const [activeTab, setActiveTab] = useState<"papers" | "report" | "gaps">("papers");
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [expandedPaper, setExpandedPaper] = useState<string | null>(null);
  const [activeTopic, setActiveTopic] = useState<string>("");

  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const handleStartSearch = async (query: string, sources: string[]) => {
    setIsSearching(true);
    setError(null);
    setLogs(["Initializing discovery session..."]);
    setProgress(0.05);
    setSessionData(null);
    setActiveTopic(query);

    try {
      // 1. Post to research endpoint
      const response = await axios.post("http://localhost:8000/api/research", {
        topic: query,
        depth: 2,
        max_papers: 10, // keep small for quick, high-speed responses
        sources: sources,
      });

      const session = response.data;
      const sessionId = session.id;
      setLogs((prev) => [...prev, `Session created: ${sessionId}. Opening WebSocket stream...`]);

      // 2. Open WebSocket stream
      const ws = new WebSocket(`ws://localhost:8000/ws/research/${sessionId}`);

      ws.onmessage = async (event) => {
        const messageData = JSON.parse(event.data);
        if (messageData.type === "progress") {
          setLogs((prev) => [...prev, messageData.message]);
          setProgress(messageData.progress);
          
          // If progress is complete, trigger fetch immediately
          if (messageData.progress >= 1.0) {
            ws.close(); // This will trigger ws.onclose and fetch the results
          }
        }
      };

      ws.onclose = async () => {
        setLogs((prev) => [...prev, "Syncing final data..."]);
        
        // 3. Fetch completed data
        try {
          const resultsResponse = await axios.get(`http://localhost:8000/api/research/${sessionId}/results`);
          setSessionData(resultsResponse.data);
          setProgress(1.0);
          setIsSearching(false);
          setLogs((prev) => [...prev, "✨ Synthesis fully synced! Displaying results."]);
        } catch (err: any) {
          setError(`Failed to fetch research results: ${err.message}`);
          setIsSearching(false);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
        setLogs((prev) => [...prev, "⚠️ WebSocket connection interrupted. Polling backup data..."]);
      };

    } catch (err: any) {
      console.error(err);
      setError(
        err.code === "ERR_NETWORK" 
          ? "Unable to connect to local QORA backend server. Ensure python backend is running on http://localhost:8000."
          : `Search failed: ${err.message}`
      );
      setIsSearching(false);
    }
  };

  const recentSearches = [
    "Quantum-dot cellular automata",
    "Transformer architectures in genomics",
    "Carbon-nanotube transistors efficiency",
  ];

  return (
    <div className="flex w-full min-h-screen bg-[var(--background)]">
      <Sidebar />
      <main className="flex-1 p-8 lg:p-14 overflow-y-auto flex flex-col justify-between">
        
        {/* Error notification */}
        {error && (
          <div className="max-w-3xl mx-auto w-full mb-6 p-4 bg-red-950/30 border border-red-900/50 rounded-lg text-red-200 text-xs flex items-center gap-3">
            <AlertCircle size={16} className="text-red-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Canvas Area */}
        <div className="max-w-4xl mx-auto w-full flex-1 flex flex-col justify-center">
          
          {!isSearching && !sessionData && (
            <div className="max-w-3xl mx-auto w-full space-y-8 my-auto">
              <header className="text-center space-y-2">
                <h1 className="text-4xl font-light tracking-tight text-white font-mono">
                  QORA
                </h1>
                <p className="text-neutral-500 text-sm md:text-base font-light">
                  Autonomous Scientific Research and Citation Intelligence Engine.
                </p>
              </header>

              <SearchBox onSearch={handleStartSearch} isSearching={isSearching} />

              <div className="pt-4 max-w-xl mx-auto">
                <div className="text-[10px] font-semibold text-neutral-600 uppercase tracking-widest mb-3 text-center">Quick Discovery</div>
                <div className="space-y-1.5">
                  {recentSearches.map((search, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleStartSearch(search, ["arxiv", "semantic_scholar"])}
                      className="w-full flex items-center justify-between px-3 py-2 rounded-md bg-[var(--panel)] border border-[var(--border)] hover:bg-[var(--panel-hover)] hover:border-neutral-800 transition-all text-xs text-neutral-400 hover:text-white"
                    >
                      <span className="font-light">{search}</span>
                      <ArrowUpRight size={12} className="text-neutral-600" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Running / Searching Console View */}
          {isSearching && !sessionData && (
            <div className="max-w-2xl mx-auto w-full space-y-6 my-auto">
              <div className="flex items-center justify-between text-xs text-neutral-400">
                <span className="font-mono flex items-center gap-2">
                  <Terminal size={14} className="text-neutral-500" />
                  session_stream: {activeTopic}
                </span>
                <span>{Math.round(progress * 100)}% Complete</span>
              </div>

              {/* Progress Line */}
              <div className="w-full h-1 bg-neutral-900 rounded-full overflow-hidden border border-[var(--border)]">
                <div 
                  className="h-full bg-white transition-all duration-300"
                  style={{ width: `${progress * 100}%` }}
                />
              </div>

              {/* Live console logging */}
              <div className="bg-[#050505] border border-[var(--border)] rounded-lg p-5 font-mono text-[11px] text-neutral-400 h-64 overflow-y-auto space-y-1.5 shadow-inner">
                {logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <span className="text-neutral-600 shrink-0 select-none">[{index + 1}]</span>
                    <span className={log.startsWith("❌") ? "text-red-400" : log.startsWith("📄") ? "text-neutral-300" : "text-neutral-400"}>
                      {log}
                    </span>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            </div>
          )}

          {/* Results dashboard */}
          {sessionData && (
            <div className="w-full space-y-8 mt-6">
              <header className="flex flex-col md:flex-row md:items-center justify-between border-b border-[var(--border)] pb-6 gap-4">
                <div>
                  <div className="text-[10px] font-semibold text-neutral-500 uppercase tracking-widest mb-1">Discovery Output</div>
                  <h2 className="text-2xl font-light text-white">{activeTopic}</h2>
                </div>
                
                {/* Clean Tabs */}
                <div className="flex items-center gap-1.5 bg-neutral-950 p-1 rounded-lg border border-[var(--border)] self-start font-mono text-xs">
                  <button
                    onClick={() => setActiveTab("papers")}
                    className={`px-3 py-1.5 rounded-md transition-all ${
                      activeTab === "papers" 
                        ? "bg-neutral-800 text-white font-medium" 
                        : "text-neutral-500 hover:text-neutral-300"
                    }`}
                  >
                    Papers ({sessionData.papers.length})
                  </button>
                  <button
                    onClick={() => setActiveTab("report")}
                    className={`px-3 py-1.5 rounded-md transition-all ${
                      activeTab === "report" 
                        ? "bg-neutral-800 text-white font-medium" 
                        : "text-neutral-500 hover:text-neutral-300"
                    }`}
                  >
                    Literature Review
                  </button>
                  <button
                    onClick={() => setActiveTab("gaps")}
                    className={`px-3 py-1.5 rounded-md transition-all ${
                      activeTab === "gaps" 
                        ? "bg-neutral-800 text-white font-medium" 
                        : "text-neutral-500 hover:text-neutral-300"
                    }`}
                  >
                    Gaps & Hypotheses
                  </button>
                </div>
              </header>

              {/* Tab 1: Papers View */}
              {activeTab === "papers" && (
                <div className="space-y-4">
                  {sessionData.papers.map((paper) => {
                    const isExpanded = expandedPaper === paper.id;
                    return (
                      <div 
                        key={paper.id} 
                        className="bg-[var(--panel)] border border-[var(--border)] rounded-lg overflow-hidden transition-all duration-200 hover:border-neutral-800"
                      >
                        {/* Summary Header */}
                        <div 
                          onClick={() => setExpandedPaper(isExpanded ? null : paper.id)}
                          className="p-5 flex items-start justify-between gap-4 cursor-pointer"
                        >
                          <div className="space-y-1.5">
                            <div className="flex items-center gap-3">
                              <span className="text-[10px] bg-neutral-800 px-2 py-0.5 rounded font-mono text-neutral-400 capitalize">{paper.source}</span>
                              {paper.year && <span className="text-[10px] text-neutral-500 font-mono">{paper.year}</span>}
                              {paper.citations > 0 && (
                                <span className="text-[10px] text-neutral-500 font-mono">Citations: {paper.citations}</span>
                              )}
                            </div>
                            <h3 className="text-sm font-medium text-white pr-4">{paper.title}</h3>
                            <p className="text-xs text-neutral-500 font-light truncate max-w-2xl">
                              {paper.authors.join(", ")}
                            </p>
                          </div>
                          
                          <div className="text-neutral-500 pt-1">
                            {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                          </div>
                        </div>

                        {/* Extended Details */}
                        {isExpanded && (
                          <div className="border-t border-[var(--border)] p-6 bg-[#090909] text-xs md:text-sm text-neutral-300 space-y-6">
                            {/* Actions / Source Links */}
                            <div className="flex gap-4 border-b border-[var(--border)] pb-4 font-mono text-[10px]">
                              {paper.url && (
                                <a href={paper.url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:text-white transition-colors">
                                  View Source <ExternalLink size={12} />
                                </a>
                              )}
                              {paper.pdf_url && (
                                <a href={paper.pdf_url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:text-white transition-colors">
                                  Download PDF <ExternalLink size={12} />
                                </a>
                              )}
                            </div>

                            {/* Abstract */}
                            <div className="space-y-1.5">
                              <h4 className="font-semibold text-neutral-400 text-xs uppercase tracking-wider">Abstract</h4>
                              <p className="font-light leading-relaxed text-neutral-400">{paper.abstract || "No abstract available."}</p>
                            </div>

                            {/* AI Summary Section (only if available) */}
                            {paper.summary && (
                              <div className="bg-neutral-950 border border-[var(--border)] p-4 rounded-lg space-y-4">
                                <div className="flex items-center gap-2 text-white font-medium text-xs">
                                  <Sparkles size={14} className="text-amber-400" />
                                  <span>AI Analysis Summary</span>
                                </div>
                                <p className="font-light text-neutral-300 leading-relaxed">{paper.summary}</p>
                                
                                {paper.key_findings && paper.key_findings.length > 0 && (
                                  <div className="space-y-1.5">
                                    <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-widest">Key Findings</span>
                                    <ul className="list-disc pl-4 space-y-1 text-neutral-400 font-light">
                                      {paper.key_findings.map((f, i) => <li key={i}>{f}</li>)}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Tab 2: Literature Review string renderer */}
              {activeTab === "report" && (
                <div className="bg-[var(--panel)] border border-[var(--border)] rounded-xl p-8 max-w-3xl mx-auto shadow-sm">
                  <article className="prose prose-invert prose-sm max-w-none text-neutral-300 font-light leading-relaxed space-y-6 whitespace-pre-wrap">
                    {sessionData.report}
                  </article>
                </div>
              )}

              {/* Tab 3: Gaps & Hypotheses View */}
              {activeTab === "gaps" && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Left Column: Gaps */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2 mb-2">
                      <Compass size={16} className="text-neutral-400" />
                      Detected Research Gaps
                    </h3>
                    
                    {sessionData.intelligence.gaps?.map((gap, idx) => (
                      <div key={idx} className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-5 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-white text-sm">{gap.gap}</span>
                          <span className={`text-[9px] px-2 py-0.5 rounded uppercase font-mono ${
                            gap.severity === "high" ? "bg-red-950 text-red-400 border border-red-900" : "bg-neutral-800 text-neutral-400"
                          }`}>
                            {gap.severity}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-400 font-light leading-relaxed">{gap.description}</p>
                      </div>
                    ))}
                  </div>

                  {/* Right Column: Hypotheses */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2 mb-2">
                      <Sparkles size={16} className="text-neutral-400" />
                      Proposed Hypotheses
                    </h3>
                    
                    {sessionData.intelligence.hypotheses?.map((hypo, idx) => (
                      <div key={idx} className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-5 space-y-3">
                        <div>
                          <div className="text-[10px] font-semibold text-neutral-500 uppercase tracking-widest mb-1">Hypothesis {idx + 1}</div>
                          <span className="font-medium text-white text-sm block">{hypo.hypothesis}</span>
                        </div>
                        
                        <div className="space-y-1">
                          <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-widest block">Rationale</span>
                          <p className="text-xs text-neutral-400 font-light leading-relaxed">{hypo.rationale}</p>
                        </div>

                        <div className="space-y-1 pt-1.5 border-t border-[var(--border)]">
                          <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-widest block">Approach</span>
                          <p className="text-xs text-neutral-400 font-light leading-relaxed">{hypo.approach}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Start new discovery button */}
              <div className="flex justify-center pt-8">
                <button
                  onClick={() => setSessionData(null)}
                  className="bg-neutral-100 hover:bg-white text-black px-5 py-2.5 rounded-lg text-xs font-semibold font-mono"
                >
                  Start New Discovery
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Minimal Bottom Info Panel (only show on home search dashboard) */}
        {!isSearching && !sessionData && (
          <div className="max-w-4xl mx-auto w-full mt-20 pt-8 border-t border-[var(--border)]">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-neutral-500 font-light">
              <div className="flex items-start gap-3">
                <BookOpen size={16} className="text-neutral-600 mt-0.5" />
                <div>
                  <p className="font-medium text-neutral-400">Broad Academic Coverage</p>
                  <p className="mt-1 leading-relaxed">Direct pipeline access to ArXiv, PubMed, Semantic Scholar, and OpenAlex databases.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <GitMerge size={16} className="text-neutral-600 mt-0.5" />
                <div>
                  <p className="font-medium text-neutral-400">Deep Citation Traversal</p>
                  <p className="mt-1 leading-relaxed">Runs graph traversals on citation history to build complete evolutionary lineages.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <FileCheck2 size={16} className="text-neutral-600 mt-0.5" />
                <div>
                  <p className="font-medium text-neutral-400">Structured Synthesis</p>
                  <p className="mt-1 leading-relaxed">Extracts methodologies, results, and research gaps directly into clean LaTeX / Markdown.</p>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
