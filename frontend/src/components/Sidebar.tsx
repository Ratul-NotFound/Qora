"use client";

import { Search, Map, FileText, Settings, FlaskConical } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Discover", href: "/", icon: Search },
    { name: "Knowledge Graph", href: "/graph", icon: Map },
    { name: "Literature Review", href: "/reports", icon: FileText },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <nav className="glass-panel w-64 m-4 rounded-2xl p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center gap-3 mb-12">
          <div className="p-2 bg-blue-500/20 text-blue-400 rounded-xl">
            <FlaskConical size={28} />
          </div>
          <span className="text-xl font-bold tracking-wider">QORA</span>
        </div>

        <ul className="space-y-2">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <li key={link.name}>
                <Link
                  href={link.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                    isActive
                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <Icon size={20} />
                  <span className="font-medium">{link.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="text-xs text-slate-500 text-center">
        <p>Qora Research AI</p>
        <p>Version 2.0.0 (Cloud)</p>
      </div>
    </nav>
  );
}
