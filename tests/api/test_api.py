from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from fastapi.testclient import TestClient
from sqlalchemy import event, select

from mcp_ri.api.main import create_app
from mcp_ri.api.settings import APISettings
from mcp_ri.api.persistence import TrajectoryEventRecord, TrajectoryRecord, TrajectoryVersion
from mcp_ri.trajectory.trajectory_builder import build_trajectory


def _create(client, learner_id="synthetic_learner_a"):
    return client.post(
        f"/api/v1/learners/{learner_id}/trajectories",
        json={
            "target_concept_id": "ednet_skill:1",
            "primary_learning_goal": "Synthetic test goal supplied by the API caller.",
            "learning_objectives": ["Synthetic objective supplied by the API caller."],
        },
    )


def test_api_initialization_and_generated_openapi(api):
    assert api.client.app.title == "MCP-RI Backend API"
    spec = api.client.get("/api/v1/openapi.json").json()
    assert spec["info"]["version"] == "1.0.0"
    assert "/api/v1/health" in spec["paths"]
    assert "/api/v1/learners/{learner_id}/trajectories/{trajectory_id}/actions" in spec["paths"]


def test_health_reports_database_and_each_module(api):
    response = api.client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["database"] == "available"
    assert data["status"] == "healthy"
    assert data["modules"]["phase9_behavioral_state"]["available"] is True
    assert data["modules"]["phase12_representation"]["delivery_provider"] is False
    assert data["modules"]["model_inference"]["available"] is False


def test_database_initializes_with_alembic_migration(tmp_path):
    missing = tmp_path / "not-present.jsonl"
    from mcp_ri.api.settings import APISettings

    settings = APISettings(
        database_url=f"sqlite:///{tmp_path / 'migration.sqlite3'}",
        cors_origins=("http://localhost:3000",),
        phase9_states_path=missing,
        phase10_evidence_path=missing,
        phase10_groups_path=missing,
        phase11_states_path=missing,
        phase12_plans_path=missing,
    )
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        with app.state.database.session() as session:
            version = session.execute(select(TrajectoryRecord).limit(1)).all()
            contract = session.execute(
                __import__("sqlalchemy").text("SELECT value FROM app_metadata WHERE key='schema_contract'")
            ).scalar_one()
            assert version == []
            assert contract == "migrations/0002_learning_studio"


def test_learner_list_and_detail_do_not_invent_data(api):
    response = api.client.get("/api/v1/learners?limit=1")
    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 2
    assert page["has_more"] is True
    learner_id = page["items"][0]["learner_id"]
    detail = api.client.get(f"/api/v1/learners/{learner_id}")
    assert detail.status_code == 200
    assert "phase9_states" in detail.json()["data"]["available_data"]
    assert api.client.get("/api/v1/learners/nonexistent").status_code == 404


def test_behavioral_state_is_served_from_indexed_phase9_artifact(api):
    response = api.client.get("/api/v1/learners/synthetic_learner_a/state")
    assert response.status_code == 200
    state = response.json()["data"]
    assert state["learner_id"] == "synthetic_learner_a"
    assert state["observation_summary"]["total_interactions"] == 2
    assert "limitations" in state


def test_cognitive_state_retains_uncertainty_and_evidence_references(api):
    response = api.client.get("/api/v1/learners/synthetic_learner_a/cognitive-state")
    assert response.status_code == 200
    state = response.json()["data"]
    assert state["learner_id"] == "synthetic_learner_a"
    assert state["evidence_references"]
    assert "overall_uncertainty" in state["uncertainty"]


