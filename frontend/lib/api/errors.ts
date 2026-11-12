export type ApiErrorKind = "configuration" | "network" | "timeout" | "aborted" | "http" | "invalid-json" | "invalid-envelope";

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | null;
  readonly code: string | null;
  readonly requestId: string | null;
  readonly fields: string[] | null;

  constructor(message: string, options: {
    kind: ApiErrorKind;
    status?: number | null;
    code?: string | null;
    requestId?: string | null;
    fields?: string[] | null;
  }) {
    super(message);
    this.name = "ApiError";
    this.kind = options.kind;
    this.status = options.status ?? null;
    this.code = options.code ?? null;
    this.requestId = options.requestId ?? null;
    this.fields = options.fields ?? null;
  }
}

export function safeErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "The request could not be completed. Please try again.";
}
