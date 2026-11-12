import { ApiError } from "./errors";

export type FailedConnectionState = "disconnected" | "error";

export function failedConnectionState(error: unknown): FailedConnectionState {
  if (!(error instanceof ApiError)) return "error";
  if (error.kind === "network" || error.kind === "timeout" || error.kind === "aborted") return "disconnected";
  if (error.kind === "configuration" && error.message.includes("is not set")) return "disconnected";
  return "error";
}
