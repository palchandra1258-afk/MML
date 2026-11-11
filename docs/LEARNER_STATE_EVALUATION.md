# Phase 9 — Full Validation Evaluation

**Run:** `phase9-learner-state-20261106T081823Z`

**Status:** completed; unseen-learner validation partition only. The locked test labels/state were not evaluated.

## Run coverage and outputs

The script scanned the processed EdNet file once (95,293,926 interactions; 5,888,235,415 compressed bytes), using the existing seed-2025 learner hash to identify validation learners. This preserves 4,599 unlabeled rows whose split field is blank in preprocessing but whose learner belongs to the validation partition. The report contains 14,241,124 validation interaction rows: 14,236,525 labeled responses and 4,599 unlabeled events.

The generated JSONL contains 117,785 learner states. The data summary lists 117,784 learners with validation targets; the additional state belongs to one of the five learners with no derivable target, assigned to validation by the same learner hash. Its state has no labeled outcomes and is explicitly marked as having no evidence. All 117,785 states passed the versioned JSON Schema and numeric/count consistency checks during generation.

The full learner state stream remains in the local run directory and is excluded from Git because it contains learner-level records. The committed machine-readable summary is [`evaluation.json`](../results/reports/phase9-learner-state-20261106T081823Z/evaluation.json); run metadata is in [`run.json`](../results/reports/phase9-learner-state-20261106T081823Z/run.json).

## Descriptive experiments

| Experiment | Observed result | Interpretation |
|---|---:|---|
| A. Historical state | 117,784 learners had at least one labeled response; mean historical accuracy averaged equally over learners: 0.4918 | This is learner-macro observed correctness on this validation cohort, not cognitive-state accuracy. It differs from row-weighted validation prevalence because learners are weighted equally. |
| B. Recent state | 117,784 learners had recent and historical estimates; mean absolute difference: 0.0599 | Recent 10-response learner accuracy differs from each learner's full-history accuracy by about 6.0 percentage points on average. It is descriptive, not evidence of a cognitive transition. |
| C. Beta smoothing | Beta(1,1) prior; mean absolute shrinkage 0.0386 per learner and 0.1913 per learner-skill state | Skill estimates shrink much more because many learner-skill pairs have only a few attempts. |
| D. Temporal trend | Learners: 26,474 declining, 21,883 improving, 17,729 stable, 51,699 insufficient evidence | Trend means the latest-five accuracy minus preceding-five accuracy crossed the fixed ±0.10 threshold. It does not establish learning gain or decline. |
| E. Evidence sufficiency | Learners: 48,256 high, 54,604 moderate, 14,924 low, 1 none. Skill states: 283,249 high, 815,333 moderate, 2,798,134 low, 850 none. | Counts reflect the declared sample-size tiers. The 3,897,566 skill states include skills observed only on unlabeled events, hence 850 zero-evidence concept entries. |

The file contains 3,897,566 learner-skill states. Their attempt-count buckets are: 850 with zero labeled attempts, 2,798,134 with 1–4, 815,333 with 5–19, and 283,249 with at least 20. These counts make the shrinkage/evidence result explicit: sparse per-skill outcomes are common.

The 20 focused learner-state unit tests passed under Python 3.12.3. `python3 -m unittest discover -s tests -v` ran 38 tests: 35 passed, one existing ML test module was skipped, and two existing ML test modules failed during import because `joblib` and `torch` are unavailable in the active interpreter. No Phase 9 test failed. `jsonschema==4.10.3` was added to `requirements-training.txt` to make full schema validation reproducible.

## Validation scope and limitations

- Every emitted state was validated while it was generated. Rates are bounded to `[0,1]`, intervals are ordered, and response counts reconcile.
- Unit tests separately verify historical-prefix reconstruction, source chronology, missing outcomes, multi-skill mapping, duplicate preservation and future-row invariance.
- No per-event prediction table is stored, and the current interpreter lacks `joblib`, scikit-learn, XGBoost and PyTorch. Prediction integration and calibration were therefore not run. Existing report-level correctness metrics cannot be substituted for state-specific predictions.
- No direct cognitive-state labels exist, so direct understanding, misconception, confusion, or mismatch accuracy is `null` and cannot be calculated.
- Wilson intervals assume a binomial response proportion and do not account for all dependence among repeated learner events. Confidence tiers are deterministic evidence summaries, not calibrated probabilities.
- The output is a large derived state file (about 2.6 GiB uncompressed); it is not a copy of raw or processed input rows, but it retains detailed per-skill counts and last-interaction references. Keep it under the same access controls as learner-level data.

## Reproduction

```bash
python3 -m unittest -v tests/test_learner_state.py
python3 scripts/learner_state/build_and_evaluate.py
```

The builder creates a new timestamped directory and refuses to overwrite an existing output directory. It scans the processed table once and never invokes training or reads test labels into state.
