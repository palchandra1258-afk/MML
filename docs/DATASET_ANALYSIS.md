# MCP-RI Dataset Analysis and Verification

**Verification date:** 4 November 2026. No dataset was downloaded or opened locally for this investigation. “Verified” below means the claim is supported by the cited source; it does not mean that the files have been inspected. Dataset pages and access terms can change.

## Executive finding

CMU DataShop is a strong *candidate* for a constrained equation-solving experiment: DataShop's documented transaction export can include anonymous learner IDs, session IDs, timestamps, attempt outcomes, step/task names and knowledge components. However, the exact Multimodal Interface for Solving Equations project page is currently blocked to this investigation (HTTP 403), and the project's exact dataset version, current transaction count, actual exported columns, linked handwriting/audio artifacts, and project-specific reuse terms could not be verified. A historical DataShop pipeline list also identifies records under this project (IDs 145 and 165), which does not establish that the project link's `datasetId=501` is the same dataset or that those records are currently accessible. The prior audit's 12,568 transaction figure is therefore **not confirmed** here.

EdNet is the best verified choice for the first next-response-outcome model. Its official repository describes per-student files, ordered timestamps, question IDs, submitted answers and elapsed times; the released content table supplies correct answers and skill tags. That permits a response-correctness target by joining a response with the question answer key. It is a behavioral tutoring log, not the project's full multimodal or representation-intervention dataset.

## CMU DataShop: Multimodal Interface for Solving Equations

### Official source and access

The CMU/DataShop project page is referenced as project 33 by a peer-reviewed data-fusion review. DataShop's official access guide says to create a DataShop account through university/InCommon or Google sign-in; public datasets become available after login, while private projects require a request to the PI/data provider. The official API documentation describes transaction export and web services. This investigation could not fetch the specific project page or inspect its logged-in status, so current public/private status and exact download button/API access for this project remain unresolved.

### Verified repository-level schema (not project-specific proof)

The official DataShop transaction schema/API can represent:

- `anon_student_id`, `session_id`, `time`, `duration`;
- problem hierarchy/name/view and step name;
- `attempt_at_step`, `outcome` (examples include `CORRECT`), selection/input and tutor feedback;
- `kcs`/KC and KC category columns when mapped for the dataset;
- condition, help level and hint counts when available.

These are documented DataShop export fields, not a verified field inventory for the equation-solving project. A field may be absent/empty in a particular dataset. DataShop's own documentation notes KC fields can be empty. The data may also contain linked problem content, but that is distinct from raw speech, video or handwriting files.

### Modalities and project identity

The project title and project-33 link suggest an equation tutor with multimodal input. A historical CMU/learnlab pipeline page lists “Handwriting Examples - Winter 2006” (DB ID 145) and “Handwriting - Spring 2007” (DB ID 165) beneath “A Multimodal Interface for Solving Equations.” This supports the existence of related handwriting datasets, but is a historical pipeline page, not a current inventory. An old project poster says students used handwriting and speech to enter equations. None of these sources proves that speech recordings, images/ink traces or their alignment are present in current downloadable dataset 501.

### Learners, sessions, chronology and outcomes

DataShop's general schema supports anonymous learner identifiers, session identifiers and timestamps. It supports transaction-level outcomes/attempts and optionally KCs. Project-specific availability and completeness are unverified. The official DataShop API documentation's example includes two transactions for one anonymous learner/session and a `CORRECT` outcome, but an example format cannot establish the contents of this project.

### Dataset size and license/reuse

No current official project-specific size/transaction count was verifiable. The 12,568 figure recorded in earlier planning material should not be used as verified dataset size. DataShop says public datasets can be used after account creation, but terms and acknowledgements can be dataset-specific; the project's terms page needs inspection after access. General DataShop public access should not be described as a blanket open license or as permission to redistribute.

### Can it support the first model?

