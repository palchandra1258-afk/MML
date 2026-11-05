# EdNet KT1 Training Dataset Specification

## Output artifact

The reproducible processor `scripts/preprocess_ednet.py` reads the preserved official KT1 and question-content archives and emits one gzip-compressed CSV, one row per raw KT1 interaction:

`data/processed/ednet/ednet_kt1_features.csv.gz`

It writes aggregate provenance and split counts to `data/processed/ednet/ednet_preprocessing_summary.json`. The CSV includes labelled and unlabelled event rows, so no source interaction is silently dropped. For supervised fitting, select rows whose `correctness` field is `0` or `1`. The raw answer, answer key, current elapsed duration, duplicate flag, learner/source fields and split assignments are for label/provenance/audit use; use only the explicit feature whitelist for model inputs.

The complete processed snapshot contains 95,293,926 interaction rows, of which 95,266,280 are labelled targets and 27,646 have blank answers and no target. The compressed artifact is 5,888,235,415 bytes. Its decompressed line count (including the header) matches the expected interaction count, and the gzip CRC check completed successfully.

The processor uses Python's standard library and handles one learner file at a time. It does not load all interactions into memory, generate a second feature table, or require Parquet dependencies. Development runs can set `--max-learners`; final runs omit that limit. The seed defaults to `2025` and can be configured.

## Standardized interaction columns

| Column | Meaning |
|---|---|
| `learner_id` | Learner identifier from the original `u<number>.csv` filename. |
| `source_row_order` | Zero-based row order within that learner's original CSV. |
| `timestamp` | Original timestamp string (verified parseable for the complete source); shifted by EdNet. |
| `question_id` | Original KT1 question identifier. |
| `submitted_answer` | Original response choice; blank stays blank. |
| `correct_answer` | Joined official key for target construction only. |
| `correctness` | `1`, `0`, or blank when target cannot be established. |
| `skill_tags` | Joined current-question expert tags; blank when unavailable. |
| `session_id` | Original `solving_id`, preserved without assuming a numeric scale. |
| `source_dataset` | Constant `EdNet-KT1`. |
| `is_exact_duplicate` | `1` for later exact five-field copies within the same learner; copies are retained. |
| `split_unseen_learner` | Learner-disjoint protocol partition for eligible target rows; blank for unlabelled rows. |
| `split_future_known_learner` | Per-learner chronological protocol partition for eligible target rows; blank for unlabelled rows. |
| `elapsed_time_ms` | The current event's original duration; post-response provenance only, never a feature. |
| Feature columns | See `docs/FEATURE_ENGINEERING.md`; exact list is exported in the summary and code constant. |

The current processor output also retains current question ID, part and tags as features. There is no `event_type` because KT1 does not provide one.

## Target and eligibility

For each row, join `question_id` to `contents/questions.csv`; derive correctness only when `user_answer` and the joined `correct_answer` are valid choice codes. The target is whether the submitted answer equals the key. Do not interpret it as cognition.

- Labelled rows are eligible supervised examples, including the first response from a learner as a cold-start case.
- Blank or otherwise unlabelled rows remain in the processed event stream and can contribute logged-event chronology, but do not count as target examples or update correctness/skill-history features.
- Exact duplicates remain as separate rows and are separately flagged; primary counts and history include them.
- The current answer, key, target and elapsed time are excluded from `FEATURE_COLUMNS`.

## Format, nulls, and provenance

Output is UTF-8 CSV compressed with ordered concatenated gzip members, fixed column order, stable row order, and deterministic gzip timestamps. The first shard contains the only header. Missing numeric values are empty cells; no artificial zero is introduced for unavailable data. A true zero remains zero. Source archive SHA-256 values, configuration, counts, feature columns, and both split summaries are written to the JSON sidecar. No model training or performance results are part of preprocessing.

## Complete-run label and split counts

There are 62,248,682 correct and 33,017,598 incorrect derivable targets in total. These are dataset label counts, not model results.

| Protocol | Split | Learners represented | Targets | Correct | Incorrect |
|---|---|---:|---:|---:|---:|
| Unseen learners | Train | 549,251 | 66,898,246 | 43,725,275 | 23,172,971 |
| Unseen learners | Validation | 117,784 | 14,236,525 | 9,288,983 | 4,947,542 |
| Unseen learners | Test | 117,269 | 14,131,509 | 9,234,424 | 4,897,085 |
| Future known learners | Train | 784,304 | 66,348,221 | 43,180,703 | 23,167,518 |
| Future known learners | Validation | 715,712 | 14,241,038 | 9,479,258 | 4,761,780 |
| Future known learners | Test | 756,936 | 14,677,021 | 9,588,721 | 5,088,300 |

Five learners have no derivable target and therefore appear in no unseen-learner split count. In the future-known protocol the same learner can appear in multiple temporal splits by design.