def test_evidence_listing_filter_pagination_and_detail(api):
    first = api.client.get("/api/v1/learners/synthetic_learner_a/evidence?limit=1&offset=0")
    assert first.status_code == 200
    page = first.json()["data"]
    assert page["total"] == 2
    assert page["has_more"] is True
    evidence_id = page["items"][0]["evidence_id"]
    filtered = api.client.get(
        "/api/v1/learners/synthetic_learner_a/evidence?evidence_type=interaction"
    )
    assert filtered.json()["data"]["total"] == 2
    detail = api.client.get(f"/api/v1/learners/synthetic_learner_a/evidence/{evidence_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["provenance"]["source_dataset"] == "synthetic-api-test-fixture"
    assert detail.json()["data"]["grouping_information"]
    assert detail.json()["data"]["alignment_links"]


def test_evidence_type_filter_can_return_empty_page(api):
    response = api.client.get("/api/v1/learners/synthetic_learner_a/evidence?evidence_type=audio")
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []
    assert response.json()["data"]["total"] == 0


def test_representation_plan_keeps_recommendation_and_delivery_status_separate(api):
    page = api.client.get("/api/v1/learners/synthetic_learner_a/representations").json()["data"]
    assert page["total"] == 1
    plan_id = page["items"][0]["plan_id"]
    response = api.client.get(f"/api/v1/learners/synthetic_learner_a/representations/{plan_id}")
    assert response.status_code == 200
    plan = response.json()["data"]
    assert plan["decision"]["selected_representation"] is None
    assert plan["decision"]["delivery_status"] == "not_selected"


def test_trajectory_and_diversion_get_endpoints_start_empty(api):
    assert api.client.get("/api/v1/learners/synthetic_learner_a/trajectories").json()["data"]["total"] == 0
    assert api.client.get("/api/v1/learners/synthetic_learner_a/diversions").json()["data"]["total"] == 0


def test_trajectory_creation_calls_phase13_service_and_persists_references(api):
    response = _create(api.client)
    assert response.status_code == 201, response.text
    trajectory = response.json()["data"]
    assert trajectory["current_status"] == "CREATED"
    assert trajectory["primary_learning_goal"].startswith("Synthetic test goal")
    assert trajectory["prerequisites"] == []
    assert trajectory["context"]["supporting_evidence_ids"] == []
    detail = api.client.get(
        f"/api/v1/learners/synthetic_learner_a/trajectories/{trajectory['trajectory_id']}"
    )
    assert detail.status_code == 200
    assert detail.json()["data"] == trajectory


def test_phase13_invalid_transition_maps_to_conflict(api):
    trajectory = _create(api.client).json()["data"]
    response = api.client.post(
        f"/api/v1/learners/synthetic_learner_a/trajectories/{trajectory['trajectory_id']}/actions",
        json={"action": "advance_step"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_trajectory_action_persists_version_and_append_only_history(api):
    trajectory = _create(api.client).json()["data"]
    created_id = trajectory["trajectory_id"]
    activated = api.client.post(
        f"/api/v1/learners/synthetic_learner_a/trajectories/{created_id}/actions",
        json={"action": "activate"},
    )
    assert activated.status_code == 200
    assert activated.json()["data"]["trajectory_version"] == 2
    completed = api.client.post(
        f"/api/v1/learners/synthetic_learner_a/trajectories/{created_id}/actions",
        json={"action": "advance_step"},
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["current_status"] == "COMPLETED"
    history = api.client.get(
        f"/api/v1/learners/synthetic_learner_a/trajectories/{created_id}/history?limit=10"
    ).json()["data"]["items"]
    assert [item["event_type"] for item in history] == ["TRAJECTORY_CREATED", "STATE_TRANSITION", "PROGRESS_UPDATED"]
    assert [item["trajectory_version"] for item in history] == [1, 2, 3]


def test_trajectory_history_and_versions_survive_new_app_instance(api):
    trajectory = _create(api.client).json()["data"]
    trajectory_id = trajectory["trajectory_id"]
    settings = api.settings
    second_app = create_app(settings, migrate_on_start=False)
    with TestClient(second_app, raise_server_exceptions=False) as second_client:
        response = second_client.get(
            f"/api/v1/learners/synthetic_learner_a/trajectories/{trajectory_id}/history"
        )
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1
        with second_app.state.database.session() as session:
            versions = session.scalars(
                select(TrajectoryVersion.version)
                .where(TrajectoryVersion.trajectory_id == trajectory_id)
                .order_by(TrajectoryVersion.version)
            ).all()
            assert versions == [1]


def test_missing_trajectory_history_and_diversion_are_safe_404s(api):
    paths = [
        "/api/v1/learners/synthetic_learner_a/trajectories/does-not-exist",
        "/api/v1/learners/synthetic_learner_a/trajectories/does-not-exist/history",
        "/api/v1/learners/synthetic_learner_a/diversions/does-not-exist",
    ]
    for path in paths:
        response = api.client.get(path)
        assert response.status_code == 404
        assert response.json()["success"] is False
        assert "filesystem" not in json.dumps(response.json()).lower()


def test_request_validation_uses_consistent_error_envelope(api):
    response = api.client.get("/api/v1/learners?limit=1000")
    assert response.status_code == 422
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_REQUEST"
    assert payload["request_id"]
    assert "input" not in json.dumps(payload)


def test_pagination_bounds_are_enforced(api):
    response = api.client.get("/api/v1/learners?limit=101")
    assert response.status_code == 422
    page = api.client.get("/api/v1/learners?limit=1&offset=1")
    assert page.status_code == 200
    assert page.json()["data"]["offset"] == 1


def test_cors_allows_configured_next_development_origin(api):
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = api.client.options(
            "/api/v1/learners",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_default_cors_allows_localhost_and_loopback_alias(monkeypatch):
    monkeypatch.delenv("MCP_RI_CORS_ORIGINS", raising=False)
    settings = APISettings.from_environment()
    assert settings.cors_origins == ("http://localhost:3000", "http://127.0.0.1:3000")


def test_phase13_create_rolls_back_if_history_event_insert_fails(api):
    def fail_event_insert(_mapper, _connection, _target):
        raise RuntimeError("synthetic database failure")

    event.listen(TrajectoryEventRecord, "before_insert", fail_event_insert)
    try:
        response = api.client.post(
            "/api/v1/learners/synthetic_learner_a/trajectories",
            json={
                "target_concept_id": "ednet_skill:1",
                "primary_learning_goal": "Rollback fixture request.",
            },
        )
    finally:
        event.remove(TrajectoryEventRecord, "before_insert", fail_event_insert)
    assert response.status_code == 500
    with api.app.state.database.session() as session:
        assert session.scalars(select(TrajectoryRecord)).all() == []
        assert session.scalars(select(TrajectoryEventRecord)).all() == []


def test_api_response_matches_generated_openapi_schema(api):
    response = api.client.get("/api/v1/learners?limit=1")
    openapi = api.client.get("/api/v1/openapi.json").json()
    schema = openapi["paths"]["/api/v1/learners"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]

    def resolve(node):
        if isinstance(node, list):
            return [resolve(item) for item in node]
        if not isinstance(node, dict):
            return node
        reference = node.get("$ref")
        if reference:
            name = reference.rsplit("/", 1)[-1]
            base = resolve(openapi["components"]["schemas"][name])
            return {**base, **{key: resolve(value) for key, value in node.items() if key != "$ref"}}
        return {key: resolve(value) for key, value in node.items()}

    jsonschema.validate(response.json(), resolve(schema))


def test_openapi_documents_consistent_error_responses(api):
    spec = api.client.get("/api/v1/openapi.json").json()
    response_codes = spec["paths"]["/api/v1/learners"]["get"]["responses"]
    assert "404" in response_codes
    assert "409" in response_codes
    assert "422" in response_codes
    assert "503" in response_codes
    assert "ErrorEnvelope" in json.dumps(spec["components"]["schemas"])
    generated_file = Path(__file__).resolve().parents[2] / "shared/api-contracts/openapi.json"
    assert json.loads(generated_file.read_text(encoding="utf-8")) == spec
