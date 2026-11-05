How can a persistent cognitive system perceive a human through multiple forms of interaction, construct a calibrated representation of what is cognitively happening, and use that representation to decide how knowledge should be presented, externalized, or manipulated next? 

Problem Statement

Universal Cognitive Infrastructure requires more than the ability to generate explanations or respond to user queries. To adapt meaningfully over time, it must be able to perceive evidence distributed across voice, language, visual artifacts and interaction trajectories; transform that evidence into a persistent, concept-grounded and uncertainty-aware representation of the user's evolving cognitive context; and use that representation to determine how knowledge should be presented, externalized, manipulated or continued next.

The challenge becomes particularly important when a learner interrupts an ongoing teaching trajectory. The system must distinguish a simple question from evidence of a deeper representational or conceptual mismatch, create an appropriate contextual diversion when necessary, preserve continuity with the original learning trajectory, and adapt its subsequent representation based on what occurred during the diversion. Existing systems typically treat these events as isolated prompts or rely on static mastery estimates, leaving a major gap between multimodal interaction and persistent, state-aware representation decisions.

## Research Objective

> **To develop and evaluate a Multimodal Cognitive Perception and Representation Intelligence framework that integrates language and voice interaction, visual artifacts and interaction trajectories into a temporally persistent, concept-grounded and uncertainty-aware representation of a learner's cognitive context. The research will investigate whether this representation can improve the detection of cognitive and representational mismatches, enable context-preserving diversions from an ongoing teaching trajectory, and support more effective selection of textual, visual, spatial, symbolic, interactive or simulated representations than unimodal, static, heuristic or mastery-only approaches.**

**Project Output**

**The project will produce and evaluate a Multimodal Cognitive Perception and Adaptive Representation prototype that integrates language/voice, visual context and interaction trajectories to construct temporally grounded cognitive evidence, detect potential representation mismatches, and select an appropriate adaptive representation or contextual diversion during an ongoing teaching trajectory. The resulting system will serve as an experimental perceptual and adaptation layer for Universal Cognitive Infrastructure, demonstrating how a persistent cognitive environment can move beyond prompt-response interaction toward continuous perception, state-aware adaptation and representation-level intervention.** 

**Multimodal Cognitive Perception and Representation Intelligence** 

### Core problem

> **A Universal Cognitive Infrastructure cannot adapt meaningfully to a person if it cannot construct a reliable representation of what is cognitively happening; and even with such a representation, it cannot act intelligently unless it can determine which form of representation—textual, visual, spatial, interactive, symbolic or simulated—is most appropriate for the next cognitive moment.**

> 

> 

### Research objective

> **Develop and evaluate a multimodal framework that integrates language, visual artifacts and interaction trajectories into a temporally grounded and uncertainty-aware cognitive-state representation, then investigates whether this representation can improve adaptive selection of knowledge representations compared with unimodal, static, heuristic or mastery-only approaches.**

# **2\. The most useful datasets for your exact project**

I have divided these by relevance to **MCI-1: Multimodal Cognitive Perception and Representation Intelligence**.

---

## **Dataset Tier 1 — Directly useful for MCI**

### **1\. [MUTLA: Multimodal Teaching and Learning Analytics](https://arxiv.org/abs/1910.06078?utm_source=chatgpt.com)**

**Modalities:**

* learning logs  
* webcam video  
* EEG  
* synchronized timestamps  
* educational problem solving

MUTLA was created specifically for multimodal teaching and learning analytics and contains synchronized learning records, video, and EEG from students using an AI learning system.

### **Why it is highly relevant**

This maps directly onto:

Multimodal Observation  
        ↓  
Student Behavior  
        ↓  
Latent Learning State

You can investigate:

* modality-specific encoders  
* multimodal fusion  
* temporal modeling  
* missing-modality experiments  
* engagement/state prediction

### **Limitation**

It is stronger for:

behavior / engagement

than for:

fine-grained conceptual misconception

Still, it is one of the closest datasets to your **multimodal cognitive perception** layer.

---

## **2\. [Math Data Corpus / MMLA Grand Challenge](https://research.monash.edu/en/publications/multimodal-learning-analytics-description-of-math-data-corpus-for-2/?utm_source=chatgpt.com)**

**Modalities:**

* speech  
* digital pen  
* handwritten mathematical work  
* image sequences  
* temporal synchronization  
* problem-solving correctness  
* representational content

The Math Data Corpus was created specifically as an early MMLA benchmark and records students collaboratively solving mathematical problems using synchronized speech, digital-pen and image data. It also includes coding related to problem segmentation, correctness and representational content.

### **Why I find this especially interesting for you**

This is unusually close to your original MCI formulation:

What the learner says  
\+  
What the learner writes/draws  
\+  
How the learner progresses

This enables experiments around:

> **Does agreement or disagreement between verbal explanation and written representation reveal cognitive state?**

For example:

Speech:  
"I understand the equation."

Digital Pen:  
Incorrect transformation.

That is extremely close to your proposed **cross-modal cognitive consistency/disagreement** hypothesis.

### **My assessment**

**One of the most conceptually aligned datasets for MCI-1.**

The practical question is current access/distribution, which should be checked before committing because the original corpus was distributed through a challenge/research setting rather than a modern dataset hub.

---

## **3\. [Multimodal Interface for Solving Equations — CMU DataShop](https://pslcdatashop.web.cmu.edu/index.jsp?datasetId=501&utm_source=chatgpt.com)**

This is a public CMU LearnLab/DataShop project containing interaction data around a multimodal interface for solving algebraic equations. The public project lists 12,568 transactions and terms of use.

### **Why it matters**

It gives you:

Problem  
\+  
Handwriting  
\+  
Interaction  
\+  
Learning trajectory

This is useful for building an early version of:

interaction evidence  
        ↓  
cognitive inference

And it is particularly valuable because the task is **conceptually constrained**.

For your semester research, constrained domains are better than trying to model "general human cognition."

---

# **3\. Datasets for large-scale cognitive trajectory modeling**

## **4\. [EdNet](https://github.com/riiid/ednet?utm_source=chatgpt.com)**

EdNet is one of the largest public educational interaction datasets: more than 131 million interactions from more than 780,000 learners, with increasingly detailed action streams across multiple dataset levels. Its richer levels include question interactions, repeated response behavior, explanations, lectures, video/audio interactions and fine-grained actions.

This is **not a classical multimodal dataset** in the sense of synchronized text-video-audio.

But it is extremely valuable for:

temporal cognitive trajectory

For example:

enter problem  
    ↓  
select answer A  
    ↓  
change answer  
    ↓  
erase option  
    ↓  
play explanation  
    ↓  
