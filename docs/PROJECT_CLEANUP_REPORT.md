# MCP-RI Repository Cleanup Report

Date: 2026-11-11 (Asia/Kolkata)

The pre-cleanup inventory and duplicate scan are recorded in [`PROJECT_CLEANUP_AUDIT.md`](PROJECT_CLEANUP_AUDIT.md). The repository already had 58 changed paths before this task. Those user changes were preserved; only the README's stale frontend note was updated as part of the requested documentation cleanup.

## Storage

The comparable disk usage measurements below use `du -sB1`. The post-cleanup measurement follows regeneration of the small Next.js route type declarations required by TypeScript and includes the audit and cleanup reports.

| Metric | Before cleanup (bytes) | After cleanup (bytes) | Difference |
|---|---:|---:|---:|
| Total working directory | 11,145,494,528 | 10,984,251,392 | -161,243,136 |
| Frontend | 670,474,240 | 499,843,072 | -170,631,168 |
| Backend source (`src/`) | 1,179,648 | 548,864 | -630,784 |
| Data | 7,105,884,160 | 7,105,884,160 | 0 |
| Models | 62,394,368 | 62,394,368 | 0 |
| Research results | 2,880,364,544 | 2,880,364,544 | 0 |
| Documentation | 532,480 | 548,864 | +16,384 |

The cleanup script removed 531 generated files totaling 159,712,838 apparent bytes. Whole-directory allocated disk usage fell by 161,243,136 bytes (about 154 MiB). Differences between apparent file bytes and allocated bytes reflect filesystem allocation, generated outputs created and cleared during validation, and the regenerated Next route declarations. The total inventory went from 28,365 files / 3,087 directories to 27,589 files / 2,973 directories; this net difference includes transient build/test outputs and the audit/report/type declaration files added during the task.

The frontend remains 499,843,072 bytes because its installed `node_modules` (498,323,456 bytes) were retained. The raw dataset is 1,201,360,896 bytes; the processed dataset is 5,888,258,048 bytes. The largest retained research output is the 2,765,973,726-byte Phase 9 validation state JSONL. Git's `.git/` directory remains 218,501,120 bytes. Git history was not modified, so no Git history size reduction is claimed.

## Cleanup performed

- Removed generated Python `__pycache__/` trees outside installed environments, `.pytest_cache/`, bulky `frontend/.next/` build/cache output, `frontend/.api-test-dist/`, and `frontend/tsconfig.tsbuildinfo` after verification. Regenerated and retained only `.next/types/` using `npx next typegen`; the frontend TypeScript source references generated `PageProps` and `LayoutProps`, so those small declarations are needed for a clean type check.
- Removed no application source, React components, hooks, utilities, static assets, datasets, model checkpoints, results, database files, dependencies, or historical documentation.
- Removed no exact duplicate content. The 11 SHA-256 duplicate groups in the audit all involve timestamped research runs, checkpoint paths with distinct run provenance, manifests, or empty output files; all were preserved.
- Moved or archived no files. Documentation remains in its existing `docs/` and `frontend/docs/` organization. Added this audit and cleanup report, and added frontend startup guidance to the root README while preserving the pre-existing Phase 14 README changes.
- Changed no dependency manifests or lockfiles. No clearly unused dependency was established from the manifests and current imports.
- Changed no `.gitignore` entries; existing rules already cover Python caches, local environments/tools, frontend build/dependency outputs, local databases, and large/generated research data.
- No tracked files were deleted. No Git reset, clean, history rewrite, or other destructive Git operation was run. `git diff --check` passed after cleanup.

## Research and user data preserved

- Original raw EdNet archive and processed feature table remain unchanged.
- Trained model checkpoints remain unchanged, including byte-identical DKT checkpoints under distinct run directories.
- Final metrics, calibration artifacts, model comparisons, Phase 9–13 outputs, evaluation snapshot, experiment configurations and provenance documents remain unchanged.
- The local SQLite database remains unchanged. The Uvicorn startup smoke check used a temporary database under `/tmp`.
- No synthetic fixture or engineering check is represented as learner evidence or scientific validation.

## Validation

| Check | Result |
|---|---|
| Python compilation (`compileall` over `src`, `scripts`, `migrations`, `tests`) | Passed |
| Full backend pytest suite | Could not collect all tests: the existing `.venv-api` lacks `joblib` and `numpy`; one test was skipped before collection stopped |
| Backend API tests (`tests/api`) | 21 passed in 9.22 seconds, including API health checks and migration coverage using temporary test databases |
| Uvicorn entry point and HTTP health request | Started successfully; `/api/v1/health` returned HTTP 200 with database available and overall status `degraded` because the temporary database had no indexed research artifacts |
| Frontend lint (`npm run lint`) | Passed |
| Frontend API tests (`npm run test:api`) | 7 passed |
| TypeScript (`npx next typegen && npx tsc --noEmit`) | Passed |
| Frontend production build (`npm run build`) | Failed in Turbopack when it attempted to create a process and bind a port (`Operation not permitted`); an escalated retry showed the same failure. `npx next build --webpack` also failed because Next could not parse TypeScript's `--showConfig` output. No successful production build is claimed. |
| Git whitespace validation (`git diff --check`) | Passed |

No packages were installed to work around missing training dependencies, and the existing virtual environment was not recreated. The API suite and startup smoke check used temporary databases so the local project database was not mutated.

## Remaining review candidates and maintenance

- Keep large raw/processed datasets and row-level learner outputs in their current protected locations or move them only under a separately reviewed storage plan that updates paths and provenance. They are not safe cleanup targets.
- Manually compare the identical timestamped Phase 13 outputs and identical DKT checkpoint files only if a future storage policy permits consolidating historical run directories. Current evidence is insufficient to treat them as redundant experiments.
- Review the empty placeholder directories under `data/` and `models/` when deciding the long-term repository layout; they may be intentional staging locations.
- `.tools/` is an ignored local GitHub CLI installation plus downloaded archive (about 98 MB). It was preserved because it appears to be an installed local tool, not an unambiguously disposable project artifact.
- Continue keeping caches/build output ignored, retain `package-lock.json`, and avoid committing raw datasets, local SQLite files, or row-level learner exports.
