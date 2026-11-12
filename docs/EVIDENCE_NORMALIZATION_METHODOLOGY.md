# Evidence Normalization Methodology

## Processing order

1. A modality adapter maps only available source fields into a draft record.
2. The normalizer supplies schema version, stable evidence ID, content fingerprint, processing/ingestion UTC times, default arrays and uncertainty structure.
3. JSON Schema and semantic checks reject malformed records.
4. The in-memory registry retains records, records possible same-learner content duplicates, and accepts explicit unresolved conflicts.
5. The aligner emits source-session links, explicit relationships or timestamp candidates with uncertainty. Grouping uses session/explicit relations only.
6. Only interaction evidence is mapped to the existing Phase 9 updater.

## Time handling

`event_timestamp` retains the upstream event value. `ingestion_timestamp` and `processing_timestamp` are actual UTC values created during normalization. They answer when the evidence was ingested/processed and are not substituted for event time.

EdNet timestamps are shifted numeric millisecond values and are preserved as strings along with their source description and millisecond precision. The code does not convert them to wall-clock time. A timestamp from another adapter defaults to unknown precision unless its caller supplies precision metadata. Cross-source numeric proximity is considered only when both records explicitly have millisecond precision.

EdNet's processed `source_row_order` is zero-based per learner and is retained as `sequence_number`; tied event times do not reorder the source events. The sample reader consumes the already ordered processed stream and filters to labeled `split_unseen_learner=validation` rows.

## Provenance and identity

For EdNet, `source_record_id` is `{learner_id}:{source_row_order}` and `source_file` is `data/raw/ednet/ednet-kt1.zip#KT1/{learner_id}.csv`. This is a locator to the original learner CSV member. Adapters for caller-provided modalities require the caller to supply any actual source ID/path; they do not invent one.

Evidence IDs are stable from source event identity and dataset fields. Content fingerprints hash canonical JSON for evidence content. Identical content for the same learner but distinct IDs is treated as a possible duplicate. Both records remain present and point to one another in `duplicate_candidates`; the registry does not infer whether the repetition is accidental.

## Modality transformations

- **Interaction:** existing processed columns are reused. Existing skill-tag parsing is reused and IDs are namespaced. No second raw-to-feature pipeline is created.
- **Text:** raw text is retained; normalized text applies CRLF/CR-to-LF, Unicode NFC and outer trimming. Token count uses a whitespace split, not linguistic tokenization. No meaning or correctness is inferred.
- **Audio:** bytes are referenced, not embedded. Local SHA-256 is streamed. Standard-library WAV metadata is read when possible. Transcript status is pending unless caller-supplied transcript/provenance exists; a caller may explicitly report extraction failure.
- **Visual:** bytes are referenced, not embedded. Local SHA-256 is streamed and PNG/JPEG headers provide format and dimensions where readable. OCR status is pending unless caller-supplied text/provenance exists; a caller may explicitly report extraction failure.
- **Temporal history:** Phase 9 state is projected to a small summary and state reference. Full state/history is not duplicated into each evidence item.

## Missingness and failure

`missing_fields` enumerates data not available in the record. `quality_flags` and `uncertainty.flags` explain conditions such as missing source assets, transcription/OCR pending, or extraction failure. `processing.status` distinguishes `processed`, `partial`, `pending`, `reference_only`, and `failed`. A missing modality is marked unavailable in a group; it is never encoded as a zero, a negative response or a failed learner behavior.

## Reproducibility and limits

The real-data run defaults to one labeled row from each of 1,000 distinct unseen-learner validation users. This learner-balanced coverage sample is not a random event sample or population-performance estimate. The stream stops after collecting the sample and an integration trace; the trace replays all source rows before the learner's second labeled event before applying the new event. It writes a small JSONL and report rather than another full dataset/state output. Adapters for text/audio/visual and conflict/alignment edge cases are exercised through generated test fixtures. No external downloads, model training, test-partition evaluation or raw-data modification occur.
