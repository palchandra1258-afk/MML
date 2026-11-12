import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints } from "../api/endpoints";
import type { ApiResult, BehavioralStateRecord } from "../api/types";

export function createLearnerStateService(client: ApiClient) {
  return {
    get(learnerId: string, signal?: AbortSignal): Promise<ApiResult<BehavioralStateRecord>> {
      return client.get<BehavioralStateRecord>(endpoints.learnerState(learnerId), { signal });
    },
  };
}
export const learnerStateService = {
  get: (learnerId: string, signal?: AbortSignal) => createLearnerStateService(getApiClient()).get(learnerId, signal),
};
