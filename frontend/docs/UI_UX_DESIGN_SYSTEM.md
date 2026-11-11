# UI/UX design system direction

## Identity

Use a quiet research-lab visual language: warm off-white canvas, deep ink/navy text, restrained teal for active learning flow, and muted amber for uncertainty/deferred states. Red is reserved for actual errors or destructive states, never low performance. Avoid “AI glow,” decoration-only charts, excessive gradients, and celebratory mastery language.

## Layout and type

Desktop shell: collapsible left rail (primary navigation), compact top bar (page title, source/run context, profile/experience switch only if supported), main content with a readable max width, and optional right context rail for evidence and definitions. On narrow screens, navigation becomes an accessible menu; context rail becomes an in-flow section. Use a clear type scale with body text 16px equivalent, comfortable line height, tabular numerals for values, and monospace only for technical IDs/code.

## Color and status semantics

- Neutral/blue: source information and navigation.
- Teal: active trajectory and completed recorded steps; “completed” means recorded workflow completion, not mastery.
- Amber: provisional, uncertain, sparse, deferred, or awaiting evidence.
- Purple: model/rule-derived interpretation, with explicit “estimate” label.
- Red: service failure or data integrity issue only.

Color is never the sole carrier: pair with a label and icon/text. A “capability unavailable” state must differ from “loading,” “no data,” and “error.”

## Components and content patterns

- **Provenance chip:** source type, run/source, and synthetic/real-data label.
- **Evidence summary:** observed count/window, coverage/missingness and click-through.
- **Estimate panel:** “provisional” heading, estimate, support level, separate uncertainty dimensions, rationale, evidence and contradictions.
- **Decision panel:** action status (executable/deferred/requires evidence), why, alternatives, and content/capability grounding.
- **Continuity card:** parent goal, interrupted step, diversion reason, snapshot/version, current state, and next recorded outcome.
- **Metric definition:** value plus denominator, window, source, tooltip/details, and non-cognitive interpretation.
- **Empty/loading/error states:** retain page purpose and explain what data is missing or what can be retried.

## Visualization choices

| Data | Recommended view | Guardrail |
|---|---|---|
| Objective/path steps and diversion relationship | Vertical path/timeline with parent-child branch and preserved-step marker | Show actual supplied steps only. Do not fabricate curriculum nodes. |
| Behavioral outcome over ordered observations | Small line/dot series only when per-event data and time ordering are available; otherwise labeled summary + interval | Do not treat accuracy trend as cognitive change. Include sample count/window; avoid smoothing away missing rows. |
| Per-skill performance | Sortable table with interval bars/dots | Better than radar chart for sparse, heterogeneous skill counts. Keep skill IDs as dataset tags unless names validated. |
| Uncertainty | Interval/range plot plus separate categorical dimensions | Wilson interval applies to response correctness, not cognitive estimates. Never show it as a cognitive confidence band. |
| Evidence | Chronological list/timeline with modality, provenance, alignment quality and missingness | EdNet shifted timestamps must not be shown as absolute calendar event time without qualification. |
| Representation rule outcome | Decision flow/trace with passed, failed, unavailable checks and alternatives | Rule execution is not evidence of educational effectiveness. |
| Model evaluation | Metric table and paired plots/curves linked to report metadata | Show split, sample, model, date, target and metric definition. Not learner-facing. |

## Interaction and accessibility

Use semantic landmarks/headings, keyboard-operable menus/tables, visible focus ring, skip link, sufficient contrast, reduced-motion support, accessible names, and non-color status language. Charts need text summaries or data tables. Tables reflow or scroll with clear headers on mobile; do not truncate critical provenance. Use progressive disclosure for technical details, while keeping limitations visible adjacent to claims.

## Responsive behavior

Prioritize wide desktop research layout, then laptop and tablet. At mobile widths: single column, collapsible navigation, no side-by-side evidence/decision panels, horizontally scrollable data tables with accessible labels, and concise chart summaries. Preserve the diversion-parent relationship in a vertical path layout rather than hiding it.
