# Frontend information architecture

## Navigation hierarchy

```text
Learner
├── Overview
├── Learning
│   ├── Current workspace
│   └── Supporting concept / diversion (only when present)
├── Learning path
│   └── Diversion and resumption detail (contextual)
└── Progress

Research console
├── Overview
├── Learners / learner record
│   ├── Behavioral state
│   ├── Cognitive estimates
│   └── Trajectory history
├── Representation decisions
├── Evidence explorer
└── Research & evaluation
    ├── Model evaluation
    ├── Data quality / modality availability
    └── System status and limitations
```

Role-aware navigation is a presentation plan only; authentication, authorization, and user/learner identity resolution are out of scope. Do not show research-only metrics or raw learner identifiers in the learner experience. In this initial stage, the active persona may be a clearly labeled demonstration scenario.

## Route proposal

| Route | Audience | Purpose |
|---|---|---|
| `/` | Both | Route to the selected experience or research overview in demo mode; later use role-aware routing. |
| `/dashboard` | Learner | Current supported context, progress sourced from the service, recent activity, and next action. |
| `/learning` | Learner | Workspace shell with actual content if a provider exists; otherwise explain availability and offer only supported evidence-request actions. |
| `/learning-path` | Learner | Primary goal and objective steps with active diversion state. |
| `/learning-path/diversions/[id]` | Learner | Reason, preserved context, bounded supporting work, and resumption status. |
| `/research` | Researcher | System/data health and evaluation scope. |
| `/research/learners/[id]` | Researcher | Learner record with tabs for observed state, provisional estimates, and trajectory. |
| `/research/representations/[planId]` | Researcher | Plan, rule trace, alternatives, capability, evidence, and limitations. |
| `/research/evidence` | Researcher | Filterable evidence records, provenance, temporal alignment, gaps, and conflicts. |
| `/research/evaluation` | Researcher | Dataset/model reports and metrics with split, date, denominator, and interpretation. |

Routes are proposed. Backend resource identifiers and URL shapes must be reconciled with Phase 14 OpenAPI before implementation.

## Screen-to-journey map

| Screen | Journey A | B | C | D |
|---|:---:|:---:|:---:|:---:|
| Learner overview | ● | ● | ● | |
| Learning workspace | ● | ● | ● | |
| Behavioral state | | ● | | ● |
| Cognitive estimate detail | | ● | ● | ● |
| Representation decision | | ● | ● | ● |
| Learning path / diversion | | | ● | ● |
| Evidence explorer | | ● | ● | ● |
| Research evaluation | | | | ● (context only) |

## Persistent context model

Every decision detail should retain links back to the record that produced it. Researcher detail uses a shared context header containing learner pseudonym/ID (when permitted), source/run label, event-time window, and record version. A decision chain view connects evidence → behavioral summary → provisional estimate → representation plan → trajectory decision. Missing edges are explicitly displayed as unavailable references, not silently omitted.
