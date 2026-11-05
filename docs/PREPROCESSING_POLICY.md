# EdNet KT1 Preprocessing Policy

## Scope and source preservation

The supervised task predicts whether the answer submitted for a question will match the official question-content answer key. This is a behavioral response-outcome prediction, not a direct measurement of understanding, confusion, or cognitive state. The raw archives under `data/raw/ednet/` are read-only inputs. Processing writes one gzip-compressed CSV containing one output row for each raw KT1 interaction; it does not edit or extract over the source files. Re-running against the same archives and seed reproduces the row order, values, and split assignments.

## Blank and unlabelled answers

- The KT1 schema has no abandonment reason, response-status reason, or separate missingness explanation. The cause of the 27,646 blank `user_answer` values cannot be determined from these files.
- A blank answer is not labelled incorrect. It is retained in the standardized interaction stream with blank `submitted_answer` and `correctness`; it is excluded from supervised target counts and from answered/correct historical counts.
- A blank-answer event still contributes to `source_row_order`, `n_prior_logged_events`, and the timestamp gap for later events. Its recorded nonnegative elapsed duration can be exposed as the immediately previous logged event's duration, since it is historical by the later prediction time. It does not update response accuracy or skill-performance summaries.
- Nonblank answers with an invalid response code, absent answer key, or unmatched question are retained but receive no target. The full validation found no invalid response codes, missing answer keys, or unmatched question IDs.
- Tags recorded as blank or `-1` are unavailable. They are represented as an empty tag list and do not update skill histories. Raw values remain preserved in the original archives.

The full preprocessing pass observed 27,646 blank `user_answer` cells, no other blank KT1 source fields, and no unavailable (blank, malformed, or negative) `elapsed_time` values. It observed 19,430 interaction rows whose joined skill tags were unavailable. The cause of blank answers remains unknown because KT1 has no reason/status field.

## Exact duplicate records

An exact duplicate is a later row for the same learner whose complete five-field KT1 tuple (`timestamp`, `solving_id`, `question_id`, `user_answer`, `elapsed_time`) exactly matches an earlier row. The audit found 4,983 such later rows. The available schema has no event UUID or attempt sequence that can prove whether a repeated identical tuple is a logging duplicate or a meaningful repeated event. Therefore the primary processed table **preserves every row** and flags later exact matches with `is_exact_duplicate=1`; it does not silently deduplicate. Preserved copies each remain eligible target examples and update history in source order, which can give these events extra weight. A later sensitivity analysis should compare this declared policy with deduplication, while keeping the raw archives unchanged.

## Timestamps and event ordering

- Process each learner CSV independently and retain its original row order. `source_row_order` is zero-based within that file.
- The complete validation found parseable timestamps for every row, no decreasing adjacent timestamps, and 1,314,673 adjacent ties. Do not sort by timestamp and do not invent an ordering among ties: source row order is the tie-breaker.
- The processor fails if it encounters a decreasing timestamp instead of reordering it silently.
- Timestamps are shifted by the dataset publisher. Use event order and within-learner time differences only. Do not interpret the absolute clock as original calendar time or derive time-of-day features.

## Missing-value and field policy

Blank CSV cells are counted as missing. Duration values that are blank, malformed, or negative are unavailable rather than converted to zero. A zero elapsed duration remains zero because it is a recorded nonnegative value. Tag `-1` is a documented missing/sentinel value. No imputation is performed during preprocessing; numeric missing features remain empty in CSV and should be handled by a later model pipeline fitted on training data only.

The processed summary records raw blank counts, unavailable elapsed durations, missing skill-tag rows, invalid timestamps/answers, unmatched questions, exact duplicate rows, target eligibility, and split counts. The current target row's answer and elapsed duration are preserved as target/provenance fields but excluded from the model feature whitelist.

## Supervised target and example eligibility

For a KT1 event, join `question_id` to the official question-content table. If `user_answer` and `correct_answer` are both valid `a`–`d` values, set `correctness=1` when they match and `0` otherwise. The answer key is used only to produce this target. Every raw interaction receives a standardized row; only rows with a derivable correctness label count as supervised examples.

The first eligible response from each learner is retained as a cold-start example with zero prior attempts and empty historical rates. A later example's historical correctness counts use only earlier eligible responses. Blank-answer events are retained as logged events but do not become labelled targets or answered attempts. No examples are removed for being duplicates.

On the complete snapshot, **95,266,280** of 95,293,926 interactions had derivable targets; **27,646** were excluded from supervised targets due to blank answers. No row was excluded for an invalid answer, unmatched question, missing answer key, or invalid timestamp. All 4,983 exact duplicate rows remain in the processed table.

## Split policies

Two mutually distinct split assignments are stored for each eligible target:

1. `split_unseen_learner`: deterministic 70/15/15 approximate assignment by a seeded hash of the learner ID. Every example from a learner remains in one partition.
2. `split_future_known_learner`: within each learner's eligible target sequence, use the first 70% for training, the next 15% for validation, and the final 15% for testing (integer boundaries are deterministic; a learner with at least one target has at least one training target). This simulates later predictions for known learners. A validation/test feature may use only that learner's earlier observed events and labels, as they would be known at that later time.

Never combine the two partition columns or describe them as one split. Fit encoders, transformations, model parameters and calibration on the appropriate training/validation partitions only. The test partition is held for final evaluation.

## Reproducibility and limits

`scripts/preprocess_ednet.py` accepts a configurable data root, random seed, development learner limit, learner index range, and output path. The complete run used four contiguous learner ranges, processed one learner at a time within each range, and merged their ordered gzip members with `scripts/merge_ednet_shards.py`. The merged stream has one CSV header and exactly 95,293,926 data rows; its gzip CRC and decompressed line count were checked. The default output is gzip CSV rather than Parquet because `pyarrow` is not installed in the inspected environment; this avoids adding a dependency. No model has been trained. Aggregate counts and output provenance are recorded in `data/processed/ednet/ednet_preprocessing_summary.json`.
