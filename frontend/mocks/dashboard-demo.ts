/** Fictional scenario used only to demonstrate layout and status language. Not a learner record. */
export const dashboardDemo = {
  objective: "Explore how evidence can inform a learning decision",
  objectiveNote: "Illustrative objective · not supplied by EdNet or an active course",
  progress: { completed: 2, total: 5, label: "2 of 5 scenario steps" },
  trajectory: [
    { title: "Starting point", status: "Recorded in demo" },
    { title: "Evidence review", status: "Current demo step" },
    { title: "Representation plan", status: "Not yet shown" },
    { title: "Return to the main goal", status: "Illustrative continuation" },
  ],
  activity: [
    { title: "Reviewed interaction evidence", detail: "Synthetic walkthrough · just now", icon: "evidence" },
    { title: "Estimate marked provisional", detail: "Synthetic walkthrough · earlier", icon: "mind" },
    { title: "Representation delivery unavailable", detail: "System capability status · demo", icon: "layers" },
  ],
} as const;
