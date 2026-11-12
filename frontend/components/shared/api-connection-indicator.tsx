"use client";

import { useApiHealth } from "@/hooks/use-api-health";

const labels = {
  connecting: "Connecting",
  connected: "Connected",
  disconnected: "Disconnected",
  error: "Connection error",
  mock: "Mock mode",
} as const;

export function ApiConnectionIndicator() {
  const { state, health, message, checkedAt, retry } = useApiHealth();
  const label = state === "connected" && health?.status === "degraded" ? "Connected · degraded" : labels[state];
  const timestamp = checkedAt ? ` Health check time: ${checkedAt}.` : "";
  const detail = `${message ?? "Checking backend connection."}${timestamp}`;
  const canRetry = state === "disconnected" || state === "error";
  return <div className={`connection-control connection-control--${state}`} title={detail} aria-live="polite" aria-atomic="true">
    <span className="connection-dot" aria-hidden="true"/>
    <span className="connection-label">{label}</span>
    {canRetry && <button type="button" className="connection-retry" onClick={retry}>Retry</button>}
  </div>;
}
