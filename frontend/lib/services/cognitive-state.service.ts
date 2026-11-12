import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { ApiResult, CognitiveStateRecord } from "../api/types";

export function createCognitiveStateService(client: ApiClient) {
  return {
    getLatest(learnerId: string, signal?: AbortSignal): Promise<ApiResult<CognitiveStateRecord>> {
      return client.get<CognitiveStateRecord>(endpoints.cognitiveState(learnerId), { signal });
    },
  };
}
export const cognitiveStateService = {
  getLatest: (learnerId: string, signal?: AbortSignal) => createCognitiveStateService(getApiClient()).getLatest(learnerId, signal),
};
