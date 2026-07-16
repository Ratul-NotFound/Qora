"use client";

import { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function SearchBox() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    // TODO: Connect to backend WebSocket API
    setTimeout(() => {
      setIsSearching(false);
    }, 2000);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSearch} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
        
        <div className="relative flex items-center bg-slate-900/80 backdrop-blur-xl border border-slate-700 rounded-2xl overflow-hidden shadow-2xl">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="E.g., Quantum error correction in surface codes..."
            className="w-full bg-transparent text-slate-200 px-6 py-5 outline-none placeholder:text-slate-500 text-lg"
          />
          <button
            type="submit"
            disabled={isSearching}
            className="flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white px-8 py-5 transition-colors font-medium border-l border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed min-w-[140px]"
          >
            {isSearching ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              >
                <Loader2 size={24} />
              </motion.div>
            ) : (
              <>
                <Search size={20} className="mr-2" />
                Analyze
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
