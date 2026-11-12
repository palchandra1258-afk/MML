import { ApiError } from "./errors";
import type { ApiPage, ApiResult } from "./types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function isApiPage(value: unknown): value is ApiPage<unknown> {
  if (!isRecord(value) || !Array.isArray(value.items)) return false;
  const { limit, offset, total, has_more: hasMore, items } = value;
  if (!Number.isInteger(limit) || (limit as number) <= 0) return false;
  if (!Number.isInteger(offset) || (offset as number) < 0) return false;
  if (!Number.isInteger(total) || (total as number) < 0) return false;
  if (typeof hasMore !== "boolean" || items.length > (limit as number)) return false;
  if (items.length > 0 && (offset as number) + items.length > (total as number)) return false;
  if (hasMore !== ((offset as number) + items.length < (total as number))) return false;
  return items.every(isRecord);
}

/** Validate pagination metadata before it reaches list and selection components. */
export function validateApiPage<T>(result: ApiResult<unknown>): ApiResult<ApiPage<T>> {
  if (result.data === undefined) return result as ApiResult<ApiPage<T>>;
  if (!isApiPage(result.data)) {
    throw new ApiError("The backend returned invalid pagination data.", {
      kind: "invalid-envelope",
      status: result.status,
      requestId: result.requestId,
    });
  }
  return { ...result, data: result.data as ApiPage<T> };
}
