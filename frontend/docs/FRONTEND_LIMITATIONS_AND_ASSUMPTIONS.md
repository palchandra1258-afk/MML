# Frontend limitations and assumptions

## Verified repository facts

- Frontend starter is Next.js 16.4.6 App Router, React 19.3.0, TypeScript 5 and Tailwind CSS 4.3.3; no additional UI/data/chart packages are installed.
- Phase 9 summarizes EdNet submitted-answer correctness and item skill tags. Beta(1,1) smoothing, Wilson intervals, recent windows and evidence tiers describe response behavior, not understanding. Per-event next-response prediction is null in the recorded run.
- Phase 10 supports provenance-aware evidence structures/adapters. Only EdNet interaction evidence is validated against learner data; text/audio/visual use synthetic fixtures. No ASR/OCR or learned multimodal fusion is implemented; conflicts remain unresolved rather than cognitively interpreted.
- Phase 11 emits provisional behavioral categories/hypotheses and diagnostic-information recommendations. There is no cognitive-state ground truth.
- Phase 12 emits auditable recommendation plans and alternatives. All eight delivery categories are unavailable by default; plan output does not generate or deliver content.
- Phase 13 implements deterministic trajectory/diversion/context/resumption/history logic and reports. Default dependency registry is empty; EdNet tags do not encode prerequisites. History is process-local/in-memory in the implementation; bounded sample produced zero diversions. Its thresholds are operational, not mastery criteria.
- The separate Phase 14 backend/API/OpenAPI is not present in this frontend contract; integration details remain pending.

## UI assumptions

- The first usable interface may be a research/demo interface, with a simple learner experience modeled for later content integration.
- Two audiences are needed, but role-aware routes are not authorization. Authentication is out of scope.
- Synthetic demonstration flows are useful only when persistently and record-level labeled.
- Backend identity, pagination, auth, persistence, timestamps and endpoint contracts must be determined from OpenAPI rather than inferred from Python schemas.

## Claims the interface must not make

Do not claim that correctness equals mastery, that a hypothesis is diagnosis/confusion, that a dataset tag is a validated concept, that a recommendation was delivered, that an available provider caused exposure, that an operational return rule proves mastery, that a trajectory wrapper is an actual assigned course, or that model performance establishes cognitive accuracy/learning improvement. Do not describe shifted EdNet timestamps as real-world response times.

## Risks and dependencies

1. **API schema drift:** plans refer to internal artifact schemas, not HTTP contracts. Mitigation: wait for OpenAPI, version types, add mapping boundary.
2. **Synthetic/real confusion:** demo scenes combine intended modalities unavailable in real data. Mitigation: provenance badges and isolated data sources.
3. **Overclaiming uncertainty:** Wilson intervals or ordinal support tiers can be misread as cognitive probability. Mitigation: label scope next to each graphic and show definitions.
4. **False curriculum structure:** no validated prerequisite graph or learner goal exists in EdNet. Mitigation: only render supplied objectives/edges; disclose provenance.
5. **Non-executable suggestions:** no content providers exist. Mitigation: distinguish deferred from executable and never offer fake lesson controls.
6. **Persistence gap:** Phase 13 history is in-memory; Phase 14 must define durable transactional storage before production continuity is promised.
7. **Privacy/access:** real learner-level data needs backend authorization, retention and privacy decisions before deployment. No browser-only role switch can secure it.
8. **Accessibility of dense research views:** detail and charts risk overload. Mitigation: progressive disclosure, table alternatives, keyboard and responsive checks.

## Unresolved questions for review / Phase 14

- Which first release is intended: static research artifact explorer, synthetic UX prototype, or API-backed learner/researcher surface?
- What are Phase 14's canonical resource IDs, routes, pagination, error envelope, auth/access policies and freshness guarantees?
- Will Phase 14 expose report artifacts and versioned historical trajectory reconstruction, or only current state?
- What content/activity provider, if any, can make a representation executable and confirm actual exposure?
- What source and human review process could supply verified learning objectives and dependency relationships?
- How should actual EdNet-derived research samples be accessed, retained and shown while protecting pseudonymous learner records?
- Does a learner-facing entry point belong in the first implementation, given there is currently no executable content capability?
