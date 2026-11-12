from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from mcp_ri.api.artifact_index import index_artifact
from mcp_ri.api.main import create_app
from mcp_ri.api.settings import APISettings
from mcp_ri.cognitive_state.estimator import estimate_cognitive_state
from mcp_ri.evidence.grouping import group_evidence
from mcp_ri.evidence.normalizer import base_record
from mcp_ri.learner_state.state_builder import build_state_from_rows
from mcp_ri.representation.plan_builder import build_representation_plan


def _fixture_records(learner_id: str) -> dict[str, list[dict]]:
    rows = [
        {
            "learner_id": learner_id,
            "source_row_order": sequence,
            "timestamp": str(1_700_000_000_000 + sequence * 1000),
            "question_id": f"fixture-question-{sequence}",
            "correctness": str(int(sequence == 0)),
            "skill_tags": "1",
            "is_exact_duplicate": "0",
        }
        for sequence in range(2)
    ]
    behavioral_state = build_state_from_rows(learner_id, rows)
    evidence = [
        base_record(
            learner_id=learner_id,
            session_id=f"fixture-session-{learner_id}",
            evidence_type="interaction",
            event_timestamp=row["timestamp"],
            sequence_number=row["source_row_order"],
            temporal_precision="millisecond",
            timestamp_source="synthetic API test fixture",
            source_dataset="synthetic-api-test-fixture",
            source_file=None,
            source_record_id=f"{learner_id}:{row['source_row_order']}",
            source_modality="interaction",
            processing_method="synthetic_test_fixture",
            content={
                "question_id": row["question_id"],
                "solving_id": None,
                "submitted_answer": "A",
                "correctness": int(row["correctness"]),
                "skill_ids": ["ednet_skill:1"],
                "is_exact_duplicate": False,
            },
            extraction_method="synthetic_test_fixture",
            transformation_history=["synthetic test fixture"],
            uncertainty_flags=["synthetic_fixture"],
            uncertainty_notes=["Test-only record; not an observed learner event."],
        )
        for row in rows
    ]
    cognitive_state = estimate_cognitive_state(
        behavioral_state, evidence, sequence_start=0, sequence_end=1,
    )
    representation_plan = build_representation_plan(
        cognitive_state,
        "ednet_skill:1",
        behavioral_state=behavioral_state,
        evidence_records=evidence,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return {
        "phase9_states": [behavioral_state],
        "phase10_evidence": evidence,
        "phase11_states": [cognitive_state],
        "phase12_plans": [representation_plan],
    }


def _write_jsonl(path: Path, documents: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for document in documents:
            stream.write(json.dumps(document, ensure_ascii=False, allow_nan=False) + "\n")


@pytest.fixture
def api(tmp_path: Path):
    artifact_paths = {
        "phase9_states": tmp_path / "phase9.jsonl",
        "phase10_evidence": tmp_path / "phase10.jsonl",
        "phase10_groups": tmp_path / "phase10_groups.jsonl",
        "phase11_states": tmp_path / "phase11.jsonl",
        "phase12_plans": tmp_path / "phase12.jsonl",
    }
    records_by_artifact = {name: [] for name in artifact_paths}
    for learner_id in ("synthetic_learner_a", "synthetic_learner_b"):
        learner_records = _fixture_records(learner_id)
        learner_records["phase10_groups"] = group_evidence(learner_records["phase10_evidence"])
        for artifact_name, records in learner_records.items():
            records_by_artifact[artifact_name].extend(records)
    for name, path in artifact_paths.items():
        _write_jsonl(path, records_by_artifact[name])

    settings = APISettings(
        database_url=f"sqlite:///{tmp_path / 'application.sqlite3'}",
        cors_origins=("http://localhost:3000", "http://127.0.0.1:3000"),
        phase9_states_path=artifact_paths["phase9_states"],
        phase10_evidence_path=artifact_paths["phase10_evidence"],
        phase10_groups_path=artifact_paths["phase10_groups"],
        phase11_states_path=artifact_paths["phase11_states"],
        phase12_plans_path=artifact_paths["phase12_plans"],
    )
    app = create_app(settings, migrate_on_start=False)
    with TestClient(app, raise_server_exceptions=False) as client:
        with app.state.database.session_factory.begin() as session:
            for name, path in artifact_paths.items():
                index_artifact(session, name, path)
        yield SimpleNamespace(client=client, app=app, paths=artifact_paths, settings=settings)


@pytest.fixture
def synthetic_records():
    """Explicitly synthetic and schema-valid phase records for service tests."""
    return _fixture_records("synthetic_learner_a")