pause  
    ↓  
retry

That is already a rich behavioral modality.

### **Why I would use it**

EdNet can support research into:

* sequential modeling  
* knowledge tracing  
* behavioral uncertainty  
* temporal representation learning  
* intervention modeling  
* contextual bandits  
* offline RL foundations

The particularly interesting part for MCI is that EdNet explicitly records behaviors such as repeated answer changes and interactions with explanations and multimedia, providing much richer evidence than a simple correct/incorrect sequence.

### **My assessment**

**Essential infrastructure dataset**, even though it cannot by itself answer the complete multimodal question.

---

## **5\. [Open University Learning Analytics Dataset (OULAD)](https://research.stem.open.ac.uk/ouanalyse/dataset/?utm_source=chatgpt.com)**

OULAD contains anonymized course, student, assessment and virtual-learning-environment interaction data across seven subject areas and 22 course presentations. The underlying Scientific Data description reports 32,593 students and more than 10 million VLE interaction entries.

Useful for:

* behavioral trajectories  
* performance prediction  
* temporal learner modeling  
* baseline state models  
* representation-selection simulations

### **Limitation**

Primarily clickstream and structured educational data.

So:

Excellent temporal baseline

but not:

complete multimodal perception.  
---

# **4\. The dataset I would watch very closely: EduMUSE**

## **6\. [EduMUSE Dataset](https://huggingface.co/datasets/upb-nlp/EduMUSE/blob/main/README.md?utm_source=chatgpt.com)**

This is particularly interesting because it appeared very recently.

EduMUSE is built from OpenStax undergraduate textbooks and integrates:

* structured instructional text  
* figures  
* exercises  
* images  
* solutions where available  
* subsection-level instructional context

The dataset is openly released under CC BY 4.0, and the associated research describes it as a multimodal educational dataset for studying how instructional context affects vision-language educational reasoning.

### **Why it matters for UCI**

This is not primarily a **learner behavior** dataset.

It is a **knowledge representation dataset**.

That makes it extremely valuable for the other half of MCI:

Knowledge  
      ↓  
Possible Representations  
      ↓  
Representation Intelligence

EduMUSE gives you a corpus containing:

Conceptual Text  
\+  
Figures  
\+  
Exercises  
\+  
Solutions  
\+  
Contextual Alignment

That could become the knowledge/content side of your system.

---

# **5\. A very useful recent dataset: ES-KT-24**

## **7\. [ES-KT-24: Multimodal Knowledge Tracing Benchmark](https://arxiv.org/abs/2409.10244?utm_source=chatgpt.com)**

This dataset combines:

* educational game-playing video  
* synthetic question text  
* detailed game logs  
* 15,032 users  
* millions of interactions  
* multiple subjects and languages

The paper explicitly positions it as a multimodal knowledge-tracing benchmark and reports 7.78 million interactions.

### **Why it matters**

It bridges:

Knowledge Tracing  
\+  
Video  
\+  
Language  
\+  
Interaction

That is highly relevant to your proposed transition:

Static mastery  
        →  
Multimodal cognitive state  
---

# **6\. Multimodal engagement and cognitive-state datasets**

## **8\. [PE-HRI Dataset](https://zenodo.org/records/4633092?utm_source=chatgpt.com)**

This dataset studies **productive engagement** in a collaborative educational activity and contains multimodal team behaviors and learning outcomes in a robot-mediated constructivist learning setting.

Useful for:

multimodal engagement  
\+  
collaboration  
\+  
learning outcomes

This could be useful later when UCI moves from:

individual cognition

to:

shared cognitive environments.  
---

## **9\. [BBBD: Brain, Body, and Behavior Dataset](https://www.nature.com/articles/s41597-026-07215-1?utm_source=chatgpt.com)**

This is a very recent 2026 dataset containing recordings from 178 participants across five educational-video experiments, with approximately 110 hours of synchronized:

* EEG  
* EOG  
* ECG  
* respiration  
* pupil size  
* gaze  
* saccades  
* blinks  
* fixations  
* head motion

The data is time-aligned to educational video and standardized in BIDS format.

### **Why it matters**

This is useful if you want to explore:

cognitive state  
≠  
just clickstream

It could support research around:

* attention  
* cognitive response  
* physiological correlates  
* multimodal temporal fusion

### **Limitation**

This is sensor-heavy and may not align with the first deployable UCI product.

Therefore I would treat it as:

> **research validation data**

rather than the foundation of the initial product architecture.

---

## **10\. [DAiSEE: Dataset for Affective States in E-Environments](https://arxiv.org/abs/1609.01885?utm_source=chatgpt.com)**

DAiSEE contains 9,068 video snippets from 112 users, with labels for:

* boredom  
* confusion  
* engagement  
* frustration

Each state is rated across four levels.

This is useful for one narrow but important MCI question:

> Can observable multimodal or visual behavior contribute to a latent-state representation?

It should **not** be your main dataset because it is too narrow for the full cognitive-state model.

But it is useful as a benchmark.

---

# **7\. A dataset I would include for advanced multimodal research**

## **11\. [NUS Multi-Sensor Presentation Dataset](https://sites.google.com/site/yongkangwong/datasets?utm_source=chatgpt.com)**

NUSMSP includes multimodal recordings of 51 real-world presentations using:

* Kinect  
* ambient visual sensors  
* egocentric sensors  
* depth  
* audio

The dataset was created around automated analysis and feedback for presentation skills.

Not directly aligned with conceptual learning.

But useful for studying:

multimodal temporal fusion  
\+  
behavior interpretation  
\+  
performance prediction  
---

# **8\. A very relevant new dataset: SOPHIAS**

## **12\. [SOPHIAS: Student Oral Presentation Dataset](https://arxiv.org/abs/2601.07576?utm_source=chatgpt.com)**

SOPHIAS contains:

* 50 presentations  
* 65 undergraduate and master's students  
* video  
* audio  
* eye tracking  
* smartwatch physiology  
* clicker/keyboard/mouse interactions  
* slides  
* teacher evaluations  
* peer evaluations  
* self-assessments  
* timestamped contextual annotations

The paper describes the dataset as publicly available for research through GitHub and Science Data Bank.

This is useful for studying the relationship:

Multimodal Evidence  
        ↓  
Latent Performance / Cognitive / Behavioral State  
        ↓  
Human Evaluation  
---

# **9\. My dataset ranking for your semester**

If I were designing MCI-1, I would prioritize:

### **Tier A — Core**

1. **Math Data Corpus**  
2. **CMU Multimodal Interface for Solving Equations**  
3. **EdNet**  
4. **EduMUSE**

### **Tier B — Benchmark / representation research**

