"""Versioned curriculum, lesson, attempt, and Student Studio API models."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from typing_extensions import Union


Identifier = Annotated[str, StringConstraints(min_length=1, max_length=160, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")]
ContentVersion = Annotated[str, StringConstraints(min_length=1, max_length=40)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LearningObjective(StrictModel):
    objective_id: Identifier
    text: str = Field(min_length=1, max_length=500)


class TopicSummary(StrictModel):
    topic_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1200)
    learning_objectives: list[LearningObjective]
    estimated_minutes: int = Field(ge=1, le=240)
    prerequisites_status: Literal["not_established", "validated"] = "not_established"
    prerequisite_topic_ids: list[Identifier] = Field(default_factory=list)
    lesson_id: Identifier
    practice_question_count: int = Field(ge=0)


class CurriculumUnit(StrictModel):
    unit_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1200)
    topics: list[TopicSummary]


class CurriculumCourse(StrictModel):
    course_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1200)
    units: list[CurriculumUnit]


class CurriculumSubject(StrictModel):
    subject_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1200)
    courses: list[CurriculumCourse]


class HeadingBlock(StrictModel):
    type: Literal["heading"]
    level: Literal[2, 3]
    text: str = Field(min_length=1, max_length=300)


class ParagraphBlock(StrictModel):
    type: Literal["paragraph"]
    text: str = Field(min_length=1, max_length=4000)


class DefinitionBlock(StrictModel):
    type: Literal["definition"]
    term: str = Field(min_length=1, max_length=160)
    definition: str = Field(min_length=1, max_length=2000)


class FormulaBlock(StrictModel):
    type: Literal["formula"]
    label: str = Field(min_length=1, max_length=200)
    expression: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=1200)


class WorkedExampleBlock(StrictModel):
    type: Literal["worked_example"]
    prompt: str = Field(min_length=1, max_length=1200)
    steps: list[str] = Field(min_length=1, max_length=12)
    result: str = Field(min_length=1, max_length=500)


class KeyPointBlock(StrictModel):
    type: Literal["key_point"]
    text: str = Field(min_length=1, max_length=1200)


class MisconceptionBlock(StrictModel):
    type: Literal["misconception"]
    claim: str = Field(min_length=1, max_length=500)
    correction: str = Field(min_length=1, max_length=1200)


LessonBlock = Annotated[
    Union[
        HeadingBlock,
        ParagraphBlock,
        DefinitionBlock,
        FormulaBlock,
        WorkedExampleBlock,
        KeyPointBlock,
        MisconceptionBlock,
    ],
    Field(discriminator="type"),
]


class LessonSection(StrictModel):
    section_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    required: bool = True
    blocks: list[LessonBlock] = Field(min_length=1)


class LessonContent(StrictModel):
    lesson_id: Identifier
    topic_id: Identifier
    course_id: Identifier
    title: str = Field(min_length=1, max_length=200)
    introduction: str = Field(min_length=1, max_length=2000)
    learning_objectives: list[LearningObjective] = Field(min_length=1)
    estimated_minutes: int = Field(ge=1, le=240)
    content_version: ContentVersion
    content_source: Literal["curated_static"] = "curated_static"
    sections: list[LessonSection] = Field(min_length=1)


class ChoiceGrading(StrictModel):
    kind: Literal["choice"]
    correct_option_ids: list[Identifier] = Field(min_length=1)


class NumericGrading(StrictModel):
    kind: Literal["numeric"]
    expected_value: Decimal
    absolute_tolerance: Decimal = Decimal("0")
    relative_tolerance: Decimal = Decimal("0")


GradingSpecification = Annotated[Union[ChoiceGrading, NumericGrading], Field(discriminator="kind")]


class QuestionOption(StrictModel):
    option_id: Identifier
    text: str = Field(min_length=1, max_length=1000)


class QuestionRecord(StrictModel):
    question_id: Identifier
    lesson_id: Identifier
    topic_id: Identifier
    objective_id: Identifier
    question_type: Literal["single_choice", "multiple_choice", "numeric"]
    prompt: str = Field(min_length=1, max_length=3000)
    options: list[QuestionOption] = Field(default_factory=list)
    grading: GradingSpecification
    expected_answer: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=2000)
    difficulty: Literal["introductory", "intermediate", "challenge"]
    content_version: ContentVersion


class PublicQuestion(StrictModel):
    question_id: Identifier
    lesson_id: Identifier
    topic_id: Identifier
    objective_id: Identifier
    question_type: Literal["single_choice", "multiple_choice", "numeric"]
    prompt: str
    options: list[QuestionOption]
    difficulty: Literal["introductory", "intermediate", "challenge"]
    content_version: ContentVersion


class CurriculumFile(StrictModel):
    curriculum_version: ContentVersion
    subjects: list[CurriculumSubject]
    lessons: list[LessonContent]
    questions: list[QuestionRecord]


class CurriculumCatalog(StrictModel):
    curriculum_version: ContentVersion
    subjects: list[CurriculumSubject]


class TopicDetails(StrictModel):
    subject_id: Identifier
    subject_title: str
    course_id: Identifier
    course_title: str
    unit_id: Identifier
    unit_title: str
    topic: TopicSummary


class StudentStudioProfile(StrictModel):
    profile_id: Identifier
    display_name: str
    identity_mode: Literal["local_demo"]
    notice: str


class LessonProgressUpdate(StrictModel):
    session_id: Identifier
    current_section_id: Identifier
    completed_section_ids: list[Identifier] = Field(default_factory=list)


class LessonProgressData(StrictModel):
    lesson_id: Identifier
    status: Literal["not_started", "in_progress", "completed", "needs_review"]
    current_section_id: Identifier | None
    completed_section_ids: list[Identifier]
    completed_required_sections: int
    required_section_count: int
    completion_percentage: int = Field(ge=0, le=100)
    content_complete: bool
    review_reason: str | None = None
    updated_at: str | None = None


class LearningSessionData(StrictModel):
    session_id: Identifier
    profile_id: Identifier
    lesson_id: Identifier
    started_at: str
    resumed: bool
    progress: LessonProgressData


class LearningSessionRequest(StrictModel):
    lesson_id: Identifier


class AnswerSubmission(StrictModel):
    submission_id: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    response: dict[str, Any]
    session_id: Identifier | None = None


class LearningProcessingStatus(StrictModel):
    interaction: Literal["saved"]
    evidence: Literal["recorded"]
    behavioral_state: Literal["updated"]
    behavioral_state_version: int = Field(ge=1)


class RecommendedActivity(StrictModel):
    activity_type: Literal["review_lesson", "continue_lesson", "additional_practice"]
    topic_id: Identifier
    lesson_id: Identifier
    title: str = Field(min_length=1, max_length=200)


class PersonalizedRecommendation(StrictModel):
    recommendation_id: Identifier
    learner_id: Identifier
    activity: RecommendedActivity
    reason: str = Field(min_length=1, max_length=1000)
    supporting_evidence_ids: list[Identifier] = Field(min_length=1)
    source_behavioral_state_version: int = Field(ge=1)
    created_at: str
    status: Literal["current", "superseded"]
    limitations: list[str]


class RecommendationDecision(StrictModel):
    status: Literal["personalized", "more_evidence_needed"]
    message: str
    source_behavioral_state_version: int | None = Field(default=None, ge=1)
    recommendation: PersonalizedRecommendation | None = None


class QuestionPractice(StrictModel):
    lesson_id: Identifier
    content_version: ContentVersion
    questions: list[PublicQuestion]


class AnswerFeedback(StrictModel):
    attempt_id: Identifier
    evidence_id: Identifier
    question_id: Identifier
    attempt_number: int = Field(ge=1)
    is_correct: bool
    submitted_response: dict[str, Any]
    expected_answer: str
    explanation: str
    feedback_message: str
    submitted_at: str
    content_version: ContentVersion
    idempotent_replay: bool = False
    processing: LearningProcessingStatus | None = None
    recommendation: RecommendationDecision | None = None


class CourseProgress(StrictModel):
    course_id: Identifier
    subject_id: Identifier
    title: str
    status: Literal["not_started", "in_progress", "completed", "needs_review"]
    lessons_completed: int = Field(ge=0)
    lesson_count: int = Field(ge=0)
    completion_percentage: int = Field(ge=0, le=100)
    topics_started: int = Field(ge=0)
    practice_attempts: int = Field(ge=0)
    correct_attempts: int = Field(ge=0)
    response_accuracy: float | None = Field(default=None, ge=0, le=1)


class StudentProgressSummary(StrictModel):
    courses_started: int = Field(ge=0)
    topics_started: int = Field(ge=0)
    lessons_started: int = Field(ge=0)
    lessons_completed: int = Field(ge=0)
    lessons_needing_review: int = Field(ge=0)
    lesson_sections_completed: int = Field(ge=0)
    lesson_sections_total: int = Field(ge=0)
    practice_attempts: int = Field(ge=0)
    correct_attempts: int = Field(ge=0)
    incorrect_attempts: int = Field(ge=0)
    response_accuracy: float | None = Field(default=None, ge=0, le=1)


class StudentProgressData(StrictModel):
    profile: StudentStudioProfile
    summary: StudentProgressSummary
    courses: list[CourseProgress]
    recent_lesson_ids: list[Identifier]
    updated_at: str | None = None


class LearningHistoryEntry(StrictModel):
    entry_id: Identifier
    event_type: Literal["lesson_started", "answer_submitted"]
    occurred_at: str
    course_id: Identifier
    topic_id: Identifier
    lesson_id: Identifier
    lesson_title: str
    question_id: Identifier | None = None
    is_correct: bool | None = None
    attempt_number: int | None = Field(default=None, ge=1)
    content_version: ContentVersion


class LearningHistoryData(StrictModel):
    profile: StudentStudioProfile
    items: list[LearningHistoryEntry]
    total: int = Field(ge=0)


class StudentEvidenceData(StrictModel):
    profile: StudentStudioProfile
    items: list[dict[str, Any]]
    total: int = Field(ge=0)


class StudentBehavioralStateVersionData(StrictModel):
    profile_id: Identifier
    state_version: int = Field(ge=1)
    source_event_sequence: int = Field(ge=0)
    last_evidence_id: Identifier
    evidence_count: int = Field(ge=1)
    previous_state_version: int | None = Field(default=None, ge=1)
    state_timestamp: str
    state: dict[str, Any]
    supporting_evidence_ids: list[Identifier]
    created_at: str


class StudentBehavioralStateVersionsData(StrictModel):
    profile: StudentStudioProfile
    items: list[StudentBehavioralStateVersionData]
    total: int = Field(ge=0)


class StudentBehavioralStateData(StrictModel):
    profile: StudentStudioProfile
    source: Literal["student_studio_interactions"]
    state: dict[str, Any]
    state_version: int | None = Field(default=None, ge=1)
    previous_state_version: int | None = Field(default=None, ge=1)
    supporting_evidence_ids: list[Identifier] = Field(default_factory=list)


class DownstreamAvailability(StrictModel):
    status: Literal["available", "not_available"]
    reason: str


class StudentIntelligenceStatusData(StrictModel):
    profile: StudentStudioProfile
    source_behavioral_state_version: int | None = Field(default=None, ge=1)
    evidence_count: int = Field(ge=0)
    cognitive_state: DownstreamAvailability
    representation_planning: DownstreamAvailability
    trajectory: DownstreamAvailability


class StudentRecommendationData(StrictModel):
    profile: StudentStudioProfile
    decision: RecommendationDecision
