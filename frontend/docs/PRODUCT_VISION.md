# Product vision

## Product purpose

MCP-RI's frontend should make a research system's continuity and reasoning inspectable. It should connect observed learner activity to a provisional state estimate, show how that estimate informs a representation decision, and make trajectory changes—including a temporary diversion and restoration of the interrupted step—understandable over time.

The central product promise is a **persistent, evidence-driven system that estimates learner state, makes explainable representation decisions, and adapts learning trajectories while preserving teaching continuity**. The interface communicates this as an auditable chain, not as an opaque AI score or a claim that cognition is directly measured.

## Product principles

1. **Evidence before interpretation.** Show the source, time/window, and coverage of an observation before the estimate that uses it.
2. **Inference stays provisional.** Say “possible difficulty,” “provisional estimate,” or “evidence suggests.” Do not label a learner as confused, deficient, mastered, or diagnosed.
3. **Recommendation is not delivery.** All eight representation-delivery capabilities are currently unavailable. A recommendation/deferred plan is not an executable lesson and no interactive lesson should be simulated as real.
4. **Continuity is visible.** When a diversion exists, show the parent goal, preserved interrupted step, supporting concept, reason, progress, and explicit resumption/replan status together.
5. **Uncertainty and missingness are data.** Surface sparse evidence, modality gaps, contradictions, alignment uncertainty, and provenance rather than hiding them in a generic confidence badge.
6. **Separate audiences.** Learners get clear next-step language; researchers can inspect schema-level details, IDs, rule traces, thresholds, and evaluation limits.
7. **No unsupported measures.** Every displayed metric names its meaning, window, denominator, source, and applicable caveat.

## Current evidence and product readiness

The repository includes EdNet-derived behavioral state summaries, evidence-record adapters, rule-based provisional cognitive estimates, versioned representation plans, and trajectory/diversion/resumption orchestration artifacts. EdNet is not a text/audio/visual learner corpus in this implementation. Text/audio/visual adapters are exercised with synthetic fixtures; no real learner-generated multimodal corpus is available here. There is no validated cognitive-state ground truth, no validated dependency graph, no content delivery provider, no durable Phase 13 database, and no Phase 14 API contract in this frontend directory.

Accordingly, the first reviewable product should be understood as a research inspection and interaction-design shell. Learner activities, lesson objectives, and progress must come from an actual content/backend source or explicitly synthetic scenario fixtures. They must not be inferred from EdNet tags.

## Outcomes the interface should support

- A learner can locate the current supplied objective and know whether a real activity is available.
- A learner can understand the next action and whether it is a real activity, request for evidence, or deferred capability.
- A researcher can trace each state/plan/trajectory decision to records and identify missing or contradictory input.
- A researcher can reconstruct the primary trajectory around a diversion and verify the same interrupted step is restored.
- A reviewer can distinguish validated software behavior from claims about cognition or learning outcomes.

## Out of scope for initial planning

Authentication and permissions, content authoring/delivery, diagnosis, automatic modality-preference inference, actual multimodal fusion, validated mastery judgments, causal intervention claims, and production-scale learner analytics are not established by current code and are not promised by this plan.
