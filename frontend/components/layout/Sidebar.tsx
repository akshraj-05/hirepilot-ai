"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "@/components/ThemeProvider";

const nav = [
  { href: "/", label: "Dashboard", icon: "◆" },
  { href: "/jobs", label: "Job postings", icon: "▤" },
  { href: "/upload", label: "Upload & analyze", icon: "↑" },
  { href: "/candidates", label: "Candidates", icon: "≡" },
  { href: "/meetings", label: "Meetings", icon: "◷" },
  { href: "/integrations", label: "Integrations", icon: "◇" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggle } = useTheme();

  function handleLogout() {
    localStorage.removeItem("hp_user");
    document.cookie = "hp_auth=; path=/; max-age=0";
    router.replace("/login");
  }

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-[var(--hp-sidebar)] text-[var(--hp-sidebar-text)]">
      <div className="flex h-14 items-center gap-2 border-b border-white/10 px-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--hp-accent)] text-sm font-bold text-white">
          HP
        </span>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-[var(--hp-sidebar-active)]">HirePilot AI</div>
          <div className="text-[11px] opacity-80">Hiring workspace</div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 p-3">
        {nav.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                active
                  ? "bg-white/10 font-medium text-[var(--hp-sidebar-active)]"
                  : "hover:bg-white/5 hover:text-[var(--hp-sidebar-active)]"
              }`}
            >
              <span className="w-4 text-center text-xs opacity-70">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3 flex flex-col gap-0.5">
        <button
          onClick={toggle}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-[var(--hp-sidebar-text)] transition-colors hover:bg-white/5 hover:text-[var(--hp-sidebar-active)]"
        >
          <span className="w-4 text-center text-xs opacity-70">
            {theme === "dark" ? "☀" : "☾"}
          </span>
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-[var(--hp-sidebar-text)] transition-colors hover:bg-white/5 hover:text-[var(--hp-sidebar-active)]"
        >
          <span className="w-4 text-center text-xs opacity-70">→</span>
          Sign out
        </button>
      </div>
    </aside>
  );
}
