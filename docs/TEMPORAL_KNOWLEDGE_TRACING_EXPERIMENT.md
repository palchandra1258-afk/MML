# Phase 8: Temporal Response Prediction with DKT and SAKT

**Experiment:** `phase8-temporal-20261105T073420Z-seed2025`

**Status:** Completed; validation only. No test labels were used, and the test partition was not evaluated.

## Question and claim boundary

This experiment asks whether a learner's sequence of prior question IDs and recorded response correctness can predict the correctness of a later submitted answer. It evaluates a behavioral outcome. It does **not** measure understanding, confusion, mastery, confidence, or any other cognitive state. EdNet contains no labels for those constructs.

Two sequence architectures were trained from scratch: an LSTM based on Deep Knowledge Tracing (DKT) and a causal self-attention model in the SAKT family. DKT introduced recurrent sequence modeling for this next-response task; SAKT uses the current exercise as a query over prior question-response interactions. These architectures are useful modeling references, but a latent vector or attention weight is not a validated cognitive-state measure ([DKT](https://arxiv.org/abs/1506.05908), [SAKT](https://arxiv.org/abs/1907.06837)).

## Data and leakage controls

- Processed source: `data/processed/ednet/ednet_kt1_features.csv.gz` (5,888,235,415 bytes); original archives were left unchanged.
- The existing unseen-learner split was retained. The same deterministic 5% sample of training learners used for Phases 6–7 supplied training data: **27,310 learners**, **3,255,537 labeled interactions**, and **3,228,227 within-learner next-response transitions**.
- The question vocabulary came from the existing training-only encoder and has 12,180 entries including an unknown-item bucket. There were 741 validation question IDs mapped to that bucket.
- Validation learners were deterministically assigned by learner ID hash to disjoint early-stopping, calibration, and report-only groups. Actual counts were 11,790 / 11,728 / 94,266 learners, respectively. Role assignment is at learner level, so a learner cannot appear in more than one role.
- Early-stopping received 1,411,811 next-response transitions; calibration received 1,324,710 transitions; report-only evaluation received **11,382,220 transitions from 90,982 learners**.
- The report-only role contained 11,476,486 labeled response rows before removing each learner's first response. The first response has no prior interaction and therefore has no sequence-model prediction; 94,266 such cold-start rows were omitted for *all* models in the matched comparison.
- Within each learner, the preprocessed source order was retained. Overlapping windows of at most 200 interactions preserve the sequence; a window stride of 199 means each next-response target is scored once. The current target correctness, answer, and post-response elapsed time are not supplied as features. No future response is used to construct a preceding prediction.
- DKT uses the past question/correctness pairs to produce logits for the item vocabulary, then selects the logit for the current question. SAKT uses the current question as its query and only earlier question/correctness pairs as causal keys and values.
- The two networks use question ID and prior correctness only. They do not use question text, skill tags, current correctness, current answer, current elapsed time, audio, images, or video.
- Validation labels were used only in the designated early-stop or calibration role, or for the final report-only score. Test rows were skipped for training/scoring; no test correctness values were used and no test scores were calculated.

The sequence setup follows the common next-response prediction formulation, but the evaluation protocol matters: knowledge-tracing benchmark work has documented that different preprocessing and leakage-prone evaluation settings can materially change results ([pyKT benchmark paper](https://arxiv.org/abs/2206.11460)).

## Models and training

| Model | Architecture trained from scratch | Optimizer and loss | Best checkpoint selection |
|---|---|---|---|
| DKT | One-layer LSTM; 128-dimensional interaction embeddings and hidden state; 0.2 dropout; output projection across 12,180 question IDs | AdamW, learning rate 0.001, weight decay 1e-5; masked binary cross-entropy | Minimum early-stop log loss; selected epoch 2 of 4 |
| SAKT-style | One causal attention block; 128 dimensions; four attention heads; question and position embeddings; prior interaction embeddings; 4x feed-forward layer; 0.2 dropout | AdamW, learning rate 0.001, weight decay 1e-5; masked binary cross-entropy | Minimum early-stop log loss; selected epoch 4 of 6 |

Both models used seed 2025, maximum window length 200, gradient norm clipping at 1.0, batch sizes 32 (DKT) and 96 (SAKT), maximum 8 epochs, and patience 2. Padding positions were masked out of the loss. No pretrained weights or open-source model checkpoints were used. The architecture choices were implemented in the project training script; the cited papers informed the design rather than supplying copied result claims.

## Results

On the matched report-only validation cohort, SAKT achieved 0.713321 accuracy, 0.746430 ROC-AUC, 0.841102 average precision, 0.555102 log loss, and 0.187996 Brier score. The existing SGD logistic model on these same rows scored 0.708493, 0.742434, 0.836592, 0.563414, and 0.191093, respectively. SAKT's F1 was lower (0.795652 vs 0.803036). DKT's accuracy and probability scores improved over logistic, but its ROC-AUC was slightly lower and its F1 was also lower. This comparison matches target, learner partitions, report rows, and scoring, but the input pipelines differ: logistic uses engineered item/skill/history features; the sequence models use question ID and prior response correctness. It therefore does not isolate architecture effects. Full metrics, calibration-adjusted scores, and paired intervals are in [PHASE8_SEQUENCE_MODEL_COMPARISON.md](PHASE8_SEQUENCE_MODEL_COMPARISON.md) and the machine-readable run report.

One important qualification is the estimand: row-weighted SAKT accuracy was higher than logistic, while the learner-macro paired accuracy difference was small and its 95% interval crossed zero. DKT's learner-macro accuracy difference favored logistic even though its row-weighted accuracy was higher. A gain in pooled interaction metrics therefore should not be read as a uniform gain for the typical learner.

The most directly comparable published EdNet reference located here, SAINT+, reports 0.7252 accuracy and 0.7914 ROC-AUC. Its experiment used a different updated EdNet version, a recent-100K-learner test cohort, a much larger training set, and larger/tuned model configurations; it used test evaluation, whereas this experiment did not. Our results are not a like-for-like comparison and do not establish equivalence or superiority. The numbers are a research reference, not a promised target ([SAINT+ paper and protocol](https://arxiv.org/html/2010.12042)).

## Compute and reproducibility

- Hardware: NVIDIA RTX 4000 Ada Generation, 20,475 MiB VRAM.
- Software: Python 3.12.3, PyTorch 2.14.1+cu130, CUDA runtime 13.0, scikit-learn 1.9.1, XGBoost 3.1.3, NumPy 2.5.4.
- End-to-end elapsed time: 2,260.1 seconds (37 minutes 40 seconds), including the 95-million-row stream, baseline scoring, sequence inference, calibration, and uncertainty analysis.
- Model fit time: DKT 76.2 seconds; SAKT 45.4 seconds. Peak process RSS was 4,811,052 KiB (~4.59 GiB); peak allocated GPU memory was 724,005,376 bytes (DKT) and 396,696,576 bytes (SAKT).
- The run records all hyperparameters, epoch histories, data hashes, software versions, counts, and checkpoint paths in `results/reports/phase8-temporal-20261105T073420Z-seed2025/experiment.json`.

Install the project's pinned training dependencies and CUDA PyTorch wheel in a Python environment with a compatible NVIDIA driver, then run from the project environment with validated data and Phase 6–7 model artifacts available:

```bash
python3 -m pip install -r requirements-training.txt
python3 -m pip install -r requirements-deep-learning.txt
python3 scripts/training/train_ednet_sequence_models.py \
  --seed 2025 --max-epochs 8 --patience 2 \
  --batch-size-dkt 32 --batch-size-sakt 96 --max-sequence-length 200
```

The first attempt, `phase8-temporal-20261105T070210Z-seed2025`, is retained with status `failed`: its SAKT attention-mask shape did not match the interaction sequence. That run produced no evaluation results. The mask/input alignment was corrected before the completed run; the failed run must not be cited as an experiment.

The focused CPU smoke suite passed all six checks (checkpoint save/load, fixed-seed initialization, future-response leakage guard, windowed prediction coverage and probability range, feature-whitelist/metric contract, and deterministic learner-role assignment):

```bash
python3 -m unittest -v tests/test_ednet_sequence_models.py
```

## Artifacts

- Training script: [`scripts/training/train_ednet_sequence_models.py`](../scripts/training/train_ednet_sequence_models.py)
- Run report: [`experiment.json`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/experiment.json)
- Raw and temperature-scaled metric table: [`validation_metrics.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/validation_metrics.csv)
- Learner-clustered intervals: [`learner_bootstrap.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/learner_bootstrap.csv) and [`paired_learner_bootstrap_vs_logistic.csv`](../results/reports/phase8-temporal-20261105T073420Z-seed2025/paired_learner_bootstrap_vs_logistic.csv)
- Reliability plot: [`phase8-temporal-20261105T073420Z-seed2025_reliability.svg`](../results/figures/phase8-temporal-20261105T073420Z-seed2025_reliability.svg)
- Weights: `models/trained/sequence_models/phase8-temporal-20261105T073420Z-seed2025/{dkt,sakt}/model.pt`

## Limitations and next step

This is a single-seed, 5%-training-learner experiment with a compact, one-block SAKT-style model. There was no broad hyperparameter search, full-data training, time-forward assessment, test evaluation, or multimodal input. The bootstrap quantifies learner-sampling uncertainty conditional on this fitted run; it does not include variation from retraining with different seeds or train samples. Attention weights and learned embeddings were not treated as feature importance or explanation. There are no causal claims.

For the EdNet component, the next rigorous step is to predeclare the training scale and model selection criterion, then retrain *all compared models* under the same expanded training learner set before a locked test evaluation. The held-out test remains untouched until that plan is fixed. Separately, the MCP-RI multimodal cognition and representation-intervention claims still need suitable labels and prospective data; EdNet cannot validate them.
