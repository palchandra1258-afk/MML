# First Model: Data Requirements and Feasibility

## Decision

The initial model is a **next submitted-response correctness predictor**. EdNet KT1 is the best currently verified dataset among the requested candidates for this experiment. CMU DataShop remains attractive for mathematical domain alignment but its project-specific access, schema and size were not verifiable here. If DataShop later passes the checklist below, use it as a math-domain replication or substitute.

The target is observed answer correctness—not confusion, understanding, uncertainty or representation mismatch.

## EdNet fields and target construction

The official EdNet README describes KT1 as one CSV per student with question-solving logs. Documented KT1 fields include:

| Field | Use |
|---|---|
| Student-specific filename / user ID | Learner grouping and leakage-safe split; verify whether ID is explicit in file or encoded by filename in the selected archive. |
| `timestamp` | Sort events chronologically within learner; the repository says timestamps are shifted from real values for security. |
| `solving_id` | Group/bundle/session-like context; repository describes it as a per-student learning session associated with each bundle. Do not assume it is a conventional login session. |
| `question_id` | Current item identity and join key to released question metadata. |
| `user_answer` | Submitted answer for the current question. Use only to derive target after prediction; never include current response as an input. |
| `elapsed_time` | Response duration. For predicting correctness before answer submission, exclude the current question's elapsed time because it is only known after responding. Prior-question elapsed times may be features. |
| Question content: `correct_answer` | Join by question ID and derive binary target: `1` if submitted answer equals answer key; else `0`. |
| Question content: `tags` | Available question/skill metadata for current question if nonmissing and correctly joined. Keep mapping fitted/processed without test outcomes. |
| Question content: `bundle_id`, `part`, `deployed_at` | Optional current-item context; check exact schema and consider whether deployed_at creates temporal leakage or merely item metadata. |

The official repository lists the content table as containing question ID, bundle ID, explanation ID, correct answer, part, tags and deployed_at. The response correctness label is thus **derived from released answer keys**, not supplied as a cognitive annotation. Verify answer-key coverage, response encoding and rows with missing/ambiguous answer keys before training.

### Training example construction

For each learner `u`, create a chronological sequence of response records. For response position `j`, construct an example:

```text
X(u,j) = [current question_id / tags / bundle metadata,
          history of responses at positions < j,
          history of prior correctness labels,
          prior elapsed times and sequence counts where appropriate]
y(u,j) = 1[user_answer(u,j) == correct_answer(question_id(u,j))]
```

The first response has no learner history and can be excluded from the history-conditioned model or retained as a cold-start case in a separate baseline. All features must be available at the intended prediction time. Specifically:

- Exclude current `user_answer`, current `is_correct` (derived target), and current `elapsed_time` from `X`.
- Avoid using future questions, later attempts, post-answer explanations, or any dataset-generated mastery/proficiency state computed using the target response unless its timestamp and computation cutoff are proven safe.
- Compare an item-only baseline (question ID/tags) and history-only baseline against combined item + prior history.
- A target example predicts a submitted answer, not the UI's intermediate answer selection. KT1 contains the final question-response sequence; KT2 can support a separate experiment for multiple `respond` events followed by `submit`.

## Chronology and sequence preservation

1. Process each learner file independently and sort by numeric timestamp. Preserve original row order and solving/bundle IDs for tie-breaking and diagnostics.
2. The EdNet source states timestamps are fixed-shifted for security. The shift should preserve order if consistently applied, but inspect timestamp ties and per-user monotonicity during the later data audit.
3. Keep all questions from one bundle in their original order; do not randomize events. Report whether the prediction decision occurs before a bundle or before each question, because this changes which same-bundle responses are legal history.
4. For the first clean task, predict each question's outcome from strictly earlier submitted responses. A more deployment-faithful within-bundle task can be a separate analysis with a prespecified availability rule.
5. Fit feature encoders/scalers using training learners only. Avoid generating rolling target features using a response that occurs at or after the example's target time.

## Learner-level splitting and leakage prevention

