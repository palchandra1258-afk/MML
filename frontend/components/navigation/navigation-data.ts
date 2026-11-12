export type NavItem = { label: string; href: string; icon: string };
export type NavGroup = { label: string; items: NavItem[] };

export const navigation: NavGroup[] = [
  {
    label: "Research learner records",
    items: [
      { label: "Overview", href: "/", icon: "overview" },
      { label: "My learning", href: "/learning", icon: "book" },
      { label: "Learning progress", href: "/progress", icon: "progress" },
      { label: "Learning trajectory", href: "/trajectory", icon: "trajectory" },
    ],
  },
  {
    label: "Cognitive intelligence",
    items: [
      { label: "Learner state", href: "/learner-state", icon: "state" },
      { label: "Cognitive state", href: "/cognitive-state", icon: "mind" },
      { label: "Representation intelligence", href: "/representations", icon: "layers" },
      { label: "Evidence explorer", href: "/evidence", icon: "evidence" },
    ],
  },
  {
    label: "Research",
    items: [
      { label: "Research dashboard", href: "/research", icon: "research" },
      { label: "Model evaluation", href: "/evaluation", icon: "chart" },
      { label: "System status", href: "/system-status", icon: "system" },
    ],
  },
];

export const studentNavigation: NavGroup[] = [
  {
    label: "Student learning studio",
    items: [
      { label: "Home", href: "/studio", icon: "overview" },
      { label: "Explore subjects", href: "/studio/explore", icon: "evidence" },
      { label: "My progress", href: "/studio/progress", icon: "progress" },
      { label: "Learning history", href: "/studio/history", icon: "trajectory" },
    ],
  },
];

export const routeContent: Record<string, { title: string; eyebrow: string; description: string }> = {
  learning: { title: "My learning", eyebrow: "Learning studio", description: "A focused space for supported learning activities and the context around them." },
  progress: { title: "Learning progress", eyebrow: "Learning studio", description: "Review recorded progress with its source and time window." },
  trajectory: { title: "Learning trajectory", eyebrow: "Learning studio", description: "Follow the current goal, learning steps, and any context-preserving diversions." },
  "learner-state": { title: "Learner state", eyebrow: "Cognitive intelligence", description: "Explore observed response history and its limits." },
  "cognitive-state": { title: "Cognitive state", eyebrow: "Cognitive intelligence", description: "Inspect provisional estimates, their evidence, and uncertainty." },
  representations: { title: "Representation intelligence", eyebrow: "Cognitive intelligence", description: "See how evidence informs representation plans and why actions may be deferred." },
  evidence: { title: "Evidence explorer", eyebrow: "Cognitive intelligence", description: "Trace observations to their source, processing status, and temporal context." },
  research: { title: "Research dashboard", eyebrow: "Research console", description: "Review the research artifacts and the boundaries of what they establish." },
  evaluation: { title: "Model evaluation", eyebrow: "Research console", description: "Inspect model results in the context of their target, split, and evaluation scope." },
  "system-status": { title: "System status", eyebrow: "Research console", description: "Review the shared API health check and backend module availability." },
};
