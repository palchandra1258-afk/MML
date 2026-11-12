import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints, withQuery } from "../api/endpoints";
import { validateApiPage } from "../api/pagination";
import type { ApiPage, ApiResult, EvidenceRecord, PageQuery } from "../api/types";

export interface EvidenceQuery extends PageQuery { evidenceType?: string; }

export function createEvidenceService(client: ApiClient) {
  return {
    list(learnerId: string, query: EvidenceQuery = {}): Promise<ApiResult<ApiPage<EvidenceRecord>>> {
      return client.get<unknown>(withQuery(endpoints.evidence(learnerId), {
        limit: query.limit,
        offset: query.offset,
        evidence_type: query.evidenceType,
      }), { signal: query.signal }).then((result) => validateApiPage<EvidenceRecord>(result));
    },
    get(learnerId: string, evidenceId: string, signal?: AbortSignal): Promise<ApiResult<EvidenceRecord>> {
      return client.get<EvidenceRecord>(endpoints.evidenceRecord(learnerId, evidenceId), { signal });
    },
  };
}
export const evidenceService = {
  list: (learnerId: string, query: EvidenceQuery = {}) => createEvidenceService(getApiClient()).list(learnerId, query),
  get: (learnerId: string, evidenceId: string, signal?: AbortSignal) => createEvidenceService(getApiClient()).get(learnerId, evidenceId, signal),
};