- Split learner IDs before expanding events into examples. All examples for one learner must stay in a single partition.
- Prefer train/validation/test grouped by learner (e.g. 70/15/15 as a planning starting point; choose final percentages after counts/class balance audit). Do not split randomly by response rows.
- Tune model/features only using grouped validation. Use the test set once after decisions are frozen.
- To assess temporal deployment, add a distinct time-forward evaluation. Since EdNet timestamps are shifted, use within-learner order or dataset sequence positions rather than interpreting absolute calendar time.
- If training and test learners have identical item IDs, that tests new learners on known items. Add an optional item/skill-held-out split if generalization to unseen questions is a research question.
- Report number of learners and examples per split, class prevalence, answer-key coverage, missing fields, duplicate/tied times and the number of excluded examples.

## Baselines and model choice

1. **Majority/prevalence baseline:** predict training-set class prior; provides a minimum reference.
2. **Persistence / learner-history baseline:** use a simple prior correctness rate (overall, recent window, and per-tag only when enough history exists). This is a transparent knowledge-tracing baseline.
3. **Item-only logistic regression:** question ID/tags/bundle metadata predicts response correctness without learner history.
4. **History-only logistic regression:** prior correctness counts/rates, attempt counts and prior elapsed-time summaries.
5. **Combined logistic regression:** item + prior-history features. This is appropriate because the target is binary, features can be encoded sparsely and model coefficients offer an interpretable baseline. Use regularization and handle class imbalance only within training data.
6. **Gradient-boosted trees:** compare nonlinear interactions on tabular summaries. Keep hyperparameter search bounded and learner-grouped.
7. **Sequence model later:** GRU or temporal convolution on ordered response/item events, only after the static models and leakage checks are complete. Deep sequential models are not presumed superior.

Logistic regression is a sound first trained model if there are enough independent learners, both outcome classes, and a sparse-feature/preprocessing strategy. Its performance will be limited by item/learner heterogeneity and the chosen split; that is useful scientific information, not a reason to skip it.

## Metrics

For binary correctness, report:

- AUROC and AUPRC (especially if correctness classes are imbalanced);
- macro-F1, balanced accuracy, precision, recall and confusion matrix at a threshold selected on validation data;
- log loss and Brier score for probability quality;
- calibration plot/ECE with binning method and sample counts;
- learner-grouped confidence intervals (e.g. bootstrap by learner), not row-independent intervals.

Accuracy may be included but should not be the only metric. No result is predicted in advance. Report per-item/tag analyses only when sample counts permit and label them exploratory otherwise.

## CMU DataShop feasibility checklist for the same model

DataShop's general export format supports `anon_student_id`, `session_id`, `time`, `problem_name`, `step_name`, `attempt_at_step`, `outcome`, input/selection and optional KC columns. To establish the same model is genuinely trainable on this exact project, verify the downloaded project export contains:

- multiple distinct anonymous learners and enough repeated response events;
- meaningful time/order and session semantics;
- an outcome value available per attempt (e.g. correct/incorrect) with documented coding;
- stable task/step identity and, if claimed, populated concept/KC mapping;
- train/validation/test splits with enough learner groups;
- appropriate dataset-specific terms and research-use permission.

Construct each example from strictly earlier transactions within the same learner; target the outcome on a future/current attempt and keep that outcome out of features. Feedback classification, tutor response and hint data generated after the target attempt must not leak into inputs. If timestamps only have date granularity or transactions cannot be aligned unambiguously, use transaction row/order semantics only if officially documented and preserve session boundaries.

Because current project-specific fields and access remain unverified, CMU DataShop cannot yet be called genuinely suitable for the first committed experiment. It can become the more domain-aligned primary after the checks pass.

## Sources

- [EdNet official README: hierarchy, user files, timestamps, KT1 fields and download links](https://github.com/riiid/ednet)
- [EdNet official question-content schema](https://github.com/riiid/ednet#contents)
- [DataShop official API schema](https://pslcdatashop.web.cmu.edu/api/DataShop%20Public%20API-v0.41.pdf)
- [DataShop access instructions](https://datashop.dev.datashop.org/help?page=access)
