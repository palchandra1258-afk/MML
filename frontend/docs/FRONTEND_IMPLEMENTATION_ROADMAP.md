# Frontend implementation roadmap

F0–F7 are implemented. F8 and later milestones remain planned.

| Milestone | Scope and deliverable | Dependencies / exit evidence |
|---|---|---|
| F0 — Product and architecture planning | Vision, IA, personas/journeys, design direction, screen specs, component inventory, integration/mock/limitations plan | This document set reviewed; unresolved questions assigned. |
| F1 — Design system and shell | Typography/tokens, responsive shell, accessible navigation, source/status/empty/loading/error primitives | Complete. |
| F2 — API integration foundation | OpenAPI-derived client/services, environment config, health connectivity indicator, explicit demo mode, actual API overview, isolated tests | Complete for health and learner-index summary. Detailed per-learner screens remain future work. |
| F3 — Learner dashboard and learning workspace | Learner index/record selection, overview, observed progress and concept explorer, provisional cognitive insights, read-only trajectory/history/diversion context, workspace availability | Complete. Uses existing F2 services, displays source/uncertainty, and does not deliver learning activity. |
| F4 — Representation intelligence | Taxonomy and default registry snapshots, learner-scoped paginated plan explorer, traceable details, capability states, filtering and two-plan comparison | Complete. The taxonomy and registry have no API endpoint; source snapshots are labeled. Plan execution, historical cognitive snapshots, and validation outcomes remain unavailable through the current API. |
| F5 — Multimodal evidence explorer | Paginated learner-scoped records, provenance, embedded groups/alignment, missingness, and evidence-context limits | Complete. No conflict record or downstream reverse-lookup endpoint; filters remain page-scoped where the API has no server filter. |
| F6 — Research and model evaluation | Research artifact audit, model comparison, prediction metrics, calibration, Phase 9–13 validation and provenance | Complete. Uses a committed aggregate snapshot of allowlisted reports because the API has no report catalog route; no learner-level exports are loaded. |
| F7 — End-to-end integration and final quality review | Integrate routes and learner journey, show saved trajectory/history/diversion context, resolve active diversion references, validate pagination, handle 404 accurately, review accessibility/responsive behavior, and document system limits | Complete. Lint, 64 Node API/integration tests, TypeScript, build, and diff check pass. Headless Firefox route, responsive, disconnected-state, and mobile-navigation checks pass; live API learner data was unavailable. No real diversion/resumption occurred. See [`F7_END_TO_END_INTEGRATION.md`](F7_END_TO_END_INTEGRATION.md). |
| F8 — Backend integration expansion | Connect detailed routes, pagination controls, mutations, and record views | Phase 14 contract exists; do not implement operations absent from OpenAPI. |
| F9 — End-to-end quality | Learner/research journeys, keyboard/accessibility, responsive, API data consistency and failure cases | Working API/content dependencies. Testing plan and tools selected before execution. |

## Sequencing rationale

F1 established shell and source/status semantics; F2 connected API health and the learner index; F3 added the learner experience over existing read services; F4 added read-only representation decision explainability; F5 added evidence provenance and relationship inspection; F6 made research reports inspectable from a versioned static snapshot; F7 integrated the application navigation and failure handling and documented the actual trajectory boundaries. Trajectory branch mutations remain a backend dependency. Content, interaction submission, and diversion/resumption writes remain unavailable. Browser journey testing and any complete learning activity require the relevant tools and service contracts.
