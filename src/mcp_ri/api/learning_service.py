"""Curated Student Studio content, activity persistence and evidence integration."""

from __future__ import annotations

import json
import math
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mcp_ri.evidence.normalizer import base_record
from mcp_ri.evidence.state_bridge import apply_interaction_evidence
from mcp_ri.learner_state.state_builder import LearnerStateAccumulator

from .errors import APIError
from .learning_schemas import (
    AnswerFeedback,
    CurriculumCatalog,
    CurriculumFile,
    LearningHistoryEntry,
    LearningSessionData,
    LessonContent,
    LessonProgressData,
    PublicQuestion,
    QuestionPractice,
    StudentBehavioralStateData,
    StudentEvidenceData,
    StudentProgressData,
    StudentProgressSummary,
    StudentStudioProfile,
    TopicDetails,
    AnswerSubmission,
    CourseProgress,
)
from .persistence import StudentStudioProfile as StudentStudioProfileRow
from .persistence import StudentLearningAttempt as StudentLearningAttemptRow
from .persistence import StudentLearningSession as StudentLearningSessionRow
from .persistence import StudentLessonProgress as StudentLessonProgressRow
from .persistence import utc_now


PROFILE_ID = "studio-local-demo"
PROFILE_NAME = "Local demo learner"
PROFILE_NOTICE = "This local demonstration profile is separate from research and EdNet learner records. It is not an authenticated account."
CURRICULUM_PATH = Path(__file__).resolve().parents[1] / "learning" / "curriculum.json"


def _load_curriculum() -> CurriculumFile:
    raw = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    question_counts: dict[str, int] = {}
    for question in raw["questions"]:
        question_counts[question["lesson_id"]] = question_counts.get(question["lesson_id"], 0) + 1
    for subject in raw["subjects"]:
        for course in subject["courses"]:
            for unit in course["units"]:
                for topic in unit["topics"]:
                    if "objectives" in topic:  # Compact authored source, expanded to the API schema here.
                        topic["learning_objectives"] = [
                            {"objective_id": f"{topic['topic_id']}-objective-{index + 1}", "text": text}
                            for index, text in enumerate(topic.pop("objectives"))
                        ]
                    if "minutes" in topic:
                        topic["estimated_minutes"] = topic.pop("minutes")
                    topic.setdefault("prerequisites_status", "not_established")
                    topic.setdefault("prerequisite_topic_ids", [])
                    topic.setdefault("lesson_id", topic["topic_id"])
                    topic.setdefault("practice_question_count", question_counts.get(topic["lesson_id"], 0))
    curriculum = CurriculumFile.model_validate(raw)
    lesson_ids = {lesson.lesson_id for lesson in curriculum.lessons}
    question_ids: set[str] = set()
    for subject in curriculum.subjects:
        for course in subject.courses:
            for unit in course.units:
                for topic in unit.topics:
                    if topic.lesson_id not in lesson_ids:
                        raise ValueError(f"curriculum topic {topic.topic_id!r} references an unknown lesson")
    for lesson in curriculum.lessons:
        if lesson.topic_id not in {topic.topic_id for subject in curriculum.subjects for course in subject.courses for unit in course.units for topic in unit.topics}:
            raise ValueError(f"curriculum lesson {lesson.lesson_id!r} references an unknown topic")
    for question in curriculum.questions:
        if question.question_id in question_ids or question.lesson_id not in lesson_ids:
            raise ValueError(f"curriculum question {question.question_id!r} has a duplicate ID or unknown lesson")
        question_ids.add(question.question_id)
        option_ids = {option.option_id for option in question.options}
        if question.grading.kind == "choice" and not set(question.grading.correct_option_ids) <= option_ids:
            raise ValueError(f"curriculum question {question.question_id!r} has an unknown answer option")
        if question.grading.kind == "numeric" and min(question.grading.absolute_tolerance, question.grading.relative_tolerance) < 0:
            raise ValueError(f"curriculum question {question.question_id!r} has a negative tolerance")
    return curriculum


@lru_cache(maxsize=1)
def curriculum() -> CurriculumFile:
    return _load_curriculum()