5. **MUTLA**  
6. **ES-KT-24**  
7. **PE-HRI**

### **Tier C — Cognitive/affective modeling**

8. **BBBD**  
9. **DAiSEE**  
10. **NUSMSP**  
11. **SOPHIAS**

### **Tier D — Temporal behavioral baselines**

12. **OULAD**

# **The 12 most closely aligned research papers**

I would divide the reading into **three layers**.

---

## **Layer A — Direct foundations for your problem**

### **Paper 1**

### [**Multimodal Machine Learning: A Survey and Taxonomy**](https://arxiv.org/abs/1705.09406?utm_source=chatgpt.com)

**Baltrušaitis, Ahuja, Morency — 2019**

This is foundational because it gives you the core multimodal problem taxonomy:

* representation  
* translation  
* alignment  
* fusion  
* co-learning

These map directly onto MCI.

MCI perception problem  
       │  
       ├── Representation  
       ├── Alignment  
       ├── Fusion  
       └── Missing modalities  
---

### **Paper 2**

### [**A Review on Data Fusion in Multimodal Learning Analytics and Educational Data Mining**](https://wires.onlinelibrary.wiley.com/doi/full/10.1002/widm.1458?utm_source=chatgpt.com)

**Chango et al. — 2022**

This is probably one of the most important literature reviews for your project.

It surveys multimodal data fusion specifically in:

* educational data mining  
* learning analytics  
* physical/digital modalities  
* physiological data  
* interaction data

It also explicitly identifies the fragmented nature of publicly available multimodal educational datasets.

---

### **Paper 3**

### [**Multimodal Learning Analytics: Description of Math Data Corpus**](https://research.monash.edu/en/publications/multimodal-learning-analytics-description-of-math-data-corpus-for-2/?utm_source=chatgpt.com)

**Oviatt, Cohen, Weibel — 2013**

This is an early foundational paper for MMLA.

Why it matters for you:

It explicitly investigates whether synchronized:

speech  
\+  
digital pen  
\+  
visual representation

can reveal:

expertise  
\+  
problem-solving behavior  
\+  
learning-oriented patterns

That is conceptually extremely close to MCI-1.

---

### **Paper 4**

### [**Unraveling Students' Interaction Around a Tangible Interface Using Multimodal Learning Analytics**](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/JEDM102/0?utm_source=chatgpt.com)

**Schneider & Blikstein — 2015**

This paper combines:

* interaction logs  
* gestures  
* tangible interaction  
* machine learning

to predict learning outcomes.

The key relevance is methodological:

> different behavioral modalities can reveal information unavailable from a single interaction stream.

---

# **Layer B — Cognitive-state inference**

### **Paper 5**

### [**Multimodal Learning Analytics to Investigate Cognitive Load During Online Problem Solving**](https://bera-journals.onlinelibrary.wiley.com/doi/abs/10.1111/bjet.12958?utm_source=chatgpt.com)

**Larmuseau et al. — 2020**

This paper combines:

* self-reported cognitive load  
* galvanic skin response  
* skin temperature  
* heart rate  
* heart-rate variability

to study cognitive load during online problem solving.

It is important because it directly addresses:

latent cognitive state

from:

multimodal evidence

The study also demonstrates an important caution: richer multimodal signals do not automatically produce simple or universally strong cognitive-state inference.

---

### **Paper 6**

### [**Enhancing Online Learning: A Multimodal Approach for Cognitive Load Assessment**](https://www.tandfonline.com/doi/full/10.1080/10447318.2024.2327198?utm_source=chatgpt.com)

This work builds cognitive-load assessment using:

* EEG  
* eye tracking  
* facial information

with a multimodal neural architecture.

It is directly relevant to your:

Multimodal Observation  
        ↓  
Latent Cognitive State

problem.

---

### **Paper 7**

### [**Leveraging Privileged Multimodal Data to Model Cognitive States in an Interactive Learning Platform**](https://educationaldatamining.org/edm2026/proceedings/2026.EDM.full-papers.226/index.html?utm_source=chatgpt.com)

**Sonmez Unal et al. — EDM 2026**

This may actually be the **closest current paper to one component of MCI-1**.

The paper starts with the observation that typical ITS models rely on:

* correctness  
* response time  
* behavioral logs

which are only indirect evidence of cognition.

It then uses richer modalities such as:

* think-alouds  
* written action descriptions

during training to improve cognitive-state modeling, while using cheaper behavioral data at inference.

That is highly relevant to UCI because it addresses the real-world problem:

> You may not always have all modalities at runtime.

I would consider this **mandatory reading**.

---

### **Paper 8**

### [**Multimodal Learning Analytics for Predicting Student Collaboration Satisfaction in Collaborative Game-Based Learning**](https://www.educationaldatamining.org/edm2024/proceedings/2024.EDM-long-papers.19/?utm_source=chatgpt.com)

**Acosta et al. — EDM 2024**

This paper combines:

* facial information  
* gaze  
* head pose  
* trace logs  
* textual interaction information

and evaluates:

* individual modalities  
* multimodal architectures  
* cross-attention  
* ablations

This is extremely useful for your architecture and experimental methodology.

---

# **Layer C — Data and temporal modeling**

### **Paper 9**

### [**MUTLA: A Large-Scale Dataset for Multimodal Teaching and Learning Analytics**](https://arxiv.org/abs/1910.06078?utm_source=chatgpt.com)

This introduces synchronized:

* learning logs  
* video  
* EEG

in real learning environments.

It is important for both dataset design and multimodal alignment.

---

### **Paper 10**

### [**ES-KT-24: A Multimodal Knowledge Tracing Benchmark Dataset**](https://arxiv.org/abs/2409.10244?utm_source=chatgpt.com)

This paper extends knowledge tracing into a multimodal setting with:

* game video  
* question text  
* interaction logs

This is directly relevant to moving beyond:

correct / incorrect

toward:

multimodal learner trajectory.  
---

### **Paper 11**

### [**EduMUSE: A Multimodal Educational Dataset with Automatically Extracted Instructional Context**](https://aclanthology.org/2026.bea-1.25/?utm_source=chatgpt.com)

**Dutulescu et al. — BEA 2026**

This is more relevant to **Representation Intelligence** than learner modeling.

It studies how:

* instructional text  
* figures  
* exercises  
* contextual alignment

affect multimodal educational understanding.

It provides a strong resource for the:

Knowledge  
        ↓  
Representation

side of MCI.

---

### **Paper 12**

### [**From Heartbeats to Actions: Multimodal Learning Analytics of Cognitive and Behavior Engagement in Real Classrooms**](https://www.sciencedirect.com/science/article/pii/S0959475226000101?utm_source=chatgpt.com)

