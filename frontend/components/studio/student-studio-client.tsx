"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  getLearningService,
  type AnswerFeedback,
  type CurriculumCatalog,
  type HistoryEntry,
  type LearningHistory,
  type LearningSession,
  type Lesson,
  type LessonProgress,
  type Practice,
  type PublicQuestion,
  type StudentProgress,
  type TopicDetails,
} from "@/lib/services/learning.service";

type View = "home" | "explore" | "subject" | "topic" | "lesson" | "practice" | "progress" | "history";

function ErrorPanel({ message, retry }: { message: string; retry: () => void }) {
  return <div className="studio-error panel" role="alert"><div><strong>Student Studio could not load this data</strong><p>{message}</p></div><button className="button button--secondary" onClick={retry}>Try again</button></div>;
}

function EmptyPanel({ title, description }: { title: string; description: string }) {
  return <div className="studio-empty panel"><span className="studio-empty-mark">i</span><div><strong>{title}</strong><p>{description}</p></div></div>;
}

function TopicCard({ item }: { item: TopicDetails }) {
  return <article className="studio-topic-card panel">
    <div className="studio-card-meta"><span>{item.subject_title}</span><span>{item.topic.estimated_minutes} min</span></div>
    <h3>{item.topic.title}</h3><p>{item.topic.description}</p>
    <div className="studio-card-foot"><span>{item.topic.practice_question_count} practice questions</span><Link href={`/studio/topics/${item.topic.topic_id}`}>View topic <span aria-hidden="true">→</span></Link></div>
  </article>;
}

function flattenTopics(catalog: CurriculumCatalog | null): TopicDetails[] {
  if (!catalog) return [];
  return catalog.subjects.flatMap((subject) => subject.courses.flatMap((course) => course.units.flatMap((unit) => unit.topics.map((topic) => ({
    subject_id: subject.subject_id,
    subject_title: subject.title,
    course_id: course.course_id,
    course_title: course.title,
    unit_id: unit.unit_id,
    unit_title: unit.title,
    topic,
  })))));
}

