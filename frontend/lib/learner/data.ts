import type { ApiPage, ApiResult, PageQuery } from "../api/types";

export type PageLoader<T> = (query: PageQuery) => Promise<ApiResult<ApiPage<T>>>;

/** The backend orders artifact records by source event time, so the final page is the latest indexed sample. */
export async function loadLatestIndexedPage<T>(
  load: PageLoader<T>,
  limit: number,
  signal?: AbortSignal,
): Promise<ApiResult<ApiPage<T>>> {
  const firstPage = await load({ limit, offset: 0, signal });
  if (!firstPage.data?.has_more) return firstPage;
  const offset = Math.max(0, firstPage.data.total - limit);
  return load({ limit, offset, signal });
}
