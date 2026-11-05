# Temporal Knowledge Tracing Experiment Design

## Research scope

This experiment advances the temporal-model stage of MCP-RI using the only learner-level dataset currently acquired in this workspace: EdNet KT1 plus its question-content table. The exact target is whether a submitted answer matches the official answer key. This is a behavioral response-outcome prediction task. It does not directly measure understanding, confusion, cognitive state, misconception, representation need, or learning benefit.

The research reference says the full multimodal perception-to-representation loop is not covered by one public dataset. EdNet KT1 has question/answer interactions and metadata, but no learner speech, webcam video, diagrams, physiological channels, cognitive-state labels, representation assignments, or post-representation outcomes. This experiment can evaluate a temporal behavioral component only.

## Question and comparison

**Question:** Does a learned sequence model improve prediction of a learner's next submitted response over the existing static-history/tabular models, when trained and assessed on the same EdNet unseen-learner protocol?

Models:

- DKT-style LSTM: observed question/correctness interaction embeddings feed an LSTM; each hidden state predicts the response to the next question among the train-vocabulary question IDs.
- SAKT-style causal cross-attention: the next question is a query, and attention reads only the preceding question/correctness interactions.
- Existing reference models: prevalence, last-response persistence, historical accuracy, Phase 6 SGD logistic regression, Phase 7 Random Forest, and the 600-round resumed XGBoost model.

The neural models are trained from scratch. No pretrained education model is fine-tuned. The PyTorch implementation follows the sequential prediction setup of DKT and SAKT; it is a task-specific implementation, not a claim to reproduce every original paper setting.

## Prediction contract

At target position `t`, the model sees the current question `q_t` and only earlier labeled interactions `(q_i, y_i)` for `i < t`. It predicts `y_t`, where `y_t` is derived from the submitted answer and the official key. The current submitted answer, current correctness label, answer key, current elapsed time, future events and future correctness labels are not inputs.

EdNet rows without a derivable correctness label are excluded from sequence training and evaluation; the observed quality audit found 27,646 such rows across the full dataset. Exact duplicates are retained, matching the existing preprocessing policy. Equal timestamps preserve source-file order. Question IDs use the Phase 6 training-sample vocabulary plus an unknown bucket, so validation response outcomes do not fit the vocabulary.

Each learner's sequence is divided into overlapping contiguous windows of at most 200 interactions. The overlap carries one observed interaction across a training-window boundary so every available next-response transition is supervised. Hidden state is reset at window boundaries; the same windowing rule is used at validation time. The first response per learner has no preceding response and is excluded from the sequence-model comparison. Tabular predictions are scored on exactly the same post-cold-start rows for the matched comparison.

## Split and selection protocol

- Training uses the deterministic 5% learner-level sample from the existing unseen-learner training partition (seed 2025), preserving the Phase 6/7 comparison budget and sample.
- Validation learners are divided deterministically by learner hash into 10% early stopping, 10% calibration, and 80% report-only groups. All events for a learner stay in one role.
- Early stopping minimizes binary cross-entropy on the early-stop learner group. The separate calibration learner group fits a single temperature per model. Main results are reported on the remaining validation learners.
- The locked test partition is not read for labels, calibration, tuning or metrics.
- Results on this validation report cohort are development evidence, not a final test estimate.

## Training configuration

Both networks use 128-dimensional embeddings/hidden states, dropout 0.2, AdamW with learning rate `1e-3` and weight decay `1e-5`, binary cross-entropy, gradient-norm clipping at 1.0, maximum 8 epochs, and patience 2 for early stopping. DKT uses a one-layer LSTM; SAKT-style uses four attention heads and a position embedding with causal masking. Batches are padded and padding is excluded from loss. The implementation uses the available CUDA GPU when PyTorch detects it, otherwise CPU.

All parameters are fit on the training sample. Training/calibration/reporting metadata, model weights, metric tables, calibration bins, and runtime/memory information are saved under unique Phase 8 experiment IDs. PyTorch and CUDA versions are recorded. No dataset file is modified.

## Metrics and uncertainty

On the same report-only validation rows, report accuracy, precision, recall, F1, ROC-AUC, average precision, log loss, Brier score, and 15-bin equal-width ECE. Fit temperature scaling by minimizing calibration-set log loss, then report raw and scaled probability metrics on the report-only learners. Report reliability bins and a reliability figure.

Compute 1,000 learner-cluster bootstrap draws for per-learner mean log loss, Brier score and accuracy. Compute paired learner-cluster intervals for sequence-model differences versus logistic regression. These are uncertainty estimates for the validation cohort, not population guarantees. Attention weights and hidden states are not treated as causal explanations or feature importance.

## Interpretation and limitations

The main comparison measures whether item-response sequence information improves held-out-learner response prediction in EdNet's TOEIC practice domain. It does not validate the project’s multimodal hypothesis. EdNet's large number of response rows does not make the number of independent learners or domains equally large. The question vocabulary and histories are available for inference only under the defined after-question-presentation protocol. Current item identity can encode item selection/difficulty structure. Random learner splits allow the same questions in train and validation, so unseen-question generalization is not evaluated.

Results cannot be called equivalent or superior to papers unless the task, dataset, preprocessing, split, target, and metric protocol match. Published benchmark scores are not directly comparable to this local protocol. No expected result is specified in advance; the sequence models may underperform the logistic baseline.

## References

- Piech et al., [Deep Knowledge Tracing](https://arxiv.org/abs/1506.05908), 2015.
- Pandey and Karypis, [A Self-Attentive model for Knowledge Tracing](https://arxiv.org/abs/1907.06837), 2019.
- Ghosh, Heffernan and Lan, [Context-Aware Attentive Knowledge Tracing](https://arxiv.org/abs/2007.12324), KDD 2020. AKT is a potential later implementation; this run uses the lower-complexity DKT/SAKT-style comparisons first.
- Choi et al., [SAINT+: Integrating Temporal Features for EdNet Correctness Prediction](https://arxiv.org/abs/2010.12042), 2020.
- Liu et al., [pyKT: A Python Library to Benchmark Deep Learning based Knowledge Tracing Models](https://arxiv.org/abs/2206.11460), 2022. Its standardized setup includes one-step-ahead evaluation and sequence lengths up to 200; its target, split, preprocessing and tuning protocol still differ from this project.
- [Official PyTorch installation instructions](https://pytorch.org/get-started/locally/).
