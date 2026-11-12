"use client";

import { EmptyState, LoadingState } from "@/components/shared/data-states";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiHealth } from "@/hooks/use-api-health";
import type { HealthData, JsonValue } from "@/lib/api/types";

const moduleLabels: Record<string, string> = {
  phase9_behavioral_state: "Behavioral state",
  phase10_evidence: "Evidence records",
  phase10_grouping: "Evidence grouping",
  phase11_cognitive_state: "Cognitive state",
  phase12_representation: "Representation planning",
  phase13_trajectory: "Trajectory service",
  model_inference: "Model inference",
};

function readString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function readCount(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toLocaleString() : "Not reported";
}

function formatTimestamp(value: string | undefined): { dateTime: string; label: string } | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return {
    dateTime: date.toISOString(),
    label: date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "medium" }),
  };
}

function moduleFields(value: unknown): Record<string, JsonValue> {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, JsonValue> : {};
}

function moduleAvailability(value: Record<string, JsonValue>): { label: string; tone: "teal" | "amber" } {
  if (value.available === true) return { label: "Available", tone: "teal" };
  if (value.available === false) return { label: "Unavailable", tone: "amber" };
  return { label: "Not reported", tone: "amber" };
}

function HealthModules({ health }: { health: HealthData }) {
  const modules = Object.entries(health.modules);
  if (!modules.length) return <EmptyState title="No module status was reported">The API health response did not include module entries.</EmptyState>;
  return <div className="system-status-table-wrap" role="region" aria-label="Research module readiness table" tabIndex={0}><table className="system-status-table"><caption>Module availability reported by the API health endpoint</caption><thead><tr><th scope="col">Module</th><th scope="col">Availability</th><th scope="col">Mode</th><th scope="col">Indexed records</th></tr></thead><tbody>{modules.map(([key, rawFields]) => {
    const fields = moduleFields(rawFields);
    const status = moduleAvailability(fields);
    return <tr key={key}><th scope="row">{moduleLabels[key] ?? key.replaceAll("_", " ")}</th><td><StatusBadge tone={status.tone} dot>{status.label}</StatusBadge></td><td>{readString(fields.mode)?.replaceAll("_", " ") ?? "Not reported"}</td><td>{readCount(fields.record_count)}</td></tr>;
  })}</tbody></table></div>;
}

export function SystemStatusPage() {
  const { state, health, message, checkedAt, retry } = useApiHealth();
  const healthTimestamp = formatTimestamp(checkedAt ?? health?.timestamp);
  const statusLabel = state === "connected" && health?.status === "degraded" ? "Connected · degraded" : state === "connected" ? "Connected" : state === "mock" ? "Synthetic mode" : state === "connecting" ? "Connecting" : state === "disconnected" ? "Disconnected" : "Connection error";
  const tone = state === "connected" && health?.status === "healthy" ? "teal" : "amber";

  return <div className="system-status-page">
    <header className="system-status-heading"><div><p className="eyebrow">PLATFORM READINESS</p><h2>System status<span className="welcome-period">.</span></h2><p>Inspect the latest shared API health result and the module availability reported by the backend.</p></div><StatusBadge tone={tone} dot>{statusLabel}</StatusBadge></header>

    <section className="panel system-status-summary">
      <SectionHeading eyebrow="SHARED HEALTH CHECK" title="Backend connection" detail="This page uses the same health check as the top-bar indicator; opening it does not issue a second request."/>
      {state === "connecting" && <LoadingState label="Checking backend health"/>}
      {state === "mock" && <EmptyState title="Live API status is unavailable in mock mode">Mock mode sends no health request. The synthetic dashboard remains separate from live learner and module records.</EmptyState>}
      {(state === "disconnected" || state === "error") && <EmptyState title={state === "disconnected" ? "Backend is disconnected" : "Backend health could not be confirmed"} action={<button type="button" className="button button--secondary" onClick={retry}>Retry health check</button>}>{message ?? "The health endpoint has not returned a valid response."}</EmptyState>}
      {state === "connected" && health && <><div className="system-status-facts"><div><span>API version</span><strong>{health.api_version}</strong></div><div><span>Database</span><strong>{health.database === "available" ? "Available" : "Unavailable"}</strong></div><div><span>Health state</span><strong>{health.status === "healthy" ? "Healthy" : "Degraded"}</strong></div><div><span>Health timestamp</span><strong>{healthTimestamp ? <time dateTime={healthTimestamp.dateTime}>{healthTimestamp.label}</time> : "Not reported"}</strong></div></div><p className="system-status-message">{message}</p></>}
    </section>

    {state === "connected" && health && <section className="panel system-status-modules">
      <SectionHeading eyebrow="BACKEND HEALTH RESPONSE" title="Research module readiness" detail="Availability, operating mode, and record counts are shown only when the health endpoint supplies them."/>
      <HealthModules health={health}/>
    </section>}
  </div>;
}
