# MCP-RI Repository Cleanup Audit

Audit date: 2026-11-11 (Asia/Kolkata)

This is the pre-cleanup baseline. The working tree already contained user changes before this audit; those changes are outside the cleanup baseline and must be preserved.

## Repository baseline

- Repository root: `/home/mml_07/Desktop/MML`
- Git root: repository root; no history rewrite or reset was performed.
- Initial working tree: 58 changed paths reported by `git status --short` (tracked edits and untracked user files).
- Initial inventory: 28,365 files and 3,087 directories, including ignored environments, dependencies, generated files, and Git internals.
- Initial disk usage: 11,064,567,057 bytes (`du -sb .`, about 11.1 GB decimal / 10.3 GiB).
- `git diff --check` was clean at audit time.

## Major directory sizes

| Directory | Initial bytes (du) | Notes |
|---|---:|---|
| `data/` | 7,105,884,160 | Raw and processed EdNet, local SQLite application database |
| `results/` | 2,880,364,544 | Timestamped research outputs, including large row-level reports |
| `frontend/` | 670,474,240 | Source, installed `node_modules`, Next build output and API test output |
| `.git/` | 218,501,120 | Existing repository objects and history |
| `.venv-api/` | 117,006,336 | Existing backend environment; retain and do not recreate |
| `.tools/` | 98,271,232 | Local GitHub CLI and downloaded package; retain pending owner review |
| `models/` | 62,394,368 | Baselines, preprocessing configuration, trained model checkpoints |
| `docs/` | 532,480 | Research, architecture, integration and methodology documents |
| `src/` | 1,179,648 | Python application source |
| `scripts/` | 647,168 | Data, training, research, and API scripts |
| `tests/` | 585,728 | Python tests and API tests |

Sizes are filesystem usage at audit time and can include directory allocation overhead. The frontend size includes dependency and build directories. The total is not equivalent to Git clone size.

## Largest individual files

| Bytes | Path | Classification |
|---:|---|---|
| 5,888,235,415 | `data/processed/ednet/ednet_kt1_features.csv.gz` | Large processed dataset; research input, preserve |
| 2,765,973,726 | `results/reports/phase9-learner-state-20261106T081823Z/validation_learner_states.jsonl` | Large validation output and API artifact source, preserve |
| 1,201,164,464 | `data/raw/ednet/ednet-kt1.zip` | Original raw dataset archive, preserve |
| 155,904,464 | `.git/objects/pack/pack-de96e63244912baa69d3538d68b026d452665e5c.pack` | Existing Git history, preserve |
| 40,641,748 | `results/reports/phase12-representation-20261106T110830Z/representation_plans.jsonl` | Research plans, preserve |
| 19,609,346 | `models/trained/sequence_models/phase8-temporal-20261105T073420Z-seed2025/sakt/model.pt` | Trained model checkpoint, preserve |
| 19,288,503 | `models/trained/sequence_models/phase8-temporal-20261105T073420Z-seed2025/dkt/model.pt` | Trained model checkpoint, preserve |
| 19,288,503 | `models/trained/sequence_models/phase8-temporal-20261105T070210Z-seed2025/dkt/model.pt` | Trained model checkpoint with distinct run provenance, preserve |
| 16,240,640 | `data/application/mcp_ri.sqlite3` | Local application database, preserve |

Other large representation plan outputs and validation reports remain under `results/reports/` and are treated as research records.

## Repository structure and functionality discovered

- Backend source is in `src/mcp_ri/`, including data processing, learner state, evidence, cognitive state, representation, trajectory and FastAPI modules.
- FastAPI application entry point exists at `src/mcp_ri/api/main.py`; the documented startup command uses `PYTHONPATH=src` and `.venv-api/bin/uvicorn`.
- Persistence uses local SQLite at `data/application/mcp_ri.sqlite3`; artifact indexing reads existing report files.
- Root Python tests cover preprocessing, models and the state/evidence/representation/trajectory components; `tests/api/` covers the API.
- Frontend uses Next.js App Router. `/` is explicit and `app/[section]/page.tsx` serves sections registered in `frontend/components/navigation/navigation-data.ts`: `/learning`, `/progress`, `/trajectory`, `/learner-state`, `/cognitive-state`, `/representations`, `/evidence`, `/research`, `/evaluation`, and `/system-status`.
- Frontend sources, API integration tests, typed research snapshot, and `package-lock.json` are present. The manifest declares Next.js, React, React DOM, ESLint, Tailwind and TypeScript dependencies; no dependency was identified for removal during this discovery pass.
- Documentation is already organized under root `docs/` and `frontend/docs/`; numerous similarly named reports describe distinct phases, methods or runs, so names alone are insufficient grounds for consolidation.

## Generated and local directories

- `.pytest_cache/`, Python `__pycache__/` directories, `frontend/.next/`, `frontend/.api-test-dist/`, and `frontend/tsconfig.tsbuildinfo` are local generated/cache artifacts and are not tracked by Git.
- `frontend/node_modules/` and `.venv-api/` are local installed environments; they are ignored and reproducible, but are retained because removing them disrupts the current development setup and offers a much larger, user-visible environment reset.
- `.tools/` is ignored, but contains an installed `gh` executable and its downloaded archive. It is not assumed disposable.
- Empty directories include data/model placeholders and Git metadata directories. No empty directory is removed based only on being empty.
- One 2,249-byte Next development log exists under `frontend/.next/dev/logs/next-development.log`. No `next dev`, Uvicorn or pytest process was running during audit. The log is in generated build output.

## Duplicate scan

SHA-256 comparisons were made for same-size files outside `.git/`, `.venv-api/`, `frontend/node_modules/`, `frontend/.next/`, and `.tools/`. The scan covered 528 files and found 11 groups of byte-identical files. It found no duplicate source files or static assets in the scanned project files.

- Two DKT checkpoint paths have identical bytes but different phase 8 run directories.
- Multiple Phase 13 timestamped report runs contain identical `trajectories.jsonl`, `decisions.jsonl`, `history_events.jsonl`, or summary JSON files.
- Several run manifests are byte-identical to their corresponding experiment metadata files.
- Empty JSONL files also hash identically across unrelated outputs.

These files retain run identity, layout, or provenance and are not removed. Identical content does not establish that the experiment record is redundant.

## Git and research safety

- `.gitignore` already ignores Python caches, `.pytest_cache/`, local environments/tools, EdNet raw and processed large files, local SQLite databases, and row-level report JSONL files. `frontend/.gitignore` already ignores `node_modules`, `.next`, `.api-test-dist`, TypeScript build info, and environment files while allowing `.env.example`.
- No generated cache paths were tracked by Git at audit time.
- Existing tracked and untracked user work is present; no pre-existing path is treated as cleanup output.
- Raw and processed datasets, SQLite data, trained checkpoints, experiment outputs, reports, evaluation snapshots, OpenAPI artifacts, and provenance documents are research-sensitive and will be preserved.

## Initial cleanup candidates and decisions

The safe cleanup phase may remove generated caches and reproducible build output (`.pytest_cache/`, `__pycache__/`, `frontend/.next/`, `frontend/.api-test-dist/`, and `frontend/tsconfig.tsbuildinfo`) after relevant validation commands finish. These items are not research artifacts and are ignored by Git. Installed environments, `.tools/`, datasets, model checkpoints, SQLite, result files, source, and documentation are retained. No dependencies, source modules, static assets, reports, checkpoints, or datasets were removed during discovery.
