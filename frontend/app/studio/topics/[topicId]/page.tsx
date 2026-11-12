import { Suspense } from "react";
import { StudentStudioClient } from "@/components/studio/student-studio-client";

async function TopicContent({ params }: PageProps<"/studio/topics/[topicId]">) {
  const { topicId } = await params;
  return <StudentStudioClient view="topic" id={topicId}/>;
}

export default function TopicPage(props: PageProps<"/studio/topics/[topicId]">) {
  return <Suspense fallback={<div className="studio-loading panel">Opening topic…</div>}><TopicContent {...props}/></Suspense>;
}
