# Phase 14 Persistence Methodology

## Research artifacts

The API reads the configured Phase 9 state, Phase 10 evidence/group, Phase 11 cognitive-state, and Phase 12 representation-plan JSONL files. It does not rewrite them, load the large Phase 9 dataset at startup, or copy JSON payloads into SQLite.

Run `scripts/api/index_artifacts.py` to stream each file and create a compact index: record ID, learner ID, source record type/time when present, byte offset/length, and group/evidence link IDs. The indexer checks each JSON line as it reads it. Source file size and nanosecond modification time are recorded. The API treats the index as current only while both match; a changed source must be reindexed. This fingerprint is an operational freshness check, not a cryptographic integrity proof.

Indexing has a one-time full sequential read of the 2.6 GB Phase 9 validation state file. The research source remains read-only; the local SQLite database stores only offsets and identifiers. Do not point the API at locked-test outputs.

## Application records

Only API-authored trajectory state is persisted as a full domain object. Related Phase 9–12 state/evidence/plan records remain references to their source IDs. Trajectory versions and event payloads are stored as JSON snapshots so Phase 13 schemas can evolve independently from relational query columns. The database stores no raw EdNet interaction table.

## Recovery and consistency

The API uses one SQLAlchemy transaction for each trajectory create/action. SQLite foreign keys protect learner and history relationships; unique keys reject duplicate versions/events. Compare-and-swap on the current version rejects competing updates. The Phase 13 in-memory history/manager is reconstructed from durable events on demand, so process memory is not the only copy.

SQLite is the local single-file store and is suitable for this prototype's serialized write volume. For PostgreSQL, install a psycopg SQLAlchemy driver, set `MCP_RI_DATABASE_URL=postgresql+psycopg://...`, review deployment credentials/network security, and apply Alembic migrations. PostgreSQL behavior has not been tested here.
