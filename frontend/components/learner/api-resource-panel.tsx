"use client";

import type { ReactNode } from "react";
import { ApiError } from "@/lib/api/errors";
import type { ApiResourceState } from "@/hooks/use-api-resource";
import { EmptyState, ErrorState, LoadingState, NotFoundState } from "@/components/shared/data-states";

export function ApiResourcePanel<T>({
  resource,
  retry,
  loadingLabel,
  emptyTitle,
  emptyMessage,
  children,
}: {
  resource: ApiResourceState<T>;
  retry: () => void;
  loadingLabel: string;
  emptyTitle: string;
  emptyMessage: string;
  children: (data: T, requestId: string | null) => ReactNode;
}) {
  if (resource.status === "idle") {
    return <EmptyState title={emptyTitle}>{emptyMessage}</EmptyState>;
  }
  if (resource.status === "loading") return <LoadingState label={loadingLabel}/>;
  if (resource.status === "error") {
    if (resource.error instanceof ApiError && resource.error.status === 404) return <NotFoundState error={resource.error} requestId={resource.requestId} onRetry={retry}/>;
    return <ErrorState error={resource.error} requestId={resource.requestId} onRetry={retry}/>;
  }
  if (resource.data === undefined) {
    return <EmptyState title={emptyTitle}>The API returned an empty response. {emptyMessage}</EmptyState>;
  }
  return <>{children(resource.data, resource.requestId)}</>;
}
