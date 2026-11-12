import { getApiConfig } from "./config";
import { ApiError } from "./errors";
import type { ApiErrorEnvelope, ApiResult } from "./types";

/** HTTP methods exposed by the current Phase 14 OpenAPI contract. */
export type ApiMethod = "GET" | "POST";
export type FetchFunction = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;

export interface ApiClientOptions {
  baseUrl: string;
  timeoutMs: number;
  fetchImpl?: FetchFunction;
}

export interface ApiRequestOptions {
  method?: ApiMethod;
  body?: unknown;
  signal?: AbortSignal;
  headers?: HeadersInit;
}

export interface ApiClient {
  request<T>(path: string, options?: ApiRequestOptions): Promise<ApiResult<T>>;
  get<T>(path: string, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<ApiResult<T>>;
  post<T, Body>(path: string, body: Body, options?: Omit<ApiRequestOptions, "method" | "body">): Promise<ApiResult<T>>;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requestIdFrom(value: unknown, response: Response): string | null {
  if (isObject(value) && typeof value.request_id === "string") return value.request_id;
  return response.headers.get("X-Request-ID");
}

function errorEnvelope(value: unknown): ApiErrorEnvelope | null {
  if (!isObject(value) || value.success !== false || !isObject(value.error)) return null;
  if (typeof value.error.code !== "string" || typeof value.error.message !== "string") return null;
  if (typeof value.timestamp !== "string" || typeof value.request_id !== "string") return null;
  const fields = value.error.fields;
  if (fields !== undefined && fields !== null && (!Array.isArray(fields) || !fields.every((field) => typeof field === "string"))) return null;
  let normalizedFields: string[] | null | undefined;
  if (fields === null) normalizedFields = null;
  else if (Array.isArray(fields)) normalizedFields = fields.filter((field): field is string => typeof field === "string");
  return {
    success: false,
    error: { code: value.error.code, message: value.error.message, ...(normalizedFields !== undefined ? { fields: normalizedFields } : {}) },
    timestamp: value.timestamp,
    request_id: value.request_id,
  };
}

function endpointUrl(baseUrl: string, path: string): URL {
  return new URL(path.replace(/^\/+/, ""), `${baseUrl.replace(/\/+$/, "")}/`);
}

function createRequestId(): string {
  const random = Math.random().toString(36).slice(2, 10);
  return `mcp-ri-${Date.now().toString(36)}-${random}`;
}

export function createApiClient(options: ApiClientOptions): ApiClient {
  const fetchImpl = options.fetchImpl ?? fetch;

  async function request<T>(path: string, requestOptions: ApiRequestOptions = {}): Promise<ApiResult<T>> {
    const method = requestOptions.method ?? "GET";
    const controller = new AbortController();
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, options.timeoutMs);
    const abortFromCaller = () => controller.abort();
    if (requestOptions.signal?.aborted) controller.abort();
    else requestOptions.signal?.addEventListener("abort", abortFromCaller, { once: true });

    const headers = new Headers(requestOptions.headers);
    headers.set("Accept", "application/json");
    headers.set("X-Request-ID", headers.get("X-Request-ID") ?? createRequestId());
    if (requestOptions.body !== undefined) headers.set("Content-Type", "application/json");

    try {
      const response = await fetchImpl(endpointUrl(options.baseUrl, path), {
        method,
        headers,
        signal: controller.signal,
        ...(requestOptions.body !== undefined ? { body: JSON.stringify(requestOptions.body) } : {}),
      });
      const text = await response.text();
      let parsed: unknown;
      if (text.trim()) {
        try {
          parsed = JSON.parse(text);
        } catch {
          if (response.ok) throw new ApiError("The backend returned an invalid JSON response.", { kind: "invalid-json", status: response.status, requestId: response.headers.get("X-Request-ID") });
        }
      }

      const requestId = requestIdFrom(parsed, response);
      if (!response.ok) {
        const knownError = errorEnvelope(parsed);
        throw new ApiError(
          knownError?.error.message ?? `The backend request failed with HTTP ${response.status}.`,
          {
            kind: "http",
            status: response.status,
            code: knownError?.error.code ?? null,
            requestId: knownError?.request_id ?? requestId,
            fields: knownError?.error.fields ?? null,
          },
        );
      }
      if (!text.trim()) return { data: undefined, requestId, status: response.status };
      if (!isObject(parsed) || parsed.success !== true || !("data" in parsed) || typeof parsed.request_id !== "string") {
        throw new ApiError("The backend response did not match the API envelope.", { kind: "invalid-envelope", status: response.status, requestId });
      }
      // OpenAPI-derived generic type; consumers still receive server JSON at runtime.
      return { data: parsed.data as T, requestId: parsed.request_id, status: response.status };
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (timedOut) throw new ApiError("The backend request timed out.", { kind: "timeout" });
      if (requestOptions.signal?.aborted) throw new ApiError("The request was cancelled.", { kind: "aborted" });
      throw new ApiError("The backend could not be reached.", { kind: "network" });
    } finally {
      clearTimeout(timeout);
      requestOptions.signal?.removeEventListener("abort", abortFromCaller);
    }
  }

  return {
    request,
    get<T>(path: string, requestOptions?: Omit<ApiRequestOptions, "method" | "body">) {
      return request<T>(path, { ...requestOptions, method: "GET" });
    },
    post<T, Body>(path: string, body: Body, requestOptions?: Omit<ApiRequestOptions, "method" | "body">) {
      return request<T>(path, { ...requestOptions, method: "POST", body });
    },
  };
}

export function getApiClient(): ApiClient {
  const config = getApiConfig();
  if (config.mode === "mock") throw new ApiError("API requests are disabled while mock mode is enabled.", { kind: "configuration" });
  if (config.configurationError || !config.baseUrl) {
    throw new ApiError(config.configurationError?.message ?? "The API base URL is not configured.", { kind: "configuration" });
  }
  return createApiClient({ baseUrl: config.baseUrl, timeoutMs: config.timeoutMs });
}