This recent work combines physiological and behavioral evidence to study dynamic cognitive and behavioral engagement.

It reinforces an important direction for your research:

> Cognitive state should potentially be modeled as a **trajectory**, not as an isolated classification event.

---

# **11\. Additional papers I strongly recommend**

These are not all equally close to the exact MCI project, but they are strategically useful.

### [**Multimodal Representation Learning Survey**](https://arxiv.org/abs/2302.00389?utm_source=chatgpt.com)

Useful for:

* multimodal transformers  
* multimodal pretraining  
* alignment  
* representation learning

### [**Lessons Learnt from a Multimodal Learning Analytics Deployment In-the-Wild**](https://arxiv.org/abs/2303.09099?utm_source=chatgpt.com)

Very important for the actual UCI product reality:

* sensors  
* privacy  
* consent  
* deployment complexity  
* missing/noisy data

It synthesizes lessons from a two-year deployment involving 399 students and 17 educators.

### [**Exploring the Effect of Student Confusion in Massive Open Online Courses**](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/JEDM2016-8-1?utm_source=chatgpt.com)

Interesting because it models confusion from behavioral and textual traces rather than direct physiological sensing.

This is closer to what UCI may realistically deploy.

### [**Multimodal Graph Learning for Student Engagement Prediction**](https://www.sciencedirect.com/science/article/pii/S1566253524000022?utm_source=chatgpt.com)

Useful if we decide to investigate graph-based multimodal fusion.

---

# **12\. The biggest research discovery: the exact end-to-end dataset does not exist**

This is the important conclusion.

I have **not found a public dataset that simultaneously contains**:

Natural language explanation  
\+  
Sketch / diagram  
\+  
Interaction trajectory  
\+  
Temporal history  
\+  
Concept-level grounding  
\+  
Cognitive-state labels  
\+  
Uncertainty labels  
\+  
Repeated longitudinal observations  
\+  
Different knowledge representations  
\+  
Intervention selection  
\+  
Post-intervention learning outcomes

Existing datasets usually look like:

Dataset A  
text \+ interaction

or:

Dataset B  
video \+ EEG

or:

Dataset C  
speech \+ digital pen

or:

Dataset D  
content text \+ images \+ questions

or:

Dataset E  
behavior trajectory \+ correctness

But the UCI/MCI loop is:

MULTIMODAL EVIDENCE  
        ↓  
COGNITIVE STATE  
        ↓  
UNCERTAINTY  
        ↓  
CONCEPT GROUNDING  
        ↓  
REPRESENTATION DECISION  
        ↓  
INTERVENTION  
        ↓  
OUTCOME  
        ↓  
STATE UPDATE

I do not see a public benchmark that covers that entire chain.

And that is probably where the genuine novelty begins.

---

# **13\. This suggests a much stronger research strategy**

Instead of trying to train one massive model from scratch:

## **Phase 1 — Public benchmark research**

Use:

Math Data Corpus  
\+  
DataShop  
\+  
MUTLA  
\+  
EdNet  
\+  
EduMUSE

to investigate separate components.

### **Study A**

Multimodal Fusion→Cognitive State

### **Study B**

Temporal Interaction→State Trajectory

### **Study C**

CrossModal Agreement/Disagreement→State Uncertainty

### **Study D**

Concept+State→Representation Choice

---

# **14\. Then create the missing dataset yourself**

This is where I think the semester project could become genuinely original.

Build a **small but carefully controlled MCI Dataset**.

Not thousands of students.

Even:

30–100 participants

could be useful for a semester-scale exploratory study if the experimental design and annotation quality are strong.

The collection could look like:

CONCEPTUAL TASK

        │  
        ▼

Student explains concept  
        │  
        ├──────────────► TEXT / SPEECH  
        │  
        ▼

Student draws representation  
        │  
        ├──────────────► SKETCH / DIAGRAM  
        │  
        ▼

Student solves problem  
        │  
        ├──────────────► INTERACTION TRAJECTORY  
        │  
        ▼

Student answers question  
        │  
        ├──────────────► PERFORMANCE  
        │  
        ▼

System chooses representation  
        │  
        ▼  
┌─────────────┬─────────────┬─────────────┐  
│ TEXT        │ DIAGRAM     │ INTERACTIVE │  
│ EXPLANATION │             │ EXAMPLE     │  
└─────────────┴─────────────┴─────────────┘  
        │  
        ▼

POST-INTERVENTION TEST  
        │  
        ▼

LEARNING OUTCOME

This dataset would contain something that the existing datasets largely lack:

> **The causal connection between inferred state, chosen representation, and resulting cognitive outcome.**

That is extremely valuable.

---

# **15\. The research opportunity becomes much clearer**

I now think the strongest research question may not simply be:

> "Can multimodal learning predict cognitive state?"

That problem is already being actively studied.

A stronger question for you is:

# **Can multimodal evidence be transformed into a concept-grounded, temporally persistent and uncertainty-aware cognitive representation that improves the selection of subsequent knowledge representations?**

Formally:

O1:t​→Zt​→S^t​→Rt​→Yt+1​

Where:

* O1:t​: multimodal observations  
* Zt​: learned multimodal representation  
* S^t​: inferred cognitive state  
* Rt​: selected representation  
* Yt+1​: learning outcome

The interesting contribution is not necessarily any individual component.

It is the **bridge**.

---

# **16\. The real research gap I would now formulate**

After this scan, I would formulate the gap as follows:

> Existing Multimodal Learning Analytics research demonstrates that heterogeneous behavioral, visual, linguistic and physiological signals can provide complementary evidence about learning and cognitive processes. However, available research and datasets remain fragmented across sensing modalities, isolated prediction tasks and short-term outcomes. There is limited work on converting multimodal observations into a temporally evolving, concept-grounded and uncertainty-aware cognitive state that can directly drive decisions about how knowledge should be represented to the learner. Likewise, there is no clear public benchmark that closes the complete loop from multimodal perception through cognitive-state inference to adaptive representational intervention and observed outcome.

The existing literature supports the individual pieces—multimodal state modeling, fusion, temporal traces, cognitive load and adaptive educational systems—but the complete closed loop remains fragmented.

---

# **17\. Why this is important specifically for UCI**

This is where the research becomes strategically valuable.

UCI already contains the architectural intention:

Human Interaction  
        ↓  
World State  
        ↓  
Cognitive State  
        ↓  
Representation Intelligence  
        ↓  
Cognitive Surface

The architecture already identifies multimodal perception becoming durable cognitive state as an open research frontier, and Representation Intelligence as a system that should produce inspectable representation plans rather than simply generating arbitrary UI.

Your MCI research could provide the missing scientific bridge:

         CURRENT GAP

