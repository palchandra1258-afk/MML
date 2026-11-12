export type PublicEnvironment = {
  apiBaseUrl?: string;
  useMockData?: string;
  timeoutMs?: string;
  nodeEnvironment?: string;
};

export type ApiRuntimeConfig = {
  mode: "api" | "mock";
  baseUrl: string | null;
  timeoutMs: number;
  nodeEnvironment: string;
  configurationError?: { kind: "missing" | "invalid"; message: string };
};

class EnvironmentConfigIssue extends Error {
  constructor(readonly kind: "missing" | "invalid", message: string) {
    super(message);
  }
}

const DEFAULT_TIMEOUT_MS = 10_000;
const MIN_TIMEOUT_MS = 250;
const MAX_TIMEOUT_MS = 120_000;

function parseTimeout(value: string | undefined): number {
  if (value === undefined || value.trim() === "") return DEFAULT_TIMEOUT_MS;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < MIN_TIMEOUT_MS || parsed > MAX_TIMEOUT_MS) {
    throw new Error(`NEXT_PUBLIC_API_TIMEOUT_MS must be an integer from ${MIN_TIMEOUT_MS} to ${MAX_TIMEOUT_MS}.`);
  }
  return parsed;
}

function parseBaseUrl(value: string | undefined, nodeEnvironment: string): string {
  if (!value?.trim()) throw new EnvironmentConfigIssue("missing", "NEXT_PUBLIC_API_BASE_URL is not set.");
  let parsed: URL;
  try {
    parsed = new URL(value);
  } catch {
    throw new EnvironmentConfigIssue("invalid", "NEXT_PUBLIC_API_BASE_URL must be an absolute HTTP(S) URL.");
  }
  if ((parsed.protocol !== "http:" && parsed.protocol !== "https:") || parsed.username || parsed.password || parsed.search || parsed.hash) {
    throw new EnvironmentConfigIssue("invalid", "NEXT_PUBLIC_API_BASE_URL must use HTTP(S), cannot include credentials, and cannot include a query or fragment.");
  }
  if (nodeEnvironment === "production" && parsed.protocol !== "https:" && !["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname)) {
    throw new EnvironmentConfigIssue("invalid", "Production API URLs must use HTTPS.");
  }
  return parsed.toString().replace(/\/+$/, "");
}

export function resolveApiConfig(environment: PublicEnvironment): ApiRuntimeConfig {
  const mockValue = environment.useMockData?.trim().toLowerCase();
  const mode = mockValue === "true" ? "mock" : "api";
  const nodeEnvironment = environment.nodeEnvironment ?? "development";
  let timeoutMs = DEFAULT_TIMEOUT_MS;
  let configurationError: ApiRuntimeConfig["configurationError"];

  if (mockValue !== undefined && mockValue !== "" && mockValue !== "true" && mockValue !== "false") {
    configurationError = { kind: "invalid", message: "NEXT_PUBLIC_USE_MOCK_DATA must be true or false." };
  }

  try {
    timeoutMs = parseTimeout(environment.timeoutMs);
  } catch (error) {
    configurationError = { kind: "invalid", message: error instanceof Error ? error.message : "Invalid API timeout." };
  }

  if (mode === "mock") {
    return { mode, baseUrl: null, timeoutMs, nodeEnvironment, ...(configurationError ? { configurationError } : {}) };
  }

  let baseUrl: string | null = null;
  try {
    baseUrl = parseBaseUrl(environment.apiBaseUrl, nodeEnvironment);
  } catch (error) {
    const issue = error instanceof EnvironmentConfigIssue ? error : new EnvironmentConfigIssue("invalid", "The API configuration is invalid.");
    configurationError ??= { kind: issue.kind, message: issue.message };
  }
  return { mode, baseUrl, timeoutMs, nodeEnvironment, ...(configurationError ? { configurationError } : {}) };
}

/** Reads public API settings plus NODE_ENV; no secret-bearing environment values are used. */
export function getApiConfig(): ApiRuntimeConfig {
  return resolveApiConfig({
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL,
    useMockData: process.env.NEXT_PUBLIC_USE_MOCK_DATA,
    timeoutMs: process.env.NEXT_PUBLIC_API_TIMEOUT_MS,
    nodeEnvironment: process.env.NODE_ENV,
  });
}
