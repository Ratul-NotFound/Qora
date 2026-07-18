"use client";

import { useState } from "react";
import { Search, Sparkles, Loader2, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SearchBoxProps {
  onSearch: (query: string, sources: string[]) => void;
  isSearching: boolean;
}

export default function SearchBox({ onSearch, isSearching }: SearchBoxProps) {
  const [query, setQuery] = useState("");
  const [focusMode, setFocusMode] = useState("all");

  const modes = [
    { id: "all", label: "All Sources", sources: ["arxiv", "semantic_scholar", "pubmed", "openalex", "core"] },
    { id: "cs", label: "Computer Science", sources: ["arxiv", "semantic_scholar", "openalex", "core"] },
    { id: "bio", label: "Bio / Medicine", sources: ["pubmed", "semantic_scholar", "openalex"] },
    { id: "physics", label: "Physics / Math", sources: ["arxiv", "semantic_scholar"] },
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isSearching) return;
    
    const activeMode = modes.find(m => m.id === focusMode) || modes[0];
    onSearch(query, activeMode.sources);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSearch} className="w-full relative">
        <div className="bg-[var(--panel)] border border-[var(--border)] rounded-xl shadow-lg transition-all duration-300 focus-within:border-[var(--border-focus)] focus-within:shadow-[0_0_40px_rgba(255,255,255,0.015)] p-2">
          <div className="flex items-center">
            <div className="pl-3 pr-2 text-neutral-500">
              <Sparkles size={16} strokeWidth={2} className="text-neutral-400" />
            </div>
            
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isSearching}
              placeholder="Ask anything, find literature, detect research gaps..."
              className="w-full bg-transparent text-white px-2 py-3 outline-none placeholder:text-neutral-600 text-sm md:text-base font-light disabled:opacity-50"
            />
            
            <AnimatePresence>
              {query && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  type="submit"
                  disabled={isSearching}
                  className="bg-neutral-100 hover:bg-white text-black p-2.5 rounded-lg transition-all duration-200 flex items-center justify-center disabled:opacity-50"
                >
                  {isSearching ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <ArrowRight size={16} strokeWidth={2.5} />
                  )}
                </motion.button>
              )}
            </AnimatePresence>
          </div>

          <div className="flex items-center justify-between border-t border-[var(--border)] mt-2 pt-2 px-2 text-xs">
            <div className="flex items-center gap-1.5 overflow-x-auto py-1">
              {modes.map((mode) => (
                <button
                  key={mode.id}
                  type="button"
                  disabled={isSearching}
                  onClick={() => setFocusMode(mode.id)}
                  className={`px-2.5 py-1 rounded-md transition-all ${
                    focusMode === mode.id
                      ? "bg-neutral-800 text-white font-medium"
                      : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900"
                  } disabled:opacity-50`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
            <div className="hidden md:flex items-center gap-1 text-neutral-600 font-mono scale-95 select-none">
              <span>Enter</span>
              <span className="text-[10px] bg-neutral-900 px-1.5 py-0.5 rounded border border-neutral-800">↵</span>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
