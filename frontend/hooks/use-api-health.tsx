"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { getApiConfig } from "@/lib/api/config";
import { ApiError } from "@/lib/api/errors";
import { failedConnectionState } from "@/lib/api/connection-state";
import { getHealth, isHealthData } from "@/lib/services/health.service";
import type { HealthData } from "@/lib/api/types";

export type ConnectionState = "connecting" | "connected" | "disconnected" | "error" | "mock";

export interface ApiHealthState {
  state: ConnectionState;
  health?: HealthData;
  message?: string;
  checkedAt?: string;
  retry: () => void;
}

type HealthCheckResult = {
  attempt: number;
  state: Exclude<ConnectionState, "connecting" | "mock">;
  health?: HealthData;
  message: string;
  checkedAt: string;
};

const ApiHealthContext = createContext<ApiHealthState | null>(null);

export function ApiHealthProvider({ children }: { children: ReactNode }) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<HealthCheckResult | null>(null);
  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  const config = getApiConfig();
  const mode = config.mode;
  const baseUrl = config.baseUrl;
  const timeoutMs = config.timeoutMs;
  const configErrorKind = config.configurationError?.kind;
  const configErrorMessage = config.configurationError?.message;

  useEffect(() => {
    if (mode === "mock" || configErrorKind || !baseUrl) return;
    const controller = new AbortController();
    void getHealth(controller.signal).then((response) => {
      if (controller.signal.aborted) return;
      if (!isHealthData(response.data)) {
        setResult({
          attempt,
          state: "error",
          message: "The health endpoint returned data that does not match its API contract.",
          checkedAt: new Date().toISOString(),
        });
        return;
      }
      setResult({
        attempt,
        state: "connected",
        health: response.data,
        message: response.data.status === "degraded" ? "The API is reachable, but one or more services or artifact indexes are degraded." : "The backend health endpoint responded successfully.",
        checkedAt: response.data.timestamp,
      });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      setResult({
        attempt,
        state: failedConnectionState(error),
        message: error instanceof ApiError ? error.message : "The backend health check failed.",
        checkedAt: new Date().toISOString(),
      });
    });
    return () => controller.abort();
  }, [attempt, mode, baseUrl, timeoutMs, configErrorKind]);

  let value: ApiHealthState;
  if (mode === "mock") {
    value = { state: "mock", message: "Synthetic demonstration mode is enabled. No API health request was sent.", retry };
  } else if (configErrorKind) {
    value = {
      state: configErrorKind === "missing" ? "disconnected" : "error",
      message: configErrorMessage,
      retry,
    };
  } else if (result?.attempt === attempt) {
    value = { state: result.state, health: result.health, message: result.message, checkedAt: result.checkedAt, retry };
  } else {
    value = { state: "connecting", message: "Checking backend connection.", retry };
  }

  return <ApiHealthContext.Provider value={value}>{children}</ApiHealthContext.Provider>;
}

export function useApiHealth(): ApiHealthState {
  const context = useContext(ApiHealthContext);
  if (!context) throw new Error("useApiHealth must be used within ApiHealthProvider.");
  return context;
}
