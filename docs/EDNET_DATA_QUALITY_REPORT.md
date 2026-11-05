# EdNet KT1 Data Quality Report

Generated from the acquired official archives. This report contains aggregate counts only; it does not publish learner IDs or response records.

## Dataset counts

- Learner files: 784,309
- Interaction rows: 95,293,926
- Question-content rows: 13,169
- Unique question IDs in content: 13,169

## Schema and missing values

- KT1 columns: elapsed_time, question_id, solving_id, timestamp, user_answer
- Blank/whitespace missing values by column: `{"user_answer": 27646}`. This count does not treat nonblank sentinel values as missing.
- Duplicate complete records within learner files: 4,983

## Timestamp and mapping checks

- Valid timestamps: 95,293,926
- Invalid/missing timestamps: 0
- Non-monotonic adjacent transitions: 0
- Equal adjacent timestamp transitions: 1,314,673
- Timestamp order in source-file order: nondecreasing for all learner files; equal timestamps require preserving source row order as the tie-breaker.
- Matched response rows: 95,293,926
- Unmatched response rows: 0 (0 unique question IDs)
- Rows with usable answer key and submitted answer: 95,266,280
- Rows with skill tags: 95,274,496
- Question-content rows with blank answer keys: 0; blank or `-1` tag rows: 797
- Invalid submitted-answer rows: 0

## Prediction-task feasibility

- Structural feasibility: **yes**
- Target: submitted answer matches the joined official answer key. This is a behavioral response-outcome target, not a direct measure of understanding, confusion or cognitive state.
- Current answer, derived target and current elapsed time are excluded from inputs; historical features must use strictly earlier interactions.
- Structural support is strong: every interaction question ID joins to content, and 95,266,280 rows have a derivable target. Rows without a submitted answer cannot be target examples; their history treatment remains a preprocessing decision.
- Resolve how to handle 4,983 exact duplicate records before training. They are counted, not removed. Also preserve source order for the 1,314,673 equal-timestamp transitions.
- Learner-level train/validation/test assignment must happen before fitting; preserve event order within each learner split. Do not split response rows randomly across partitions.

See `ednet_quality_summary.json` for complete aggregate fields.
