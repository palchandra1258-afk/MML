# Phase 14 Database Architecture

## Choice and compatibility

The initial database is SQLite through SQLAlchemy 2.x. The ORM uses portable `JSON`, string timestamps, primary/foreign keys, and unique constraints. A future PostgreSQL deployment can use a PostgreSQL SQLAlchemy URL and driver, then migrate with the same Alembic revisions. PostgreSQL runtime and migration testing are not part of this phase.

The default local database is `data/application/mcp_ri.sqlite3`, ignored by Git. The API enables SQLite foreign-key enforcement. Alembic revision `0001_initial` creates the schema; application startup applies pending revisions, and `scripts/api/migrate_database.py` applies them explicitly.

## Tables

| Table | Purpose and constraints |
|---|---|
| `app_metadata` | Schema contract marker. |
| `learner_references` | Learner IDs referenced by application-created trajectories; source and UTC creation time. |
| `artifact_files` | Indexed artifact name, source byte size, modification time, record count, indexing time. |
| `artifact_records` | Artifact/record key, learner ID, optional record type/time, byte offset and length. Composite primary key; indexed learner lookup. No source JSON payload is copied here. |
| `artifact_record_links` | Indexes group-to-evidence links; foreign key to the group record and an index for evidence lookup. |
| `trajectories` | Mutable current pointer/status/snapshot for each trajectory, tied to a learner reference. |
| `trajectory_versions` | Immutable JSON snapshot per `(trajectory_id, version)`. |
| `trajectory_history_events` | Immutable Phase 13 event payload plus API event order; unique event ID, unique order per trajectory, FK to trajectory and prior event. |
| `diversions` / `diversion_versions` | Durable diversion snapshot and immutable versions for future safe HTTP integration. No Phase 14 HTTP write currently creates them. |
| `trajectory_context_snapshots` | Durable context snapshot tied to an existing parent trajectory version. No Phase 14 HTTP write currently creates them. |

`created_at`, `updated_at`, `recorded_at`, and `occurred_at` values created by the application use UTC ISO-8601 strings. Dataset timestamps are preserved with their source meaning; EdNet timestamps are publisher-shifted values, not wall-clock UTC.

## Transaction and recovery model

Trajectory creation inserts the learner reference if needed, current trajectory, initial immutable version, and initial history event in one transaction. An action runs through `TrajectoryManager`, uses a compare-and-swap condition on `current_version`, then inserts the new immutable version/event and updates the current pointer atomically. A failed insert rolls the whole operation back.

On a later request or process restart, the service reads the append-only events in `event_order`, replays them through `TrajectoryHistory.append_event()`, and calls `TrajectoryManager.restore()`. Phase 13 validation remains the authority for reconstruction and transition rules.

Historical versions/events are never updated or deleted by API operations. The current `trajectories` row is a replaceable read pointer; it is not the history source of truth.
