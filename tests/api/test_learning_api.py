from __future__ import annotations


def test_curriculum_catalog_search_and_public_practice_hide_answer_keys(api):
    client = api.client
    catalog = client.get("/api/v1/curriculum").json()["data"]
    assert {subject["subject_id"] for subject in catalog["subjects"]} == {
        "mathematics", "statistics", "computer-science", "artificial-intelligence", "finance",
    }
    topics = [topic for subject in catalog["subjects"] for course in subject["courses"]
              for unit in course["units"] for topic in unit["topics"]]
    assert len(topics) == 7
    assert all(topic["prerequisites_status"] == "not_established" for topic in topics)

    found = client.get("/api/v1/curriculum/search", params={"q": "bayes"}).json()["data"]
    assert len(found) == 1
    assert found[0]["topic"]["topic_id"] == "bayes-theorem"
    assert found[0]["topic"]["practice_question_count"] == 2

    practice = client.get("/api/v1/curriculum/lessons/expected-value/practice").json()["data"]
    assert len(practice["questions"]) == 3
    assert {question["question_type"] for question in practice["questions"]} == {"single_choice", "multiple_choice", "numeric"}
    assert all("grading" not in question and "expected_answer" not in question and "explanation" not in question
               for question in practice["questions"])


def test_answers_are_server_evaluated_idempotent_and_append_only(api):
    client = api.client
    session = client.post("/api/v1/studio/lessons/conditional-probability/sessions").json()["data"]
    payload = {
        "submission_id": "attempt-key-one",
        "session_id": session["session_id"],
        "response": {"option_ids": ["a"]},
    }
    first = client.post("/api/v1/studio/questions/conditional-probability-q1/answer", json=payload)
    assert first.status_code == 200
    result = first.json()["data"]
    assert result["is_correct"] is True
    assert result["attempt_number"] == 1
    assert result["expected_answer"] == "2/3"

    replay = client.post("/api/v1/studio/questions/conditional-probability-q1/answer", json=payload).json()["data"]
    assert replay["attempt_id"] == result["attempt_id"]
    assert replay["idempotent_replay"] is True

    changed = {**payload, "response": {"option_ids": ["b"]}}
    assert client.post("/api/v1/studio/questions/conditional-probability-q1/answer", json=changed).status_code == 409
    second = {**payload, "submission_id": "attempt-key-two", "response": {"option_ids": ["b"]}}
    incorrect = client.post("/api/v1/studio/questions/conditional-probability-q1/answer", json=second).json()["data"]
    assert incorrect["is_correct"] is False
    assert incorrect["attempt_number"] == 2
    assert incorrect["attempt_id"] != result["attempt_id"]

    evidence = client.get("/api/v1/studio/evidence").json()["data"]
    assert evidence["total"] == 2
    assert all(record["provenance"]["source_dataset"] == "mcp-ri-student-studio" for record in evidence["items"])
    assert all(record["content"]["skill_ids"] == [] for record in evidence["items"])
    assert {record["content"]["correctness"] for record in evidence["items"]} == {0, 1}


def test_numeric_tolerance_progress_resume_history_and_phase9_boundary(api):
    client = api.client
    started = client.post("/api/v1/studio/lessons/expected-value/sessions").json()["data"]
    assert started["resumed"] is False
    replayed_start = client.post("/api/v1/studio/lessons/expected-value/sessions").json()["data"]
    assert replayed_start["resumed"] is True
    assert replayed_start["session_id"] == started["session_id"]

    answer = client.post("/api/v1/studio/questions/expected-value-q3/answer", json={
        "submission_id": "numeric-attempt-1",
        "session_id": started["session_id"],
        "response": {"value": "2.0005"},
    }).json()["data"]
    assert answer["is_correct"] is True

    lesson = client.get("/api/v1/curriculum/lessons/expected-value").json()["data"]
    sections = lesson["sections"]
    progress = None
    for section in sections:
        progress = client.post("/api/v1/studio/lessons/expected-value/progress", json={
            "session_id": started["session_id"],
            "current_section_id": section["section_id"],
            "completed_section_ids": [item["section_id"] for item in sections[:sections.index(section) + 1]],
        }).json()["data"]
    assert progress["status"] == "completed"
    assert progress["content_complete"] is True
    assert progress["completion_percentage"] == 100

    summary = client.get("/api/v1/studio/progress").json()["data"]
    assert summary["summary"]["lessons_completed"] == 1
    assert summary["summary"]["practice_attempts"] == 1
    assert summary["summary"]["response_accuracy"] == 1
    assert summary["courses"][0]["completion_percentage"] == 20

    history = client.get("/api/v1/studio/history").json()["data"]
    assert history["total"] == 2
    assert {entry["event_type"] for entry in history["items"]} == {"lesson_started", "answer_submitted"}
    state = client.get("/api/v1/studio/behavioral-state").json()["data"]
    assert state["state"]["observation_summary"]["labelled_responses"] == 1
    assert state["state"]["concept_states"] == []
    assert any("separate from EdNet" in item for item in state["state"]["limitations"])


def test_invalid_answers_and_wrong_answers_do_not_claim_mastery(api):
    client = api.client
    session = client.post("/api/v1/studio/lessons/introduction-to-probability/sessions").json()["data"]
    invalid = client.post("/api/v1/studio/questions/introduction-to-probability-q1/answer", json={
        "submission_id": "invalid-choice-key",
        "session_id": session["session_id"],
        "response": {"option_ids": ["not-an-option"]},
    })
    assert invalid.status_code == 422

    wrong = client.post("/api/v1/studio/questions/introduction-to-probability-q1/answer", json={
        "submission_id": "wrong-choice-key",
        "session_id": session["session_id"],
        "response": {"option_ids": ["b"]},
    }).json()["data"]
    assert wrong["is_correct"] is False
    progress = client.get("/api/v1/studio/progress").json()["data"]
    assert progress["summary"]["lessons_needing_review"] == 1
    assert progress["summary"]["lessons_completed"] == 0
