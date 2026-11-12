# Modality Availability Report

**Inspected:** 6 November 2026. **Scope:** files under the current workspace `data/raw/` and `data/processed/`, the EdNet summaries and the Phase 9 implementation/results. No external datasets were downloaded.

| Modality | Actual learner data available? | Source | Timestamp available? | Labels available? | Limitations |
|---|---|---|---|---|---|
| Text/language | No learner-authored text. | EdNet question-content metadata exists, but is not a learner explanation or transcript. | No learner-text timestamps. | No text labels. | Adapter is validated only on synthetic text. |
| Voice/speech | No. | No learner audio or transcripts in the local raw/processed inventory. | No. | No. | WAV metadata/reference adapter only; no ASR model/runtime and no real speech data. |
| Visual artifacts | No. | No learner images, diagrams, handwriting, video or pen traces in the local data inventory. | No. | No. | PNG/JPEG header metadata and hashing only; no OCR/vision inference. Adapter tested with a generated PNG. |
| Interaction | Yes. | EdNet KT1 raw archive and the existing processed table `data/processed/ednet/ednet_kt1_features.csv.gz`. | Yes: 95,293,926 rows have valid shifted source timestamps; source order is retained. | Yes: 95,266,280 answer-key-derived correctness values. | EdNet is interaction evidence. Its timestamp is question-given time, not answer submission time; correctness is an outcome, not a cognitive label. |
| Temporal history | Yes, derived. | Chronological interaction stream plus Phase 9 accumulator/schema and validation outputs. | Yes, inherited from source event time/order. | No cognitive labels. Behavioral correctness summaries are available. | Derived history is limited to observed EdNet events and the supplied cutoff; it does not establish understanding. |

## Inventory evidence

The local raw EdNet inventory contains KT1 interaction and question-content archives. The processed inventory contains the feature table and aggregate preprocessing/quality summaries. No other raw learner dataset or media directory is part of the inspected snapshot. Model artifacts are not additional evidence modalities.

The preprocessing summary reports 784,309 learner files, 95,293,926 interaction rows, 95,266,280 eligible correctness targets and 27,646 blank-answer events. The quality summary reports valid timestamps on all interaction rows. The Phase 9 validation output covers 117,785 learners and describes behavioral response history only.

## Reproduction

Run `python3 scripts/evidence/inspect_modality_availability.py` to inspect current summaries and print a machine-readable JSON inventory. The script does not open or copy the large interaction table. Its inventory can change if data is added to the workspace; update this report only after checking what the new data actually contains and is licensed to support.
