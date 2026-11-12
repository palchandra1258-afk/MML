"use client";

import { useEffect, useMemo, useState } from "react";
import { DemoDashboard } from "@/components/dashboard/demo-dashboard";
import { SectionHeading } from "@/components/shared/section-heading";
import { ApiDataBoundary } from "@/components/shared/api-data-boundary";
import { DataSourceLabel, EmptyState, ErrorState, LoadingState } from "@/components/shared/data-states";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiHealth } from "@/hooks/use-api-health";
import { getApiConfig } from "@/lib/api/config";
import { ApiError } from "@/lib/api/errors";
import { learnerService } from "@/lib/services/learner.service";
import type { ApiPage, JsonValue, LearnerSummary } from "@/lib/api/types";

function readModuleField(value: Record<string, JsonValue> | undefined, field: string): JsonValue | undefined {
  const result = value?.[field];
  return typeof result === "string" || typeof result === "number" || typeof result === "boolean" || result === null ? result : undefined;
}

const modules = [
  ["phase9_behavioral_state", "Behavioral states"],
  ["phase10_evidence", "Evidence records"],
  ["phase10_grouping", "Evidence grouping"],
  ["phase11_cognitive_state", "Cognitive estimates"],
  ["phase12_representation", "Representation plans"],
  ["phase13_trajectory", "Trajectory service"],
  ["model_inference", "Model inference"],
] as const;

type LearnerIndexResult =
  | { key: string; kind: "success"; page: ApiPage<LearnerSummary> | undefined; requestId: string | null }
  | { key: string; kind: "error"; error: unknown; requestId: string | null };

