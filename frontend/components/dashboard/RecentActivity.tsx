import type { ActivityItem } from "@/utils/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";

type RecentActivityProps = {
  items: ActivityItem[];
  className?: string;
};

/**
 * Timeline-style list for dashboard “recent activity”.
 */
export function RecentActivity({ items, className = "" }: RecentActivityProps) {
  return (
    <Card
      title="Recent activity"
      description="Latest AI reviews and team actions."
      className={`flex min-h-0 flex-col ${className}`}
    >
      <ul className="min-h-0 flex-1 space-y-4">
        {items.map((a) => (
          <li
            key={a.id}
            className="flex gap-3 border-b border-[var(--hp-border)] pb-4 last:border-0 last:pb-0"
          >
            <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[var(--hp-accent)]" />
            <div className="min-w-0 flex-1">
              <p className="text-sm text-[var(--hp-text)]">{a.message}</p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <span className="text-xs text-[var(--hp-text-muted)]">
                  {a.timeLabel}
                </span>
                {a.status && <Badge status={a.status} />}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
