'use client';

import { useState, useEffect, useMemo } from 'react';
import Sidebar from '@/components/Sidebar';
import axios from 'axios';
import { Loader2, AlertTriangle, Lightbulb } from 'lucide-react';
import { motion } from 'framer-motion';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function GapsPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const sessionsRes = await axios.get(`${API_URL}/api/sessions`);
        const sessions = sessionsRes.data;
        if (sessions.length > 0) {
          const recentSession = sessions[0];
          const resultsRes = await axios.get(`${API_URL}/api/research/${recentSession.id}/results`);
          setData(resultsRes.data.intelligence);
        }
      } catch (error) {
        console.error('Failed to fetch gaps data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const timelineData = useMemo(() => {
    if (!data?.graph_data?.nodes) return [];
    const counts: Record<number, number> = {};
    data.graph_data.nodes.forEach((node: any) => {
      if (node.type === 'paper' && node.year) {
        counts[node.year] = (counts[node.year] || 0) + 1;
      }
    });
    return Object.entries(counts).map(([year, count]) => ({ year: parseInt(year), count })).sort((a, b) => a.year - b.year);
  }, [data]);

  const maxCount = timelineData.length ? Math.max(...timelineData.map(d => d.count)) : 1;

  const getSeverityColor = (sev: string) => {
    switch(sev?.toLowerCase()) {
      case 'high': return 'text-red-400 bg-red-400/10 border-red-400/20';
      case 'medium': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
      case 'low': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
      default: return 'text-neutral-400 bg-neutral-400/10 border-neutral-400/20';
    }
  };

  return (
    <div className="flex h-screen bg-[var(--background)] text-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col relative h-full">
        <header className="p-6 border-b border-[var(--border)] shrink-0">
          <h1 className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
            Gaps & Trends
          </h1>
        </header>

        {loading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
          </div>
        ) : !data ? (
          <div className="flex-1 flex items-center justify-center text-neutral-500 font-light">
            No intelligence data available.
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto p-6 md:p-8 flex flex-col gap-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 shrink-0">
              {/* Gaps Section */}
              <section className="flex flex-col gap-4">
                <div className="flex items-center gap-2 text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
                  <AlertTriangle className="w-3 h-3" /> Literature Gaps
                </div>
                <div className="space-y-4">
                  {data.gaps?.length > 0 ? data.gaps.map((gap: any, i: number) => (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                      key={i} className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-5"
                    >
                      <div className="flex justify-between items-start mb-3">
                        <h3 className="text-sm font-medium">{gap.gap}</h3>
                        <span className={`text-[9px] uppercase tracking-widest font-mono px-2 py-0.5 rounded-full border ${getSeverityColor(gap.severity)}`}>
                          {gap.severity}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 font-light leading-relaxed">{gap.description}</p>
                    </motion.div>
                  )) : (
                    <div className="text-sm text-neutral-500 font-light p-4 border border-[var(--border)] rounded-lg bg-[var(--panel)]">No gaps identified.</div>
                  )}
                </div>
              </section>

              {/* Hypotheses Section */}
              <section className="flex flex-col gap-4">
                <div className="flex items-center gap-2 text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
                  <Lightbulb className="w-3 h-3" /> Hypotheses
                </div>
                <div className="space-y-4">
                  {data.hypotheses?.length > 0 ? data.hypotheses.map((hyp: any, i: number) => (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 + 0.2 }}
                      key={i} className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-5"
                    >
                      <h3 className="text-sm font-medium mb-2">{hyp.hypothesis}</h3>
                      <p className="text-xs text-neutral-400 font-light leading-relaxed mb-4">{hyp.rationale}</p>
                      
                      <div className="flex flex-wrap gap-2 mt-4">
                         <span className="text-[9px] font-mono px-2 py-1 bg-white/5 rounded text-neutral-300">
                           <span className="text-neutral-500 mr-1">Novelty:</span> {hyp.novelty}
                         </span>
                         <span className="text-[9px] font-mono px-2 py-1 bg-white/5 rounded text-neutral-300">
                           <span className="text-neutral-500 mr-1">Feasibility:</span> {hyp.feasibility}
                         </span>
                         <span className="text-[9px] font-mono px-2 py-1 bg-white/5 rounded text-neutral-300">
                           <span className="text-neutral-500 mr-1">Impact:</span> {hyp.impact}
                         </span>
                      </div>
                    </motion.div>
                  )) : (
                    <div className="text-sm text-neutral-500 font-light p-4 border border-[var(--border)] rounded-lg bg-[var(--panel)]">No hypotheses generated.</div>
                  )}
                </div>
              </section>
            </div>

            {/* Timeline Section */}
            <section className="mt-8 flex flex-col gap-4">
              <div className="text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
                Publication Timeline
              </div>
              <div className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-6 h-48 flex items-end justify-between gap-1 overflow-x-auto">
                {timelineData.length > 0 ? timelineData.map((d: any, i: number) => {
                  const heightPercentage = Math.max((d.count / maxCount) * 100, 5);
                  return (
                    <div key={d.year} className="flex flex-col items-center gap-2 group min-w-[30px] flex-1">
                      <div className="relative w-full flex justify-center h-full items-end">
                        <div 
                          className="w-full max-w-[40px] bg-neutral-700 group-hover:bg-neutral-500 transition-colors rounded-t-sm"
                          style={{ height: `${heightPercentage}%` }}
                        />
                        <div className="absolute -top-6 text-[10px] font-mono text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity">
                          {d.count}
                        </div>
                      </div>
                      <div className="text-[9px] font-mono text-neutral-500 transform -rotate-45 origin-top-left mt-2">
                        {d.year}
                      </div>
                    </div>
                  );
                }) : (
                   <div className="w-full h-full flex items-center justify-center text-sm text-neutral-500 font-light">
                     No timeline data available.
                   </div>
                )}
              </div>
            </section>

          </div>
        )}
      </main>
    </div>
  );
}
