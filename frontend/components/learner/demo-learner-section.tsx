import Link from "next/link";
import { dashboardDemo } from "@/mocks/dashboard-demo";
import { DataSourceLabel, EmptyState } from "@/components/shared/data-states";
import { StatusBadge } from "@/components/shared/status-badge";
import type { LearnerSection } from "@/components/learner/learner-section-types";

const labels: Record<LearnerSection | "overview", { title: string; description: string }> = {
  overview: { title: "Synthetic learning overview", description: "A fictional scenario that demonstrates the interface only." },
  learning: { title: "Synthetic learning workspace", description: "This walkthrough does not include a lesson or answerable activity." },
  progress: { title: "Synthetic learning progress", description: "No synthetic response history is included in this walkthrough." },
  "learner-state": { title: "Synthetic behavioral record", description: "No synthetic behavioral snapshot is included in this walkthrough." },
  "cognitive-state": { title: "Synthetic cognitive insights", description: "No synthetic estimate is included in this walkthrough." },
  trajectory: { title: "Synthetic trajectory", description: "The overview scenario is illustrative and is not a persisted trajectory." },
};

export function DemoLearnerSection({ section }: { section: LearnerSection | "overview" }) {
  const copy = labels[section];
  return <div className="learner-experience-page">
    <div className="demo-banner"><div><strong>Synthetic demonstration</strong><span>This view sends no API requests and contains no real learner record.</span></div><StatusBadge tone="amber">Mock mode</StatusBadge><DataSourceLabel kind="demo"/></div>
    <header className="learner-page-heading"><div><p className="eyebrow">LEARNING STUDIO · DEMO</p><h2>{copy.title}<span className="welcome-period">.</span></h2><p>{copy.description}</p></div></header>
    {section === "overview" ? <section className="panel learner-demo-objective"><span className="eyebrow">FICTIONAL DEMO OBJECTIVE</span><h3>{dashboardDemo.objective}</h3><p>{dashboardDemo.objectiveNote}</p><div className="learner-demo-links"><Link className="button button--secondary" href="/learning">Open workspace</Link><Link className="text-link" href="/progress">View progress view</Link></div></section> : <EmptyState title="No demonstration record is available">The mock scenario does not invent evidence or learner-state fields for this page. Return to the <Link href="/">synthetic overview</Link> or switch mock mode off to connect the API.</EmptyState>}
    <aside className="learning-activity-unavailable"><span className="research-data-notice-icon" aria-hidden="true">i</span><div><strong>No learning activity is delivered</strong><p>The backend does not provide lesson content, quiz questions, or interaction submission.</p></div></aside>
  </div>;
}
