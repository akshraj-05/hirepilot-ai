type ProgressBarProps = {
  /** 0–100 */
  value: number;
  className?: string;
  /** Visually emphasize high scores */
  showLabel?: boolean;
};

/**
 * Linear progress for match score visualization.
 */
export function ProgressBar({
  value,
  className = "",
  showLabel = true,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));
  const barColor =
    clamped >= 80
      ? "bg-[var(--hp-shortlist)]"
      : clamped >= 60
        ? "bg-[var(--hp-review)]"
        : "bg-[var(--hp-reject)]";

  return (
    <div className={`w-full ${className}`}>
      <div className="mb-1 flex items-center justify-between gap-2">
        {showLabel && (
          <span className="text-xs font-medium text-[var(--hp-text-muted)]">
            Match
          </span>
        )}
        {showLabel && (
          <span className="text-sm font-semibold tabular-nums text-[var(--hp-text)]">
            {clamped}%
          </span>
        )}
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-[var(--hp-border)]"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
