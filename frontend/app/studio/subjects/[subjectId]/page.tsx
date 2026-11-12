import { Suspense } from "react";
import { StudentStudioClient } from "@/components/studio/student-studio-client";

async function SubjectContent({ params }: PageProps<"/studio/subjects/[subjectId]">) {
  const { subjectId } = await params;
  return <StudentStudioClient view="subject" id={subjectId}/>;
}

export default function SubjectPage(props: PageProps<"/studio/subjects/[subjectId]">) {
  return <Suspense fallback={<div className="studio-loading panel">Opening subject…</div>}><SubjectContent {...props}/></Suspense>;
}