Multimodal Input             Cognitive Surface  
       │                           ▲  
       │                           │  
       ▼                           │  
   ???????? ────────────────────────┘

MCI becomes:

Multimodal Input  
        ↓  
Multimodal Evidence Model  
        ↓  
Concept-Grounded Representation  
        ↓  
Temporal Cognitive State  
        ↓  
Uncertainty \+ Calibration  
        ↓  
Representation Intelligence  
        ↓  
Cognitive Surface  
        ↓  
Outcome  
        ↓  
New Evidence  
        ↺

That is directly relevant to the UCI direction rather than being an unrelated academic project.

---

# **18\. My strongest recommendation**

I would **not** make the semester project:

> "Build a multimodal learner-state classifier."

Too ordinary.

I would instead define the project as:

# **MCI-1: Multimodal Cognitive State Representation for Adaptive Knowledge Presentation**

### **Central research question**

> **Can heterogeneous multimodal evidence—particularly linguistic explanation, visual representation and interaction trajectory—be integrated into a temporally grounded and uncertainty-aware representation of learner cognitive state that supports better selection of subsequent knowledge representations than unimodal or mastery-only approaches?**

---

## **The project would have three concrete research contributions**

### **Contribution 1**

### **Multimodal Cognitive Representation**

Learn:

Zt​=f(Text,Visual,Interaction,History)

---

### **Contribution 2**

### **Cross-modal Cognitive Consistency**

Investigate:

Agreement(Text,Diagram,Behavior)

and:

Disagreement(Text,Diagram,Behavior)

as possible evidence about:

* unstable understanding  
* misconception  
* uncertainty  
* partial knowledge

This is the area I personally find **most promising for originality**.

---

### **Contribution 3**

### **State-Aware Representation Selection**

Compare:

Fixed representation

vs:

Mastery-only adaptation

vs:

Multimodal cognitive-state adaptation

Then test:

Which representation→better learning outcome?   
![][image1]

# **1\. The Core Context: What This Research Is Actually About**

The research should not be framed merely as:

> “Can we use multimodal learning to detect whether a student is confused?”

That is too narrow.

The deeper problem comes directly from the direction of **Universal Cognitive Infrastructure (UCI)**.

UCI is moving toward a persistent cognitive environment in which teaching, explanation, exploration, interaction, memory, and knowledge manipulation occur on a shared **Cognitive Surface**. The architecture already treats frames, narration, interaction, durable learner state, world state, representation planning, and multimodal cognitive objects as part of the broader substrate.

The immediate product experience can be understood as a continuous teaching-and-thinking loop.

A concept is not simply displayed as a static lesson.

Instead:

Knowledge / Curriculum / Source  
            ↓  
      Teaching trajectory  
            ↓  
      Cognitive Frames  
            ↓  
 Voice explanation \+ Cognitive Surface  
            ↓  
      Human interaction  
            ↓  
 New evidence about understanding  
            ↓  
      Adapted continuation

The Cognitive Frame architecture already separates spoken teaching from the minimal persistent visual representation on the surface. The board is not intended to become an endlessly growing document; rather, teaching can be carried through narration while the surface retains the visual and interactive structures that deserve persistent cognitive attention.

This creates a much deeper opportunity.

---

# **2\. The Actual Product Situation**

Imagine the system is teaching a concept.

The user is moving through a planned cognitive trajectory:

Frame 1  
   ↓  
Frame 2  
   ↓  
Frame 3  
   ↓  
Frame 4  
   ↓  
Frame 5

Each frame may contain a synchronized combination of:

* voice explanation,  
* text,  
* diagrams,  
* images,  
* equations,  
* spatial structures,  
* examples,  
* interactive elements,  
* simulations,  
* source material,  
* and persistent cognitive objects.

The learner is listening and interacting with the Cognitive Surface.

Then, in the middle of the explanation, the learner says:

> “Wait. I don't understand why this happens.”

Or:

> “Can you show me visually?”

Or:

> “What does this connect to?”

Or:

> “I understand the formula, but I don't understand what it actually means.”

At that moment, something important happens.

The learner has **diverted from the planned teaching trajectory**.

But this should not simply create a new isolated chat conversation.

It should become part of the same persistent cognitive process.

---

# **3\. The Diversion Problem**

The system has to understand:

### **Where were we?**

### **What was being taught?**

### **What representation was currently being used?**

### **What had already been established?**

### **What exactly caused the interruption?**

### **Is the learner asking for clarification, an alternative representation, a deeper explanation, or an entirely different conceptual branch?**

### **What should be preserved from the current trajectory?**

### **What should change?**

And, critically:

### **How should the system return to the original trajectory without making the learner feel that the conversation has been reset?**

Conceptually:

                        MAIN TEACHING TRAJECTORY

Frame 1 ─── Frame 2 ─── Frame 3 ─── Frame 4 ─── Frame 5  
                            │  
                            │  
                            ▼  
                      USER INTERRUPTS  
                            │  
                            ▼  
                   "I don't understand"  
                            │  
                            ▼  
                    COGNITIVE DIVERSION  
                            │  
              ┌─────────────┼─────────────┐  
              ▼             ▼             ▼  
        Clarification   Visualization   Example  
              │             │             │  
              └─────────────┼─────────────┘  
                            ▼  
                     UPDATED STATE  
                            │  
                            ▼  
                  RETURN / REPLAN / CONTINUE  
                            │  
                            ▼  
                       Frame 4'  
                            │  
                            ▼  
                       Frame 5'

This is where the research becomes highly relevant to UCI.

The current architecture already points toward first-class cognitive branching, durable state, interruption handling, and replayable event histories, but the full **Cognitive Branch** primitive is explicitly still a research frontier rather than a completed cognitive runtime capability.

So the research should not assume that branching itself is already solved.

Instead, multimodal cognitive perception can help answer:

> **What kind of branch should occur, why did it occur, what cognitive state triggered it, and how should the system continue afterward?**

---

# **4\. The Core Problem**

## **Persistent cognitive systems can observe a human through many forms of interaction, but they lack a reliable mechanism for transforming those heterogeneous observations into a calibrated, temporally persistent understanding of what is cognitively happening and using that understanding to determine what should happen next.**

A learner does not communicate understanding through a single channel.

Understanding may appear through:

Voice  
\+  
Language  
\+  
Questions  
\+  
Interaction patterns  
\+  
Timing  
\+  
Corrections  
\+  
Drawings  
\+  
Annotations  
\+  
Spatial manipulation  
\+  
Images and visual artifacts  
\+  
Problem-solving trajectories  
\+  
History of previous interactions

The problem is not merely collecting these signals.

The deeper problem is:

