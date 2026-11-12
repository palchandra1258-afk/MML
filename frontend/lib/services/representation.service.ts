import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints, withQuery } from "../api/endpoints";
import { validateApiPage } from "../api/pagination";
import type { ApiPage, ApiResult, PageQuery, RepresentationRecord } from "../api/types";

export function createRepresentationService(client: ApiClient) {
  return {
    list(learnerId: string, query: PageQuery = {}): Promise<ApiResult<ApiPage<RepresentationRecord>>> {
      return client.get<unknown>(withQuery(endpoints.representations(learnerId), { limit: query.limit, offset: query.offset }), { signal: query.signal })
        .then((result) => validateApiPage<RepresentationRecord>(result));
    },
    get(learnerId: string, planId: string, signal?: AbortSignal): Promise<ApiResult<RepresentationRecord>> {
      return client.get<RepresentationRecord>(endpoints.representation(learnerId, planId), { signal });
    },
  };
}
export const representationService = {
  list: (learnerId: string, query: PageQuery = {}) => createRepresentationService(getApiClient()).list(learnerId, query),
  get: (learnerId: string, planId: string, signal?: AbortSignal) => createRepresentationService(getApiClient()).get(learnerId, planId, signal),
};
