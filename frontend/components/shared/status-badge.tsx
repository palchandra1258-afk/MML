import type { ReactNode } from "react";

export function StatusBadge({ children, tone = "neutral", dot = false }: { children: ReactNode; tone?: "neutral" | "teal" | "amber" | "purple"; dot?: boolean }) {
  return <span className={`status-badge status-badge--${tone}`}>{dot && <span className="status-dot"/>}{children}</span>;
}
