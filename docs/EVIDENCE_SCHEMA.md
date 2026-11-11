# MCP-RI Evidence Schema v1

## Record contract

`schemas/evidence_record_v1.schema.json` defines the modality-independent evidence item. It is intentionally permissive about modality-specific `content` while constraining identity, time, provenance, processing state, missing fields and uncertainty.

| Field group | Key fields | Meaning |
|---|---|---|
| Identification | `schema_version`, `evidence_id`, `learner_id`, `session_id`, `evidence_type` | `evidence_id` is stable for a source event; `session_id` is nullable. |
| Temporal | `event_timestamp`, `ingestion_timestamp`, `sequence_number`, `temporal_precision`, `timestamp_source` | Source event time is kept separate from actual UTC ingestion time. No event time is synthesized. |
| Provenance | `source_dataset`, `source_file`, `source_record_id`, `source_modality`, `processing_method`, `processing_version` | Trace to the upstream row/reference and transformation. |
| Content | modality-specific object | Large audio/image bytes are not embedded. Store a reference and, when local bytes are inspectable, SHA-256 and metadata. |
| Processing | `status`, `processing_timestamp`, `extraction_method`, `quality_flags`, `missing_fields`, `transformation_history` | `partial`, `pending`, `reference_only`, or `failed` distinguish incomplete extraction from a usable metadata record. |
| Uncertainty | `flags`, `processing_confidence`, `notes` | Processing confidence is not learner/cognitive confidence. It may remain null. |
| Relationships | `related_evidence_ids`, `duplicate_candidates`, `content_fingerprint` | Explicit relations and possible duplicate links are retained, never silently deduplicated. |

Evidence types are `text`, `audio`, `visual`, `interaction`, and `temporal_history`. The shared adapter implementation is under `src/mcp_ri/evidence/`; `validate_evidence` uses Draft 2020-12 JSON Schema when the pinned `jsonschema` dependency is installed, followed by semantic checks.

## Related contracts

- `evidence_group_v1.schema.json`: record IDs, grouping basis, present modalities, per-modality availability, within-group alignment links, and uncertainty flags.
- `evidence_alignment_v1.schema.json`: a candidate link with type, millisecond delta when known, uncertainty tier, and flags.
- `evidence_conflict_v1.schema.json`: involved IDs, source modalities, event-time relationship, description and resolution status. `cognitive_interpretation` is constrained to null.

## Stable IDs and hashes

The evidence ID is SHA-256-derived from evidence type, learner, dataset, source record, optional session and event timestamp, truncated to a readable 128-bit identifier. When source record identity is absent, the content fingerprint is used as part of the ID. The content fingerprint is SHA-256 of canonical JSON for the modality content. These identifiers support stable reference and possible duplicate detection; they do not prove that two source events are semantically identical.

## EdNet mapping

The interaction adapter reads the existing processed table, not the raw archive in parallel. `learner_id` and `source_row_order` form the source record key and map to `ednet-kt1.zip#KT1/{learner_id}.csv`. It preserves the source question, submitted answer, derived correctness, parsed skill IDs, session ID, timestamp and duplicate flag. `solving_id` remains a content field; it is not assumed to be a session. Skill IDs are namespaced as `ednet_skill:{tag}` using the existing EdNet parsing logic.

The timestamp remains a source string and is marked millisecond precision. The source note states it is a shifted question-given timestamp. It is not converted to calendar UTC or described as response-submission time. `ingestion_timestamp` records when the local adapter normalized the record.

## Missing and incomplete values

Missing content fields appear in `processing.missing_fields`; record-level flags explain uncertainty. For example, an audio record can retain a URI, format and WAV metadata while its transcript is `pending`. A local visual reference can remain usable when OCR is `failed`. Group modality availability indicates whether any record of that modality is present in the group; extraction status remains on each evidence record.

## Conflict records

Conflicts are created only when a caller supplies at least two known evidence IDs and a description. The system does not infer conflict semantics from a correctness label and text automatically. Resolution begins at `unresolved`; no winner or diagnosis is selected. The representation permits a later investigation without mutating or discarding source records.