> **How do we transform them into a persistent representation of the learner's evolving cognitive situation?**

For example:

Voice:  
"I understand it."

But the learner's interaction trajectory may show:

Repeated retries  
→ incorrect transformation  
→ hesitation  
→ request for a simpler example

Or the learner may say:

> “I don't understand.”

But the actual difficulty may be very different.

They may be struggling with:

* a prerequisite concept,  
* a particular misconception,  
* an abstraction gap,  
* the current representation,  
* excessive complexity,  
* a missing visual model,  
* or a disconnect between symbolic knowledge and intuition.

Therefore:

Observable interaction  
        ≠  
Cognitive state

The system must infer, rather than assume.

And because inference can be wrong:

Cognitive inference  
        ≠  
Cognitive certainty

The system therefore needs a **calibrated and uncertainty-aware representation**.

---

# **5\. The Central Research Problem**

## **How can a persistent cognitive system perceive a human through multiple forms of interaction, construct a calibrated and temporally grounded representation of what is cognitively happening, and use that representation to decide how knowledge should be presented, externalized, manipulated, or continued next?**

This divides into three connected challenges.

---

## **Challenge 1 — Multimodal Cognitive Perception**

The system receives heterogeneous evidence:

Ot​={Lt​,Vt​,It​,Ht​}

Where:

* Lt​ \= linguistic evidence, including voice and language,  
* Vt​ \= visual evidence and artifacts,  
* It​ \= interaction trajectory,  
* Ht​ \= relevant historical context.

The question is:

> What can these signals collectively tell us that no individual modality can tell us alone?

The system should not merely concatenate modalities.

It should investigate:

Agreement  
Disagreement  
Temporal sequence  
Cross-modal dependency  
Missing evidence  
Contradictory evidence  
Confidence

For example:

Language:  
"I understand gradient descent."

Visual artifact:  
Incorrect direction of optimization.

Interaction:  
Repeatedly changes answer after seeing the graph.

Individually, these signals are incomplete.

Together, they may indicate:

Partial understanding  
\+  
symbolic familiarity  
\+  
weak conceptual grounding

But importantly, the system should represent this as an inference with uncertainty—not as unquestionable truth.

---

# **6\. Challenge 2 — Persistent Cognitive State**

The research should move beyond a static classifier:

Input → Confused

Instead:

Past trajectory  
        \+  
Current interaction  
        \+  
Multimodal evidence  
        ↓  
Persistent cognitive-state representation

Conceptually:

St​=f(St−1​,Ot​)

Where St​ is not simply:

understands / does not understand

but a structured representation potentially containing:

Current concept  
Current objective  
Estimated understanding  
Confidence  
Uncertainty  
Potential misconception  
Representation difficulty  
Interaction history  
Current teaching position  
Diversion context  
Relevant prerequisite state

This aligns directly with the UCI idea of a continuously updated world-state and cognitive identity/knowledge-state model, where history and learner state inform future system behavior.

The important research question becomes:

> **Can multimodal evidence produce a more useful cognitive-state representation than unimodal signals or conventional mastery estimates alone?**

---

# **7\. Challenge 3 — Representation Intelligence**

Even if the system correctly infers:

> “The learner is struggling.”

That alone is insufficient.

The next question is:

> **What should the system do with that knowledge?**

Suppose the current representation is:

Symbolic equation

The system might decide to transform the same underlying concept into:

Visual diagram

or:

Spatial model

or:

Interactive manipulation

or:

Simulation

or:

Concrete example

or:

Step-by-step symbolic derivation

The deeper question is therefore:

Cognitive State+Concept Structure+Current Representation+Interaction Context ⇓ Next Representation Decision

This is precisely where the existing Representation Intelligence architecture becomes strategically important.

The Representation Intelligence Agent is already conceived as a separate cognitive capability that receives concept type, learner state, source evidence, directives and constraints, and produces an inspectable **RepresentationPlan** rather than arbitrary freeform UI. Its decisions are intended to be recorded and answerable through “why this representation?”

Your research can provide a much deeper scientific foundation for the **learner-state input** to that decision.

---

# **8\. The Key Insight: The Research Connects Two Existing UCI Directions**

The architecture already has the beginnings of:

### **A. Cognitive perception and persistent state**

Human interaction  
        ↓  
Events  
        ↓  
World / learner state  
        ↓  
Memory and continuity

### **B. Representation Intelligence**

Concept  
\+  
Context  
\+  
Learner state  
        ↓  
Representation Plan  
        ↓  
Cognitive Surface

The research sits exactly between them.

                   HUMAN

                       │  
                       ▼

          MULTIMODAL INTERACTION  
       Voice • Language • Surface  
       Visual Artifacts • Trajectory

                       │  
                       ▼

       MULTIMODAL COGNITIVE PERCEPTION  
                       │  
                       ▼

       CALIBRATED COGNITIVE STATE  
       Understanding • uncertainty  
       misconception • representation need  
       current context • trajectory

                       │  
                       ▼

          REPRESENTATION INTELLIGENCE  
                       │  
                       ▼

        WHAT SHOULD HAPPEN NEXT?

       Text • Diagram • Spatial Model  
       Simulation • Interaction • Voice  
       Example • Practice • Diversion

                       │  
                       ▼

              COGNITIVE SURFACE

                       │  
                       ▼

               NEW INTERACTION  
                       │  
                       └──────────────↺

That, in my view, is the clearest definition of the research's role within UCI.

---

# **9\. The Diversion-and-Continuity Loop**

This should become one of the most important concrete scenarios for the research.

## **Normal teaching**

Teaching trajectory  
       ↓  
Frame 17  
       ↓  
Frame 18  
       ↓  
Frame 19

At Frame 18, the user says:

> “Wait, I understand the calculation, but I don't understand why the graph behaves like that.”

The system should not merely answer the sentence.

It should construct something like:

CURRENT STATE

Teaching goal:  
Understand gradient descent

Current frame:  
18

Current representation:  
Mathematical \+ graph

Observed issue:  
Symbolic understanding may exceed  
geometric understanding

Evidence:  
Voice question  
\+  
interaction history  
\+  
current concept  
\+  
previous performance

Inference:  
Possible representation mismatch

Confidence:  
0.68

The system may then create a **temporary cognitive diversion**:

MAIN TRACK  
    │  
    ├───────────────┐  
    │               │  
    ▼               ▼  
Frame 18       Visual diversion  
                    │  
                    ▼  
             Interactive landscape  
                    │  
                    ▼  
             User manipulates point  
                    │  
                    ▼  
             State updated  
                    │  
                    ▼  
                 Fold back  
                    │  
                    ▼  
               Resume Frame 19

