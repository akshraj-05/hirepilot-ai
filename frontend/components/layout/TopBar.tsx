import type { ReactNode } from "react";

type TopBarProps = {
  title: string;
  subtitle?: string;
  /** Optional content rendered on the right side (e.g. action buttons) */
  actions?: ReactNode;
};

/**
 * Page header area (top of main column, next to optional actions).
 */
export function TopBar({ title, subtitle, actions }: TopBarProps) {
  return (
    <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-[var(--hp-text)]">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm text-[var(--hp-text-muted)]">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  );
}
