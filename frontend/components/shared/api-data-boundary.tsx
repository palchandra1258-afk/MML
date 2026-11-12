import type { ReactNode } from "react";

/** Keeps an API record's source visible when a view presents its contents. */
export function ApiDataBoundary({ children, requestId, timestamp }: { children: ReactNode; requestId?: string | null; timestamp?: string | null }) {
  return <div className="api-data-boundary"><div className="api-data-meta"><span className="data-source data-source--api"><span className="data-source-dot" aria-hidden="true"/>Live API data</span>{timestamp && <time dateTime={timestamp}>Record timestamp: {timestamp}</time>}{requestId && <span>Request {requestId}</span>}</div>{children}</div>;
}
