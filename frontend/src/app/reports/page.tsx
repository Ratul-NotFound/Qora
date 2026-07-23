'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Loader2, FileText, Download, Copy, Check } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReportsPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [reportData, setReportData] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/sessions`);
        setSessions(res.data);
      } catch (error) {
        console.error('Failed to fetch sessions:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchSessions();
  }, []);

  const loadReport = async (id: string) => {
    setSelectedSessionId(id);
    setReportLoading(true);
    try {
      const res = await axios.get(`${API_URL}/api/research/${id}/results`);
      setReportData(res.data);
    } catch (error) {
      console.error('Failed to load report:', error);
    } finally {
      setReportLoading(false);
    }
  };

  const handleCopy = () => {
    if (reportData?.report) {
      navigator.clipboard.writeText(reportData.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadMd = async () => {
    if (!selectedSessionId) return;
    try {
      const res = await axios.get(`${API_URL}/api/research/${selectedSessionId}/export/markdown`);
      const blob = new Blob([res.data], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${selectedSessionId}.md`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed', error);
    }
  };

  const handleDownloadBibtex = async () => {
    if (!selectedSessionId) return;
    try {
      const res = await axios.get(`${API_URL}/api/research/${selectedSessionId}/export/bibtex`);
      const blob = new Blob([res.data], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `citations-${selectedSessionId}.bib`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed', error);
    }
  };

  return (
    <div className="flex h-screen bg-[var(--background)] text-white overflow-hidden">
      <Sidebar />
      
      <div className="w-80 border-r border-[var(--border)] bg-[var(--panel)] flex flex-col">
        <header className="p-6 border-b border-[var(--border)]">
          <h1 className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
            Past Sessions
          </h1>
        </header>
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-4 h-4 animate-spin text-neutral-500" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-xs text-neutral-500 text-center py-8 font-light">No sessions found.</div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => loadReport(session.id)}
                className={`w-full text-left p-4 rounded-lg border transition-colors ${
                  selectedSessionId === session.id
                    ? 'bg-[var(--panel-hover)] border-neutral-700'
                    : 'bg-transparent border-[var(--border)] hover:bg-[var(--panel-hover)]'
                }`}
              >
                <div className="text-sm font-light mb-2 truncate" title={session.topic}>{session.topic}</div>
                <div className="flex items-center justify-between text-xs text-neutral-500 font-mono">
                  <span>{new Date(session.created_at).toLocaleDateString()}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[9px] ${
                    session.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'
                  }`}>
                    {session.status}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <main className="flex-1 flex flex-col relative">
        {selectedSessionId ? (
          reportLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
            </div>
          ) : reportData ? (
            <>
              <header className="p-6 border-b border-[var(--border)] flex items-center justify-between bg-[var(--background)] z-10">
                <div className="flex items-center gap-2 text-neutral-400">
                  <FileText className="w-4 h-4" />
                  <h2 className="text-sm font-light truncate max-w-md">{reportData.session?.topic}</h2>
                </div>
                <div className="flex gap-2">
                  <button onClick={handleCopy} className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono border border-[var(--border)] rounded-md hover:bg-[var(--panel-hover)] transition-colors">
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    Copy Markdown
                  </button>
                  <button onClick={handleDownloadMd} className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono border border-[var(--border)] rounded-md hover:bg-[var(--panel-hover)] transition-colors">
                    <Download className="w-3 h-3" />
                    .md
                  </button>
                  <button onClick={handleDownloadBibtex} className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono border border-[var(--border)] rounded-md hover:bg-[var(--panel-hover)] transition-colors">
                    <Download className="w-3 h-3" />
                    BibTeX
                  </button>
                </div>
              </header>
              <div className="flex-1 overflow-y-auto p-8 lg:p-12">
                <div className="max-w-3xl mx-auto prose prose-invert prose-neutral font-light">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {reportData.report || 'No report content available.'}
                  </ReactMarkdown>
                </div>
              </div>
            </>
          ) : (
             <div className="flex-1 flex items-center justify-center text-neutral-500 font-light">
               Report not found.
             </div>
          )
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-neutral-500 font-light p-8 text-center">
            <FileText className="w-8 h-8 mb-4 opacity-50" />
            <p>Select a session to view its report.</p>
          </div>
        )}
      </main>
    </div>
  );
}