This is conceptually aligned with the UCI research direction of a Cognitive Branch: temporary expansion that can be folded back while preserving the useful result and allowing the main trajectory to continue.

The important research problem is:

> **Can multimodal evidence determine when the system should branch, what kind of representation the branch should create, and how the result of that branch should alter continuation?**

---

# **10\. Refined Research Objective**

## **Research Objective**

> **Develop and evaluate a multimodal cognitive perception framework that integrates language and voice interaction, visual artifacts, and interaction trajectories into a temporally grounded and uncertainty-aware representation of a user's evolving cognitive context. The framework will investigate whether this representation can identify representation mismatches, support context-preserving cognitive diversions, and improve the adaptive selection of textual, visual, spatial, interactive, symbolic, or simulated knowledge representations compared with unimodal, static, heuristic, or mastery-only approaches.**

This is strong because it does not claim:

> “We will solve cognition.”

It claims something experimentally meaningful:

1. **Perceive multimodal evidence.**  
2. **Construct a structured cognitive representation.**  
3. **Maintain it over time.**  
4. **Model uncertainty.**  
5. **Detect when the current teaching trajectory or representation may be inadequate.**  
6. **Choose an alternative representation or cognitive diversion.**  
7. **Observe the outcome.**  
8. **Update the state and continue.**

---

# **11\. What We Eventually Aim to Produce**

The eventual outcome should be a research and prototype capability:

# **A Multimodal Cognitive Adaptation Loop**

            ┌──────────────────────────┐  
             │   TEACHING TRAJECTORY    │  
             │                          │  
             │ Frames \+ Voice \+ Surface │  
             └────────────┬─────────────┘  
                          │  
                          ▼  
              ┌──────────────────────┐  
              │ MULTIMODAL EVIDENCE  │  
              │                      │  
              │ Voice / Language     │  
              │ Visual Artifacts     │  
              │ Interaction          │  
              │ Temporal History     │  
              └───────────┬──────────┘  
                          │  
                          ▼  
              ┌──────────────────────┐  
              │ COGNITIVE PERCEPTION │  
              │                      │  
              │ Fusion               │  
              │ Alignment            │  
              │ Cross-modal signals  │  
              │ Temporal modeling    │  
              └───────────┬──────────┘  
                          │  
                          ▼  
              ┌──────────────────────┐  
              │ COGNITIVE STATE      │  
              │                      │  
              │ Concept grounding    │  
              │ Understanding        │  
              │ Uncertainty          │  
              │ Misconception        │  
              │ Representation need  │  
              └───────────┬──────────┘  
                          │  
                ┌─────────┴─────────┐  
                │                   │  
                ▼                   ▼  
         CONTINUE TRACK       CREATE DIVERSION  
                │                   │  
                │                   ▼  
                │           Representation change  
                │                   │  
                │                   ▼  
                │             Interaction  
                │                   │  
                └───────────┬───────┘  
                            ▼  
                      UPDATE STATE  
                            │  
                            ▼  
                    REPLAN / RESUME  
                            │  
                            ↺  
---

# **12\. The Specific Research Deliverable**

The semester project should ultimately aim to produce:

## **MCP-RI: Multimodal Cognitive Perception and Representation Intelligence**

A prototype framework containing four layers.

### **Layer 1 — Multimodal Evidence Modeling**

Input:

* spoken/language interaction,  
* visual artifacts,  
* user interactions,  
* temporal trajectories.

Output:

Zt​=Multimodal Representation

---

### **Layer 2 — Cognitive State Estimation**

Infer:

St​={Concept,Understanding,Uncertainty,Potential Misconception,Representation Need,Context}

With explicit confidence rather than pretending the state is certain.

---

### **Layer 3 — Representation Decision**

Given:

St​+Concept+Goal+Current Context

choose:

Continue  
Explain differently  
Visualize  
Externalize spatially  
Create interactive representation  
Create simulation  
Provide example  
Ask diagnostic question  
Practice  
Branch temporarily  
Return to main trajectory  
---

### **Layer 4 — Outcome and Update**

Observe:

User response  
\+  
interaction  
\+  
performance  
\+  
new multimodal evidence

Then update:

St+1​

This creates the closed loop.

---

# **13\. The Most Effective Final Problem Statement**

## **Problem Statement**

> **Universal Cognitive Infrastructure requires more than the ability to generate explanations or respond to user queries. To adapt meaningfully over time, it must be able to perceive evidence distributed across voice, language, visual artifacts and interaction trajectories; transform that evidence into a persistent, concept-grounded and uncertainty-aware representation of the user's evolving cognitive context; and use that representation to determine how knowledge should be presented, externalized, manipulated or continued next.**

> **The challenge becomes particularly important when a learner interrupts an ongoing teaching trajectory. The system must distinguish a simple question from evidence of a deeper representational or conceptual mismatch, create an appropriate contextual diversion when necessary, preserve continuity with the original learning trajectory, and adapt its subsequent representation based on what occurred during the diversion. Existing systems typically treat these events as isolated prompts or rely on static mastery estimates, leaving a major gap between multimodal interaction and persistent, state-aware representation decisions.**

---

# **14\. The Most Effective Final Objective**

## **Research Objective**

> **To develop and evaluate a Multimodal Cognitive Perception and Representation Intelligence framework that integrates language and voice interaction, visual artifacts and interaction trajectories into a temporally persistent, concept-grounded and uncertainty-aware representation of a learner's cognitive context. The research will investigate whether this representation can improve the detection of cognitive and representational mismatches, enable context-preserving diversions from an ongoing teaching trajectory, and support more effective selection of textual, visual, spatial, symbolic, interactive or simulated representations than unimodal, static, heuristic or mastery-only approaches.**

---

# **15\. The North-Star Research Question**

## **How can a persistent cognitive system transform multimodal evidence of human interaction into a calibrated representation of what is cognitively happening, and use that representation to continuously decide what knowledge representation, cognitive action, diversion, or continuation should occur next?**

That is, in my opinion, the strongest formulation.

It is:

* fundamentally multimodal,  
* deeply connected to AI/ML/DL,  
* expandable toward agents and RL,  
* directly connected to persistent systems,  
* relevant to representation learning,  
* experimentally approachable,  
* and genuinely valuable to UCI.

Most importantly, it does **not** attempt to research the entirety of UCI.

It isolates one critical loop:

PERCEPTION  
    ↓  
STATE  
    ↓  
DECISION  
    ↓  
REPRESENTATION  
    ↓  
INTERACTION  
    ↓  
UPDATED STATE

That loop can become an actual deep research capability inside Universal Cognitive Infrastructure.

---

# **Research Papers — Original Links**

