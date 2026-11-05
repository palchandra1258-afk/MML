# MCP-RI End-to-End Data Flow

## Flow overview

```text
Approved dataset or consented study session
        │
        ▼
Ingestion + schema validation + pseudonymous IDs
        │
        ├── language / transcript / optional audio
        ├── visual artifact / optional pen trace
        ├── interaction events / response outcomes
        └── concept, task, teaching position (only if supplied)
        │
        ▼
Timestamp normalization + modality quality + missingness mask
        │
        ▼
Modality-specific preprocessing and frozen pretrained inference
        │
        ▼
Aligned EvidenceBundle Z_t + source provenance
        │
        ▼
Target-specific state model (only for available, valid labels)
        │
        ▼
StateEstimate S_t: probabilities / uncertainty / evidence / unknowns
        │
        ▼
Representation Planner
  inspectable rule-based action; diagnostic fallback under uncertainty
        │
        ▼
RepresentationPlan R_t: continue / clarify / alternate form / diversion
        │
        ▼
Exposure and interaction recorder
        │
        ▼
Follow-up outcome Y_(t+1) + new observations
        │
        └──► append-only event history → updated S_(t+1) → continue/replan
```

## Step-by-step contract

### 1. Source and permission gate

Each experiment declares its dataset and version, license/terms, permitted purpose, modality inventory, unit of observation, population, labels, and split unit. For new human data, the protocol, consent, retention and ethics approvals are prerequisites. A listed dataset is not treated as downloaded, available or approved until checked.

### 2. Ingest observations

Convert source records into normalized event objects while retaining source IDs and raw timestamp values. Avoid joining people across datasets unless a valid shared key and consent/access basis exists; ordinarily the datasets are analyzed in separate experiments. Record concept and item IDs only when provided or manually curated under a documented protocol.

### 3. Preprocess by modality

- Text: normalize minimally; preserve original text and language metadata; derive pretrained embeddings or lexical baseline features.
- Audio: if present and permitted, run a frozen pretrained ASR model and retain transcript confidence/timing. Do not silently use ASR transcription as a human-labeled transcript.
- Visual: if present, derive frozen vision/OCR features or annotations. Record artifact resolution and quality.
- Interaction: sort by reliable timestamp; create event transitions and windows without interpreting them as cognition.
- Labels: keep annotation/target tables separate from model features and document who/what generated each label.

### 4. Align and bundle evidence

Create analysis windows based on the dataset's task/session structure. Keep original times and alignment uncertainty. For asynchronous observations, do not invent exact synchronization. Build per-modality masks so a fusion model can distinguish “not observed” from a meaningful zero value. Retain event IDs used in every bundle.

### 5. Infer a task-defined state

The estimator only predicts targets present in that experiment. Example: if a dataset has correctness labels, a model may predict correctness on a held-out future item. If it has engagement annotation, it may predict that annotation with explicit construct naming. Neither result automatically validates a general cognitive-state estimator. Persist probabilities, uncertainty and model version alongside the exact target definition.

### 6. Plan a representation action

The initial planner consumes the state estimate together with current concept, user request, context and available representations. It applies inspectable rules, leaves unavailable options out, and favors a clarifying/diagnostic action when state confidence is low. It emits a representation plan and keeps a return pointer to the interrupted teaching trajectory. Existing public datasets may not contain these plans or action assignments; in that case, this stage is evaluated as a prototype workflow rather than as a learned policy.

### 7. Observe outcomes and update

Record what was actually presented, whether the learner used it, and a predeclared follow-up outcome. Distinguish exposure from selection and selection from benefit. Add new evidence and outcome records to the event history. Update state in a new version, retaining the prior estimate and its evidence.

## Dataset-to-experiment mapping (candidate, subject to validation)

| Candidate from research reference | Modalities/labels described in reference | Appropriate initial use | Not supported without further evidence |
|---|---|---|---|
| Math Data Corpus / MMLA Grand Challenge | Speech, digital pen/handwriting, image sequences, timestamps, problem-solving correctness and representational-content coding | Cross-modal evidence, alignment, representation-content or correctness prediction if data/schema/access permit | General misconception, calibrated cognition, adaptive action benefit |
| CMU DataShop Multimodal Interface for Solving Equations | Equation-solving interaction/handwriting transactions as described in reference | Constrained interaction trajectory baseline if relevant fields and access terms are confirmed | Voice/video multimodal fusion or representation intervention effects unless present in verified records |
| MUTLA | Learning logs, webcam video, EEG, synchronized timestamps | Engagement/state-related benchmark only for its documented labels and target | Fine-grained conceptual misconception unless separately labeled |
| EdNet | Large interaction/action traces and item responses as described | Temporal behavioral or knowledge-tracing baseline | Synchronized natural speech/video and cognitive-state ground truth |
| OULAD | Course/assessment/VLE interaction records | Structured temporal behavioral baseline | Rich visual/audio evidence or direct cognitive labels |
| EduMUSE | Text, figures, exercises, solutions and instructional context | Content/representation resource; concept/content alignment | Learner interaction or cognitive-state model training |
| ES-KT-24 | Game video, question text and logs as described | Multimodal knowledge-tracing benchmark if verified | Learner cognitive-state labels beyond provided targets |
| DAiSEE | Video snippets and affective labels (boredom, confusion, engagement, frustration) as described | Narrow visual affect-label benchmark with careful construct caveats | Concept grounding or representation selection benefit |
| PE-HRI, BBBD, NUSMSP, SOPHIAS | Specialized collaborative, physiological or presentation modalities as described | Optional component-specific external validation after fit review | Direct substitute for the core learner/concept/representation loop |

This mapping follows the research reference's descriptions and does not verify current dataset facts, access, terms or label schemas. Conduct that verification before selecting a primary dataset.

## Data split and leakage controls

- Split by learner, not event/window, wherever learner IDs exist.
- Use session/time-forward splits for temporal generalization; fit scalers, vocabulary, imputation and feature selection on training data only.
- Keep duplicate or derived views of a participant in one split.
- If data is grouped by class/course/institution, consider group-held-out evaluation and report its limits.
- Freeze a test split before model selection; nested/grouped validation for tuning where sample size supports it.
- Compare modality models on a matched cohort, report missingness, and add a separate deployment-like evaluation with naturally absent modalities if feasible.

## Privacy and retention flow

Raw audio/video/physiology should be retained only when permitted and necessary. Store identifying keys separately from features; restrict access; document retention/deletion and transformations. Derived embeddings can remain sensitive and should not be assumed anonymous. Dataset terms and institutional review govern actual handling.
