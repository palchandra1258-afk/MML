# MCP-RI: Multimodal Cognitive Perception and Representation Intelligence

This repository contains the MCP-RI research specification, technical planning, EdNet KT1 data validation and preprocessing pipeline, and baseline and advanced tabular experiments. The current EdNet experiment predicts **next submitted-answer correctness** as a behavioral outcome; it is not a direct measurement of understanding, confusion, or cognitive state.

## Research records

- The primary research specification is `MML-Research-Project (1).md`.
- Architecture, dataset, preprocessing, split, feature, and experimental decisions are documented under `docs/`.
- Phase 6 baseline and Phase 7 tree-model reports are in `docs/`.
- Unique run configurations and measured metrics are saved under `results/reports/phase7-*`.

## Data and licensing

EdNet raw and processed interaction data are not committed. Acquire data only through the documented official procedure and follow the dataset's CC BY-NC 4.0 terms and attribution requirements. The repository `.gitignore` excludes raw archives and generated row-level tables. Experiment reports describe the exact dataset, split, feature whitelist, and run settings.

## Training environment

The project used a Python environment with dependencies listed in `requirements-training.txt`. The Phase 7 XGBoost model was trained with XGBoost 3.1.3. Data paths can be configured through the scripts' `--data-root` option or `MCP_RI_DATA_DIR`.

The tabular training and resumption entry points are:

```bash
python scripts/training/train_ednet_baselines.py --data-root data --output-root .
python scripts/training/train_ednet_advanced.py --data-root data --output-root .
python scripts/training/resume_ednet_xgboost.py --data-root data --output-root .
```

The training scripts use the unseen-learner protocol and reserve the test partition. Review each run configuration before repeating a training job.

## Tests

Run the test suite in an environment with the training requirements installed:

```bash
python -m unittest discover -s tests -v
```
