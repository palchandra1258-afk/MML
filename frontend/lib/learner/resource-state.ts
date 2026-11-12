export type ResourceValue<T> =
  | { key: string; attempt: number; status: "success"; data: T | undefined; requestId: string | null }
  | { key: string; attempt: number; status: "error"; error: unknown; requestId: string | null };

export type ResolvedResource<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T | undefined; requestId: string | null }
  | { status: "error"; error: unknown; requestId: string | null };

export function resolveResource<T>(key: string | null, attempt: number, value: ResourceValue<T> | null): ResolvedResource<T> {
  if (key === null) return { status: "idle" };
  if (!value || value.key !== key || value.attempt !== attempt) return { status: "loading" };
  if (value.status === "error") return { status: "error", error: value.error, requestId: value.requestId };
  return { status: "success", data: value.data, requestId: value.requestId };
}

export function nextResourceAttempt(attempt: number): number {
  return attempt + 1;
}
