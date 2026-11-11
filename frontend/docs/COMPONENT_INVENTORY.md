# Component inventory

Components are candidate responsibilities, not a request to create every component or directory at once. Implement after F0 approval, beginning with shared semantics and only the first milestone's screens.

| Component | Responsibility | Key data / behavior |
|---|---|---|
| `AppShell` | Shared responsive frame and landmarks | audience-specific navigation supplied by route context; no auth enforcement |
| `PrimaryNavigation` | Keyboard-accessible grouped links | active route, collapsed/mobile state |
| `PageHeader` | Title, concise context, source/run chip | no decorative status metrics |
| `SourceBadge` | Mark EdNet, synthetic fixture, API record, or unavailable | source must come from metadata, not component guess |
| `LoadState` | Consistent loading/empty/error patterns | accessible status announcements and retry callback |
| `ProvenanceSummary` | Source, timestamp semantics, processing | evidence record fields; expandable technical detail |
| `EvidenceList` / `EvidenceRecordDetail` | Browse source events and links | pagination/filter contract pending |
| `MissingnessNotice` | Explain absent modality/field/data | missingness distinct from negative evidence |
| `ConflictPanel` | Show unresolved conflict and sources | no automatic source winner |
| `EstimateSummary` | Learner-safe provisional summary | language map, rationale, evidence sufficiency; hide schema jargon for learner |
| `UncertaintyBreakdown` | Show dimensions and reasons | do not imply calibrated cognitive probability |
| `BehaviorMetric` | Value with definition, sample/window/source | observed response correctness only |
| `PerformanceInterval` | Show outcome estimate range | Wilson interval, correct scope label |
| `SkillPerformanceTable` | Compare tagged item history | tag remains dataset metadata; sort and responsive behavior |
| `DecisionTrace` | Explain evaluated rules/checks | rule IDs/statuses and linked evidence for research role |
| `RepresentationAvailability` | Show category status and reason | planned vs unavailable vs available provider |
| `AlternativeList` | Show rejected options/reasons | do not style rejected as learner failure |
| `TrajectoryPath` | Show ordered objectives/steps/branch | only supplied records; accessible linear alternative |
| `ContinuityCard` | Keep parent goal and interrupted step visible | context snapshot and parent version |
| `DiversionStatus` | Describe bounded supporting activity | diagnostic review wording; available actions from backend |
| `VersionHistory` | Browse immutable estimates/plans/trajectory versions | version ID, timestamps, parent links |
| `EvaluationMetricTable` | Research metrics and metadata | split/target/denominator/date/definition |
| `ChartWithTable` | Accessible chart plus equivalent data | chosen only for supported data shape |

## Formatting and mapping helpers

Keep domain wording in small tested mappings at the view-model boundary, not scattered conditionals. Unknown enum values must render as “Unrecognized status (see record)” in research views and a safe generic status in learner views. Format null explicitly (“not available” / “not observed”), not as zero. Keep shifted EdNet timestamp caveat adjacent wherever the date is presented.
