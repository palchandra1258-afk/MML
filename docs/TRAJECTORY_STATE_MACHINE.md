# Trajectory State Machine

## States and allowed transitions

| Current state | Allowed next states |
|---|---|
| `CREATED` | `ACTIVE`, `CANCELLED` |
| `ACTIVE` | `PAUSED`, `DIVERTED`, `COMPLETED`, `REPLANNED`, `CANCELLED` |
| `PAUSED` | `ACTIVE`, `CANCELLED` |
| `DIVERTED` | `RESUMING`, `PAUSED`, `CANCELLED` |
| `RESUMING` | `ACTIVE`, `DIVERTED`, `REPLANNED`, `COMPLETED`, `CANCELLED` |
| `REPLANNED` | `ACTIVE`, `CANCELLED` |
| `COMPLETED` | none |
| `CANCELLED` | none |

`validate_transition` is the single transition authority. Invalid transitions raise `ValueError` before history is mutated. Entering a diversion increments trajectory version and records the active diversion ID and depth. A resumption decision records an explicit `RESUMING` version before returning to `ACTIVE`, completing, or replanning.

## Event requirements

Each history event records previous/new state, timestamp, trigger, explanation, evidence IDs, optional Phase 11/12 references, prior event ID, and a trajectory snapshot. Same-state decisions and progress records can append at the current trajectory version; they cannot alter that version's snapshot. State-changing events increment the version by one.

`TrajectoryHistory.reconstruct(trajectory_id, version)` returns the immutable record captured at that version. `history_for_trajectory`, `diversions_for_trajectory`, `parent_trajectory_of_diversion`, `get_context_snapshot`, and `inspect_transition` expose audit queries.

## History implementation boundary

The store is process-local. The Phase 13 runner exports the current append-only event sequence and versioned diversion records as JSONL. A durable concurrent store, retention service, and transactional write protocol remain deployment work.
