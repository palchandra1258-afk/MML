"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api/errors";
import type { ApiPage, LearnerDetail, LearnerSummary } from "@/lib/api/types";
import { learnerService } from "@/lib/services/learner.service";
import { useApiResource } from "@/hooks/use-api-resource";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import { ApiResourcePanel } from "@/components/learner/api-resource-panel";
import { ErrorState } from "@/components/shared/data-states";

const PAGE_SIZE = 20;

export function LearnerRecordPicker() {
  const { learner: selectedLearner, selectLearner } = useLearnerSelection();
  const [offset, setOffset] = useState(0);
  const [recordId, setRecordId] = useState("");
  const [lookup, setLookup] = useState<{ status: "idle" | "loading" | "success" } | { status: "error"; error: unknown }>({ status: "idle" });
  const lookupController = useRef<AbortController | null>(null);

  const loadIndex = useCallback((signal: AbortSignal) => learnerService.list({ limit: PAGE_SIZE, offset, signal }), [offset]);
  const { resource: index, retry: retryIndex } = useApiResource<ApiPage<LearnerSummary>>(`learner-index:${offset}`, loadIndex);

  useEffect(() => () => lookupController.current?.abort(), []);

  const openRecord = useCallback(async (rawId: string) => {
    const id = rawId.trim();
    if (!id) return;
    lookupController.current?.abort();
    const controller = new AbortController();
    lookupController.current = controller;
    setLookup({ status: "loading" });
    try {
      const response = await learnerService.get(id, controller.signal);
      if (controller.signal.aborted) return;
      if (!response.data) throw new Error("The learner endpoint returned no record.");
      const detail: LearnerDetail = response.data;
      selectLearner(detail);
      setRecordId(detail.learner_id);
      setLookup({ status: "success" });
    } catch (error) {
      if (controller.signal.aborted) return;
      setLookup({ status: "error", error });
    }
  }, [selectLearner]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void openRecord(recordId);
  };

  const page = index.status === "success" ? index.data : undefined;
  const selectedOnPage = page?.items.some((item) => item.learner_id === selectedLearner?.learner_id) ?? false;

  return <section className="learner-picker panel" aria-labelledby="record-picker-heading">
    <div className="learner-picker-heading">
      <div><p className="eyebrow">RESEARCH RECORD</p><h3 id="record-picker-heading">Choose a learner record</h3><p>These are pseudonymous dataset records, not authenticated learner accounts.</p></div>
      {page && <span className="learner-index-total">{page.total.toLocaleString()} indexed records</span>}
    </div>

    <div className="learner-picker-grid">
      <div className="learner-index-picker">
        <label htmlFor="learner-index-select">Browse index page</label>
        <select id="learner-index-select" value={selectedOnPage ? selectedLearner?.learner_id : ""} disabled={!page || page.items.length === 0 || lookup.status === "loading"} onChange={(event) => { if (event.target.value) void openRecord(event.target.value); }}>
          <option value="">{page ? "Choose a record from this page" : "Loading learner index…"}</option>
          {selectedLearner && !selectedOnPage && <option value={selectedLearner.learner_id}>{selectedLearner.learner_id} · selected record</option>}
          {page?.items.map((item) => <option value={item.learner_id} key={item.learner_id}>{item.learner_id} · {item.available_data.join(", ") || "no indexed data categories"}</option>)}
        </select>
        <div className="learner-index-pagination"><button type="button" className="button button--secondary" disabled={offset === 0 || index.status === "loading"} onClick={() => setOffset((current) => Math.max(0, current - PAGE_SIZE))}>Previous</button><span>{page ? `${page.offset + 1}–${Math.min(page.offset + page.items.length, page.total)} of ${page.total.toLocaleString()}` : "Index page"}</span><button type="button" className="button button--secondary" disabled={!page?.has_more || index.status === "loading"} onClick={() => setOffset((current) => current + PAGE_SIZE)}>Next</button></div>
        <ApiResourcePanel resource={index} retry={retryIndex} loadingLabel="Loading learner index" emptyTitle="No learner records are indexed" emptyMessage="The backend returned no learner summaries.">
          {() => null}
        </ApiResourcePanel>
      </div>

      <form className="learner-id-lookup" onSubmit={handleSubmit}>
        <label htmlFor="learner-record-id">Open a record by ID</label>
        <div className="learner-id-lookup-controls"><input id="learner-record-id" value={recordId} onChange={(event) => setRecordId(event.target.value)} autoComplete="off" placeholder="For example, u135328"/><button type="submit" className="button button--primary" disabled={!recordId.trim() || lookup.status === "loading"}>{lookup.status === "loading" ? "Opening…" : "Open record"}</button></div>
        <p>Record IDs are provided by the backend index. No identity or session lookup is available.</p>
        {lookup.status === "error" && <ErrorState error={lookup.error} requestId={lookup.error instanceof ApiError ? lookup.error.requestId : null} onRetry={() => void openRecord(recordId)}/>}
      </form>
    </div>

    {selectedLearner && <div className="selected-learner-record" aria-live="polite"><div><span className="selected-learner-label">Selected record</span><strong>{selectedLearner.learner_id}</strong><span>{selectedLearner.source === "research_artifacts" ? "Research artifact record" : "Application record"}</span></div><div className="selected-record-data">{selectedLearner.available_data.map((item) => <span key={item}>{item.replaceAll("_", " ")}</span>)}{selectedLearner.trajectory_count > 0 && <span>{selectedLearner.trajectory_count} trajectory records</span>}</div></div>}
  </section>;
}