**Potentially, but it is not yet verified enough to commit as the primary dataset.** If the project is accessible and its transaction export contains learner/session/time, ordered attempts, a documented outcome and enough learner groups, a next-step response-outcome experiment is feasible. Construct examples by ordering each learner's transactions and predicting outcome on a subsequent attempt from prior attempts/task/KC context. Keep the same learner entirely in one split. Do not use current-attempt outcome, feedback generated after the attempt, or post-target fields as inputs.

Before deciding, confirm: exact dataset ID/version, access status, count of unique learners/sessions/transactions, export columns and nonmissingness, ordering semantics, outcome coding, KC model coverage, and whether linked handwriting/speech files exist and are usable. If these checks fail, DataShop is not the first-model source.

## Other candidate datasets

| Dataset | Available modalities | Temporal information | Labels | Access requirements | Training suitability | Limitations |
|---|---|---|---|---|---|---|
| **CMU DataShop: Multimodal Interface for Solving Equations** | Project-specific modalities unverified. DataShop transaction format is structured interaction; historical project entries name handwriting samples. Speech/ink availability for the exact dataset is unresolved. | DataShop schema supports learner/session IDs, timestamp, duration, attempt order. Exact project's coverage unverified. | DataShop schema supports outcome/attempt and optional KCs. Exact target coverage unverified. | Create account for public projects; request PI access for private projects. Dataset-specific terms may apply. Project 33/501 current access unresolved. | **Conditional candidate** for next-attempt outcome; highly constrained algebra task if records/labels are accessible. | 403 blocks page review here; reported 12,568 size unconfirmed; ambiguous project/dataset IDs; multimedia files not verified. |
| **Math Data Corpus / ICMI MMLA Grand Challenge** | Time-synchronized speech, digital pen and images. Collected from groups collaborating on mathematics problems. | Synchronized multimodal recordings; group/session/problem structure. A published account describes 12 sessions, 18 high-school students, groups of three and about 16 hours, but verify against current corpus documentation. | Initial codes for problem segmentation, group problem correctness and representational content of writing; challenge targets included group expert identification and correct/incorrect problems. | The original paper says challenge participants received access after a collaborator agreement. Current availability should be confirmed with the rights holder; old competition window is not proof of present access. | **Strong supplementary multimodal study**, potentially small exploratory supervised tasks if annotation granularity supports it. | Small number of independent groups; group-level outcomes do not automatically become individual next-response labels; gated agreement; limited generalization. |
| **EdNet** | KT1: question/answer logs. KT2 adds response-action sequences; KT3 adds explanation/lecture actions; KT4 adds further UI actions including audio/video controls. No learner webcam or natural speech is documented in the core levels. | Timestamped events; user-specific files; `solving_id`/bundle grouping in KT1; higher levels preserve action sequences. Published timestamps are shifted for security, while ordering remains usable subject to data checks. | KT1 submitted answer; question content table supplies correct answer and tags, enabling derived `is_correct`; question metadata also provides bundle/question IDs. Not cognition labels. | Official GitHub offers archives; CC BY-NC 4.0 research-purpose license. Non-commercial restriction applies; retain attribution and verify license for all intended uses. | **Best verified first-model dataset** for predicting response correctness from prior learner history and current item features. KT1 is enough for response outcome; KT2+ for within-question action behavior. | TOEIC English tutoring domain, not math; no cognitive mismatch or representation-choice outcomes; high volume can mask fewer independent learners; timestamp values shifted; NC license. |
| **EduMUSE** | Instructional text, figures/images, exercise text, solutions where available, subsection context and model-scored QA/loss fields. | Hierarchy by book/chapter/section/exercise; no learner event chronology. | Exercise answers/solutions and VLM-derived scores/alignment. Subsection alignment is model-selected and explicitly not human-verified ground truth. | Hugging Face dataset snapshot/files. Listed CC BY 4.0 with attribution to OpenStax and dataset. Download may require handling JSON plus image archives; no learner access gate described. | Useful for Layer 3 content/representation inventory, vision-language content tasks, text-vs-visual context ablation. | Not learner data, not temporal, no learner ID, no cognitive state or intervention/outcome labels. Not suitable for first model. |
| **MUTLA** | Learning/question logs, webcam videos, EEG/brainwave files and device attention/event records. | Time-synchronized to question windows; records have learner IDs/session/question start and submission times as described by the paper. | The paper's intended analysis is engagement; it describes response logs and proficiency/tag context. A validated confusion/mismatch label was not verified. | Paper points to a TinyURL for public access, but current redirect/files, data-use terms and license were not verified. Do not assume unrestricted access. | Potential supplementary multimodal engagement/evidence-fusion study if files, annotations and terms are confirmed. | 156 participants in 2 Chinese after-school centers per paper; not a large independent-learner sample for deep fusion; sensor-heavy; construct is not fine-grained conceptual mismatch. |
| **OULAD** | Relational course/student/assessment data and VLE activity aggregates (`studentVle` daily click counts); no speech/video/visual learner artifacts documented. | Daily VLE interactions by student/module/presentation; assessment submission days and scores; course timelines. | Assessment scores and final result; not item-level response correctness for the VLE click rows. | Open University source and UCI repository provide download; CC BY 4.0 listed by UCI. Attribute source. | Useful backup for course-level temporal performance prediction and behavior baselines, not the proposed response-level next-answer target. | Clicks are aggregated daily; no multimodal signals; assessment outcomes are coarse and may be temporally sparse. |

