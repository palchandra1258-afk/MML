# F7 — End-to-end integration and final quality review

## Scope and integration architecture

F7 completes the frontend integration pass over F1–F6. The Next.js App Router provides the route shell; `AppShell` owns one shared API health provider and the selected pseudonymous learner context. Existing learner, evidence, representation, trajectory, and health services continue to use the OpenAPI-derived API client. The `/system-status` route now renders the same health result already used by the shell rather than showing a planned-view placeholder or issuing a duplicate request.

List services validate the common pagination envelope before UI components consume it. Malformed page metadata becomes a typed protocol error. A successful empty page remains an empty result; a 404 is presented as a not-found API resource with retry rather than as a zero-row dataset. Network, timeout, HTTP 5xx, invalid JSON, invalid envelopes, and aborted requests remain distinct API errors. API failures never switch the application to mock data.

## Route and navigation audit

| Route | Frontend screen | Data source / scope |
|---|---|---|
| `/` | Learner overview and record picker | Learner index and selected learner artifacts from the API; separate explicit mock overview |
| `/learning` | Learning workspace | Selected learner saved plan and trajectory context; activity delivery unavailable |
| `/progress` | Learning progress | Selected learner behavioral state and concept evidence |
| `/learner-state` | Behavioral state explorer | Same persisted Phase 9 snapshot, framed as observed behavior |
| `/cognitive-state` | Cognitive insights | Latest saved Phase 11 estimate and uncertainty |
| `/evidence` | Evidence explorer | Learner-scoped Phase 10 records and embedded annotations |
| `/representations` | Representation intelligence | Learner-scoped saved plans plus labeled repository taxonomy/capability snapshots |
| `/trajectory` | Trajectory, history, and diversion records | Persisted trajectory, event history, and diversion reads |
| `/research` | Research dashboard | F6 aggregate artifact snapshot |
| `/evaluation` | Model evaluation | Same F6 research/evaluation screen; both routes remain supported intentionally |
| `/system-status` | API and module readiness | Shared health response; retry uses the shared health provider |

There is no separate `/learners` route: learner selection and pseudonymous lookup live on Overview and in shared learner-scoped screens. All visible navigation targets map to a screen; the former system-status planned placeholder is now connected to live health state. Unknown dynamic section paths continue to use Next.js `notFound()`.

## Learner journey and evidence-to-trajectory navigation

Overview links to behavioral state, cognitive insights, evidence, representation context, and trajectory details. In the trajectory detail, actual saved evidence, cognitive-state, and representation-plan IDs remain visible. When a reference exists, a link opens the corresponding learner-scoped explorer, while the global learner selection stays in the shared app context. Additional links make the behavioral view and saved learning workspace easy to reach.

The links are navigation between views, not proof of an artifact relationship. Evidence and trajectory APIs do not provide a general reverse lookup or a complete chain across every phase. The evidence explorer does not deep-select a trajectory reference ID; the cognitive screen exposes the latest estimate rather than arbitrary historical state IDs. The UI therefore retains source IDs and explicitly says learner-level similarity does not establish causality or chronology.

No complete live pipeline is represented. The API does not expose lesson delivery, learner response submission, intervention receipts, or outcome-linked state updates. The F7 trajectory page states these gaps beside the saved path context.

## Trajectory and history experience

`components/learner/trajectory-page.tsx` reads persisted trajectory records and their append-only event histories. It shows goal, status, version, current recorded step, completed and pending step records, expected progression, timestamps, and saved context references. History is loaded from the latest indexed event page and displayed newest returned first; the source and page scope remain visible.

Diversion snapshots show their saved reason, parent/context IDs, previous step, saved resumption condition, resolution, evidence-reference count, progress evaluations, and revision count. If a selected trajectory has an `active_diversion_id` outside the displayed diversion page, the frontend calls the existing learner-scoped diversion detail GET route for that exact saved ID. The detail is marked as referenced by that trajectory. Missing detail remains an API not-found/error state.

The screen does not issue trajectory writes. Although OpenAPI supports trajectory creation and `activate`, `pause`, and `advance_step` actions, the UI does not call them. There is no diversion mutation or resumption endpoint, no context-snapshot retrieval endpoint, and no lesson or outcome route. A saved `resume_condition` is review context; it is not a resumption assessment or successful transition. No success notification or hypothetical real event is generated.

## Diversion, resumption, and synthetic boundaries

F6 reports 100 bounded trajectories and zero diversions because the real dependency registry was empty and each decision requested more evidence. This is not evidence that real prerequisite edges or learner resumption were validated. Phase 14 exposes read routes for persisted diversion records but no HTTP mutation for diversion creation/closure/resumption.

Mock mode remains opt-in (`NEXT_PUBLIC_USE_MOCK_DATA=true`) and carries a visible synthetic banner. Its fictional overview is isolated from API learner data; learner subpages do not create evidence, cognitive estimates, trajectory events, or diversion/resumption records. F7 does not add a synthetic diversion lifecycle. Researchers can inspect the isolated mock overview, but a lifecycle demonstration still requires a separately authored synthetic scenario if needed for a presentation.

## API failure and partial-data handling

