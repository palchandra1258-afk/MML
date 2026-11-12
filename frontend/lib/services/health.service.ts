import type { ApiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import { getApiClient } from "../api/client";
import type { ApiResult, HealthData } from "../api/types";

export function isHealthData(value: unknown): value is HealthData {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return false;
  const health = value as Record<string, unknown>;
  return (health.status === "healthy" || health.status === "degraded")
    && typeof health.api_version === "string"
    && (health.database === "available" || health.database === "unavailable")
    && typeof health.modules === "object" && health.modules !== null && !Array.isArray(health.modules)
    && typeof health.timestamp === "string";
}

export function createHealthService(client: ApiClient) {
  return {
    getHealth(signal?: AbortSignal): Promise<ApiResult<HealthData>> {
      return client.get<HealthData>(endpoints.health, { signal });
    },
  };
}

export function getHealth(signal?: AbortSignal): Promise<ApiResult<HealthData>> {
  return createHealthService(getApiClient()).getHealth(signal);
}
