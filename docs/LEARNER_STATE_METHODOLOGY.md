# Phase 9 — Learner State Methodology

## Purpose and target

The module summarizes recorded EdNet KT1 interactions and answer correctness. It operates on the existing processed table and skill tags; it does not preprocess raw archives or fit a model. All output performance fields refer to the probability of a recorded submitted answer being correct under the historical response process. Actual learner understanding remains unobserved.

## Mathematical definitions

For learner (u), let (y_{u,t}\in\{0,1\}) be a labeled observed response at source-ordered event (t). Let (S_{u,t}) be the set of distinct available skill tags attached to that question. An unlabeled event has no (y_{u,t}), remains an interaction, and contributes no response outcome.

For a set of prior labeled outcomes (H), define (n=|H|), (c=\sum_{y\in H}y), and (e=n-c).

- **Observed historical accuracy:** (\hat p=c/n) when (n>0), otherwise unknown (`null`).
- **Recent accuracy:** mean of at most the latest 10 labeled learner outcomes overall, or latest 5 outcomes for a skill. It is `null` if there are none.
- **Bayesian smoothed performance:** with a uniform Beta prior, (p\sim\mathrm{Beta}(1,1)), and Bernoulli responses, the posterior is (\mathrm{Beta}(c+1,e+1)). The serialized point estimate is its mean:
  \[
  \tilde p = \frac{c+1}{n+2}.
  \]
  This is a response-correctness estimate under an exchangeability assumption. It is not a learner ability or mastery score. The same prior is used globally and per skill; it is not empirically fitted.
- **Performance change/trend:** with at least 10 labeled observations, subtract mean of the preceding 5 from mean of the latest 5. Change \(\le -0.10\) is `declining`; change \(\ge 0.10\) is `improving`; otherwise `stable`. With fewer than 10 observations, trend is `insufficient_evidence`. Ten and 0.10 are transparent operational thresholds, not validated educational cutoffs.
- **95% uncertainty interval:** Wilson score interval for the observed Bernoulli accuracy, using (z=1.9599639845). For (n=0), report `[0,1]`. It describes finite-sample uncertainty for an outcome proportion under a binomial model; repeated observations may violate independence and the interval is not a cognitive-state interval.
- **Evidence sufficiency:** none at (n=0); low for (1\le n<5); moderate for (5\le n<20); high for (n\ge20).
- **Confidence/uncertainty categories:** low evidence implies low confidence/high uncertainty. At moderate evidence, confidence becomes moderate only when Wilson width is at most 0.35. At high evidence, confidence is high only when width is at most 0.20; otherwise it is moderate. These are deterministic descriptive categories, not calibrated confidence probabilities.

The global recent window and each skill's window are updated only by labeled responses. An unlabeled interaction still updates interaction totals, mapping coverage, last-seen metadata and event timestamp.

## Potential issues

Flags are designed for review, not diagnosis:

- `insufficient_evidence`: fewer than five labeled outcomes;
- `repeated_recent_incorrect_responses`: at least three incorrect among the latest up to five responses (requires at least three);
- `recent_performance_decline`: the latest-five minus previous-five change is at most -0.10;
- `inconsistent_recent_responses`: latest window has at least two correct and two incorrect outcomes.

Flags may co-occur. No response pattern is called a misconception. Poor prediction calibration is not currently a state flag because no per-event predictions were available to assess here.

## Leakage control and missing data

The builder consumes processed rows in their existing source order, enforces strictly increasing `source_row_order`, and rejects decreasing numeric timestamps. Equal timestamps are permitted and preserve their source sequence. A historical state is produced by replaying only rows through its chosen cutoff. The full validation export never reads test rows into an accumulator; its scanner skips them. Skill tags are parsed from the existing `skill_tags`/`current_skill_tags` fields, split on semicolons, deduplicated within an event, and sentinel `-1` is omitted. A question with no tag still increments the learner interaction count and the missing-mapping count.

Exact duplicate rows remain separate evidence, consistent with the existing preprocessing policy; this can give repeated records extra weight. Blank answers remain in the stream and do not change response statistics. If correctness is absent or invalid, it is treated as unlabelled rather than imputed.

## Prediction output boundary

Existing Phase 6–8 models predict next submitted-answer correctness. If an application later loads a verified model and supplies its probability, the probability is stored separately and never blended into observed accuracy or smoothed concept performance. The state builder has no model dependency and no predictions are included in this run because model libraries are missing in the active interpreter. Validation calibration of correctness models does not calibrate concept understanding.

## Schema and reproducibility

The versioned interchange schema is [`schemas/learner_state_v1.schema.json`](../schemas/learner_state_v1.schema.json). Each generated state is checked against it (using `jsonschema` when installed) plus internal count and numeric invariants. The reference implementation uses only standard-library CSV/gzip/JSON and the already present schema validator is optional. Inputs and outputs are deterministic for a fixed processed table/order. No training, test evaluation, dataset modification or model modification is performed.