function LessonBlockView({ block }: { block: Lesson["sections"][number]["blocks"][number] }) {
  if (block.type === "paragraph") return <p className="studio-lesson-paragraph">{block.text}</p>;
  if (block.type === "heading") return block.level === 2 ? <h2>{block.text}</h2> : <h3>{block.text}</h3>;
  if (block.type === "definition") return <div className="studio-definition"><strong>{block.term}</strong><p>{block.definition}</p></div>;
  if (block.type === "formula") return <div className="studio-formula"><span>{block.label}</span><strong>{block.expression}</strong><p>{block.explanation}</p></div>;
  if (block.type === "worked_example") return <div className="studio-worked-example"><span className="studio-block-label">Worked example</span><h3>{block.prompt}</h3><ol>{block.steps.map((step, index) => <li key={`${index}-${step}`}>{step}</li>)}</ol><p className="studio-example-result"><strong>Result</strong> {block.result}</p></div>;
  if (block.type === "key_point") return <div className="studio-key-point"><span aria-hidden="true">✓</span><p>{block.text}</p></div>;
  return <div className="studio-misconception"><span className="studio-block-label">Check this idea</span><p><strong>{block.claim}</strong></p><p>{block.correction}</p></div>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function StudentStudioClient({ view, id }: { view: View; id?: string }) {
  const [catalog, setCatalog] = useState<CurriculumCatalog | null>(null);
  const [topic, setTopic] = useState<TopicDetails | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [practice, setPractice] = useState<Practice | null>(null);
  const [learningSession, setLearningSession] = useState<LearningSession | null>(null);
  const [progress, setProgress] = useState<StudentProgress | null>(null);
  const [history, setHistory] = useState<LearningHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [reloadCount, setReloadCount] = useState(0);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<TopicDetails[] | null>(null);
  const [activeSection, setActiveSection] = useState(0);
  const [lessonProgress, setLessonProgress] = useState<LessonProgress | null>(null);
  const [activeQuestion, setActiveQuestion] = useState(0);
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [numericAnswer, setNumericAnswer] = useState("");
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submissionId = useRef<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setLoading(true);
      setError(null);
      setCatalog(null);
      setTopic(null);
      setLesson(null);
      setPractice(null);
      setLearningSession(null);
      setProgress(null);
      setHistory(null);
      try {
        const service = getLearningService();
        const requests: Promise<unknown>[] = [service.profile(controller.signal)];
        if (view === "home" || view === "explore" || view === "subject") requests.push(service.catalog(controller.signal));
        if (view === "home") requests.push(service.progress(controller.signal));
        if (view === "topic" && id) requests.push(service.topic(id, controller.signal));
        if (view === "lesson" && id) requests.push(service.lesson(id, controller.signal), service.startSession(id, controller.signal));
        if (view === "practice" && id) requests.push(service.practice(id, controller.signal), service.startSession(id, controller.signal));
        if (view === "progress") requests.push(service.progress(controller.signal));
        if (view === "history") requests.push(service.history(controller.signal));
        const values = await Promise.all(requests);
        let cursor = 1;
        if (view === "home" || view === "explore" || view === "subject") setCatalog((values[cursor++] as { data: CurriculumCatalog }).data);
        if (view === "home") setProgress((values[cursor++] as { data: StudentProgress }).data);
        if (view === "topic" && id) setTopic((values[cursor++] as { data: TopicDetails }).data);
        if (view === "lesson" && id) {
          setLesson((values[cursor++] as { data: Lesson }).data);
          const started = (values[cursor++] as { data: LearningSession }).data;
          setLearningSession(started);
          setLessonProgress(started.progress);
          const loadedLesson = (values[cursor - 2] as { data: Lesson }).data;
          setActiveSection(Math.max(0, started.progress.current_section_id ? loadedLesson.sections.findIndex((section) => section.section_id === started.progress.current_section_id) : 0));
        }
        if (view === "practice" && id) {
          setPractice((values[cursor++] as { data: Practice }).data);
          setLearningSession((values[cursor++] as { data: LearningSession }).data);
        }
        if (view === "progress") setProgress((values[cursor++] as { data: StudentProgress }).data);
        if (view === "history") setHistory((values[cursor++] as { data: LearningHistory }).data);
      } catch (loadError) {
        if (!controller.signal.aborted) setError(loadError instanceof Error ? loadError.message : "The API request failed.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [view, id, reloadCount]);

  const allTopics = useMemo(() => flattenTopics(catalog), [catalog]);
  const selectedSubject = catalog?.subjects.find((subject) => subject.subject_id === id);
  const selectedSubjectTopics = selectedSubject?.courses.flatMap((course) => course.units.flatMap((unit) => unit.topics.map((item) => ({
    subject_id: selectedSubject.subject_id, subject_title: selectedSubject.title, course_id: course.course_id,
    course_title: course.title, unit_id: unit.unit_id, unit_title: unit.title, topic: item,
  })))) ?? [];
  const activeLessonSection = lesson?.sections[activeSection];
  const question: PublicQuestion | undefined = practice?.questions[activeQuestion];

  async function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const service = getLearningService();
      const result = await service.search(query.trim());
      setSearchResults(result.data ?? []);
      setError(null);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Search could not be completed.");
    }
  }

  async function saveSection(sectionIndex: number, completedIds = lessonProgress?.completed_section_ids ?? []) {
    if (!lesson || !learningSession) return;
    const current = lesson.sections[sectionIndex];
    if (!current) return;
    setActiveSection(sectionIndex);
    try {
      const result = await getLearningService().saveProgress(lesson.lesson_id, {
        session_id: learningSession.session_id,
        current_section_id: current.section_id,
        completed_section_ids: completedIds,
      });
      setLessonProgress(result.data!);
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Progress could not be saved.");
    }
  }

  async function completeSection() {
    if (!lesson || !activeLessonSection) return;
    const completed = [...new Set([...(lessonProgress?.completed_section_ids ?? []), activeLessonSection.section_id])];
    await saveSection(Math.min(activeSection + 1, lesson.sections.length - 1), completed);
  }

  function chooseOption(optionId: string, multiple: boolean) {
    submissionId.current = null;
    setFeedback(null);
    setSelectedOptions((current) => multiple
      ? current.includes(optionId) ? current.filter((value) => value !== optionId) : [...current, optionId]
      : [optionId]);
  }

  async function submitAnswer() {
    if (!question || !learningSession || submitting) return;
    if (question.question_type === "numeric" ? !numericAnswer.trim() : selectedOptions.length === 0) return;
    submissionId.current ??= globalThis.crypto?.randomUUID?.() ?? `studio-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const response = question.question_type === "numeric" ? { value: numericAnswer.trim() } : { option_ids: selectedOptions };
    setSubmitting(true);
    try {
      const result = await getLearningService().submitAnswer(question.question_id, {
        submission_id: submissionId.current,
        session_id: learningSession.session_id,
        response,
      });
      setFeedback(result.data!);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Your answer could not be saved.");
    } finally {
      setSubmitting(false);
    }
  }

  function nextQuestion() {
    setFeedback(null);
    setSelectedOptions([]);
    setNumericAnswer("");
    submissionId.current = null;
    setActiveQuestion((current) => current + 1);
  }

  if (loading) return <div className="studio-loading panel"><span className="loading-indicator"/><span>Loading your learning space…</span></div>;
  if (error && !catalog && !topic && !lesson && !practice && !progress && !history) return <ErrorPanel message={error} retry={() => setReloadCount((count) => count + 1)}/>;

  if (view === "home") return <div className="student-studio-page">
    <section className="studio-welcome panel"><div><span className="studio-eyebrow">Student Learning Studio</span><h2>What would you like to learn today?</h2><p>Choose a curated topic, work through a short lesson and practice the ideas with feedback.</p></div><div className="studio-profile-tag"><span className="avatar avatar--small">LD</span><span><strong>Local demo profile</strong><small>Saved on this backend</small></span></div>
      <form className="studio-search" onSubmit={search}><label className="sr-only" htmlFor="studio-search-home">Search available topics</label><input id="studio-search-home" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search topics, for example Bayes’ theorem"/><button className="button button--primary" type="submit">Find topics</button></form>
      {searchResults && <div className="studio-search-results" aria-live="polite">{searchResults.length ? searchResults.map((item) => <TopicCard key={item.topic.topic_id} item={item}/>) : <EmptyPanel title="No matching curated lesson" description="This topic is not available yet. Browse the current catalog to choose a supported lesson."/>}</div>}
    </section>
    {error && <ErrorPanel message={error} retry={() => setReloadCount((count) => count + 1)}/>}
    <section className="studio-section"><div className="studio-section-heading"><div><span className="studio-eyebrow">Start exploring</span><h2>Subjects</h2></div><Link href="/studio/explore">See all subjects <span aria-hidden="true">→</span></Link></div><div className="studio-subject-grid">{catalog?.subjects.map((subject) => {
      const topicCount = subject.courses.reduce((sum, course) => sum + course.units.reduce((unitSum, unit) => unitSum + unit.topics.length, 0), 0);
      return <Link className="studio-subject-card panel" key={subject.subject_id} href={`/studio/subjects/${subject.subject_id}`}><span className="studio-subject-icon">{subject.title.slice(0, 1)}</span><span className="studio-subject-copy"><strong>{subject.title}</strong><small>{topicCount ? `${topicCount} curated ${topicCount === 1 ? "topic" : "topics"}` : "Lessons coming soon"}</small></span><span className="studio-subject-arrow">→</span></Link>;
    })}</div></section>
    <section className="studio-home-progress panel"><div><span className="studio-eyebrow">Your activity</span><h2>Learning builds one step at a time</h2><p>Progress is saved from lesson checkpoints and practice answers. A correct answer is not treated as proof of mastery.</p></div><div className="studio-home-progress-stats"><span><strong>{progress?.summary.lessons_completed ?? 0}</strong><small>lessons completed</small></span><span><strong>{progress?.summary.practice_attempts ?? 0}</strong><small>practice attempts</small></span></div><Link className="button button--secondary" href="/studio/progress">View my progress</Link></section>
  </div>;

  if (view === "explore") return <div className="student-studio-page"><header className="studio-page-intro"><span className="studio-eyebrow">Explore subjects</span><h2>Choose a topic to begin</h2><p>Every listed lesson has curated explanations and practice. Empty subject areas are labeled so you know what is available.</p></header>
    <form className="studio-search studio-search--compact" onSubmit={search}><label className="sr-only" htmlFor="studio-search-explore">Search available topics</label><input id="studio-search-explore" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search available topics"/><button className="button button--primary" type="submit">Search</button></form>
    {searchResults && <div className="studio-topic-grid">{searchResults.map((item) => <TopicCard key={item.topic.topic_id} item={item}/>)}</div>}
    <div className="studio-explore-subjects">{catalog?.subjects.map((subject) => <section className="studio-subject-section" key={subject.subject_id}><div className="studio-section-heading"><div><span className="studio-eyebrow">Subject</span><h2>{subject.title}</h2></div><Link href={`/studio/subjects/${subject.subject_id}`}>Open subject <span aria-hidden="true">→</span></Link></div><p>{subject.description}</p><div className="studio-topic-grid">{allTopics.filter((item) => item.subject_id === subject.subject_id).map((item) => <TopicCard key={item.topic.topic_id} item={item}/>)}</div>{subject.courses.length === 0 && <EmptyPanel title="Curated lessons are not available yet" description="This subject is listed for exploration, but no lesson content has been published here yet."/>}</section>)}</div>
  </div>;

  if (view === "subject") return <div className="student-studio-page"><header className="studio-page-intro"><span className="studio-eyebrow">Explore subjects / {selectedSubject?.title ?? "Subject"}</span><h2>{selectedSubject?.title ?? "Subject not found"}</h2><p>{selectedSubject?.description ?? "This subject could not be found in the curriculum."}</p></header>{selectedSubjectTopics.length ? <div className="studio-topic-grid">{selectedSubjectTopics.map((item) => <TopicCard key={item.topic.topic_id} item={item}/>)}</div> : <EmptyPanel title="No curated lessons yet" description="Choose another subject to view the lessons currently available."/>}</div>;

  if (view === "topic") return <div className="student-studio-page">{topic ? <><div className="studio-breadcrumb"><Link href="/studio/explore">Explore subjects</Link><span>›</span><Link href={`/studio/subjects/${topic.subject_id}`}>{topic.subject_title}</Link><span>›</span><span>{topic.topic.title}</span></div><section className="studio-topic-hero panel"><div><span className="studio-eyebrow">{topic.course_title} · {topic.unit_title}</span><h2>{topic.topic.title}</h2><p>{topic.topic.description}</p><div className="studio-topic-meta"><span>{topic.topic.estimated_minutes} minute lesson</span><span>{topic.topic.practice_question_count} practice questions</span><span>Prerequisites not established</span></div></div><Link className="button button--primary" href={`/studio/lessons/${topic.topic.lesson_id}`}>Start or resume lesson <span aria-hidden="true">→</span></Link></section><section className="studio-detail-grid"><article className="panel studio-detail-card"><span className="studio-eyebrow">Learning objectives</span><h3>By the end, you can</h3><ol>{topic.topic.learning_objectives.map((objective) => <li key={objective.objective_id}>{objective.text}</li>)}</ol></article><article className="panel studio-detail-card"><span className="studio-eyebrow">Before you start</span><h3>Prerequisites</h3><p>Validated prerequisite relationships have not been established for this topic.</p><Link href={`/studio/lessons/${topic.topic.lesson_id}`}>Open the curated lesson <span aria-hidden="true">→</span></Link></article></section></> : <EmptyPanel title="Topic unavailable" description="Return to Explore Subjects to pick one of the curated topics."/>}</div>;

  if (view === "lesson") return <div className="student-studio-page">{lesson && activeLessonSection ? <><div className="studio-breadcrumb"><Link href="/studio/explore">Explore subjects</Link><span>›</span><span>{lesson.title}</span></div><section className="studio-lesson-header panel"><div><span className="studio-eyebrow">Curated lesson · {lesson.estimated_minutes} minutes</span><h2>{lesson.title}</h2><p>{lesson.introduction}</p></div><Link className="button button--secondary" href={`/studio/practice/${lesson.lesson_id}`}>Practice questions</Link></section><section className="studio-objectives panel"><strong>Learning objectives</strong><ul>{lesson.learning_objectives.map((objective) => <li key={objective.objective_id}>{objective.text}</li>)}</ul></section>
    <div className="studio-lesson-layout"><nav className="studio-section-nav panel" aria-label="Lesson sections"><div className="studio-section-nav-title"><span className="studio-eyebrow">Lesson sections</span><strong>{lessonProgress?.completed_required_sections ?? 0} of {lessonProgress?.required_section_count ?? lesson.sections.length} complete</strong></div><div className="studio-progress-track"><span style={{ width: `${lessonProgress?.completion_percentage ?? 0}%` }}/></div>{lesson.sections.map((section, index) => <button key={section.section_id} className={`studio-section-nav-item ${index === activeSection ? "is-active" : ""} ${(lessonProgress?.completed_section_ids ?? []).includes(section.section_id) ? "is-complete" : ""}`} onClick={() => void saveSection(index)}><span>{(lessonProgress?.completed_section_ids ?? []).includes(section.section_id) ? "✓" : index + 1}</span>{section.title}</button>)}</nav>
      <article className="studio-lesson-content panel"><span className="studio-eyebrow">Section {activeSection + 1} of {lesson.sections.length}</span><h2>{activeLessonSection.title}</h2><div className="studio-lesson-blocks">{activeLessonSection.blocks.map((block, index) => <LessonBlockView key={`${activeLessonSection.section_id}-${index}`} block={block}/>)}</div><div className="studio-lesson-controls"><button className="button button--secondary" disabled={activeSection === 0} onClick={() => void saveSection(Math.max(0, activeSection - 1))}>Previous</button><span>{lessonProgress?.completion_percentage ?? 0}% lesson sections complete</span><button className="button button--primary" onClick={() => void completeSection()}>{activeSection === lesson.sections.length - 1 ? "Finish lesson" : "Mark complete and continue"}</button></div>{lessonProgress?.status === "completed" && <div className="studio-completion-note" role="status"><strong>Lesson content completed</strong><span>This records section completion. It does not represent a mastery judgment.</span></div>}</article></div>{error && <ErrorPanel message={error} retry={() => setReloadCount((count) => count + 1)}/>}</> : <EmptyPanel title="Lesson unavailable" description="Return to Explore Subjects and choose a published lesson."/>}</div>;

  if (view === "practice") return <div className="student-studio-page">{practice && question ? <><div className="studio-breadcrumb"><Link href={`/studio/lessons/${practice.lesson_id}`}>Back to lesson</Link><span>›</span><span>Practice</span></div><section className="studio-practice-header panel"><div><span className="studio-eyebrow">Practice · {practice.content_version}</span><h2>Check your understanding</h2><p>Answers are evaluated by the backend and saved as separate attempts. Feedback is about this response, not a claim of mastery.</p></div><span className="studio-question-count">Question {activeQuestion + 1} of {practice.questions.length}</span></section><div className="studio-question-card panel"><div className="studio-question-meta"><span>{question.question_type.replaceAll("_", " ")}</span><span>{question.difficulty}</span></div><h3>{question.prompt}</h3>{question.question_type === "numeric" ? <label className="studio-numeric-answer">Your answer<input inputMode="decimal" value={numericAnswer} onChange={(event) => { submissionId.current = null; setNumericAnswer(event.target.value); setFeedback(null); }} placeholder="Enter a number" disabled={Boolean(feedback)}/></label> : <div className="studio-answer-options">{question.options.map((option) => <label className={`studio-answer-option ${selectedOptions.includes(option.option_id) ? "is-selected" : ""}`} key={option.option_id}><input type={question.question_type === "single_choice" ? "radio" : "checkbox"} name={question.question_id} checked={selectedOptions.includes(option.option_id)} onChange={() => chooseOption(option.option_id, question.question_type === "multiple_choice")} disabled={Boolean(feedback)}/><span>{option.text}</span></label>)}</div>}
      {feedback && <div className={`studio-feedback ${feedback.is_correct ? "is-correct" : "is-incorrect"}`} role="status"><strong>{feedback.feedback_message}</strong><p>{feedback.explanation}</p><p><span>Answer</span> {feedback.expected_answer}</p><small>Saved attempt {feedback.attempt_number} · response outcome only</small></div>}
      <div className="studio-question-controls">{feedback ? activeQuestion + 1 < practice.questions.length ? <button className="button button--primary" onClick={nextQuestion}>Next question <span aria-hidden="true">→</span></button> : <Link className="button button--primary" href={`/studio/lessons/${practice.lesson_id}`}>Return to lesson</Link> : <button className="button button--primary" onClick={() => void submitAnswer()} disabled={submitting || (question.question_type === "numeric" ? !numericAnswer.trim() : selectedOptions.length === 0)}>{submitting ? "Saving answer…" : "Submit answer"}</button>}</div>
    </div>{error && <ErrorPanel message={error} retry={() => setReloadCount((count) => count + 1)}/>}</> : <EmptyPanel title="Practice is unavailable" description="Return to a published lesson to open its practice questions."/>}</div>;

  if (view === "progress") return <div className="student-studio-page"><header className="studio-page-intro"><span className="studio-eyebrow">My learning</span><h2>Your saved progress</h2><p>Progress is based on saved required lesson sections and recorded practice responses.</p></header>{progress && <><div className="studio-metric-grid">{[[progress.summary.lessons_started,"lessons started"],[progress.summary.lessons_completed,"lessons completed"],[progress.summary.practice_attempts,"practice attempts"],[progress.summary.lessons_needing_review,"lessons to review"]].map(([value,label]) => <div className="studio-metric-card panel" key={String(label)}><strong>{value}</strong><span>{label}</span></div>)}</div><div className="studio-course-list">{progress.courses.filter((course) => course.lesson_count > 0).map((course) => <article className="studio-course-progress panel" key={course.course_id}><div className="studio-course-progress-heading"><div><span className="studio-eyebrow">{course.status.replaceAll("_", " ")}</span><h3>{course.title}</h3></div><strong>{course.completion_percentage}%</strong></div><div className="studio-progress-track"><span style={{ width: `${course.completion_percentage}%` }}/></div><div className="studio-course-progress-foot"><span>{course.lessons_completed} of {course.lesson_count} lessons completed</span><span>{course.practice_attempts} attempts · {course.correct_attempts} correct</span></div>{course.response_accuracy !== null && <small className="studio-accuracy-note">Recorded response accuracy: {Math.round(course.response_accuracy * 100)}%. This is not a mastery score.</small>}</article>)}</div><p className="studio-history-link"><Link href="/studio/history">Review your learning history <span aria-hidden="true">→</span></Link></p></>}</div>;

  const historyItems: HistoryEntry[] = history?.items ?? [];
  return <div className="student-studio-page"><header className="studio-page-intro"><span className="studio-eyebrow">My learning</span><h2>Learning history</h2><p>Sessions and submitted answers saved by this local demo profile.</p></header>{historyItems.length ? <ol className="studio-history-list">{historyItems.map((item) => <li key={item.entry_id} className="panel"><span className={`studio-history-mark ${item.event_type === "answer_submitted" ? item.is_correct ? "is-correct" : "is-incorrect" : ""}`}>{item.event_type === "lesson_started" ? "↗" : item.is_correct ? "✓" : "·"}</span><div><strong>{item.event_type === "lesson_started" ? "Started lesson" : item.is_correct ? "Submitted a correct response" : "Submitted an incorrect response"}</strong><span>{item.lesson_title}{item.attempt_number ? ` · attempt ${item.attempt_number}` : ""}</span><small>{formatDate(item.occurred_at)}</small></div><Link href={`/studio/lessons/${item.lesson_id}`}>Open lesson</Link></li>)}</ol> : <EmptyPanel title="No learning activity yet" description="Start a lesson and your saved sessions and practice answers will appear here."/>}</div>;
}
