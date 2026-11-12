from __future__ import annotations

from sqlalchemy import inspect, text

from mcp_ri.api.persistence import (
    StudentLearningAttempt,
    StudentLearningSession,
    StudentLessonProgress,
    StudentStudioProfile,
    utc_now,
)


def test_additive_learning_migration_keeps_research_tables_and_adds_studio_tables(tmp_path):
    from mcp_ri.api.main import create_app
    from mcp_ri.api.settings import APISettings
    from fastapi.testclient import TestClient

    missing = tmp_path / "not-present.jsonl"
    settings = APISettings(
        database_url=f"sqlite:///{tmp_path / 'f9-migration.sqlite3'}",
        cors_origins=("http://localhost:3000", "http://127.0.0.1:3000"),
        phase9_states_path=missing,
        phase10_evidence_path=missing,
        phase10_groups_path=missing,
        phase11_states_path=missing,
        phase12_plans_path=missing,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        names = set(inspect(app.state.database.engine).get_table_names())
        assert {"trajectories", "artifact_records", "studio_profiles", "studio_learning_sessions", "studio_lesson_progress", "studio_learning_attempts"} <= names
        with app.state.database.session() as session:
            assert session.execute(text("SELECT value FROM app_metadata WHERE key='schema_contract'")).scalar_one() == "migrations/0002_learning_studio"


def test_student_activity_storage_is_separate_and_attempts_preserve_submission_and_evidence(api):
    with api.app.state.database.session_factory.begin() as session:
        session.add(StudentStudioProfile(profile_id="studio-local-demo", profile_type="local_demo", created_at=utc_now()))
        session.flush()
        session.add(StudentLearningSession(
            session_id="b832ac16-9ca7-44d1-97c0-fef1c5ef0b21",
            profile_id="studio-local-demo",
            lesson_id="conditional-probability",
            content_version="1.0.0",
            started_at=utc_now(),
            last_activity_at=utc_now(),
        ))
        session.flush()
        session.add(StudentLessonProgress(
            profile_id="studio-local-demo",
            lesson_id="conditional-probability",
            course_id="probability-foundations",
            topic_id="conditional-probability",
            content_version="1.0.0",
            current_section_id="conditional-definition",
            completed_section_ids=["conditional-intro"],
            started_at=utc_now(),
            updated_at=utc_now(),
            completed_at=None,
            revision=1,
        ))
        session.flush()
        session.add(StudentLearningAttempt(
            attempt_id="c9656e40-e114-4471-a845-3039cdce2da4",
            profile_id="studio-local-demo",
            session_id="b832ac16-9ca7-44d1-97c0-fef1c5ef0b21",
            submission_id="submission-foundation-test-1",
            course_id="probability-foundations",
            topic_id="conditional-probability",
            lesson_id="conditional-probability",
            question_id="conditional-probability-q1",
            attempt_number=1,
            event_sequence=1,
            submitted_response={"choice_id": "b"},
            is_correct=False,
            feedback={"explanation": "Synthetic persistence test."},
            content_version="1.0.0",
            event_timestamp=utc_now(),
            evidence_record={"source_dataset": "mcp-ri-student-studio", "content": {"correctness": 0}},
        ))

    with api.app.state.database.session() as session:
        attempt = session.get(StudentLearningAttempt, "c9656e40-e114-4471-a845-3039cdce2da4")
        assert attempt is not None
        assert attempt.submitted_response == {"choice_id": "b"}
        assert attempt.evidence_record["source_dataset"] == "mcp-ri-student-studio"
        assert attempt.profile_id == "studio-local-demo"
        assert session.get(StudentLessonProgress, ("studio-local-demo", "conditional-probability")).completed_section_ids == ["conditional-intro"]
