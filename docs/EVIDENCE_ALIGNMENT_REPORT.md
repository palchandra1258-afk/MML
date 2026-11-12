# Evidence Grouping and Alignment Report

## Rules implemented

The aligner returns evidence-level relationships; the group builder decides which records can share a group.

| Relationship | Candidate rule | Uncertainty/behavior |
|---|---|---|
| Explicit relation | One record names the other by `evidence_id`; learner IDs must match. | Low uncertainty as a declared source relationship; this is not a cognitive conclusion. |
| Source-scoped session | Same learner, same `source_dataset`, and matching nonempty `session_id`. | Session semantics are local to that source. Link notes timestamp delta when both values are available; it does not merge IDs across datasets. |
| Approximate timestamp | Same learner and numeric millisecond event times within the configured 2,000 ms tolerance, with equal nonempty timestamp-source text but no shared session key. | Medium uncertainty; remains a candidate and does not merge groups. |
| Cross-source timestamp | Same learner and numeric millisecond event times within tolerance, but clock source differs or is missing. | High uncertainty with `cross_source_clock_offset_unverified`; remains a candidate and does not merge groups. |
| No shared key | No explicit relation or source-scoped session. | Record remains a singleton; missing session is listed as uncertainty. |

Non-numeric times and values whose temporal precision is unknown do not produce proximity candidates. Sequence numbers are retained for ordering and Phase 9 replay; they are not compared across datasets as if they shared a clock. EdNet timestamps are shifted and are not interpreted as wall-clock times.

The standalone alignment schema is `schemas/evidence_alignment_v1.schema.json`. Candidate-level JSONL output remains local and is excluded from Git because it contains learner/event references. The aggregate Phase 10 report records the candidate count. The `alignment_links` field in each generated group contains links whose endpoints are both members of that group; a timestamp candidate that did not merge groups remains in the standalone alignment output.

## Group availability

The group builder records modalities present and a status for each expected modality. Missing text/audio/visual in an interaction-only group is `unavailable` with a reason. That status is absence of an evidence record, not evidence that a learner did not use a modality. If a group contains an audio/image reference whose transcript/OCR is pending, the modality is present while the evidence record reports incomplete extraction.

## Validation coverage

Automated tests cover: same-source session grouping; singleton behavior; cross-source timestamp candidates with high uncertainty and no forced merge; explicit links; missing modalities; and rejection of cross-learner explicit links. The real EdNet sample reports group counts and candidate alignment counts, but all events in that sample are interaction evidence. Cross-modal timing behavior is synthetic-test evidence only.