### Architecture fit summary

- **Layer 1 (Evidence Modeling):** Math Data Corpus is strongest for synchronized speech/pen/image; MUTLA provides logs/video/EEG if access is confirmed; EdNet/OULAD provide behavior sequences only; EduMUSE provides instructional content/images but no learner evidence.
- **Layer 2 (Cognitive State):** MUTLA's engagement aim and Math Corpus's problem/content labels can support only their own documented constructs. EdNet can support response correctness/knowledge tracing; OULAD can support course outcomes. None of these verified descriptions establishes a validated, uncertainty-labeled representation-mismatch target.
- **Layer 3 (Representation Intelligence):** EduMUSE can enrich the available content/figure catalog. None of the candidates is verified to contain randomized representation decisions and resulting learner outcomes; an initial planner remains rule-based.
- **Layer 4 (Outcome/Update):** EdNet and OULAD support subsequent response/course outcomes respectively, but not the full adaptive intervention loop. A controlled MCP-RI study likely remains necessary for action exposure and post-representation outcomes.

## Sources

- [CMU DataShop official access instructions](https://datashop.dev.datashop.org/help?page=access)
- [DataShop Public API and transaction schema (official PDF)](https://pslcdatashop.web.cmu.edu/api/DataShop%20Public%20API-v0.41.pdf)
- [CMU DataShop institutional overview](https://www.cmu.edu/datalab/tools/datashop.html)
- [Historical DataShop pipeline listing for the equation-solving project](https://learnlab.org/mediawiki-1.44.2/index.php?title=DataShop_Pipeline)
- [Project 33 reference in the 2022 data-fusion review](https://doi.org/10.1002/widm.1458)
- [Math Data Corpus paper (ICMI 2013 PDF)](https://projet.liris.cnrs.fr/imagine/pub/proceedings/ICMI-2013/icmi/p563.pdf)
- [ICMI 2013 challenge access description](https://icmi.acm.org/2013/index.php?id=challenges)
- [EdNet official repository/schema and license](https://github.com/riiid/ednet)
- [EduMUSE dataset card, structure, terms and limitations](https://huggingface.co/datasets/upb-nlp/EduMUSE)
- [EduMUSE paper](https://aclanthology.org/2026.bea-1.25/)
- [MUTLA paper and described access pointer](https://arxiv.org/abs/1910.06078)
- [OULAD dataset record and CC BY 4.0 license at UCI](https://archive.ics.uci.edu/dataset/349/open%2Buniversity%2Blearning%2Banalytics%2Bdataset)
- [OULAD data descriptor](https://doi.org/10.1038/sdata.2017.171)
