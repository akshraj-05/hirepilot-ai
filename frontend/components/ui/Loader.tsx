type LoaderProps = {
  label?: string;
  size?: "sm" | "md";
  className?: string;
};

/**
 * Accessible inline spinner for async UI states.
 */
export function Loader({
  label = "Loading",
  size = "md",
  className = "",
}: LoaderProps) {
  const dim = size === "sm" ? "h-5 w-5" : "h-8 w-8";
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 ${className}`}
      role="status"
      aria-live="polite"
    >
      <div
        className={`${dim} animate-spin rounded-full border-2 border-slate-200 border-t-[var(--hp-accent)]`}
      />
      <span className="text-sm text-[var(--hp-text-muted)]">{label}…</span>
    </div>
  );
}
