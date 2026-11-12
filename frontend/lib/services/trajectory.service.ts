import type { ApiClient } from "../api/client";
import { getApiClient } from "../api/client";
import { endpoints, withQuery } from "../api/endpoints";
import { validateApiPage } from "../api/pagination";
import type { ApiPage, ApiResult, OpenRecord, PageQuery, TrajectoryActionRequest, TrajectoryCreateRequest, TrajectoryRecord } from "../api/types";

export interface HistoryQuery extends PageQuery { limit?: number; }

export function createTrajectoryService(client: ApiClient) {
  return {
    list(learnerId: string, query: PageQuery = {}): Promise<ApiResult<ApiPage<TrajectoryRecord>>> {
      return client.get<unknown>(withQuery(endpoints.trajectories(learnerId), { limit: query.limit, offset: query.offset }), { signal: query.signal })
        .then((result) => validateApiPage<TrajectoryRecord>(result));
    },
    get(learnerId: string, trajectoryId: string, signal?: AbortSignal): Promise<ApiResult<TrajectoryRecord>> {
      return client.get<TrajectoryRecord>(endpoints.trajectory(learnerId, trajectoryId), { signal });
    },
    history(learnerId: string, trajectoryId: string, query: HistoryQuery = {}): Promise<ApiResult<ApiPage<OpenRecord>>> {
      return client.get<unknown>(withQuery(endpoints.trajectoryHistory(learnerId, trajectoryId), { limit: query.limit ?? 50, offset: query.offset }), { signal: query.signal })
        .then((result) => validateApiPage<OpenRecord>(result));
    },
    listDiversions(learnerId: string, query: PageQuery = {}): Promise<ApiResult<ApiPage<OpenRecord>>> {
      return client.get<unknown>(withQuery(endpoints.diversions(learnerId), { limit: query.limit, offset: query.offset }), { signal: query.signal })
        .then((result) => validateApiPage<OpenRecord>(result));
    },
    getDiversion(learnerId: string, diversionId: string, signal?: AbortSignal): Promise<ApiResult<OpenRecord>> {
      return client.get<OpenRecord>(endpoints.diversion(learnerId, diversionId), { signal });
    },
    create(learnerId: string, body: TrajectoryCreateRequest, signal?: AbortSignal): Promise<ApiResult<TrajectoryRecord>> {
      return client.post<TrajectoryRecord, TrajectoryCreateRequest>(endpoints.trajectories(learnerId), body, { signal });
    },
    applyAction(learnerId: string, trajectoryId: string, body: TrajectoryActionRequest, signal?: AbortSignal): Promise<ApiResult<TrajectoryRecord>> {
      return client.post<TrajectoryRecord, TrajectoryActionRequest>(endpoints.trajectoryActions(learnerId, trajectoryId), body, { signal });
    },
  };
}
export const trajectoryService = {
  list: (learnerId: string, query: PageQuery = {}) => createTrajectoryService(getApiClient()).list(learnerId, query),
  get: (learnerId: string, trajectoryId: string, signal?: AbortSignal) => createTrajectoryService(getApiClient()).get(learnerId, trajectoryId, signal),
  history: (learnerId: string, trajectoryId: string, query: HistoryQuery = {}) => createTrajectoryService(getApiClient()).history(learnerId, trajectoryId, query),
  listDiversions: (learnerId: string, query: PageQuery = {}) => createTrajectoryService(getApiClient()).listDiversions(learnerId, query),
  getDiversion: (learnerId: string, diversionId: string, signal?: AbortSignal) => createTrajectoryService(getApiClient()).getDiversion(learnerId, diversionId, signal),
  create: (learnerId: string, body: TrajectoryCreateRequest, signal?: AbortSignal) => createTrajectoryService(getApiClient()).create(learnerId, body, signal),
  applyAction: (learnerId: string, trajectoryId: string, body: TrajectoryActionRequest, signal?: AbortSignal) => createTrajectoryService(getApiClient()).applyAction(learnerId, trajectoryId, body, signal),
};
