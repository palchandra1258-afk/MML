import Link from "next/link";
import type { ReactNode } from "react";
import { useLearnerSelection } from "@/hooks/use-learner-selection";
import { DataSourceLabel, EmptyState } from "@/components/shared/data-states";
import type { LearnerDetail } from "@/lib/api/types";

export function LearnerPageHeading({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  const { learner } = useLearnerSelection();
  return <div className="learner-page-heading">
    <div><p className="eyebrow">{eyebrow}</p><h2>{title}<span className="welcome-period">.</span></h2><p>{description}</p></div>
    <DataSourceLabel kind="api" detail={learner ? `record ${learner.learner_id}` : "select a research record"}/>
  </div>;
}

export function SelectedLearnerSummary({ learner }: { learner: LearnerDetail }) {
  return <div className="learner-record-strip"><span className="learner-record-mark" aria-hidden="true">LR</span><div><span>Research artifact record</span><strong>{learner.learner_id}</strong></div><span className="learner-record-source">{learner.source === "research_artifacts" ? "Pseudonymous source record" : "Application record"}</span><Link href="/" className="text-link">Change record</Link></div>;
}

export function SelectedRecordRequired({ children }: { children?: ReactNode }) {
  return <EmptyState title="Choose a learner record first">
    {children ?? <>Select a pseudonymous research record from the <Link href="/">overview</Link> to see the data available for it.</>}
  </EmptyState>;
}

export function ResearchDataNotice({ children }: { children: ReactNode }) {
  return <aside className="research-data-notice"><span className="research-data-notice-icon" aria-hidden="true">i</span><p>{children}</p></aside>;
}
