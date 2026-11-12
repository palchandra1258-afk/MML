import type { ReactNode } from "react";
import { safeErrorMessage } from "@/lib/api/errors";

export function LoadingState({ label = "Loading data" }: { label?: string }) {
  return <div className="data-state data-state--loading" role="status"><span className="loading-indicator" aria-hidden="true"/><div><strong>{label}</strong><span>Please wait while the connected source responds.</span></div></div>;
}

export function ErrorState({ error, onRetry, requestId }: { error: unknown; onRetry?: () => void; requestId?: string | null }) {
  return <div className="data-state data-state--error" role="alert"><span className="data-state-icon" aria-hidden="true">!</span><div className="data-state-copy"><strong>We couldn’t load this data</strong><span>{safeErrorMessage(error)}</span>{requestId && <small>Request ID: {requestId}</small>}</div>{onRetry && <button type="button" className="button button--secondary data-state-action" onClick={onRetry}>Retry</button>}</div>;
}

export function NotFoundState({ error, onRetry, requestId }: { error: unknown; onRetry?: () => void; requestId?: string | null }) {
  return <div className="data-state data-state--error" role="alert"><span className="data-state-icon" aria-hidden="true">!</span><div className="data-state-copy"><strong>The requested API resource was not found</strong><span>{safeErrorMessage(error)}</span>{requestId && <small>Request ID: {requestId}</small>}</div>{onRetry && <button type="button" className="button button--secondary data-state-action" onClick={onRetry}>Retry</button>}</div>;
}

export function EmptyState({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return <div className="data-state data-state--empty"><span className="data-state-icon" aria-hidden="true">i</span><div className="data-state-copy"><strong>{title}</strong><span>{children}</span></div>{action && <div className="data-state-action">{action}</div>}</div>;
}

export function DataSourceLabel({ kind, detail }: { kind: "api" | "demo" | "unavailable"; detail?: string }) {
  const label = kind === "api" ? "Live API data" : kind === "demo" ? "Synthetic demonstration" : "Unavailable";
  return <span className={`data-source data-source--${kind}`}><span className="data-source-dot" aria-hidden="true"/>{label}{detail && <span className="data-source-detail">· {detail}</span>}</span>;
}

export function LastUpdated({ timestamp }: { timestamp?: string | null }) {
  if (!timestamp) return null;
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return null;
  return <time className="last-updated" dateTime={date.toISOString()}>Updated {date.toLocaleString()}</time>;
}
