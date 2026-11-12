"""Build and query a compact byte-offset index over immutable JSONL artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .persistence import ArtifactFile, ArtifactRecord, ArtifactRecordLink, utc_now


ARTIFACT_KEYS = (
    "phase9_states", "phase10_evidence", "phase10_groups", "phase11_states", "phase12_plans",
)


def record_identity(
    artifact_name: str,
    record: dict[str, Any],
) -> tuple[str, str, str | None, str | None, list[str]]:
    learner_id = str(record.get("learner_id", ""))
    if artifact_name == "phase9_states":
        record_id = learner_id
        record_time = record.get("state_timestamp")
    elif artifact_name == "phase10_evidence":
        record_id = str(record.get("evidence_id", ""))
        record_time = (record.get("temporal") or {}).get("event_timestamp")
    elif artifact_name == "phase10_groups":
        record_id = str(record.get("group_id", ""))
        record_time = None
    elif artifact_name == "phase11_states":
        record_id = str(record.get("cognitive_state_id", ""))
        record_time = record.get("generated_at")
    elif artifact_name == "phase12_plans":
        record_id = str(record.get("plan_id", ""))
        record_time = record.get("created_at")
    else:
        raise ValueError(f"unsupported research artifact: {artifact_name}")
    if not learner_id or not record_id:
        raise ValueError(f"{artifact_name} record is missing its learner or stable record ID")
    record_type = str(record.get("evidence_type")) if artifact_name == "phase10_evidence" else None
    if artifact_name == "phase10_groups":
        record_type = str(record.get("grouping_basis", "")) or None
    linked_ids = list(map(str, record.get("evidence_ids", []))) if artifact_name == "phase10_groups" else []
    return record_id, learner_id, str(record_time) if record_time is not None else None, record_type, linked_ids


def index_artifact(
    session: Session,
    artifact_name: str,
    source_path: Path,
    *,
    on_progress: Callable[[int], None] | None = None,
    chunk_size: int = 1000,
) -> int:
    """Replace one artifact's offsets atomically; raw JSONL remains untouched."""
    if artifact_name not in ARTIFACT_KEYS:
        raise ValueError(f"unsupported research artifact: {artifact_name}")
    path = source_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    stat = path.stat()
    session.execute(delete(ArtifactRecord).where(ArtifactRecord.artifact_name == artifact_name))
    session.execute(delete(ArtifactRecordLink).where(ArtifactRecordLink.artifact_name == artifact_name))
    session.merge(ArtifactFile(
        artifact_name=artifact_name,
        source_size=stat.st_size,
        source_mtime_ns=stat.st_mtime_ns,
        record_count=0,
        indexed_at=utc_now(),
    ))
    session.flush()

    batch: list[dict[str, Any]] = []
    link_batch: list[dict[str, Any]] = []
    record_count = 0
    with path.open("rb") as stream:
        while True:
            line_offset = stream.tell()
            raw_line = stream.readline()
            if not raw_line:
                break
            if not raw_line.strip():
                continue
            record_count += 1
            try:
                document = json.loads(raw_line)
                if not isinstance(document, dict):
                    raise ValueError("JSONL record must be an object")
                record_id, learner_id, record_time, record_type, linked_ids = record_identity(artifact_name, document)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
                raise ValueError(f"invalid {artifact_name} JSONL record at line {record_count}") from exc
            batch.append({
                "artifact_name": artifact_name,
                "record_id": record_id,
                "learner_id": learner_id,
                "record_type": record_type,
                "line_offset": line_offset,
                "byte_length": len(raw_line),
                "record_time": record_time,
            })
            link_batch.extend({
                "artifact_name": artifact_name,
                "record_id": record_id,
                "linked_record_id": linked_id,
            } for linked_id in linked_ids)
            if len(batch) >= chunk_size:
                session.execute(ArtifactRecord.__table__.insert(), batch)
                batch.clear()
            if len(link_batch) >= chunk_size:
                if batch:
                    session.execute(ArtifactRecord.__table__.insert(), batch)
                    batch.clear()
                session.execute(ArtifactRecordLink.__table__.insert(), link_batch)
                link_batch.clear()
            if on_progress and record_count % 10000 == 0:
                on_progress(record_count)
    if batch:
        session.execute(ArtifactRecord.__table__.insert(), batch)
    if link_batch:
        session.execute(ArtifactRecordLink.__table__.insert(), link_batch)
    session.query(ArtifactFile).filter_by(artifact_name=artifact_name).update({"record_count": record_count})
    return record_count


def indexed_status(session: Session, artifact_paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    files = {
        row.artifact_name: row
        for row in session.scalars(select(ArtifactFile)).all()
    }
    result: dict[str, dict[str, Any]] = {}
    for name in ARTIFACT_KEYS:
        path = artifact_paths[name]
        indexed = files.get(name)
        exists = path.is_file()
        stat = path.stat() if exists else None
        current = bool(
            indexed is not None
            and stat is not None
            and indexed.source_size == stat.st_size
            and indexed.source_mtime_ns == stat.st_mtime_ns
        )
        result[name] = {
            "available": current,
            "record_count": indexed.record_count if current else 0,
        }
    return result


def read_indexed_record(
    artifact_path: Path,
    line_offset: int,
    byte_length: int,
) -> dict[str, Any]:
    with artifact_path.open("rb") as stream:
        stream.seek(line_offset)
        raw = stream.read(byte_length)
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError("indexed artifact record is no longer a JSON object")
    return document
