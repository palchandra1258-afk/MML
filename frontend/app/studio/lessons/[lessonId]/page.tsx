import { Suspense } from "react";
import { StudentStudioClient } from "@/components/studio/student-studio-client";

async function LessonContentPage({ params }: PageProps<"/studio/lessons/[lessonId]">) {
  const { lessonId } = await params;
  return <StudentStudioClient view="lesson" id={lessonId}/>;
}

export default function LessonPage(props: PageProps<"/studio/lessons/[lessonId]">) {
  return <Suspense fallback={<div className="studio-loading panel">Opening lesson…</div>}><LessonContentPage {...props}/></Suspense>;
}
