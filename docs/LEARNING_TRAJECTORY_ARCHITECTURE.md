# Phase 13: Learning Trajectory Architecture

## Purpose and boundary

Phase 13 manages continuity around a primary learning objective: it records the current step, makes a bounded decision about a temporary supporting-concept diversion, preserves the parent context, and records continuation, resumption, closure, or replanning. It consumes Phase 9 behavioral summaries, Phase 10 evidence references, Phase 11 provisional estimates, and Phase 12 representation-plan references without changing their schemas.

The module does not infer prerequisite mastery, diagnose the learner, deliver instruction, or estimate learning benefit. A diversion is a recommendation to investigate a configured supporting concept. EdNet skill identifiers do not define a curriculum dependency graph; the default dependency registry is empty.

## Architecture

```text
Phase 9 observed response summary ─┐
Phase 10 provenance/evidence refs ─┼─► validate inputs and preserve uncertainty
Phase 11 provisional estimate ─────┤                 │
Phase 12 recommendation/capability ┘                 ▼
                                      conservative diversion rules
                                               │
                           ┌───────────────────┴──────────────────┐
                           ▼                                      ▼
                    continue primary                    create bounded diversion
                                                                  │
                                    append context snapshot + child reference
                                                                  │
                                    monitor evidence and progress versions
                                                                  │
                          continue / revise / request evidence / resume / replan
                                                                  │
                                      append-only trajectory event history
```

`TrajectoryManager` is the orchestration facade. `diversion_detector.py` is a deterministic, independently callable policy; `dependency_registry.py` stores explicitly sourced relationships; `context_preserver.py` snapshots and restores teaching position; `resumption_engine.py` evaluates evidence and a Phase 12 plan; `history.py` retains immutable versions and reconstructs a requested trajectory version.

## Data and storage

Trajectory, diversion, context snapshot, dependency registry, and history event records use separate version-1.0 JSON Schemas. The Python history store is append-only and in-memory, following existing Phase 11/12 conventions. The bounded runner exports JSONL snapshots and events into a new timestamped report directory. A production durable database or service is not implemented.

Records contain references to evidence/state/plan objects, not copies of large evidence payloads. Every diversion links to its parent trajectory version and a compact context snapshot. Event history contains trajectory snapshots so the history validator can reconstruct each historical version.

## Assumptions and limits

- The input trajectory supplies a current learning step and primary goal. EdNet itself does not provide an instructional trajectory or validated objective.
- The dependency registry is empty by default. Manually configured links remain labeled as such; synthetic links are excluded unless a test explicitly enables them.
- The bounded sample uses the first concept estimate from each selected Phase 11 snapshot. It is a software integration sample, not a population or learning-outcome evaluation.
- Phase 10 text/audio/visual content remains unavailable in the real EdNet sample. Phase 11 hypotheses remain provisional and low-confidence.
- A representation plan marked deferred for unavailable delivery is not treated as evidence of a concept gap.

See [`TRAJECTORY_STATE_MACHINE.md`](TRAJECTORY_STATE_MACHINE.md), [`DIVERSION_DETECTION_METHODOLOGY.md`](DIVERSION_DETECTION_METHODOLOGY.md), [`CONTEXT_PRESERVATION_DESIGN.md`](CONTEXT_PRESERVATION_DESIGN.md), [`RESUMPTION_ENGINE_METHODOLOGY.md`](RESUMPTION_ENGINE_METHODOLOGY.md), [`DEPENDENCY_REGISTRY_SPECIFICATION.md`](DEPENDENCY_REGISTRY_SPECIFICATION.md), and [`TRAJECTORY_EVALUATION.md`](TRAJECTORY_EVALUATION.md).
