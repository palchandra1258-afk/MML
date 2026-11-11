# Context Preservation Design

Before a diversion, Phase 13 records a compact `TrajectoryContextSnapshot` with parent trajectory ID and version, original target and goal, exact current step, completed/pending steps, prior representation plan, prior cognitive state, evidence and diagnostic recommendation IDs, active diversion references, original status/depth, and diversion reason.

The snapshot stores references and step identifiers rather than copying source evidence. The diversion points to the snapshot by `context_snapshot_id`; it also records its parent trajectory version and the interrupted step. The history evaluator compares the snapshot against the parent trajectory version that existed before diversion.

On resumption, `restore_context` returns the exact interrupted step and prior step lists. It does not restart the lesson. If a new available representation plan is chosen, the original plan remains in the snapshot/history while the active trajectory's current plan reference is updated. If the goal changes, the system records `REPLANNED` and preserves the earlier goal and step in earlier trajectory versions.

The default implementation keeps one active diversion per learner and depth one. Each diversion has a configurable limit of three distinct progress evaluations by default. A changed scope or evaluation condition is recorded as a new diversion version; changing its target requires closing it and creating a new explicitly supported diversion.
