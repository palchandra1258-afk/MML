# F5 — Multimodal evidence explorer and provenance intelligence

## Repository and API audit

The OpenAPI contract exposes:

| Screen/data | Endpoint | Contract and scope |
|---|---|---|
| Learner picker | `GET /learners?limit=&offset=` and `GET /learners/{learner_id}` | Paginated pseudonymous records and each selected record's `available_data`. |
| Evidence list | `GET /learners/{learner_id}/evidence?limit=&offset=&evidence_type=` | Required learner path; pagination plus `evidence_type` are the only list filters. |
| Evidence detail | `GET /learners/{learner_id}/evidence/{evidence_id}` | One record, annotated with group/alignment data when available. |
| Dataset/module counts | `GET /health` | `phase10_evidence.record_count` and `phase10_grouping.record_count`; no modality/source aggregate. |

There is no standalone group, alignment, conflict, or evidence-to-downstream reverse-lookup route. Group and alignment records are embedded in `EvidenceRecord` responses by the backend. The frontend reuses the existing `evidenceService`, `learnerService` through `LearnerRecordPicker`, shared health/resource hooks, F1 source/status/loading components, and the selected learner context. No API service change was needed.

The API transport schema exposes `EvidenceRecord` fields: `evidence_id`, `learner_id`, `schema_version`, `session_id`, `evidence_type`, `temporal`, `provenance`, `content`, `processing`, `uncertainty`, `related_evidence_ids`, `duplicate_candidates`, `content_fingerprint`, `grouping_information`, `alignment_links`, and `grouping_annotations_available`.

- `temporal`: event and ingestion timestamps, sequence, precision, timestamp source.
- `provenance`: source dataset/file/record ID, source modality, processing method/version.
- `processing`: status, processing timestamp, extraction method, quality flags, missing fields, transformation history.
- `uncertainty`: flags, optional processing confidence, and notes.
- `EvidenceGroup`: group/learner/session IDs, member evidence IDs, grouping basis, modalities present, per-modality availability, alignment links, uncertainty flags.
- `EvidenceAlignmentLink`: left/right evidence IDs, alignment type, optional time delta, uncertainty label/flags.

The contract has no explicit conflict object/status/description/resolution field and no downstream artifact IDs on an evidence record. Possible duplicates remain a separate field and are not interpreted as conflicts.

## Observed coverage

On 11 November 2026, the connected API health response reported 1,000 Phase 10 evidence records and 1,000 Phase 10 groups. The published Phase 10 evaluation describes the same bounded sample: 1,000 real EdNet-KT1 interaction records, each from a distinct validation learner, and 1,000 singleton groups. No timestamp alignment candidates or duplicate candidates appeared in that sample because of its one-event-per-learner design; this does not establish that the wider EdNet dataset has no alignable or duplicate events. Text/audio/visual adapter checks and conflict/alignment edge cases use synthetic fixtures.

The live record inspected for learner `u135328` returned one `interaction` evidence record with `source_modality=interaction` and `source_dataset=EdNet-KT1`, populated provenance, no processing missing fields, one embedded singleton group, no alignment link, and no duplicate candidate. Its content fields were EdNet question/solving/answer/correctness/skill metadata. These observations are examples from the connected API, not hardcoded explorer totals. The UI computes modality/type/source/metadata counts only from the current returned page. It labels health totals separately and does not infer global distributions from a learner page.

The explorer explicitly separates the actual API evidence from the synthetic text/audio/visual adapter fixtures described in the research report. Mock mode has no evidence fixtures and shows no synthetic records.

## Explorer behavior

`/evidence` provides:

- A learner picker and learner-scoped evidence index/detail.
- Backend pagination at 25 records per page, preserving `limit`, `offset`, and optional `evidence_type` query parameters.
- Current-page metrics for returned count, source modality, evidence type, source dataset, provenance, missing processing fields, quality flags, groups, alignment links, and possible duplicate candidates.
- Separate health totals for all indexed evidence/groups and API totals for the selected learner/type query.
- Client-side page filters for search, source modality, source dataset, group ID, processing status, alignment-link/uncertainty presence, possible duplicate candidates, and ingestion date. Only `evidence_type` is sent as an API filter. The interface states the current-page scope and has a reset action.
- Record detail for temporal/provenance/processing metadata, source content fields, uncertainty, missingness, groups and their member references, alignment links, possible duplicates, and related evidence IDs.
- A group explorer assembled from unique embedded group IDs on the current page. Selecting a group exposes its saved membership, modalities, availability map, grouping basis, and uncertainty flags. Member IDs can open their learner-scoped detail endpoint even when outside the current list page.
- An alignment inspector with actual endpoint IDs, type, delta, and uncertainty metadata. No semantic or causal interpretation is added.
- A conflict notice stating that conflict semantics are not exposed. Missing metadata and possible duplicate candidates remain separately visible.
- Generic links to selected-learner behavioral, cognitive, representation, and trajectory views. They are explicitly not evidence-specific links.

The provenance path displays source fields, processing metadata, the saved evidence record, embedded group/alignment annotations, and the unavailable downstream-reference stage. It does not claim an adapter or transformation was executed unless corresponding record fields are present.

## Traceability and limitations

The current evidence response exposes evidence-to-evidence relationships (`related_evidence_ids`, group member IDs, alignment endpoints, and duplicate candidates), but no behavioral-state, cognitive-state, representation-plan, or trajectory IDs. No reverse lookup by evidence ID exists. The explorer therefore does not scan downstream datasets or fabricate per-evidence links. F3/F4 context routes can be opened for the selected learner, with an explicit notice that this is not a verified relationship.

The current API data is a bounded EdNet interaction sample. Its publisher-shifted question-given timestamps are preserved and shown with `timestamp_source`; they are not presented as actual response-submission times. Text/audio/visual are schema categories and synthetic adapter test modalities, not evidence of real learner media or ASR/OCR/vision/fusion capability. An absent group annotation, missing timestamp, or empty alignment list is displayed as missing/unavailable in its scope, not as proof of a negative relationship.

## Validation

- `npm run lint` — passed.
- `npm run test:api` — passed, 34 tests (12 API client, 9 F3 learner, 8 F4 representation, 5 F5 evidence); 0 failed.
- `npx tsc --noEmit` — passed.
- `npm run build` — passed with Next.js production build and route generation.
- `git diff --check` — passed.
- Browser-based interaction/visual validation was not performed; the project has no browser test setup. Evidence filter/pagination logic, API route use, source separation, and responsive class breakpoints have source/unit coverage.

## Remaining dependencies

Live global modality/source aggregates, standalone group browsing, explicit conflict records/status/resolution, server-side source/modality/date/conflict filters, and evidence-to-downstream reverse lookup need new backend endpoints/contracts. A richer real learner media dataset is required before multimodal learner coverage can be claimed. F5 does not start F6.
