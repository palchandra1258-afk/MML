import Link from "next/link";
import { dashboardDemo } from "@/mocks/dashboard-demo";
import { NavIcon } from "@/components/navigation/nav-icon";
import { StatusBadge } from "@/components/shared/status-badge";
import { SectionHeading } from "@/components/shared/section-heading";

function Arrow() { return <span aria-hidden="true">↗</span>; }

export function DemoDashboard() {
  const progress = dashboardDemo.progress.completed / dashboardDemo.progress.total * 100;
  return <div className="dashboard-page">
    <div className="demo-banner"><span className="demo-banner-icon"><NavIcon name="system" size={16}/></span><div><strong>Synthetic walkthrough</strong><span>Every learning detail on this page is fictional demonstration content, not a real learner record.</span></div><StatusBadge tone="amber">Demo data</StatusBadge></div>

    <section className="welcome-row">
      <div><p className="eyebrow">WEDNESDAY, NOVEMBER 11</p><h2>Welcome to the learning studio<span className="welcome-period">.</span></h2><p className="welcome-copy">A clear view of the learning context, the evidence behind it, and what the system can support next.</p></div>
      <Link href="/trajectory" className="button button--secondary">View learning path <Arrow/></Link>
    </section>

    <section className="objective-card panel">
      <div className="objective-content">
        <div className="objective-meta"><StatusBadge tone="teal" dot>Current demo objective</StatusBadge><span className="mini-separator">·</span><span className="small-muted">Learning studio</span></div>
        <h3>{dashboardDemo.objective}</h3>
        <p>{dashboardDemo.objectiveNote}</p>
        <div className="objective-actions"><Link href="/learning" className="button button--primary">Open learning space <span aria-hidden="true">→</span></Link><Link href="/representations" className="text-link">How recommendations work <Arrow/></Link></div>
      </div>
      <div className="objective-side" aria-label="Demonstration progress">
        <div className="ring-wrap"><svg className="progress-ring" viewBox="0 0 100 100" role="img" aria-label={`${Math.round(progress)} percent of synthetic scenario steps recorded`}><circle className="ring-track" cx="50" cy="50" r="42"/><circle className="ring-value" cx="50" cy="50" r="42" strokeDasharray={`${progress * 2.64} 264`}/></svg><div className="ring-label"><strong>{dashboardDemo.progress.completed}</strong><span>of {dashboardDemo.progress.total}</span></div></div>
        <div><span className="small-muted">Scenario progress</span><strong className="progress-caption">{dashboardDemo.progress.label}</strong><span className="tiny-muted">Illustrative, not persisted</span></div>
      </div>
      <div className="objective-decoration" aria-hidden="true"><span/><span/><span/></div>
    </section>

    <div className="dashboard-grid">
      <section className="panel trajectory-panel">
        <SectionHeading eyebrow="Learning path" title="A continuous trajectory" detail="The current step stays connected to the larger goal." action={<Link className="icon-link" href="/trajectory" aria-label="View full learning trajectory"><Arrow/></Link>}/>
        <div className="trajectory-list">
          {dashboardDemo.trajectory.map((step, index) => <div className={`trajectory-step ${index === 1 ? "trajectory-step--current" : index < 1 ? "trajectory-step--done" : ""}`} key={step.title}>
            <div className="step-rail"><span className="step-node">{index < 1 ? "✓" : String(index + 1).padStart(2, "0")}</span>{index < dashboardDemo.trajectory.length - 1 && <span className="step-connector"/>}</div>
            <div className="step-copy"><strong>{step.title}</strong><span>{step.status}</span></div>
            {index === 1 && <StatusBadge tone="teal">In progress</StatusBadge>}
          </div>)}
        </div>
        <div className="continuity-note"><span className="continuity-line"/><p><strong>Continuity is part of the design.</strong> If a supporting detour is needed, the original step should be preserved for resumption.</p></div>
      </section>

      <section className="panel state-panel">
        <SectionHeading eyebrow="Cognitive intelligence" title="Current estimate" detail="A provisional interpretation, kept separate from observed behavior."/>
        <div className="estimate-state"><div className="estimate-icon"><NavIcon name="mind" size={21}/></div><div><StatusBadge tone="purple">Provisional estimate</StatusBadge><h3>Additional evidence needed</h3></div></div>
        <p className="estimate-description">This demonstration does not represent a real learner assessment. In MCP-RI, a state estimate remains a hypothesis linked to its supporting and contradictory evidence.</p>
        <div className="estimate-divider"/><div className="estimate-facts"><div><span>Evidence source</span><strong>Illustrative interaction record</strong></div><div><span>Confidence scope</span><strong>Support for a category, not cognition</strong></div></div>
        <Link href="/cognitive-state" className="panel-link">Explore how estimates are reviewed <span aria-hidden="true">→</span></Link>
      </section>
    </div>

    <div className="dashboard-grid dashboard-grid--lower">
      <section className="panel activity-panel">
        <SectionHeading eyebrow="Recent activity" title="A traceable history" detail="Example events from the synthetic walkthrough." action={<Link href="/evidence" className="subtle-link">Open evidence <Arrow/></Link>}/>
        <ul className="activity-list">{dashboardDemo.activity.map((activity, index) => <li key={activity.title}><span className={`activity-icon activity-icon--${index}`}><NavIcon name={activity.icon}/></span><div><strong>{activity.title}</strong><span>{activity.detail}</span></div><span className="activity-arrow" aria-hidden="true">›</span></li>)}</ul>
      </section>
      <section className="next-action-card">
        <div className="next-action-top"><span className="action-icon"><NavIcon name="layers" size={19}/></span><StatusBadge tone="amber">Unavailable today</StatusBadge></div>
        <p className="eyebrow">Recommended next action</p><h3>Review what the system can support</h3><p>Representation plans can explain a recommendation, but there is no executable learning-content provider in the current repository.</p>
        <Link href="/representations" className="action-card-link">Explore availability <span aria-hidden="true">→</span></Link>
        <div className="action-card-foot"><span className="status-dot status-dot--amber"/>No learning activity will be launched from this demo.</div>
      </section>
    </div>

    <section className="source-note"><span className="source-note-icon"><NavIcon name="evidence" size={16}/></span><p><strong>Evidence before interpretation.</strong> Behavioral summaries describe recorded response outcomes. They do not directly measure understanding, confusion, or mastery.</p><Link href="/learner-state">About the evidence <Arrow/></Link></section>
  </div>;
}
