"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api/errors";
import type { ApiResult } from "@/lib/api/types";
import { nextResourceAttempt, resolveResource, type ResourceValue, type ResolvedResource } from "@/lib/learner/resource-state";

export type ApiResourceState<T> = ResolvedResource<T>;

/** Fetches one keyed API resource, aborts stale work, and retries only on user action. */
export function useApiResource<T>(
  key: string | null,
  load: (signal: AbortSignal) => Promise<ApiResult<T>>,
) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<ResourceValue<T> | null>(null);
  const retry = useCallback(() => setAttempt((value) => nextResourceAttempt(value)), []);

  useEffect(() => {
    if (key === null) return;
    const controller = new AbortController();
    const currentAttempt = attempt;
    void Promise.resolve().then(() => load(controller.signal)).then((response) => {
      if (controller.signal.aborted) return;
      setResult({ key, attempt: currentAttempt, status: "success", data: response.data, requestId: response.requestId });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      setResult({ key, attempt: currentAttempt, status: "error", error, requestId: error instanceof ApiError ? error.requestId : null });
    });
    return () => controller.abort();
  }, [attempt, key, load]);

  return { resource: resolveResource<T>(key, attempt, result), retry };
}
