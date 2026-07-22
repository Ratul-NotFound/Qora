'use client';
import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import Sidebar from '@/components/Sidebar';
import axios from 'axios';
import { Loader2, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), {
  ssr: false,
});

export default function GraphPage() {
  const [graphData, setGraphData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    const fetchGraphData = async () => {
      try {
        const sessionsRes = await axios.get('http://localhost:8000/api/sessions');
        const sessions = sessionsRes.data;
        if (sessions.length > 0) {
          const recentSession = sessions[0];
          const resultsRes = await axios.get(`http://localhost:8000/api/research/${recentSession.id}/results`);
          const data = resultsRes.data.intelligence?.graph_data;
          setGraphData(data);
        }
      } catch (error) {
        console.error('Failed to fetch graph data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchGraphData();
  }, []);

  const getNodeColor = (node: any) => {
    if (node.type === 'method') return '#ffffff';
    switch (node.source) {
      case 'arxiv': return '#22d3ee'; // cyan
      case 'semantic_scholar': return '#8b5cf6'; // violet
      case 'pubmed': return '#10b981'; // emerald
      case 'openalex': return '#f59e0b'; // amber
      case 'core': return '#f43f5e'; // rose
      default: return '#737373'; // neutral-500
    }
  };

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="flex h-screen bg-[var(--background)] text-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 relative">
        <header className="absolute top-0 left-0 right-0 z-10 p-6 pointer-events-none">
          <h1 className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
            Citation Graph
          </h1>
        </header>
        
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
          </div>
        ) : !graphData || (!graphData.nodes?.length && !graphData.edges?.length) ? (
          <div className="absolute inset-0 flex items-center justify-center text-neutral-500 font-light">
            No graph data available for the recent session.
          </div>
        ) : (
          <div className="w-full h-full">
             <ForceGraph3D
                graphData={graphData}
                nodeColor={getNodeColor}
                nodeVal={(node: any) => node.size || 1}
                nodeLabel="label"
                onNodeClick={handleNodeClick}
                backgroundColor="#080808"
                linkColor={() => 'rgba(255,255,255,0.1)'}
             />
          </div>
        )}

        <AnimatePresence>
          {selectedNode && (
            <motion.div
              initial={{ x: 300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 300, opacity: 0 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="absolute top-4 right-4 bottom-4 w-80 bg-[var(--panel)] border border-[var(--border)] rounded-lg p-6 flex flex-col shadow-2xl"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono flex items-center gap-2">
                  <Info className="w-3 h-3" /> Node Details
                </span>
                <button onClick={() => setSelectedNode(null)} className="text-neutral-500 hover:text-white">
                  &times;
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                <h2 className="text-lg font-light mb-2">{selectedNode.label || selectedNode.id}</h2>
                <div className="space-y-4 mt-6">
                  <div>
                    <div className="text-[10px] uppercase tracking-widest text-neutral-500 font-mono mb-1">Type</div>
                    <div className="text-sm text-neutral-300 capitalize">{selectedNode.type || 'Unknown'}</div>
                  </div>
                  {selectedNode.year && (
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-neutral-500 font-mono mb-1">Year</div>
                      <div className="text-sm text-neutral-300">{selectedNode.year}</div>
                    </div>
                  )}
                  {selectedNode.source && (
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-neutral-500 font-mono mb-1">Source</div>
                      <div className="text-sm text-neutral-300 capitalize">{selectedNode.source.replace('_', ' ')}</div>
                    </div>
                  )}
                  {selectedNode.citations !== undefined && (
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-neutral-500 font-mono mb-1">Citations</div>
                      <div className="text-sm text-neutral-300">{selectedNode.citations}</div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
