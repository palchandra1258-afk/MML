# RepresentationPlan Schema v1

`schemas/representation_plan_v1.schema.json` is independent of earlier phase schemas. Every emitted plan has `schema_version="1.0"` and `taxonomy_version="1.0"`.

## Main fields

| Section | Purpose |
|---|---|
| Identification | Stable plan ID, learner/concept, creation time, plan version, prior-plan link and plan kind. |
| Input references | Phase 11 state ID/version, Phase 9 reference, supporting and contradictory evidence IDs, and relevant Phase 11 diagnostic recommendation IDs. |
| Teaching context | Current concept, objective, current representation, trajectory, previous plan, branch-return pointer, earlier diagnostic recommendations and accumulated evidence history. |
| Concept grounding | Name status, EdNet skill/question/lecture/part/bundle/explanation IDs, objective/prerequisite/example availability and grounding limitations. Reference lists are bounded to 20 IDs per type and include total counts and truncation flags. |
| Decision | Selected representation or `null`, downstream action, capability availability, rationale, deterministic method, ordinal confidence, policy trace and rejected alternatives. |
| Learning objective | Target concept, objective text/status and a bounded intended evidence outcome. |
| Representation configuration | Only fields relevant to an available selected category; empty when no category can be selected. |
| Evaluation strategy | Suggested follow-up observation and its purpose. It does not execute or claim an intervention effect. |
| Limitations | Evidence gaps, missing modalities, uncertainty, unavailable capabilities and claims boundary. |

## Availability semantics

The `selected_representation` field is non-null only when its capability is `available`, the capability reference matches, and a provider ID or content ID exists. Otherwise the plan records `null`, `delivery_status="not_selected"`, and an evidence-gathering or defer action. The alternatives list includes availability and a rejection reason for every other taxonomy category.

`decision_confidence` is ordinal and currently `low`. `confidence_scope` states that it describes support for a recommendation, not a predicted learning effect or a modality preference. The schema contains no probability-of-learning field.

The validator also checks that policy-trace evidence IDs occur in the input references, plan/context concepts match, selected capabilities are available, and temporal plan versions link to their predecessor.