- Network and timeout errors report disconnected health; HTTP/protocol errors report failure and retain a request ID when supplied.
- HTTP 404 is no longer translated into an empty result. Empty collections require a successful API page with zero items.
- API page metadata must contain object items, a positive integer limit, nonnegative integer offset and total, a boolean `has_more` consistent with `offset + items.length < total`, and no item count beyond the limit. Invalid pagination stops before it reaches list components.
- `available_data` omissions keep a resource idle and show the existing “not available” state; they are not shown as numeric zero.
- The existing `useApiResource` aborts stale requests and retries only on user action. The health provider performs one shared request, with explicit retry and no polling.
- Successful envelopes are validated at the transport layer; nested artifact records remain generically typed JSON and are not fully runtime-schema-validated. Unexpected missing fields inside an otherwise valid record remain a limitation.

## Responsive and accessibility review

Source review covered the existing 1100px, 850px, 680px, and 390px layout breakpoints. The trajectory context grid collapses from three columns to two and then one; related links become a two-column mobile grid. System-status facts collapse to two columns, while its module table uses a horizontally scrollable wrapper. Existing evidence/research tables and filters retain their prior responsive layouts.

The shell has a skip link, semantic navigation and main landmarks, active-route semantics, visible focus styling, reduced-motion CSS, and labels for the learner and evidence controls. F7 adds `aria-controls` and the expanded state to the mobile navigation toggle, closes on Escape, and returns focus to the toggle. New tables have captions and header scopes; the status table region is keyboard focusable for horizontal scrolling. Headless Firefox confirmed these mobile navigation interactions. A screen-reader, accessibility-tree, and automated contrast audit was not available. Dense F1–F6 research metadata still uses small type in places and needs further visual zoom/contrast review.

## Performance and code-quality review

The shared status page consumes the existing health context and adds no request. Trajectory detail lookup is issued only when an active diversion reference is absent from the returned diversion page. Existing resource hooks abort stale reads and avoid polling; page data loads through existing services. F7 adds no runtime dependency, image asset, chart library, or new API operation. New TypeScript code uses explicit types and no `any`. ESLint and TypeScript checks pass. The larger evidence and representation screens remain unchanged; no broad client-component refactor was justified in this quality pass.

### Dependency audit

`npm audit` reports seven moderate vulnerabilities, all transitive (`isDirect: false`) development dependencies in the `eslint-config-next` → `typescript-eslint` → `@typescript-eslint/typescript-estree` chain. The affected nested package is `minimatch@10.2.6`; npm's advisory identifies the vulnerable range through 11.0.0 and reports a fix available. The application runtime dependency tree does not contain this nested lint-tool chain. No audit fix, dependency override, or package upgrade was applied during F7.

Recommended remediation is to update the Next ESLint and TypeScript-ESLint toolchain as a compatible set, or evaluate a narrowly scoped minimatch override only after confirming the supported range. Then rerun audit, lint, tests, TypeScript, and build. Avoid forcing a major transitive upgrade without compatibility checks.

## Tests and validation

The Node test suite now includes checks for API 404 handling, invalid envelopes, pagination validation, route coverage, active diversion lookup, read-only trajectory behavior, synthetic-data isolation, shared health reuse, and keyboard-operable mobile navigation. These complement the existing API client, learner, evidence, representation, and research helper tests.

Headless Firefox 156 with geckodriver loaded all 11 visible routes with the expected active navigation item and no Next.js error overlay. At 390×844, 768×1024, and 1365×900, trajectory, research, and system-status screens had no horizontal document overflow. Screenshots were visually reviewed at all three widths for trajectory and system status, plus mobile evidence, representation, and research views. The mobile menu opened, closed on Escape with focus returned to its toggle, and closed after route navigation. Because the backend was not running and `NEXT_PUBLIC_API_BASE_URL` was not set, this browser pass covered shell, route, and disconnected-state behavior; it did not exercise a live learner record, evidence filtering, plan comparison, or persisted diversion history.

Validation from `frontend/`:

- `npm run lint` — passed.
- `npm run test:api` — passed, 64 tests, 0 failures.
- `npx tsc --noEmit` — passed.
- `npm run build` — passed; Next.js generated the root and dynamic section routes.
- `git diff --check` — passed.
- `npm audit` — reports seven moderate transitive development-tool vulnerabilities; no fix was applied.
- Browser-level validation — passed for route loading, active navigation, disconnected health state, responsive overflow checks, and mobile navigation interactions in headless Firefox; live API data journeys remain unverified.

## Remaining limitations

- No real diversion was observed in the bounded F6 evaluation, and no HTTP diversion or resumption write is available.
- No content provider, learner response submission, intervention receipt, or measured outcome/state-update chain exists.
- The API does not provide a general cross-artifact reverse lookup, historical cognitive-state detail, or context-snapshot retrieval.
- The mock walkthrough is intentionally limited to a fictional overview; it does not demonstrate diversion/resumption.
- Nested API records are not fully runtime schema-validated.
- Browser checks did not cover connected API data journeys; no backend was running in this environment. Screen-reader and automated contrast checks remain outstanding.
- Research snapshots remain static, aggregate, and governed by the F6 cohort and provenance limitations.
