# Data Models

## Success envelope

```json
{
  "success": true,
  "data": {},
  "request_id": "..."
}
```

Paginated `data` uses `{ "items": [], "limit": 20, "offset": 0, "total": 0, "has_more": false }`.

## Research records

Phase 9 behavioral states, Phase 10 evidence, Phase 11 cognitive states, and Phase 12 representation plans preserve their existing source fields and schema versions. They include source-specific uncertainty, limitations, provenance, and evidence references. Evidence responses add:

- `grouping_information`: source Phase 10 group records linked to that evidence ID.
- `alignment_links`: source links involving that evidence ID.
- `grouping_annotations_available`: `false` means the group artifact index is unavailable; an empty group list with `true` is an indexed empty result.

Representation decisions are inside `decision`. The plan's `selected_representation`, `selected_action`, `delivery_status`, and `capability_reference` distinguish a suggestion from an executable capability. No delivery operation is implemented.

## Trajectories

Trajectory payloads follow Phase 13 schema version `1.0`. `trajectory_version` identifies the immutable snapshot version. History payloads follow the Phase 13 event schema; their pagination order is separate database metadata and does not change the payload. The current trajectory row is a read pointer, while versions and events preserve history.

## Availability

`GET /learners` reports available source keys such as `phase9_states`, `phase10_evidence`, `phase10_groups`, `phase11_states`, `phase12_plans`, and `application`. The Phase 13 sample files are not shown as learner trajectories because their goals are generated placeholders.
