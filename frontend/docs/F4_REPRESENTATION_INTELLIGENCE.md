# F4 — Representation intelligence and decision explainability

## Repository and endpoint audit

The checked-in OpenAPI contract exposes learner-scoped plan list/detail routes and read routes for the latest cognitive and behavioral snapshots plus evidence list/detail. It does not expose a taxonomy, capability-registry, plan-history, plan-validation, or global representation-plan endpoint. Representation list requests require a `learner_id`, so plan totals and plan classifications must remain scoped to a selected learner. Page-derived classifications are scoped to the records on that page.

The representation taxonomy is defined by `src/mcp_ri/representation/representation_taxonomy.py` at version `1.0`. Its fields are `representation_id`, `label`, `examples`, and `configuration_fields`; it has no category or description field. The default registry in `src/mcp_ri/representation/availability_registry.py` creates one entry per taxonomy ID with `status`, `provider_id`, `content_ids`, and `reason`. The registry may be overridden by a caller, but neither that live registry nor per-capability status is exposed by an API endpoint.

The plan API returns `decision.alternative_representations` and, if selected, `decision.capability_reference`. Those are saved decision-time capability observations, not a current registry query. Phase 14 health reports `phase12_representation.available`, `mode`, `record_count`, and `delivery_provider`; this is a module/provider signal, not a per-type capability registry. Representation plan responses do not contain a validation outcome; the backend validates plans internally before persistence.

### Endpoint-to-screen mapping

| Screen | Existing endpoint/source | Scope and limit |
|---|---|---|
| System readiness | `GET /health` | Current Phase 12 module and delivery-provider summary. No per-type registry. |
| Taxonomy explorer | Versioned repository source snapshot from `representation_taxonomy.py` | Static backend definition, labeled with source/version; no taxonomy HTTP endpoint. |
| Default capability registry | Versioned repository source snapshot from `availability_registry.py` | Default configuration only; runtime overrides cannot be queried. Saved plan alternatives are shown separately. |
| Plan index and counts | `GET /learners/{learner_id}/representations?limit=&offset=` | Selected learner only. API `total` is learner-scoped; category counts describe the retrieved page, not all plans. |
| Plan detail and rule trace | `GET /learners/{learner_id}/representations/{plan_id}` | Full saved plan; it does not expose an independent validation report or execution receipt. |
| Associated cognitive state | `GET /learners/{learner_id}/cognitive-state` | Latest snapshot only. If it does not match the plan's `cognitive_state_id`/version, no historical snapshot is available by ID. |
| Associated behavioral state | `GET /learners/{learner_id}/state` | Latest snapshot only. It is associated only when its timestamp matches the plan's saved reference. |
| Evidence references | `GET /learners/{learner_id}/evidence/{evidence_id}` | Lookup each saved supporting/contradictory ID; missing index entries remain visible as unresolved references. |

## Implementation notes

This page is a research interface. It separates taxonomy definition, default repository capability configuration, live Phase 12 health, saved plan capability observations, and plan execution state. Static source snapshots must not be described as live API results. Plan status counts are nonexclusive where decision fields overlap and are labeled with their learner/page scope.

### Taxonomy and capability explorers

`/representations` is registered in the existing App Router section route and reuses the F1 shell, F2 services, API health/resource hooks, learner selector, source labels, status badges, data boundaries, and shared loading/error/empty states. The taxonomy snapshot displays the actual source fields `representation_id`, `label`, `examples`, and `configuration_fields`. It does not invent categories or descriptions. The default capability table displays `representation_id`, `status`, `provider_id`, `content_ids`, and `reason`; the registry schema has no separate description or execution-constraint fields. Health provider state and plan-time observations are shown separately. The default snapshot is versioned/labeled but cannot reflect runtime registry overrides.

### Plan explorer and detail

The index uses `representationService.list` with the API's `limit` and `offset`, shows the learner-scoped API total, and preserves pagination. Page-derived category counts can overlap and are explicitly limited to the retrieved page. Filters/search also apply only to that page and cover learner/plan/concept/evidence identifiers and other serialized saved fields, actual delivery status, selected representation, observed capability status, version, and created-date range. The selected learner scopes the backend request; no global plan endpoint is assumed.

Selecting a plan fetches the full record with `representationService.get`. Detail displays saved plan identity/version/timestamp, `input_references`, `decision` rationale and policy trace, selected action/status, capability reference and alternatives, concept grounding, learning objective, representation configuration, evaluation strategy, and limitations. Evidence IDs are resolved with the existing evidence service (bounded to 12 lookups per detail); lookup failures and IDs beyond that bound remain visible. The latest behavioral and cognitive endpoints are only attributed to the plan when the timestamp or ID/version matches its saved reference. A different latest snapshot is marked as a mismatch and is not substituted for a historical record.

Two records from the current retrieved page can be compared in an accessible, horizontally scrollable table across selected representation, delivery/action status, evidence references, cognitive-state reference, capability observations, rationale, validation availability, and execution-evidence availability. The comparison has no score or ranking and cautions when concepts/windows differ.

### Execution and scientific interpretation

The UI distinguishes a planner recommendation or deferred/no-selection action from execution. It always labels execution as not established because `RepresentationRecord` has no execution receipt and the OpenAPI contract exposes no general delivery route. It never presents a selected representation, saved `available` capability status, or repository registration as proof that content was delivered. The contract also has no plan-validation result, so the UI reports that validation outcome is not exposed rather than asserting a validation state. Confidence/uncertainty fields remain as saved with explicit scope; no effectiveness claims are added.

In mock mode or when the API is unavailable, the page keeps the clearly labeled repository source snapshots visible but shows no synthetic plan records. API errors use the existing retryable resource panel and do not fall back to mock plans.

## Validation

- `npm run lint` — passed.
- `npm run test:api` — passed, 29 tests (12 API client, 9 F3 learner, 8 F4 representation tests); 0 failed.
- `npx tsc --noEmit` — passed.
- `npm run build` — passed with Next.js production build and route generation.
- `git diff --check` — passed.
- Browser-based interaction/visual checks were not run; the project has no browser test setup. Responsive breakpoints, control semantics, empty states, and route/service wiring have source-level coverage only.

## Remaining dependencies

Runtime taxonomy/registry endpoints, plan history and validation reads, cognitive-state-by-ID/version, and execution receipts are required for live data in those areas. A general content-delivery and execution receipt contract is required before execution can be shown. This phase does not begin F5.