function ApiDashboard() {
  const { state: connection, health } = useApiHealth();
  const config = getApiConfig();
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<LearnerIndexResult | null>(null);
  const requestKey = `${attempt}:${health?.timestamp ?? ""}`;

  useEffect(() => {
    if (connection !== "connected" || config.configurationError || !config.baseUrl) return;
    const controller = new AbortController();
    void learnerService.list({ limit: 5, offset: 0, signal: controller.signal }).then((response) => {
      if (controller.signal.aborted) return;
      setResult({ key: requestKey, kind: "success", page: response.data, requestId: response.requestId });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      setResult({ key: requestKey, kind: "error", error, requestId: error instanceof ApiError ? error.requestId : null });
    });
    return () => controller.abort();
  }, [connection, config.baseUrl, config.configurationError, requestKey]);

  const currentResult = result?.key === requestKey ? result : null;
  const page = currentResult?.kind === "success" ? currentResult.page : undefined;
  const sourcePreview = useMemo(() => {
    if (!page) return [];
    return Array.from(new Set(page.items.flatMap((learner) => learner.available_data))).sort();
  }, [page]);

  const moduleData = health?.modules ?? {};
  return <div className="api-dashboard">
    <div className="api-dashboard-header"><div><p className="eyebrow">RESEARCH WORKSPACE</p><h2>Backend overview<span className="welcome-period">.</span></h2><p>Live index availability from the MCP-RI API. Learner objectives and executable learning activities are not exposed by the current API.</p></div><DataSourceLabel kind={connection === "connected" ? "api" : "unavailable"} detail={connection === "connected" ? "Phase 14 API" : "Phase 14 API not connected"}/></div>

    {connection === "connecting" && <LoadingState label="Checking backend connection"/>}
    {connection === "disconnected" && <EmptyState title="Backend is disconnected">Set <code>NEXT_PUBLIC_API_BASE_URL</code> in <code>frontend/.env.local</code> and start the FastAPI service. No demonstration data is shown unless mock mode is explicitly enabled.</EmptyState>}
    {connection === "error" && <EmptyState title="Backend health check needs attention">The health endpoint did not return a valid response. Use the retry control in the top bar. API data is not replaced with mock records.</EmptyState>}

    {connection === "connected" && <>
      <ApiDataBoundary requestId={currentResult?.kind === "success" ? currentResult.requestId : null}>
        <section className="api-index-card panel">
          <div className="api-index-main"><span className="api-index-icon" aria-hidden="true">◎</span><div><span className="eyebrow">INDEXED LEARNER RECORDS</span><strong className="api-index-value">{page ? page.total.toLocaleString() : "—"}</strong><span className="api-index-description">Available through the research artifact index. These are pseudonymous records, not active learner sessions.</span></div></div>
          <div className="api-index-meta"><StatusBadge tone={health?.status === "healthy" ? "teal" : "amber"} dot>{health?.status === "healthy" ? "API healthy" : "API reachable · degraded"}</StatusBadge><span>API version {health?.api_version ?? "unknown"}</span>{health?.timestamp && <time dateTime={health.timestamp}>Health response {health.timestamp}</time>}</div>
        </section>
      </ApiDataBoundary>

      <div className="api-dashboard-grid">
        <section className="panel api-module-panel">
          <SectionHeading eyebrow="Service readiness" title="Research modules" detail="Availability and counts come from the backend health response."/>
          <div className="api-module-list">{modules.map(([key, label]) => {
            const item = moduleData[key];
            const available = readModuleField(item, "available");
            const count = readModuleField(item, "record_count");
            const mode = readModuleField(item, "mode");
            const isAvailable = available === true;
            return <div className="api-module-row" key={key}><span className={`module-state-dot ${isAvailable ? "module-state-dot--ready" : "module-state-dot--off"}`}/><div className="api-module-name"><strong>{label}</strong><span>{typeof mode === "string" ? mode.replaceAll("_", " ") : "Status reported by API"}</span></div><div className="api-module-result">{typeof count === "number" && <strong>{count.toLocaleString()}</strong>}<span className={`module-state-label ${isAvailable ? "module-state-label--ready" : ""}`}>{isAvailable ? "Available" : available === false ? "Unavailable" : "Unknown"}</span></div></div>;
          })}</div>
        </section>

        <section className="panel api-data-panel">
          <SectionHeading eyebrow="Learner index" title="Data availability preview" detail="A sample of the first five indexed summaries. No learner identifiers are shown here."/>
          {!currentResult && <LoadingState label="Loading indexed learner summaries"/>}
          {currentResult?.kind === "error" && <ErrorState error={currentResult.error} requestId={currentResult.requestId} onRetry={() => setAttempt((value) => value + 1)}/>}
          {currentResult?.kind === "success" && currentResult.page && currentResult.page.total === 0 && <EmptyState title="No learner records are indexed">The backend returned an empty learner index.</EmptyState>}
          {currentResult?.kind === "success" && !currentResult.page && <EmptyState title="No response data was returned">The learners endpoint returned an empty response body.</EmptyState>}
          {currentResult?.kind === "success" && page && page.total > 0 && <>
            <div className="preview-summary"><strong>{page.items.length}</strong><span>summaries in this preview · {page.total.toLocaleString()} total indexed</span></div>
            <div className="availability-tags">{sourcePreview.length > 0 ? sourcePreview.map((source) => <span className="availability-tag" key={source}>{source.replaceAll("_", " ")}</span>) : <span className="muted-inline">No data categories were returned in this preview.</span>}</div>
            <p className="api-data-caveat">The API serves saved research artifacts. It does not create lesson objectives, infer active study, or serve learning content.</p>
          </>}
        </section>
      </div>

      <section className="api-capability-note"><span className="capability-note-mark">i</span><div><strong>Learning content is not connected.</strong><p>The current backend supports research artifact lookup and limited trajectory management. It does not expose interaction submission, content delivery, representation execution, or diversion/resumption mutations.</p></div></section>
    </>}
  </div>;
}

export function DashboardClient() {
  const config = getApiConfig();
  if (config.mode === "mock") return <DemoDashboard />;
  return <ApiDashboard />;
}
