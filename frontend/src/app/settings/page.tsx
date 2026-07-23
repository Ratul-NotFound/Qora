'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import axios from 'axios';
import { Loader2, Settings2, Activity, Search, Save, Check } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const [settings, setSettings] = useState({
    depth: 3,
    maxPapers: 50,
    sources: {
      arxiv: true,
      semantic_scholar: true,
      pubmed: true,
      openalex: true,
      core: true,
    }
  });

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const savedSettings = localStorage.getItem('qora_settings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (e) {}
    }

    const fetchHealth = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/health`);
        setHealth(res.data);
      } catch (error) {
        console.error('Failed to fetch health status:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
  }, []);

  const handleSave = () => {
    setSaving(true);
    localStorage.setItem('qora_settings', JSON.stringify(settings));
    setTimeout(() => setSaving(false), 500);
  };

  const StatusDot = ({ active }: { active: boolean }) => (
    <div className={`w-2 h-2 rounded-full ${active ? 'bg-emerald-500' : 'bg-red-500'}`} />
  );

  return (
    <div className="flex h-screen bg-[var(--background)] text-white overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <header className="p-6 border-b border-[var(--border)] sticky top-0 bg-[var(--background)] z-10">
          <h1 className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
            Platform Settings
          </h1>
        </header>

        <div className="max-w-4xl mx-auto p-6 md:p-12 space-y-12">
          
          {/* API Config */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
              <Settings2 className="w-3 h-3" /> API Configuration
            </div>
            <div className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-mono text-neutral-500 mb-2">Primary LLM</label>
                  <input 
                    type="text" 
                    readOnly 
                    value={health?.llm?.model || 'Loading...'} 
                    className="w-full bg-white/5 border border-[var(--border)] rounded p-2.5 text-sm font-light text-neutral-300 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-neutral-500 mb-2">Heavy LLM</label>
                  <input 
                    type="text" 
                    readOnly 
                    value={health?.llm?.heavy_model || 'Loading...'} 
                    className="w-full bg-white/5 border border-[var(--border)] rounded p-2.5 text-sm font-light text-neutral-300 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-mono text-neutral-500 mb-2">LLM Base URL</label>
                <input 
                  type="text" 
                  readOnly 
                  value={health?.llm?.base_url || 'Loading...'} 
                  className="w-full bg-white/5 border border-[var(--border)] rounded p-2.5 text-sm font-light text-neutral-300 focus:outline-none"
                />
              </div>
            </div>
          </section>

          {/* Database Status */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
              <Activity className="w-3 h-3" /> System Health
            </div>
            <div className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-6">
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-neutral-500">
                  <Loader2 className="w-4 h-4 animate-spin" /> Checking connections...
                </div>
              ) : health ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="flex items-center justify-between p-3 border border-[var(--border)] rounded bg-white/5">
                      <span className="text-sm font-light">API Server</span>
                      <StatusDot active={health.status === 'online'} />
                    </div>
                    <div className="flex items-center justify-between p-3 border border-[var(--border)] rounded bg-white/5">
                      <span className="text-sm font-light">PostgreSQL</span>
                      <StatusDot active={health.database === 'connected'} />
                    </div>
                    <div className="flex items-center justify-between p-3 border border-[var(--border)] rounded bg-white/5">
                      <span className="text-sm font-light">LLM API Key</span>
                      <StatusDot active={health.llm?.key_configured === true} />
                    </div>
                  </div>

                  {/* Source API Keys */}
                  <div className="pt-4 border-t border-[var(--border)]">
                    <div className="text-[10px] font-mono text-neutral-500 uppercase tracking-widest mb-3">Source API Keys</div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                      {health.sources && Object.entries(health.sources).map(([key, val]) => (
                        <div key={key} className="flex items-center justify-between p-2 border border-[var(--border)] rounded bg-white/5">
                          <span className="text-xs font-light capitalize">{key.replace('_', ' ')}</span>
                          <StatusDot active={val as boolean} />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-red-400 font-light flex items-center gap-2">
                  <StatusDot active={false} /> Could not connect to backend
                </div>
              )}
            </div>
          </section>

          {/* Search Defaults */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 text-neutral-400 font-mono text-[10px] uppercase tracking-widest">
              <Search className="w-3 h-3" /> Search Defaults
            </div>
            <div className="bg-[var(--panel)] border border-[var(--border)] rounded-lg p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div>
                    <label className="flex justify-between text-xs font-mono text-neutral-500 mb-2">
                      <span>Research Depth</span>
                      <span>{settings.depth}</span>
                    </label>
                    <input 
                      type="range" 
                      min="1" max="5" 
                      value={settings.depth}
                      onChange={(e) => setSettings({...settings, depth: parseInt(e.target.value)})}
                      className="w-full accent-white"
                    />
                  </div>
                  <div>
                    <label className="flex justify-between text-xs font-mono text-neutral-500 mb-2">
                      <span>Max Papers</span>
                      <span>{settings.maxPapers}</span>
                    </label>
                    <input 
                      type="range" 
                      min="10" max="100" step="10"
                      value={settings.maxPapers}
                      onChange={(e) => setSettings({...settings, maxPapers: parseInt(e.target.value)})}
                      className="w-full accent-white"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-xs font-mono text-neutral-500 mb-4">Enabled Sources</label>
                  <div className="space-y-3">
                    {Object.entries(settings.sources).map(([key, value]) => (
                      <label key={key} className="flex items-center gap-3 cursor-pointer group">
                        <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                          value ? 'bg-white border-white' : 'border-[var(--border)] group-hover:border-neutral-500'
                        }`}>
                          {value && <Check className="w-3 h-3 text-black" strokeWidth={3} />}
                        </div>
                        <span className="text-sm font-light capitalize text-neutral-300">{key.replace('_', ' ')}</span>
                        <input 
                          type="checkbox"
                          className="hidden"
                          checked={value}
                          onChange={() => setSettings({
                            ...settings, 
                            sources: { ...settings.sources, [key]: !value }
                          })}
                        />
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              
              <div className="pt-6 border-t border-[var(--border)] flex justify-end">
                <button 
                  onClick={handleSave}
                  className="flex items-center gap-2 bg-white text-black px-4 py-2 rounded text-sm font-medium hover:bg-neutral-200 transition-colors"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin text-black" /> : <Save className="w-4 h-4" />}
                  Save Defaults
                </button>
              </div>
            </div>
          </section>

          <footer className="text-center pb-8 pt-4 border-t border-[var(--border)] mt-12">
             <div className="text-[10px] font-mono text-neutral-500">QORA RESEARCH AI v2.0.0</div>
          </footer>
        </div>
      </main>
    </div>
  );
}
