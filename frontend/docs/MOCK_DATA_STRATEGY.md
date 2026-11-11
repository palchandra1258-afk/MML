# Mock-data strategy

## Why mocks are needed

The current repository has substantial real EdNet-derived behavioral and research artifacts but no backend API in this frontend and no actual learner-generated multimodal text/audio/visual evidence, content-serving feature, validated cognitive labels, or validated dependency graph. Synthetic scenarios can demonstrate layout and future flows only; they cannot demonstrate research findings.

## Source classes

- **Actual EdNet-derived:** Phase 9 response history summaries and Phase 10 interaction evidence from the described validation sample. Keep dataset/run/split and shifted timestamp semantics attached. Not raw content, learner objective, cognition, or a production live profile.
- **Research implementation artifact:** Phase 11 provisional rule outputs, Phase 12 plans, and Phase 13 bounded orchestration records. Their run scope, synthetic-vs-real fixture use, limitations and availability must travel with the data.
- **Synthetic demonstration:** fabricated learner/session/content/evidence used only to show future interaction, especially nonzero diversion/resumption and text/audio/visual combinations. Mark every record `SYNTHETIC DEMONSTRATION` in storage metadata and visible UI.
- **Unavailable:** API, executable content, delivery providers, validated objectives/dependencies, multimodal real observations, cognitive ground truth. Render unavailable states, not mock success.

## Isolation rules

1. Put fixtures in a dedicated `mocks/` module, separated by scenario and with a manifest describing why synthetic and which fields are invented.
2. Require an explicit demo-mode selection; default mode is API or honest not-configured state, never silent mock fallback.
3. Carry `source_kind`, `run_id`/scenario ID, and `synthetic` marker in view models. In learner demo screens, persistent banner; in researcher tables, a source column and filter.
4. Do not merge real EdNet outcomes with synthetic multimodal observations in a single learner history. If a conceptual storyboard juxtaposes them, visually separate panels and state the example is illustrative.
5. Never treat an EdNet skill tag as a validated concept name or objective. Use pseudonymous/sample identifiers and avoid using real learner IDs in screenshots.
6. Do not choose synthetic defaults that make a rule appear validated or all outcomes positive. Include sparse, contradictory, missing and deferred cases.
7. Synthetic records are not exported as research data and are excluded from evaluation calculations by construction.

## Demo scenario set

After contracts and screens are approved, a small fixture set can illustrate: (a) sparse correctness evidence → request more evidence; (b) contradictory evidence → preserve conflict and defer; (c) repeated errors but no explicit dependency → continue/request evidence; (d) explicitly marked synthetic dependency → diagnostic diversion with exact context preservation and resumption; (e) representation delivery unavailable → defer. Each scenario should explain which records are synthetic and which rule outcome it illustrates.
