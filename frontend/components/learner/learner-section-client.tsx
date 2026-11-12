"use client";

import Link from "next/link";
import { getApiConfig } from "@/lib/api/config";
import { useApiHealth } from "@/hooks/use-api-health";
import { CognitiveInsightsPage } from "@/components/learner/cognitive-insights-page";
import { LearningWorkspacePage } from "@/components/learner/learning-workspace-page";
import { LearnerOverviewDashboard } from "@/components/learner/learner-overview-dashboard";
import { ProgressExplorerPage } from "@/components/learner/progress-explorer-page";
import { TrajectoryPage } from "@/components/learner/trajectory-page";
import { DemoLearnerSection } from "@/components/learner/demo-learner-section";
import { EmptyState, LoadingState } from "@/components/shared/data-states";
import type { LearnerSection } from "@/components/learner/learner-section-types";

function RealLearnerSection({ section }: { section: LearnerSection }) {
  const { state } = useApiHealth();
  if (state === "connecting") return <LoadingState label="Connecting to the learner data service"/>;
  if (state === "disconnected" || state === "error") {
    return <EmptyState title="Learner records are unavailable">The backend connection is {state}. Use the retry control in the top bar after the API is available. No synthetic records replace live data.</EmptyState>;
  }

  if (section === "learning") return <LearningWorkspacePage/>;
  if (section === "progress" || section === "learner-state") return <ProgressExplorerPage variant={section}/>;
  if (section === "cognitive-state") return <CognitiveInsightsPage/>;
  if (section === "trajectory") return <TrajectoryPage/>;
  return <EmptyState title="This learner view is unavailable">Return to the <Link href="/">overview</Link> to choose a research record.</EmptyState>;
}

export function LearnerSectionClient({ section }: { section: LearnerSection }) {
  const config = getApiConfig();
  if (config.mode === "mock") return <DemoLearnerSection section={section}/>;
  return <RealLearnerSection section={section}/>;
}

export function LearnerOverviewClient() {
  const config = getApiConfig();
  if (config.mode === "mock") return <DemoLearnerSection section="overview"/>;
  return <RealLearnerSectionOverview/>;
}

function RealLearnerSectionOverview() {
  const { state } = useApiHealth();
  if (state === "connecting") return <LoadingState label="Connecting to the learner data service"/>;
  if (state === "disconnected" || state === "error") {
    return <EmptyState title="Learner records are unavailable">The backend connection is {state}. Use the retry control in the top bar after the API is available. No synthetic records replace live data.</EmptyState>;
  }
  return <LearnerOverviewDashboard/>;
}
