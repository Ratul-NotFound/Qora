"use client";

import { Search, Map, FileText, Settings, Compass, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Discover", href: "/", icon: Search },
    { name: "Citation Graph", href: "/graph", icon: Map },
    { name: "Research Review", href: "/reports", icon: FileText },
    { name: "Gaps & Trends", href: "/gaps", icon: Compass },
    { name: "System Settings", href: "/settings", icon: Settings },
  ];

  return (
    <nav className="w-60 h-screen border-r border-[var(--border)] bg-[var(--background)] flex flex-col justify-between p-5 select-none">
      <div className="space-y-6">
        <div className="flex items-center gap-2.5 px-2">
          <div className="w-5 h-5 bg-white rounded-sm flex items-center justify-center">
            <span className="text-[10px] font-bold text-black tracking-tighter">Q</span>
          </div>
          <span className="text-sm font-semibold tracking-wide uppercase text-white font-mono">QORA</span>
        </div>

        <div className="space-y-1">
          <div className="px-2 text-[10px] font-semibold text-neutral-600 uppercase tracking-widest mb-2">Research Workspace</div>
          <ul className="space-y-0.5">
            {links.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md transition-all text-xs md:text-sm font-medium ${
                      isActive
                        ? "bg-neutral-900 text-white border-l-2 border-white"
                        : "text-neutral-400 hover:bg-neutral-950 hover:text-white"
                    }`}
                  >
                    <Icon size={15} className={isActive ? "text-white" : "text-neutral-500"} />
                    <span>{link.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      <div className="space-y-3">
        <div className="p-3 bg-[var(--panel)] border border-[var(--border)] rounded-lg text-xs">
          <div className="flex items-center gap-1.5 text-neutral-300 font-medium mb-1">
            <Sparkles size={12} className="text-amber-400" />
            <span>Local Cluster</span>
          </div>
          <p className="text-neutral-500 font-light leading-relaxed">
            FastAPI + Docker backend running locally. Ready to process PDFs.
          </p>
        </div>
      </div>
    </nav>
  );
}
