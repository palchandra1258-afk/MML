# MCP-RI Dataset Selection

## Recommendation

### Primary: EdNet KT1, with the official question-content table

Use EdNet KT1 for the **first supervised experiment: predict whether the learner's next submitted answer is correct**, from information available before that answer. The official repository provides a concrete route from student-response records to labels: KT1 provides user-specific question-solving logs, timestamps, question IDs, submitted answers, elapsed times and solving/bundle IDs; the released question table provides correct answers and tags. The label is derived as `user_answer == correct_answer` after a documented join. It is an observed response-outcome target, not a confusion or cognition label.

Start with KT1 because the target and chronology are straightforward and the data is question-level. Consider KT2 only as a later extension for intermediate answer-selection events; model the final submitted response separately from intermediate actions. EdNet is the strongest verified first-model data source among the requested datasets, even though its TOEIC domain is not the project's intended math setting.

### Backup candidate for the same response-level task: CMU DataShop equation-solving transactions, conditional on access/schema verification

CMU DataShop is the preferred **domain-aligned backup candidate for the same response-level target** if the specific project is accessible and the actual export contains enough learners, ordered attempts and outcomes. Its documented repository transaction format has the needed field types, but this investigation did not verify that the equation-solving dataset's current export includes them. The exact project size, specific modalities and terms remain unresolved. Treat it as a go/no-go candidate rather than a confirmed backup until a registered account can inspect the dataset and export metadata. Among the requested candidates, no verified dataset besides EdNet currently supports the same individual next-response target without qualification.

If DataShop fails its access/schema gate, **OULAD is the verified fallback dataset for a modified first prediction experiment**, with the target changed to a later assessment score/result from earlier daily VLE activity and assessment history. It cannot replace EdNet for next-question correctness because its VLE interactions are daily click aggregates rather than item-level submitted responses.

### Supplementary datasets

1. **Math Data Corpus:** best supplemental test of language + pen/image + synchronized activity, but access requires a collaborator agreement and it is small/group-based. Use it for a narrowly defined multimodal component study, not as the first-model primary without confirming instance/label granularity.
2. **OULAD:** open, CC BY 4.0 behavioral backup for course-level temporal prediction. It can support predicting later assessment scores/final outcomes from prior VLE/assessment history, not next-question correctness.
3. **EduMUSE:** representation/content resource for Layer 3 and text/visual context ablations; not learner-state training data.
4. **MUTLA:** optional multimodal engagement experiment only if current data access, reuse terms and target labels are verified. Its engagement scope does not equal conceptual mismatch.

## Experiment sequence and division of claims

| Experiment | Dataset | Target/claim | Role |
|---|---|---|---|
| E1: response outcome baseline | EdNet KT1 + question content | Predict next submitted response correctness from prior history and current question metadata | First model; behavioral predictive baseline |
| E2: action sequence extension | EdNet KT2 | Predict final submitted correctness with intermediate answer-change/action history available before submit | Temporal/action feature experiment; not a confusion label |
| E3: domain-aligned replication | CMU DataShop if verified; otherwise Math Data Corpus using its documented correctness granularity | Dataset-specific next attempt or group problem outcome | Transfer/domain validation with target definition adjusted to available unit |
| E4: multimodal fusion | Math Data Corpus; MUTLA only if data/labels/access pass audit | Documented problem/content/engagement target | Unimodal vs multimodal component study, not end-to-end cognition |
| E5: representation knowledge base | EduMUSE | Text/figure/exercise context and QA/content measures | Content-side support for representation planning |
| E6: long-horizon course outcome baseline | OULAD | Assessment score or final-result category from earlier daily clicks/assessment history | Supplementary temporal behavior study |
| Future decision/outcome study | New controlled MCP-RI study | Predefined post-intervention concept outcome by representation condition | Needed for a claim that representation choice improves learning |

## Why EdNet is selected over CMU DataShop for the first model

The initial experiment depends on confirmed learner identifiers, event order, item identity, submitted response and answer key. EdNet's official repository documents all these ingredients across KT1 plus the question contents table, as well as student-separated files and a non-commercial research license. CMU DataShop documents a suitable general transaction format but project-specific access, schema, size and terms could not be inspected. The exact project's modalities cannot be assumed from its title. The first model should therefore use the more verifiable dataset and reserve DataShop as a domain-aligned replication if it passes the access/schema gate.

The main tradeoff is domain mismatch: EdNet is TOEIC English learning, while MCP-RI's examples and strongest research framing are mathematical representation. The first experiment validates the outcome-prediction/data pipeline only. It does not test the full multimodal or math-specific hypothesis. A later DataShop or Math Data Corpus experiment should test transfer to math when accessible.

## Selection gates before implementation

1. Recheck the EdNet repository license and intended research use. CC BY-NC 4.0 excludes commercial use without separate permission.
2. Inspect the archive's actual files and schema after approved download; verify response rows join to `correct_answer`, and measure missing content/answer-key coverage.
3. Determine whether timestamp offsets preserve within-learner chronological order and whether duplicate timestamps or bundles require deterministic tie-breaking.
4. Freeze a grouped learner split and confirm each split has enough target classes and observations.
5. For DataShop, log in; inspect project status/terms; confirm the exact dataset ID/version; export a small schema sample only after the user later authorizes data acquisition; verify IDs, outcomes, KCs, time, event counts and media assets.
6. For Math Data Corpus, contact the current rights holder and confirm whether the original collaborator agreement remains valid and whether redistribution/storage in the planned environment is permitted.

## Explicit limitations

- EdNet is not multimodal in the speech/video/diagram sense. KT2-KT4 capture interaction action types, not rich naturalistic multimodal perception.
- A next-answer correctness model is not a cognitive-state model; better prediction does not imply validated understanding inference.
- EdNet's test of this first model offers no evidence of representation action benefit.
- DataShop's exact project details remain unresolved, so do not cite the earlier 12,568 count as verified.
- Cross-dataset results should be reported separately because task, learners, event units and labels differ.
- No results are available yet; this document recommends experiments only.
