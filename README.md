# MCP-RI: Multimodal Cognitive Perception and Representation Intelligence

This repository contains the MCP-RI research specification, technical planning, EdNet KT1 validation and preprocessing pipeline, behavioral prediction experiments, and Phase 9–13 learner-state, representation-planning, and trajectory-orchestration components. EdNet correctness is an observed behavioral outcome; neither the predictors nor the state summaries directly measure understanding, confusion, or cognitive state.

## Research records

- The primary research specification is `MML-Research-Project (1).md`.
- Architecture, dataset, preprocessing, split, feature, experimental, and trajectory decisions are documented under `docs/`.
- Phase 6–8 model reports and Phase 9–12 state/representation methodology and evaluation are in `docs/`.
- Unique configurations and results are saved under `results/reports/`.

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

## Phase 9 learner states

Phase 9 emits one JSON state per unseen-learner validation learner from the existing processed EdNet table. States summarize observed correctness by learner and available skill tags, with recent windows, a Beta(1,1)-smoothed response-performance estimate, Wilson intervals and evidence tiers. Potential-issue flags indicate patterns for investigation; they are not diagnoses. Existing trained models are not loaded or retrained by this module.

```bash
python3 -m unittest -v tests/test_learner_state.py
python3 scripts/learner_state/build_and_evaluate.py
```

The script creates a new timestamped report directory and refuses to overwrite one. It streams the processed table once. See `docs/LEARNER_STATE_ARCHITECTURE.md`, `docs/LEARNER_STATE_METHODOLOGY.md`, and `docs/LEARNER_STATE_EVALUATION.md` for schema, assumptions, measured results and limits. No cognitive-state ground truth is available in EdNet.

## Phase 10 evidence records

Phase 10 adds versioned evidence records and adapters for EdNet interactions, caller-provided text, audio references/WAV metadata, visual references/image metadata, and references to Phase 9 behavioral snapshots. Only EdNet interaction evidence is validated against real learner data; the text/audio/visual adapters use synthetic fixtures. The code preserves missingness, provenance, possible duplicates, unresolved conflicts, and uncertain alignment. It does not run ASR/OCR, learned multimodal fusion, or cognitive diagnosis. See [`docs/MULTIMODAL_EVIDENCE_ARCHITECTURE.md`](docs/MULTIMODAL_EVIDENCE_ARCHITECTURE.md), [`docs/MODALITY_AVAILABILITY_REPORT.md`](docs/MODALITY_AVAILABILITY_REPORT.md), and [`docs/PHASE10_EVALUATION.md`](docs/PHASE10_EVALUATION.md).

```bash
python3 -m unittest discover -s tests/test_evidence -v
python3 scripts/evidence/inspect_modality_availability.py
python3 scripts/evidence/build_evidence_records.py --sample-size 1000
```

The evidence builder streams until it has the requested number of distinct validation learners and a chronological integration trace. Its default sample takes one labeled event per learner and is a coverage sample, not a population estimate. It does not normalize or evaluate locked-test examples and refuses to overwrite an existing run directory.

## Phase 11 cognitive-state estimates

Phase 11 adds a separate, versioned estimator in `src/mcp_ri/cognitive_state/`. It projects complete Phase 9 response-history snapshots and Phase 10 evidence into provisional concept-status categories, traceable hypotheses, separate uncertainty dimensions, and diagnostic-information recommendations. It leaves Phase 9 calculations and schema unchanged. The categories are behavioral rules, not validated cognitive states or diagnoses; EdNet has no cognitive-state ground truth. Text, audio, and visual paths are interface-tested with synthetic fixtures only.

```bash
python3 -m unittest discover -s tests/test_cognitive_state -v
python3 scripts/cognitive_state/build_cognitive_state_sample.py --sample-learners 100 --checkpoints 5 10
python3 scripts/cognitive_state/validate_cognitive_states.py results/reports/<run>/cognitive_states.jsonl
```

The bounded run uses validation learners only and does not evaluate locked-test examples. It creates a new timestamped report directory. See [`docs/COGNITIVE_STATE_ARCHITECTURE.md`](docs/COGNITIVE_STATE_ARCHITECTURE.md), [`docs/COGNITIVE_STATE_METHODOLOGY.md`](docs/COGNITIVE_STATE_METHODOLOGY.md), [`docs/COGNITIVE_STATE_SCHEMA.md`](docs/COGNITIVE_STATE_SCHEMA.md), and [`docs/COGNITIVE_STATE_EVALUATION.md`](docs/COGNITIVE_STATE_EVALUATION.md) for contracts, thresholds, measured descriptive coverage, and limitations.

## Phase 12 representation plans

Phase 12 turns Phase 11 concept estimates into auditable, versioned representation recommendations. The planner records evaluated rules, evidence, contradictions, rejected alternatives, content grounding, capability status and teaching context. It does not generate content or execute interventions. The default registry marks all representation delivery unavailable; a category is selected only when a provider or concrete content IDs are registered. EdNet skill/question metadata grounds identifiers but does not supply validated concept names, objectives, prerequisites or examples.

```bash
python3 -m unittest discover -s tests/test_representation -v
python3 scripts/representation/build_representation_plans.py --max-plans 10000
python3 scripts/representation/evaluate_representation_plans.py results/reports/<run>/representation_plans.jsonl --states results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl --output results/reports/<run>/evaluation.json
python3 scripts/representation/inspect_representation_plan.py results/reports/<run>/representation_plans.jsonl <plan_id>
```

