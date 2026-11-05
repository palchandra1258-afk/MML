# EdNet KT1 Dataset Report

## Source, license and scope

Source: [official Riiid EdNet repository](https://github.com/riiid/ednet) and its [dataset paper](https://arxiv.org/abs/1912.03072). The repository specifies EdNet KT1 as learner-separated question-response logs and publishes the question-content table. The repository license is CC BY-NC 4.0: use must be non-commercial and attribution must be retained; any sharing or adaptation must follow the license terms. The experiment predicts a behavioral response outcome; it is not a direct measurement of understanding, confusion or cognitive state.

## Observed acquisition and dataset size

- KT1 archive bytes: 1,201,163,816
- KT1 SHA-256: `0d13933f90201c5101c7fe8659e44474fa049e3fb93181a8ba6fb3e63267b535`
- Question-content archive bytes: 173,976
- Question-content SHA-256: `aa910a0436d9dbac0ba232f55e27b37ad8d39da285fcf15f1c1eb5d064be98e7`
- Learner CSV files: 784,309
- KT1 interaction rows: 95,293,926
- Unique questions in content table: 13,169

## Dataset structure and task suitability

- Observed KT1 columns: elapsed_time, question_id, solving_id, timestamp, user_answer
- Observed question-content columns: question_id, bundle_id, explanation_id, correct_answer, part, tags, deployed_at
- Rows with a derivable correctness target: 95,266,280
- Correctness-target coverage across KT1 rows: 0.999710
- Question-content row coverage: 1.000000
- Skill-tag availability across interaction rows: 0.999796
- Structural support for the proposed task: **yes**

Target correctness is obtained by joining the current response's `question_id` to the content table's `correct_answer`, then comparing it with current `user_answer`. The answer key is used only to construct the label; never use the target row's `user_answer`, `correct_answer`, derived correctness or `elapsed_time` as input. Current-question identifiers or other metadata are allowed only for a prediction protocol where that question is already presented before answer submission. Historical input may use strictly earlier learner interactions only.

## Integrity and limits

Both archives passed ZIP structure and per-member CRC checks during acquisition. SHA-256 values above identify the preserved raw files. Timestamps are shifted in the published dataset; sequence ordering is validated within each learner file, and absolute calendar time should not be interpreted as original time. See the separate data-quality report for missingness, duplicate, chronology and mapping findings.

Timestamp order in the source learner files is nondecreasing, but 1,314,673 adjacent transitions have equal timestamps; preserve source row order for those ties. The scan found 27,646 blank submitted answers and 4,983 exact duplicate records. The raw data remains unchanged; target eligibility and duplicate treatment must be explicitly documented before any training data is produced. A learner-level split is required to prevent the same learner appearing across partitions.
