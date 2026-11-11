# Frontend implementation roadmap

F0 is this planning milestone. No F1 implementation starts automatically; the planning set is for review and approval.

| Milestone | Scope and deliverable | Dependencies / exit evidence |
|---|---|---|
| F0 — Product and architecture planning | Vision, IA, personas/journeys, design direction, screen specs, component inventory, integration/mock/limitations plan | This document set reviewed; unresolved questions assigned. |
| F1 — Design system and shell | Typography/tokens, responsive shell, accessible navigation, source/status/empty/loading/error primitives | F0 approval; inspect installed Next 16 docs before implementation; no API needed. |
| F2 — Research overview + learner overview shell | Real-source and synthetic banners, no-data states, current context, path/continuity placeholders grounded in fixtures or API | Decide first demo mode and source inventory; no invented learner objective. |
| F3 — Behavioral + cognitive state | Behavioral observations, intervals, tags; provisional estimate, evidence, uncertainty, conflict, versions | Confirm artifact-read/transport strategy; no cognitive ground truth implied. |
| F4 — Representation intelligence | Plan trace, rejected alternatives, objective grounding, capability states, deferred actions | Use actual plan schema artifacts or OpenAPI; availability remains unavailable unless backend proves otherwise. |
| F5 — Trajectory, diversion, resumption | Parent path, diversion branch, preserved context, progress, resumption/replan history | Dependency registry provenance and trajectory API/history contract; include synthetic path only with label. |
| F6 — Evidence explorer | Paginated records, provenance, temporal semantics, alignment/conflicts/missingness | Evidence API and bounded query design. |
| F7 — Research evaluation | Model comparison, evaluation runs, data quality/modality availability | Authoritative report/catalog API or explicitly versioned static artifact ingestion. |
| F8 — Backend integration | Typed API client, generated/derived transport types, errors, pagination, cache/invalidation | Phase 14 OpenAPI and persistence behavior stabilized. This may move earlier for read-only screens if contract exists. |
| F9 — End-to-end quality | Learner/research journeys, keyboard/accessibility, responsive, API data consistency and failure cases | Working API/content dependencies. Testing plan and tools selected before execution. |

## Sequencing rationale

Build shell and reusable status/source semantics before analytical displays. Establish a trustworthy research overview and learner empty/availability states before visually implying a full adaptive tutor. State and representation detail precede trajectory continuity because later decisions link to their versioned records. Evidence browsing follows shared reference patterns. API integration can begin earlier as soon as OpenAPI stabilizes; it need not wait for all screens. End-to-end validation requires real backend and activity delivery contracts.
