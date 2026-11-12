# Representation Availability Registry

The default `RepresentationAvailabilityRegistry` marks all eight categories unavailable because the repository has no teaching-content generator, question-serving interface, curated example bank, diagram renderer or interactive/simulation runtime. A downstream integrator may register a capability as available only with a provider ID or concrete content IDs. Planned and unavailable categories remain non-selectable.

| Representation | Current repository capability | Grounded content |
|---|---|---|
| Textual explanation | Unavailable; no explanation generator/source | None |
| Worked example | Unavailable; no worked-example bank | None |
| Visual representation | Unavailable; no diagram renderer/content source | None |
| Symbolic representation | Unavailable; no concept-grounded solution content | None |
| Interactive representation | Unavailable; no runtime | None |
| Simulation | Unavailable; no simulator | None |
| Diagnostic representation | Unavailable; no concept-aligned question-serving capability | EdNet item IDs only; question bodies are not embedded in the Phase 12 catalog |
| Alternative/continued explanation | Unavailable; no generator or explanation source | None |

The local EdNet content archive maps skill tags to question and lecture IDs and records question `part`, `bundle_id`, `explanation_id`, and lecture metadata such as part and video length. Phase 12 excludes `correct_answer` from the catalog. Explanation and lecture IDs are references, not retrieved teaching content; no lecture video assets were found in the inspected archive. Related item IDs are not automatically used as diagnostic questions because prompt/item content and a delivery service are not part of this capability registry.

To register a real capability, provide `representation_id`, `status="available"`, a nonempty `provider_id` or `content_ids`, and a reason. The planner then may recommend it under the matching rule, but the plan remains recommendation-only until a separate component confirms exposure.
