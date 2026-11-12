import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints, withQuery } from "../api/endpoints";
import { validateApiPage } from "../api/pagination";
import type { ApiPage, ApiResult, LearnerDetail, LearnerSummary, PageQuery } from "../api/types";

export function createLearnerService(client: ApiClient) {
  return {
    list(query: PageQuery = {}): Promise<ApiResult<ApiPage<LearnerSummary>>> {
      return client.get<unknown>(withQuery(endpoints.learners, { limit: query.limit, offset: query.offset }), { signal: query.signal })
        .then((result) => validateApiPage<LearnerSummary>(result));
    },
    get(learnerId: string, signal?: AbortSignal): Promise<ApiResult<LearnerDetail>> {
      return client.get<LearnerDetail>(endpoints.learner(learnerId), { signal });
    },
  };
}

export const learnerService = {
  list: (query: PageQuery = {}) => createLearnerService(getApiClient()).list(query),
  get: (learnerId: string, signal?: AbortSignal) => createLearnerService(getApiClient()).get(learnerId, signal),
};
