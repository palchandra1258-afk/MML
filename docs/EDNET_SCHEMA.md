# EdNet KT1 Schema Observed During Validation

This file is generated from the actual archive headers. Values below are descriptive schema/coverage facts, not assumptions from the README.

- KT1 columns: elapsed_time, question_id, solving_id, timestamp, user_answer
- Question-content columns: question_id, bundle_id, explanation_id, correct_answer, part, tags, deployed_at
- Learner files: 784,309
- Interactions: 95,293,926

## Target and leakage boundary

Target correctness is derived by joining KT1 `question_id` to question content `correct_answer` and comparing with current `user_answer`. Use the answer key only to create the label: the target row's `user_answer`, `correct_answer`, derived correctness and `elapsed_time` are prohibited inputs. For each prediction row, history may contain only responses with earlier ordering for that learner. Current-question metadata is permitted only if the experimental prediction point is after the question is presented and before its answer is submitted; metadata such as `deployed_at` must not be used unless its temporal availability relative to shifted learner timestamps is established.

## Observed quality details

- All 95,293,926 response rows have a parseable timestamp and question-content match. Timestamps are nondecreasing in source-file row order. There are 1,314,673 adjacent equal-timestamp transitions; retain source row order to break these ties rather than sorting tied events arbitrarily.
- There are 27,646 blank/whitespace `user_answer` values, so those rows have no target. The blank-value scan does not treat nonblank sentinel values as missing.
- There are 4,983 exact duplicate complete records within learner files. They remain in the raw archive; a documented retention/deduplication decision is required before training.
- Every content row has a nonblank valid answer key. 797 content rows have blank or `-1` tags; 19,430 interaction rows map to such content.

## Example construction and split boundary

An eligible target example is a response row with a present valid submitted answer and a matched question answer key. Derive its binary target by comparing those two values. Build its history only from earlier rows in that same learner file, using the file order to resolve equal timestamps. Missing-answer rows do not provide correctness labels; do not infer them. Assign entire learners to train, validation or test before fitting, then retain chronological order within each learner. Any current-question metadata may enter only in a deployment setting where it is known before the answer is submitted. No preprocessing has yet removed rows or generated examples.
