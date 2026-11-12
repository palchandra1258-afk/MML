import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { routeContent } from "@/components/navigation/navigation-data";
import { NavIcon } from "@/components/navigation/nav-icon";
import { SectionHeading } from "@/components/shared/section-heading";
import { StatusBadge } from "@/components/shared/status-badge";
import { LearnerSectionClient } from "@/components/learner/learner-section-client";
import type { LearnerSection } from "@/components/learner/learner-section-types";
import { RepresentationIntelligencePage } from "@/components/representation/representation-intelligence-page";
import { EvidenceExplorerPage } from "@/components/evidence/evidence-explorer-page";
import { ResearchEvaluationPage } from "@/components/research/research-evaluation-page";
import { SystemStatusPage } from "@/components/system/system-status-page";

export function generateStaticParams() {
  return Object.keys(routeContent).map((section) => ({ section }));
}

export async function generateMetadata({ params }: PageProps<"/[section]">): Promise<Metadata> {
  const { section } = await params;
  const content = routeContent[section];
  return { title: content?.title ?? "Page not found" };
}

const routeLinks: Record<string, { href: string; label: string; icon: string }[]> = {
  learning: [{ href: "/trajectory", label: "Review learning trajectory", icon: "trajectory" }, { href: "/progress", label: "View learning progress", icon: "progress" }],
  progress: [{ href: "/trajectory", label: "Explore trajectory records", icon: "trajectory" }, { href: "/learner-state", label: "Explore observed behavior", icon: "state" }],
  trajectory: [{ href: "/representations", label: "Representation decisions", icon: "layers" }, { href: "/evidence", label: "Evidence explorer", icon: "evidence" }],
  "learner-state": [{ href: "/evidence", label: "Inspect evidence sources", icon: "evidence" }, { href: "/cognitive-state", label: "View provisional estimates", icon: "mind" }],
  "cognitive-state": [{ href: "/learner-state", label: "Observed learner state", icon: "state" }, { href: "/representations", label: "Representation plans", icon: "layers" }],
  representations: [{ href: "/cognitive-state", label: "View estimate inputs", icon: "mind" }, { href: "/trajectory", label: "Review trajectory context", icon: "trajectory" }],
  evidence: [{ href: "/learner-state", label: "Behavioral summaries", icon: "state" }, { href: "/cognitive-state", label: "Provisional estimates", icon: "mind" }],
  research: [{ href: "/evaluation", label: "Model evaluation", icon: "chart" }, { href: "/system-status", label: "System availability", icon: "system" }],
  evaluation: [{ href: "/research", label: "Research overview", icon: "research" }, { href: "/system-status", label: "System status", icon: "system" }],
  "system-status": [{ href: "/representations", label: "Representation availability", icon: "layers" }, { href: "/research", label: "Research dashboard", icon: "research" }],
};

export default async function SectionPage({ params }: PageProps<"/[section]">) {
  const { section } = await params;
  const content = routeContent[section];
  if (!content) notFound();
  if (section === "representations") return <RepresentationIntelligencePage/>;
  if (section === "evidence") return <EvidenceExplorerPage/>;
  if (section === "evaluation" || section === "research") return <ResearchEvaluationPage/>;
  if (section === "system-status") return <SystemStatusPage/>;
  const learnerSections: LearnerSection[] = ["learning", "progress", "learner-state", "cognitive-state", "trajectory"];
  if (learnerSections.includes(section as LearnerSection)) {
    return <LearnerSectionClient section={section as LearnerSection}/>;
  }
  const links = routeLinks[section] ?? [];

  return <div className="placeholder-page">
    <div className="placeholder-breadcrumb"><span>{content.eyebrow}</span><span>·</span><span>{content.title}</span></div>
    <section className="placeholder-hero panel">
      <div className="placeholder-icon"><NavIcon name={section === "learning" ? "book" : section === "evidence" ? "evidence" : section === "research" ? "research" : "layers"} size={23}/></div>
      <StatusBadge tone="amber">Planned view</StatusBadge>
      <h2>{content.title}</h2><p>{content.description}</p>
      <div className="availability-message"><span className="availability-symbol">i</span><p><strong>This page is a planned view and is not yet wired to its API service.</strong> The API connection status is shown in the top bar. No learning activity is launched here.</p></div>
    </section>
    <section className="placeholder-scope">
      <SectionHeading eyebrow="What this area will support" title="Designed for evidence and context" detail="The next implementation stage will define this view against real content and service contracts."/>
      <div className="placeholder-link-grid">{links.map((item) => <Link className="placeholder-link panel" href={item.href} key={item.href}><span className="placeholder-link-icon"><NavIcon name={item.icon}/></span><span>{item.label}</span><span className="placeholder-link-arrow">→</span></Link>)}</div>
    </section>
    <div className="prototype-note"><span className="status-dot status-dot--amber"/><span>Planned view · no record details loaded</span><Link href="/">Return to overview</Link></div>
  </div>;
}
