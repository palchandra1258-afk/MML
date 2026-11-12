# Phase 10 Evaluation

## Evaluation scope

Phase 10 evaluates evidence plumbing and provenance, not a multimodal learner model. It processes a bounded, learner-balanced coverage sample from EdNet's unseen-learner validation partition: the first labeled validation event from each of 1,000 distinct learners by default. This is not a random sample of events or a population-performance estimate. Synthetic fixtures exercise unavailable adapter modalities. A separate learner trace replays all earlier source rows before applying a new labeled event to the Phase 9 accumulator. The stream filter does not normalize or evaluate locked-test examples or inspect their correctness values.

## Experiments

| Experiment | Evidence | Checks |
|---|---|---|
| A. EdNet interaction | One labeled validation event from each of 1,000 distinct unseen learners by default. | Learner and question identity, source timestamp preservation, correctness, namespaced skill tags, source file/member and source row ID, schema validation. One event per learner avoids overweighting frequent users in this coverage sample. |
| B. Text | Synthetic authored string fixture. | Raw text retained; line endings and Unicode normalized; token-count metadata; no semantic interpretation. |
| C. Audio | Locally generated WAV fixtures. | SHA-256, WAV sample rate/channel/duration and explicit pending or failed transcription. |
| D. Visual | Locally generated PNG fixture. | SHA-256, format/dimensions and explicit pending or failed OCR. |
| E. Missingness | Interaction-only group and incomplete asset records. | Text/audio/visual marked unavailable; pending/failed extraction preserved on an available reference. |
| F. Alignment | Synthetic source-session and cross-clock records. | Session grouping, high-uncertainty timestamp candidate, and no timestamp-driven merge. |
| G. Conflict | Synthetic interaction and text evidence. | Both records retained, conflict schema valid, status unresolved and cognitive interpretation null. |
| H. Phase 9 integration | A validation learner's chronological source history through its second labeled event plus in-memory accumulator. | All preceding source rows update history; the new labeled interaction is bridged; source timestamp/provenance survives; temporal reference links the immediately prior event and new event evidence IDs. |

## Results

The real-data report is generated at run time by `scripts/evidence/build_evidence_records.py`. It records the scanned row count, actual normalized records, groups, alignment candidates, duplicate candidates, runtime and maximum resident set size. The committed aggregate is [`public_summary.json`](../results/reports/phase10-evidence-20261106T101321Z/public_summary.json). The original report and learner-level output files remain local and are excluded from Git.

The completed 6 November 2026 run scanned 865,006 processed rows to collect one labeled validation event for each of 1,000 distinct learners. All 1,000 evidence records passed schema and provenance checks. They formed 1,000 singleton groups and yielded no timestamp alignment candidates or duplicate candidates; this follows from the one-event-per-learner sample design and is not evidence that EdNet has no duplicates or alignable sessions. The run completed in 11.47 seconds with approximately 40 MiB maximum resident memory.

The integration trace replayed an existing history before applying the next source-ordered interaction. The state bridge preserved the event ordering and updated the interaction count; exact learner IDs, event values, and evidence IDs remain in local files and are excluded from Git. Synthetic integration fixtures separately exercise outcome-count changes.

`python3 scripts/evidence/validate_evidence.py` independently validated all 1,000 evidence records, 1,000 groups, the alignment JSONL and the integration trace.

The local run also generated interaction evidence, group, alignment, and integration trace JSONL/JSON files. Those row-level exports remain local and are not committed.

The tests under `tests/test_evidence/` validate schema rejection, adapters, normalization, missingness, grouping/alignment, unresolved conflicts and the Phase 9 bridge. Real-data validation applies only to EdNet interaction rows and the derived behavioral snapshot. Text/audio/visual behavior, conflict cases and cross-modal alignment use synthetic fixtures.

The focused Phase 10 suite passes 18 tests. Full repository discovery ran 56 tests: 53 passed, one ML pipeline module skipped, and two existing model-test modules could not import because `joblib` and `torch` are absent from this interpreter. Those errors occur before their assertions; the evidence and Phase 9 tests passed. The repository README documents installation of training and deep-learning dependencies for the full suite.

## Interpretation and limits

Passing these checks shows that the code can preserve and validate heterogenous evidence records and route a processed interaction into the existing behavioral updater. It does not show that text/audio/image evidence is available in EdNet, that the adapter understands a modality, that evidence improves prediction, or that the learner's cognition has been inferred. There is no ASR, OCR, learned fusion, cognitive-state label, misconception detector or representation-selection evaluation in this phase.

## Reproduction

```bash
python3 scripts/evidence/inspect_modality_availability.py
python3 -m unittest discover -s tests/test_evidence -v
python3 scripts/evidence/build_evidence_records.py --sample-size 1000
python3 scripts/evidence/validate_evidence.py \
  results/reports/<run>/interaction_evidence.jsonl \
  --groups-jsonl results/reports/<run>/evidence_groups.jsonl \
  --alignments-jsonl results/reports/<run>/alignment_candidates.jsonl \
  --integration-trace results/reports/<run>/phase9_integration_trace.json
```
