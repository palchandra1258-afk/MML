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

Role-aware navigation is a presentation plan only; authentication, authorization, and user/learner identity resolution are out of scope. The F3 prototype permits explicit selection of a pseudonymous research record and labels its ID/source; this is not a signed-in learner identity. Do not present research-only metrics as validated learner ability. Synthetic scenarios must remain visibly labeled.

## Route proposal

| Route | Audience | Purpose |
|---|---|---|
| `/` | Both | Route to the selected experience or research overview in demo mode; later use role-aware routing. |
| `/dashboard` | Learner | Current supported context, progress sourced from the service, recent activity, and next action. |
| `/learning` | Learner | Workspace shell with actual content if a provider exists; otherwise explain availability and offer only supported evidence-request actions. |
| `/learning-path` | Learner | Primary goal and objective steps with active diversion state. |
| `/learning-path/diversions/[id]` | Learner | Reason, preserved context, bounded supporting work, and resumption status. |
| `/research` | Researcher | Research overview with verified artifact coverage and evaluation scope. |
| `/research/learners/[id]` | Researcher | Learner record with tabs for observed state, provisional estimates, and trajectory. |
| `/representations` | Researcher | Learner-scoped saved plans, taxonomy/default registry snapshots, rule trace, alternatives, capability, evidence, and limitations. |
| `/evidence` | Researcher | Learner-scoped evidence records, provenance, embedded group/alignment annotations, missingness, and explicit relationship limits. |
| `/evaluation` | Researcher | Versioned dataset/model reports and metrics with split, denominator, method, source and interpretation. The F6 dashboard is also available from `/research`. |

The backend resource/endpoint mapping is documented in [`F2_API_INTEGRATION.md`](F2_API_INTEGRATION.md), [`F4_REPRESENTATION_INTELLIGENCE.md`](F4_REPRESENTATION_INTELLIGENCE.md), and [`F5_EVIDENCE_EXPLORER.md`](F5_EVIDENCE_EXPLORER.md). Other frontend page paths remain product proposals and are not required to mirror API endpoint paths.

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