* [Multimodal Machine Learning: A Survey and Taxonomy](https://arxiv.org/abs/1705.09406?utm_source=chatgpt.com)  
* [A Review on Data Fusion in Multimodal Learning Analytics and Educational Data Mining](https://doi.org/10.1002/widm.1458?utm_source=chatgpt.com)  
* Multimodal Learning Analytics: Description of Math Data Corpus for the MMLA Grand Challenge  
* Unraveling Students' Interaction Around a Tangible Interface Using Multimodal Learning Analytics  
* [Multimodal Learning Analytics to Investigate Cognitive Load During Online Problem Solving](https://doi.org/10.1111/bjet.12958?utm_source=chatgpt.com)  
* Enhancing Online Learning: A Multimodal Approach for Cognitive Load Assessment  
* [Leveraging Privileged Multimodal Data to Model Cognitive States in an Interactive Learning Platform](https://educationaldatamining.org/edm2026/proceedings/2026.EDM.full-papers.226/index.html?utm_source=chatgpt.com)  
* [Multimodal Learning Analytics for Predicting Student Collaboration Satisfaction in Collaborative Game-Based Learning](https://educationaldatamining.org/edm2024/proceedings/2024.EDM-long-papers.19/?utm_source=chatgpt.com)  
* [MUTLA: A Large-Scale Dataset for Multimodal Teaching and Learning Analytics](https://arxiv.org/abs/1910.06078?utm_source=chatgpt.com)  
* [ES-KT-24: A Multimodal Knowledge Tracing Benchmark Dataset](https://arxiv.org/abs/2409.10244?utm_source=chatgpt.com)  
* [EduMUSE: A Multimodal Educational Dataset with Automatically Extracted Instructional Context](https://aclanthology.org/2026.bea-1.25/?utm_source=chatgpt.com)  
* From Heartbeats to Actions: Multimodal Learning Analytics of Cognitive and Behavior Engagement in Real Classrooms  
* [Multimodal Representation Learning: A Survey](https://arxiv.org/abs/2302.00389?utm_source=chatgpt.com)  
* [Lessons Learnt from a Multimodal Learning Analytics Deployment In-the-Wild](https://arxiv.org/abs/2303.09099?utm_source=chatgpt.com)  
* Exploring the Effect of Student Confusion in Massive Open Online Courses

# **Datasets — Original Links**

* [MUTLA Dataset / Paper](https://arxiv.org/abs/1910.06078?utm_source=chatgpt.com)  
* Math Data Corpus for the MMLA Grand Challenge  
* [CMU DataShop — Multimodal Interface for Solving Equations](https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=501&utm_source=chatgpt.com)  
* [EdNet](https://github.com/riiid/ednet?utm_source=chatgpt.com)  
* Open University Learning Analytics Dataset (OULAD)  
* [EduMUSE Dataset](https://huggingface.co/datasets/upb-nlp/EduMUSE?utm_source=chatgpt.com)  
* [ES-KT-24 Dataset and Benchmark](https://arxiv.org/abs/2409.10244?utm_source=chatgpt.com)  
* [PE-HRI Dataset](https://zenodo.org/records/4633092?utm_source=chatgpt.com)  
* BBBD: Brain, Body, and Behavior Dataset  
* [DAiSEE: Dataset for Affective States in E-Environments](https://arxiv.org/abs/1609.01885?utm_source=chatgpt.com)  
* [NUS Multi-Sensor Presentation Dataset](https://sites.google.com/site/yongkangwong/datasets?utm_source=chatgpt.com)  
* [SOPHIAS Dataset](https://arxiv.org/abs/2601.07576?utm_source=chatgpt.com)

The strongest semester-scale framing is therefore **not “multimodal learning for education”** in general. It is:

> **Building the perceptual and decision-making loop through which a persistent cognitive system can understand when its current representation of knowledge is failing for a particular learner, create the right contextual diversion, learn from that interaction, and continue the cognitive trajectory with preserved continuity.**

[image1]: <data:image/png;base64,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JuGcXkg4SzhLOKfG3LwR4phIOMdmbr4lCgnnY5uEc/JNwjm9kHCWcJZwTo25eSOOTkCjx0g4x2puviUKCedjm4Rz8k3COb2QcJZwlnBOjbl5I46Oump8RcI5VnPzLVFIOB/bJJyTbxLO6YWEs4SzhHNqzM0bv9KvX78xqbDbb799hutLpLnHlZZIOMdmbr4lCgnnY5uEc/JNwjm9kHCWcJZwTo25eeNXXAGaLLvjjjvmub5EmntcaYmEc2zm5luikHA+tkk4J98knNMLCWcJZwnn1JibN37FFaDx2KOPPvoqw+nTp69y4yozCOgpV1999VjXX11zjystqapwrl2njteocWMzfeZZZ5WLj7TZs2eX8yXann7mGa8x9qd169bl4hJhbr4liuoI53bt24enbUV4+cCBXq3atculTYXNmjWrnC8Rlo7CmXncPpT/JzVrdsxroKpWp25dr2vXruX8iTYJ5/SiusK5fYcO3rndu5t62o2ryKZNm+bNnjPHm/jYY1F+1E/l0qbC0lE4dz/vvHK+Yxnrho6dOpXzx2LpKJyZB9bcOL+amzd+haLzueeeWzxw4MCHXDF6LJs5c+Y6huvXrz/kxrl21113LWD4yCOPTL/++uvHu/GLFi3aO2DAgAddf6zmHldaUlXh3KBhQ++sLl3M9IIFC8rFR1q8wjknJ6ec71hG4ez6EmluviWK6gjnTZs2hUXy/Pnzy8WnwniDc32JtnQUzvUbNPDGjx9vpi+55JJq5z+Eaznf0axDx45e13POKeevqkk4pxfVEc4TJ040opnTsQjnqRDNt9x6azk/TcI5ep9c37Es04RzVfIg2fbGG2+U88Vjbt74FYpOVzjfd999z+/cufO/e/bs+ZzzEMZ/wvRnuO99cvPNN096+umn56Pu/xDn9ctQ/CHoind5njmPZf+zfPnywLZt2z7gPOOYBvXCF1Y4z5kzZwvXZbfpCmfM565du/Ztu07WKatWrTrAMHJ+165d/81K4cwMuODCC70VK1aYljJkmHfZZZd527dvN/EvvPiid9nll3tr1qwJp+910UUeMt9buXKld9ttt5lWbJwsr9u553rNW7Twel98sXfvvfd6XbCtp55+2nvwwQe9l15+2atbr56p8LntoTfdZITzlVdd5XU+/XRv69at3urVq72rMI8T6r322mtGfFXnJuDmW6KojnDG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>