The builder reads the bounded Phase 11 validation output and the small EdNet question/lecture metadata archive. It does not load processed interactions or evaluate locked-test data. See [`docs/REPRESENTATION_INTELLIGENCE_ARCHITECTURE.md`](docs/REPRESENTATION_INTELLIGENCE_ARCHITECTURE.md), [`docs/REPRESENTATION_TAXONOMY.md`](docs/REPRESENTATION_TAXONOMY.md), [`docs/REPRESENTATION_AVAILABILITY.md`](docs/REPRESENTATION_AVAILABILITY.md), [`docs/REPRESENTATION_PLAN_SCHEMA.md`](docs/REPRESENTATION_PLAN_SCHEMA.md), [`docs/REPRESENTATION_DECISION_METHODOLOGY.md`](docs/REPRESENTATION_DECISION_METHODOLOGY.md), and [`docs/REPRESENTATION_EVALUATION.md`](docs/REPRESENTATION_EVALUATION.md).

## Phase 13 learning trajectories and diversions

Phase 13 adds versioned primary trajectories, explicit transition rules, conservative prerequisite-review diversions, compact context snapshots, progress/revision records, resumption and replanning decisions, and append-only history reconstruction. The default dependency registry is empty because EdNet skills do not encode prerequisites. Manually configured links are labeled, and synthetic links are excluded unless a test explicitly enables them. The Phase 13 core history object remains in-memory; Phase 14 wraps the supported trajectory operations with durable SQLite records. Recommendations do not prove a prerequisite gap or mastery.

```bash
python3 -m unittest discover -s tests/trajectory -v
python3 scripts/trajectory/build_trajectory_sample.py --max-trajectories 100
python3 scripts/trajectory/evaluate_trajectory.py results/reports/<run> \
  --states results/reports/phase11-cognitive-state-20261106T104113Z/cognitive_states.jsonl
python3 scripts/trajectory/validate_trajectory_history.py results/reports/<run>
```

See [`docs/LEARNING_TRAJECTORY_ARCHITECTURE.md`](docs/LEARNING_TRAJECTORY_ARCHITECTURE.md), [`docs/TRAJECTORY_STATE_MACHINE.md`](docs/TRAJECTORY_STATE_MACHINE.md), [`docs/DIVERSION_DETECTION_METHODOLOGY.md`](docs/DIVERSION_DETECTION_METHODOLOGY.md), and [`docs/TRAJECTORY_EVALUATION.md`](docs/TRAJECTORY_EVALUATION.md). The sample uses validation snapshots and does not read locked-test or raw/processed interaction tables.

## Phase 14 backend API and persistence

Phase 14 adds a FastAPI service under `/api/v1`, generated OpenAPI contracts, read-only access to Phase 9–12 result snapshots, Phase 10 grouping/alignment annotations, and SQLite persistence for caller-authored Phase 13 trajectories and append-only event/version history. A byte-offset index avoids copying the 2.6 GB Phase 9 state file into SQLite or loading it at server startup. The API uses Phase 13 validation for trajectory creation and actions; it does not seed placeholder objectives from Phase 13 sample reports. Authentication and model inference remain unavailable, and diversion mutations are not exposed.

```bash
python3 -m venv .venv-api
.venv-api/bin/python -m pip install -r requirements-api.txt
PYTHONPATH=src .venv-api/bin/python scripts/api/index_artifacts.py
PYTHONPATH=src .venv-api/bin/uvicorn mcp_ri.api.main:app --reload --host 127.0.0.1 --port 8000
```

The artifact index is a one-time sequential read of configured JSONL outputs; it stores IDs, timestamps, links, and byte offsets only. Health remains degraded until indexing finishes. Local API and frontend integration details are in [`docs/PHASE14_BACKEND_ARCHITECTURE.md`](docs/PHASE14_BACKEND_ARCHITECTURE.md) and [`shared/api-contracts/README.md`](shared/api-contracts/README.md).

## F9 Student Learning Studio

F9 adds a separate student experience at `/studio` with curated subject and topic discovery, seven complete lessons, backend-evaluated practice, saved section progress, history, and a local demo profile. Student attempts become normalized Phase 10 evidence and feed an aggregate Phase 9 response summary with no EdNet skill mapping. The research workspace remains available through the visible workspace switch. Authentication, cognitive inference, representation delivery, validated prerequisites, and adaptive trajectories are not claimed. See [`docs/F9_ARCHITECTURE_AUDIT.md`](docs/F9_ARCHITECTURE_AUDIT.md) and [`docs/F9_STUDENT_LEARNING_ENGINE.md`](docs/F9_STUDENT_LEARNING_ENGINE.md).

## Frontend

The Next.js 16 App Router application is in [`frontend/`](frontend/), with its route inventory, environment setup, and implementation notes in [`frontend/README.md`](frontend/README.md). After starting the backend above, start the frontend with:

```bash
cd frontend
npm install
npm run dev
```

The interface reads the backend API when configured. Synthetic walkthrough data requires the explicit `NEXT_PUBLIC_USE_MOCK_DATA=true` setting; it is not presented as learner data by default.

## Tests

Run the test suite with both the training and deep-learning requirements installed:

```bash
python -m unittest discover -s tests -v
```

The deep-learning requirements currently pin a CUDA PyTorch build; choose a compatible PyTorch install for CPU-only environments before running the sequence-model tests.
