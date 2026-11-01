import type { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
  /** Optional title row above children */
  title?: string;
  /** Subtle description under title */
  description?: string;
};

/**
 * Reusable elevated surface for dashboard sections.
 */
export function Card({ children, className = "", title, description }: CardProps) {
  return (
    <section
      className={`rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] p-5 shadow-[var(--hp-shadow)] ${className}`}
    >
      {(title || description) && (
        <header className="mb-4">
          {title && (
            <h2 className="text-sm font-semibold tracking-tight text-[var(--hp-text)]">
              {title}
            </h2>
          )}
          {description && (
            <p className="mt-0.5 text-sm text-[var(--hp-text-muted)]">
              {description}
            </p>
          )}
        </header>
      )}
      {children}
    </section>
  );
}
