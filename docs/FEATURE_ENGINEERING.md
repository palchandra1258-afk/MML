# EdNet KT1 Feature Engineering

## Prediction point

The prediction point is after the next question has been presented and before the learner submits its answer. KT1's timestamp is the time the question was given. At this point the current question ID, part, and published skill tags can be known. If a later deployment protocol predicts before the next question is selected, those current-item features must be removed and that protocol evaluated separately.

The current `submitted_answer`, `correct_answer`, derived `correctness`, and current `elapsed_time_ms` are never model inputs. The answer key is used only to construct the target. Historical inputs use strictly earlier source rows for the same learner.

## Implemented feature whitelist

The processor writes these fields as model features. Categorical text fields require an encoder fitted on training data in a later baseline-model phase; preprocessing does not fit encoders or scale values.

| Feature | Source and definition | Availability / caveat |
|---|---|---|
| `current_question_id` | Current KT1 `question_id` | Known only after the question is presented; high-cardinality categorical feature. |
| `current_part` | Question-content `part` joined by current question ID | Pre-answer item metadata; categorical, not ordinal by default. |
| `current_skill_tags` | Question-content `tags` joined by current question ID | Semicolon-separated tags; missing/sentinel tags are empty. |
| `n_prior_logged_events` | Count of earlier source rows for this learner | Includes blank-answer events and preserved duplicate rows; not an answered-attempt count. |
| `n_prior_answered_attempts` | Earlier events with a derivable submitted-answer correctness label | Blank/unlabelled events do not increment it; preserved duplicates do. |
| `n_prior_correct` | Correct labels among those earlier answered attempts | Strictly prior; no target-row outcome is included. |
| `prior_accuracy` | `n_prior_correct / n_prior_answered_attempts` | Empty when no earlier labelled response; keep the count feature to distinguish no history. |
| `recent_5_accuracy` | Accuracy over the latest up to five earlier labelled responses | Uses only preceding outcomes; empty with no history. |
| `recent_10_accuracy` | Accuracy over the latest up to ten earlier labelled responses | Uses only preceding outcomes; empty with no history. |
| `recent_accuracy_trend_5` | Accuracy in the latest five prior labelled responses minus the preceding five | Present only after ten prior labelled responses. |
| `previous_response_correctness` | Correctness of the most recent earlier labelled response | Skips blank/unlabelled events; does not read the current target. |
| `previous_response_skill_tags` | Tags on that most recent earlier labelled response | Historical item metadata; semicolon-separated. |
| `previous_elapsed_time_ms` | Nonnegative elapsed time from the immediately preceding logged event | The target event's elapsed time is excluded. Empty if the prior duration is unavailable. |
| `gap_since_previous_question_ms` | Current question-given timestamp minus the preceding logged event timestamp | A difference, not absolute clock time. Equal timestamps produce zero and retain file order. |
| `prior_skill_tag_attempts` | Sum of earlier labelled response/tag incidences for the current question's tags | Multi-tag events contribute once per matching tag; empty if current tags are unavailable. |
| `prior_skill_tag_correct` | Correct incidences among those earlier response/tag pairs | Uses only labels from earlier rows. |
| `prior_skill_tag_accuracy` | Correct incidences divided by prior tag incidences | Zero when current tags exist but have no prior history; empty when tags are unavailable. |

The canonical field `session_id` preserves KT1 `solving_id`, which EdNet describes as a learning-session/bundle-associated identifier. It is not included as a numeric model feature because its integer value is an identifier rather than a meaningful scale. KT1 has no `event_type` column, so no event type is fabricated. `deployed_at` is not a feature because the timestamps are shifted and cross-table temporal availability is not established.

## Historical update order

For each learner, compute a row's features from state accumulated before that row. Then, if its target is derivable, add its label and known tags to the history state for the next source row. Every row advances logged-event count and event timestamp. Unlabelled rows do not update correctness or skill accuracy. Exact duplicates are explicitly flagged but, under the primary preserve policy, are treated as additional logged and labelled events.

No feature uses future questions or answers. The `FEATURE_COLUMNS` constant in `src/mcp_ri/ednet_preprocessing.py` is the authoritative feature whitelist; `assert_no_target_leakage` rejects target and post-response fields in that whitelist.

## Not implemented

No item difficulty estimate, learner ability estimate, imputation, vocabulary, scaling, feature selection, deep model, or response-choice encoding is fitted here. Such transformations belong to the training pipeline and must be learned using training data only. Absolute date/time features are excluded because the source timestamps are shifted.
