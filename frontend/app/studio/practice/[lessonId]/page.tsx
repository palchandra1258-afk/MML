import { Suspense } from "react";
import { StudentStudioClient } from "@/components/studio/student-studio-client";

async function PracticeContent({ params }: PageProps<"/studio/practice/[lessonId]">) {
  const { lessonId } = await params;
  return <StudentStudioClient view="practice" id={lessonId}/>;
}

export default function PracticePage(props: PageProps<"/studio/practice/[lessonId]">) {
  return <Suspense fallback={<div className="studio-loading panel">Opening practice…</div>}><PracticeContent {...props}/></Suspense>;
}