class LearningService:
    """Own Student Studio rules while keeping the research learner namespace separate."""

    def _profile_row(self, session: Session) -> StudentStudioProfileRow:
        profile = session.get(StudentStudioProfileRow, PROFILE_ID)
        if profile is None:
            profile = StudentStudioProfileRow(profile_id=PROFILE_ID, profile_type="local_demo", created_at=utc_now())
            session.add(profile)
            session.flush()
        return profile

    @staticmethod
    def profile_data() -> dict[str, Any]:
        return StudentStudioProfile(
            profile_id=PROFILE_ID,
            display_name=PROFILE_NAME,
            identity_mode="local_demo",
            notice=PROFILE_NOTICE,
        ).model_dump()

    def catalog(self) -> dict[str, Any]:
        data = CurriculumCatalog(curriculum_version=curriculum().curriculum_version, subjects=curriculum().subjects)
        return data.model_dump(mode="json")

    def search(self, query: str) -> list[dict[str, Any]]:
        normalized = query.strip().casefold()
        items: list[dict[str, Any]] = []
        if not normalized:
            return items
        for subject in curriculum().subjects:
            for course in subject.courses:
                for unit in course.units:
                    for topic in unit.topics:
                        searchable = " ".join((topic.title, topic.description, course.title, subject.title)).casefold()
                        if normalized in searchable:
                            items.append(TopicDetails(
                                subject_id=subject.subject_id,
                                subject_title=subject.title,
                                course_id=course.course_id,
                                course_title=course.title,
                                unit_id=unit.unit_id,
                                unit_title=unit.title,
                                topic=topic,
                            ).model_dump(mode="json"))
        return items

    def topic(self, topic_id: str) -> dict[str, Any]:
        for subject in curriculum().subjects:
            for course in subject.courses:
                for unit in course.units:
                    for topic in unit.topics:
                        if topic.topic_id == topic_id:
                            return TopicDetails(
                                subject_id=subject.subject_id,
                                subject_title=subject.title,
                                course_id=course.course_id,
                                course_title=course.title,
                                unit_id=unit.unit_id,
                                unit_title=unit.title,
                                topic=topic,
                            ).model_dump(mode="json")
        raise APIError(404, "TOPIC_NOT_FOUND", "The requested topic is not available in the curated curriculum.")

    def lesson(self, lesson_id: str) -> dict[str, Any]:
        lesson = next((item for item in curriculum().lessons if item.lesson_id == lesson_id), None)
        if lesson is None:
            raise APIError(404, "LESSON_NOT_FOUND", "The requested lesson is not available in the curated curriculum.")
        return lesson.model_dump(mode="json")

    def practice(self, lesson_id: str) -> dict[str, Any]:
        lesson = next((item for item in curriculum().lessons if item.lesson_id == lesson_id), None)
        if lesson is None:
            raise APIError(404, "LESSON_NOT_FOUND", "The requested lesson is not available in the curated curriculum.")
        questions = [PublicQuestion.model_validate(item.model_dump(exclude={"grading", "expected_answer", "explanation"})).model_dump(mode="json")
                     for item in curriculum().questions if item.lesson_id == lesson_id]
        return QuestionPractice(lesson_id=lesson_id, content_version=lesson.content_version, questions=questions).model_dump(mode="json")

    def _question(self, question_id: str):
        question = next((item for item in curriculum().questions if item.question_id == question_id), None)
        if question is None:
            raise APIError(404, "QUESTION_NOT_FOUND", "The requested practice question is not available.")
        return question

    def _lesson_and_course(self, lesson_id: str) -> tuple[LessonContent, str, str, str]:
        lesson = next((item for item in curriculum().lessons if item.lesson_id == lesson_id), None)
        if lesson is None:
            raise APIError(404, "LESSON_NOT_FOUND", "The requested lesson is not available in the curated curriculum.")
        for subject in curriculum().subjects:
            for course in subject.courses:
                for unit in course.units:
                    for topic in unit.topics:
                        if topic.topic_id == lesson.topic_id:
                            return lesson, course.course_id, topic.topic_id, subject.subject_id
        raise APIError(500, "CURRICULUM_INVALID", "The lesson is not connected to a valid curriculum topic.")

    def _progress(self, session: Session, lesson: LessonContent) -> dict[str, Any]:
        row = session.get(StudentLessonProgressRow, (PROFILE_ID, lesson.lesson_id))
        required = [section.section_id for section in lesson.sections if section.required]
        completed = [] if row is None else [section_id for section_id in row.completed_section_ids if section_id in required]
        content_complete = bool(required) and all(section_id in completed for section_id in required)
        latest = session.scalar(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
            StudentLearningAttemptRow.lesson_id == lesson.lesson_id,
        ).order_by(StudentLearningAttemptRow.event_sequence.desc()).limit(1))
        status = "completed" if content_complete else "needs_review" if latest is not None and not latest.is_correct else "in_progress" if row is not None else "not_started"
        reason = "A recent response was incorrect. Revisit the lesson and try again; this is activity feedback, not a diagnosis." if status == "needs_review" else None
        return LessonProgressData(
            lesson_id=lesson.lesson_id,
            status=status,
            current_section_id=None if row is None else row.current_section_id,
            completed_section_ids=completed,
            completed_required_sections=len(completed),
            required_section_count=len(required),
            completion_percentage=round(100 * len(completed) / len(required)) if required else 0,
            content_complete=content_complete,
            review_reason=reason,
            updated_at=None if row is None else row.updated_at,
        ).model_dump(mode="json")

    def start_session(self, session: Session, lesson_id: str) -> dict[str, Any]:
        lesson, _, _, _ = self._lesson_and_course(lesson_id)
        self._profile_row(session)
        progress_row = session.get(StudentLessonProgressRow, (PROFILE_ID, lesson_id))
        now = utc_now()
        latest = session.scalar(select(StudentLearningSessionRow).where(
            StudentLearningSessionRow.profile_id == PROFILE_ID,
            StudentLearningSessionRow.lesson_id == lesson_id,
        ).order_by(StudentLearningSessionRow.last_activity_at.desc()).limit(1))
        resumed = latest is not None
        if latest is None:
            latest = StudentLearningSessionRow(
                session_id=str(uuid.uuid4()), profile_id=PROFILE_ID, lesson_id=lesson_id,
                content_version=lesson.content_version, started_at=now, last_activity_at=now,
            )
            session.add(latest)
        else:
            latest.last_activity_at = now
        if progress_row is None:
            _, course_id, topic_id, _ = self._lesson_and_course(lesson_id)
            progress_row = StudentLessonProgressRow(
                profile_id=PROFILE_ID, lesson_id=lesson_id, course_id=course_id, topic_id=topic_id,
                content_version=lesson.content_version, current_section_id=lesson.sections[0].section_id,
                completed_section_ids=[], started_at=now, updated_at=now, completed_at=None, revision=1,
            )
            session.add(progress_row)
        session.flush()
        return LearningSessionData(
            session_id=latest.session_id, profile_id=PROFILE_ID, lesson_id=lesson_id,
            started_at=latest.started_at, resumed=resumed, progress=self._progress(session, lesson),
        ).model_dump(mode="json")

    def save_progress(self, session: Session, lesson_id: str, body: Any) -> dict[str, Any]:
        lesson, course_id, topic_id, _ = self._lesson_and_course(lesson_id)
        row_session = session.get(StudentLearningSessionRow, body.session_id)
        if row_session is None or row_session.profile_id != PROFILE_ID or row_session.lesson_id != lesson_id:
            raise APIError(409, "SESSION_MISMATCH", "The learning session does not belong to this lesson.")
        section_ids = {section.section_id for section in lesson.sections}
        required = {section.section_id for section in lesson.sections if section.required}
        if body.current_section_id not in section_ids or not set(body.completed_section_ids) <= required:
            raise APIError(422, "INVALID_LESSON_PROGRESS", "The requested section is not part of this lesson.")
        self._profile_row(session)
        row = session.get(StudentLessonProgressRow, (PROFILE_ID, lesson_id))
        now = utc_now()
        if row is None:
            row = StudentLessonProgressRow(
                profile_id=PROFILE_ID, lesson_id=lesson_id, course_id=course_id, topic_id=topic_id,
                content_version=lesson.content_version, current_section_id=body.current_section_id,
                completed_section_ids=[], started_at=now, updated_at=now, completed_at=None, revision=1,
            )
            session.add(row)
        row.current_section_id = body.current_section_id
        row.completed_section_ids = sorted(set(row.completed_section_ids) | set(body.completed_section_ids))
        row.content_version = lesson.content_version
        row.updated_at = now
        row.revision += 1
        row_session.last_activity_at = now
        if required and required <= set(row.completed_section_ids):
            row.completed_at = row.completed_at or now
        session.flush()
        return self._progress(session, lesson)

    @staticmethod
    def _evaluate(question: Any, response: dict[str, Any]) -> bool:
        if question.grading.kind == "choice":
            if set(response) != {"option_ids"} or not isinstance(response["option_ids"], list):
                raise APIError(422, "INVALID_ANSWER", "Choice answers must contain an option_ids list.")
            values = response["option_ids"]
            if not values or any(not isinstance(value, str) for value in values) or len(values) != len(set(values)):
                raise APIError(422, "INVALID_ANSWER", "Select one or more distinct answer options.")
            option_ids = {option.option_id for option in question.options}
            if not set(values) <= option_ids:
                raise APIError(422, "INVALID_ANSWER", "The response contains an option that is not part of this question.")
            if question.question_type == "single_choice" and len(values) != 1:
                raise APIError(422, "INVALID_ANSWER", "Select exactly one option for this question.")
            return set(values) == set(question.grading.correct_option_ids)
        if question.grading.kind == "numeric":
            if set(response) != {"value"} or not isinstance(response["value"], (int, float, str)) or isinstance(response["value"], bool):
                raise APIError(422, "INVALID_ANSWER", "Numeric answers must contain one numeric value.")
            try:
                submitted = float(response["value"])
                expected = float(question.grading.expected_value)
            except (TypeError, ValueError):
                raise APIError(422, "INVALID_ANSWER", "Enter a valid finite number.") from None
            if not math.isfinite(submitted):
                raise APIError(422, "INVALID_ANSWER", "Enter a valid finite number.")
            tolerance = max(float(question.grading.absolute_tolerance), abs(expected) * float(question.grading.relative_tolerance))
            return abs(submitted - expected) <= tolerance
        raise APIError(422, "UNSUPPORTED_QUESTION", "This question type does not have an automatic evaluator.")

    def submit_answer(self, session: Session, question_id: str, body: AnswerSubmission) -> dict[str, Any]:
        question = self._question(question_id)
        lesson, course_id, topic_id, _ = self._lesson_and_course(question.lesson_id)
        self._profile_row(session)
        existing = session.scalar(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
            StudentLearningAttemptRow.submission_id == body.submission_id,
        ))
        if existing is not None:
            if (existing.question_id != question_id or existing.submitted_response != body.response
                    or (body.session_id is not None and existing.session_id != body.session_id)):
                raise APIError(409, "SUBMISSION_ID_REUSED", "This submission ID was already used for a different answer.")
            feedback = dict(existing.feedback)
            feedback["idempotent_replay"] = True
            return AnswerFeedback.model_validate(feedback).model_dump(mode="json")
        session_row = None
        if body.session_id is not None:
            session_row = session.get(StudentLearningSessionRow, body.session_id)
            if session_row is None or session_row.profile_id != PROFILE_ID or session_row.lesson_id != question.lesson_id:
                raise APIError(409, "SESSION_MISMATCH", "The learning session does not belong to this question’s lesson.")
        else:
            session_data = self.start_session(session, question.lesson_id)
            session_row = session.get(StudentLearningSessionRow, session_data["session_id"])
        is_correct = self._evaluate(question, body.response)
        attempt_number = (session.scalar(select(func.count()).select_from(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
            StudentLearningAttemptRow.question_id == question_id,
        )) or 0) + 1
        event_sequence = (session.scalar(select(func.max(StudentLearningAttemptRow.event_sequence)).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        )) or 0) + 1
        now = utc_now()
        attempt_id = str(uuid.uuid4())
        evidence = base_record(
            learner_id=PROFILE_ID,
            session_id=session_row.session_id,
            evidence_type="interaction",
            event_timestamp=now,
            sequence_number=event_sequence,
            temporal_precision="millisecond",
            timestamp_source="server answer-submission time",
            source_dataset="mcp-ri-student-studio",
            source_file=None,
            source_record_id=attempt_id,
            source_modality="interaction",
            processing_method="student_studio_answer_evaluator",
            content={
                "course_id": course_id,
                "topic_id": topic_id,
                "lesson_id": question.lesson_id,
                "question_id": question_id,
                "submitted_answer": body.response,
                "correctness": int(is_correct),
                "skill_ids": [],
                "is_exact_duplicate": False,
                "content_version": question.content_version,
            },
            extraction_method="server_evaluated_response",
            transformation_history=["Student Studio answer evaluated and normalized as separate platform evidence."],
            uncertainty_flags=["local_demo_profile"],
            uncertainty_notes=["This response is behavioral activity and does not establish understanding or mastery."],
        )
        feedback = AnswerFeedback(
            attempt_id=attempt_id,
            evidence_id=evidence["evidence_id"],
            question_id=question_id,
            attempt_number=attempt_number,
            is_correct=is_correct,
            submitted_response=body.response,
            expected_answer=question.expected_answer,
            explanation=question.explanation,
            feedback_message="Correct. Review the explanation to reinforce the reasoning." if is_correct else "Not quite. Review the explanation and try another question.",
            submitted_at=now,
            content_version=question.content_version,
        ).model_dump(mode="json")
        session.add(StudentLearningAttemptRow(
            attempt_id=attempt_id,
            profile_id=PROFILE_ID,
            session_id=session_row.session_id,
            submission_id=body.submission_id,
            course_id=course_id,
            topic_id=topic_id,
            lesson_id=question.lesson_id,
            question_id=question_id,
            attempt_number=attempt_number,
            event_sequence=event_sequence,
            submitted_response=body.response,
            is_correct=is_correct,
            feedback=feedback,
            content_version=question.content_version,
            event_timestamp=now,
            evidence_record=evidence,
        ))
        session_row.last_activity_at = now
        session.flush()
        return feedback

    def progress(self, session: Session) -> dict[str, Any]:
        self._profile_row(session)
        lessons_by_id = {lesson.lesson_id: lesson for lesson in curriculum().lessons}
        rows = session.scalars(select(StudentLessonProgressRow).where(
            StudentLessonProgressRow.profile_id == PROFILE_ID,
        ).order_by(StudentLessonProgressRow.updated_at.desc())).all()
        attempts = session.scalars(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        )).all()
        course_refs = {
            course.course_id: (subject.subject_id, course.title)
            for subject in curriculum().subjects for course in subject.courses
        }
        attempts_by_course: dict[str, list[StudentLearningAttemptRow]] = {}
        for attempt in attempts:
            attempts_by_course.setdefault(attempt.course_id, []).append(attempt)
        rows_by_course: dict[str, list[StudentLessonProgressRow]] = {}
        for row in rows:
            rows_by_course.setdefault(row.course_id, []).append(row)
        courses: list[dict[str, Any]] = []
        for course_id, (subject_id, title) in course_refs.items():
            lessons = [lesson for lesson in curriculum().lessons if lesson.course_id == course_id]
            course_rows = rows_by_course.get(course_id, [])
            statuses = [self._progress(session, lesson)["status"] for lesson in lessons]
            completed = sum(status == "completed" for status in statuses)
            course_attempts = attempts_by_course.get(course_id, [])
            correct = sum(attempt.is_correct for attempt in course_attempts)
            started_topics = {row.topic_id for row in course_rows}
            status = "completed" if lessons and completed == len(lessons) else "needs_review" if "needs_review" in statuses else "in_progress" if course_rows else "not_started"
            courses.append(CourseProgress(
                course_id=course_id,
                subject_id=subject_id,
                title=title,
                status=status,
                lessons_completed=completed,
                lesson_count=len(lessons),
                completion_percentage=round(100 * completed / len(lessons)) if lessons else 0,
                topics_started=len(started_topics),
                practice_attempts=len(course_attempts),
                correct_attempts=correct,
                response_accuracy=correct / len(course_attempts) if course_attempts else None,
            ).model_dump(mode="json"))
        all_status = [self._progress(session, lesson)["status"] for lesson in curriculum().lessons]
        summary = StudentProgressSummary(
            courses_started=sum(bool(rows_by_course.get(course_id)) for course_id in course_refs),
            topics_started=len({row.topic_id for row in rows}),
            lessons_started=len(rows),
            lessons_completed=sum(status == "completed" for status in all_status),
            lessons_needing_review=sum(status == "needs_review" for status in all_status),
            lesson_sections_completed=sum(len(self._progress(session, lessons_by_id[row.lesson_id])["completed_section_ids"]) for row in rows),
            lesson_sections_total=sum(len([section for section in lessons_by_id[row.lesson_id].sections if section.required]) for row in rows),
            practice_attempts=len(attempts),
            correct_attempts=sum(attempt.is_correct for attempt in attempts),
            incorrect_attempts=sum(not attempt.is_correct for attempt in attempts),
            response_accuracy=sum(attempt.is_correct for attempt in attempts) / len(attempts) if attempts else None,
        )
        return StudentProgressData(
            profile=StudentStudioProfile.model_validate(self.profile_data()),
            summary=summary,
            courses=courses,
            recent_lesson_ids=[row.lesson_id for row in rows[:8]],
            updated_at=max((row.updated_at for row in rows), default=None),
        ).model_dump(mode="json")

    def history(self, session: Session, *, limit: int, offset: int) -> dict[str, Any]:
        self._profile_row(session)
        lesson_titles = {lesson.lesson_id: lesson.title for lesson in curriculum().lessons}
        course_by_id = {course.course_id: subject.subject_id for subject in curriculum().subjects for course in subject.courses}
        items: list[dict[str, Any]] = []
        sessions = session.scalars(select(StudentLearningSessionRow).where(
            StudentLearningSessionRow.profile_id == PROFILE_ID,
        )).all()
        for row in sessions:
            _, course_id, topic_id, _ = self._lesson_and_course(row.lesson_id)
            items.append(LearningHistoryEntry(
                entry_id=row.session_id,
                event_type="lesson_started",
                occurred_at=row.started_at,
                course_id=course_id,
                topic_id=topic_id,
                lesson_id=row.lesson_id,
                lesson_title=lesson_titles[row.lesson_id],
                content_version=row.content_version,
            ).model_dump(mode="json"))
        attempts = session.scalars(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        )).all()
        for row in attempts:
            items.append(LearningHistoryEntry(
                entry_id=row.attempt_id,
                event_type="answer_submitted",
                occurred_at=row.event_timestamp,
                course_id=row.course_id,
                topic_id=row.topic_id,
                lesson_id=row.lesson_id,
                lesson_title=lesson_titles[row.lesson_id],
                question_id=row.question_id,
                is_correct=row.is_correct,
                attempt_number=row.attempt_number,
                content_version=row.content_version,
            ).model_dump(mode="json"))
        items.sort(key=lambda item: (item["occurred_at"], item["entry_id"]), reverse=True)
        total = len(items)
        return {"profile": self.profile_data(), "items": items[offset:offset + limit], "total": total}

    def evidence(self, session: Session, *, limit: int, offset: int) -> dict[str, Any]:
        self._profile_row(session)
        total = session.scalar(select(func.count()).select_from(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        )) or 0
        rows = session.scalars(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        ).order_by(StudentLearningAttemptRow.event_sequence.desc()).limit(limit).offset(offset)).all()
        return StudentEvidenceData(
            profile=StudentStudioProfile.model_validate(self.profile_data()),
            items=[row.evidence_record for row in rows],
            total=total,
        ).model_dump(mode="json")

    def behavioral_state(self, session: Session) -> dict[str, Any]:
        self._profile_row(session)
        rows = session.scalars(select(StudentLearningAttemptRow).where(
            StudentLearningAttemptRow.profile_id == PROFILE_ID,
        ).order_by(StudentLearningAttemptRow.event_sequence)).all()
        accumulator = LearnerStateAccumulator(PROFILE_ID)
        for row in rows:
            apply_interaction_evidence(accumulator, row.evidence_record)
        state = accumulator.snapshot()
        state["limitations"] = [
            limitation for limitation in state["limitations"]
            if "EdNet timestamps" not in limitation
        ] + [
            "Student Studio records use server answer-submission timestamps and an aggregate response summary.",
            "Student Studio events are separate from EdNet and have no validated topic-to-skill mapping; topic-level states, cognitive estimates and adaptive decisions are not inferred.",
        ]
        return StudentBehavioralStateData(
            profile=StudentStudioProfile.model_validate(self.profile_data()),
            source="student_studio_interactions",
            state=state,
        ).model_dump(mode="json")
