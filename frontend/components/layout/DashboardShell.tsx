import type { ReactNode } from "react";
import Link from "next/link";
import { Sidebar } from "./Sidebar";
import { ChatWidget } from "@/components/chat/ChatWidget";

const mobileLinks = [
  { href: "/", label: "Home" },
  { href: "/jobs", label: "Jobs" },
  { href: "/upload", label: "Upload" },
  { href: "/candidates", label: "Candidates" },
  { href: "/meetings", label: "Meetings" },
  { href: "/integrations", label: "Integrations" },
];

type DashboardShellProps = {
  children: ReactNode;
};

/**
 * App-wide dashboard layout: fixed sidebar + scrollable main.
 */
export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden md:flex hp-no-print">
        <Sidebar />
      </div>
      <div className="flex flex-1 flex-col overflow-hidden md:border-l md:border-[var(--hp-border)]">
        <div className="border-b border-[var(--hp-border)] bg-[var(--hp-sidebar)] md:hidden">
          <div className="flex items-center justify-between px-4 py-3">
            <span className="text-sm font-semibold text-white">HirePilot AI</span>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-2 pb-2">
            {mobileLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="shrink-0 rounded-md bg-white/10 px-3 py-1.5 text-xs font-medium text-white hover:bg-white/20"
              >
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">{children}</main>
      </div>

      {/* Chat widget floats over all dashboard pages */}
      <div className="hp-no-print">
        <ChatWidget />
      </div>
    </div>
  );
}
