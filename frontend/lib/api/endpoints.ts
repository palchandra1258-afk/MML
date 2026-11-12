/** Paths from MCP-RI Backend API 1.0.0 OpenAPI; no unexposed endpoints are listed. */
export const endpoints = {
  health: "/health",
  learners: "/learners",
  learner: (learnerId: string) => `/learners/${encodeURIComponent(learnerId)}`,
  learnerState: (learnerId: string) => `${endpoints.learner(learnerId)}/state`,
  cognitiveState: (learnerId: string) => `${endpoints.learner(learnerId)}/cognitive-state`,
  evidence: (learnerId: string) => `${endpoints.learner(learnerId)}/evidence`,
  evidenceRecord: (learnerId: string, evidenceId: string) => `${endpoints.evidence(learnerId)}/${encodeURIComponent(evidenceId)}`,
  representations: (learnerId: string) => `${endpoints.learner(learnerId)}/representations`,
  representation: (learnerId: string, planId: string) => `${endpoints.representations(learnerId)}/${encodeURIComponent(planId)}`,
  trajectories: (learnerId: string) => `${endpoints.learner(learnerId)}/trajectories`,
  trajectory: (learnerId: string, trajectoryId: string) => `${endpoints.trajectories(learnerId)}/${encodeURIComponent(trajectoryId)}`,
  trajectoryHistory: (learnerId: string, trajectoryId: string) => `${endpoints.trajectory(learnerId, trajectoryId)}/history`,
  trajectoryActions: (learnerId: string, trajectoryId: string) => `${endpoints.trajectory(learnerId, trajectoryId)}/actions`,
  diversions: (learnerId: string) => `${endpoints.learner(learnerId)}/diversions`,
  diversion: (learnerId: string, diversionId: string) => `${endpoints.diversions(learnerId)}/${encodeURIComponent(diversionId)}`,
} as const;

export function withQuery(path: string, values: Record<string, string | number | undefined>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}
