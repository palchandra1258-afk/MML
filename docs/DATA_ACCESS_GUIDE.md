# MCP-RI Dataset Access Guide

This guide records verified access instructions and the current acquisition state. EdNet KT1 and question-content archives have now been downloaded from the official links, preserved under `data/raw/ednet/`, and checked for ZIP member CRC integrity and SHA-256. Check current terms before use and do not mirror or redistribute data unless the license explicitly permits it.

## 1. CMU DataShop: equation-solving project

**Official entry point:** [CMU DataShop](https://pslcdatashop.web.cmu.edu/)  
**Project reference from literature:** [Project 33](https://pslcdatashop.web.cmu.edu/Project?id=33)  
**Official account/access instructions:** [DataShop access help](https://datashop.dev.datashop.org/help?page=access)  
**Official API documentation:** [DataShop Public API PDF](https://pslcdatashop.web.cmu.edu/api/DataShop%20Public%20API-v0.41.pdf)

### Procedure

1. Sign in through university/InCommon or Google SSO and complete DataShop account registration.
2. Search the project title **“A Multimodal Interface for Solving Equations”** and inspect each listed dataset/version. Do not assume `datasetId=501` identifies the same records as historical IDs 145/165.
3. Inspect project access status, dataset information, citation and any posted terms/acknowledgment requirements.
4. If public, use the UI export or authorized web services/API. If private, use **Request Access** and wait for PI/data-provider approval.
5. Confirm the exact transaction count and fields before selecting a modeling target. For this project, specifically check `anon_student_id`, `session_id`, `time`, `problem_name`, `step_name`, `attempt_at_step`, `outcome`, `input`/`selection`, and mapped KC columns. Confirm nonmissing counts rather than relying on the schema's possible fields.
6. Check whether separate handwriting examples, images, audio/speech recordings or problem-content files are available and linkable to transaction/session IDs. The transaction table alone does not establish media availability.
7. Save the dataset's project terms, citation, version, access date and permitted storage/use conditions with the study record.

### Verified and unresolved

DataShop's official general instructions state that a registered account can access public datasets and private datasets require PI permission. Its general API documents learner/session/time/outcome/KC-capable fields. The specific project page returned 403 to this investigation; therefore current project status, dataset-level terms, exact schema, count, media and download route are unresolved. Do not treat the prior planning note's 12,568 transactions as verified.

## 2. EdNet

**Official repository:** [riiid/ednet](https://github.com/riiid/ednet)

### Procedure and files

1. Read the repository README and license before acquisition; both were reviewed for this snapshot.
2. Choose the smallest appropriate release first: KT1 for submitted question responses; KT2 for question-solving action sequences; KT3/KT4 only when explanation/lecture/UI event types are needed.
3. The official README links the archives (KT1, KT2, KT3, KT4 and question contents) from the repository. Use those links from the README; this guide intentionally does not reproduce shortened redirect URLs.
4. For KT1, the repository documents student-specific CSV files and columns including timestamp, solving ID, question ID, submitted answer and elapsed time. Join question IDs to the released question contents table for correct answer/tags. Confirm exact archive headers after download.
5. Use student-specific file identity to group splits. Keep the question content table as metadata, not as learner observations.

### Acquired snapshot

The official README's KT1 and content links were followed without bypassing any access restriction. The resulting archives and download metadata are preserved in `data/raw/ednet/`; the raw ZIPs were not extracted or modified. The KT1 archive is 1,201,163,816 bytes and the content archive is 173,976 bytes. Each archive passed ZIP structure and member-CRC checks; SHA-256 hashes and retrieval details are in the matching `.metadata.json` sidecars. Full actual-file validation is reported in `EDNET_DATASET_REPORT.md`, `EDNET_SCHEMA.md` and `EDNET_DATA_QUALITY_REPORT.md`.

### License and restrictions

The repository states **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)** for research purposes. Attribute the source and do not use commercially without separate permission. The downloaded snapshot is for non-commercial research and must not be redistributed as though it were unrestricted. Check the current repository license and terms at the time of use.

## 3. Math Data Corpus

**Documentation:** [ICMI 2013 corpus paper](https://projet.liris.cnrs.fr/imagine/pub/proceedings/ICMI-2013/icmi/p563.pdf) and [ICMI challenge page](https://icmi.acm.org/2013/index.php?id=challenges).

The corpus paper describes time-synchronized speech, digital pen and images, with initial problem segmentation, group problem correctness and writing representation-content codes. It says corpus resources were made available to data-driven challenge participants after signing a collaborator agreement. The challenge page describes contacting workshop organizers for the agreement. These are historical procedures; verify current rights-holder contact, agreement, files, retention/storage and publication permission before attempting access. No unrestricted direct download was verified.

## 4. EduMUSE

**Dataset card/files:** [Hugging Face upb-nlp/EduMUSE](https://huggingface.co/datasets/upb-nlp/EduMUSE)  
**Paper/code:** [ACL Anthology paper](https://aclanthology.org/2026.bea-1.25/) and [official project repository](https://github.com/upb-nlp/BEA-EduMUSE).

The dataset card exposes raw JSON and image archives and lists **CC BY 4.0**, with attribution required for OpenStax source content and the dataset's multimodal alignment. The card reports a 1.13 GB total snapshot; an individual JSON file page reports 263 MB. Treat those as page-reported file sizes, which can change. No learner-level data are included, so it is for content/representation work, not the first learner-response model.

## 5. MUTLA

**Paper:** [arXiv:1910.06078](https://arxiv.org/abs/1910.06078). The paper describes a public access pointer (`tinyurl.com/SAILdata`) and time-synchronized learning records, video and EEG. The redirected current files, access terms/license, exact complete schema and label definitions were not verified in this investigation. Before use, check whether the access link still works, whether a registration/agreement is required, whether the data can be stored on the intended compute, and which annotations are actually supplied. Do not assume “publicly accessible” means an open license or commercial permission.

## 6. OULAD

**Open University source:** [OU Analyse open dataset page](https://analyse.kmi.open.ac.uk/open_dataset)  
**UCI record/download and license:** [UCI Machine Learning Repository OULAD entry](https://archive.ics.uci.edu/dataset/349/open%2Buniversity%2Blearning%2Banalytics%2Bdataset)  
**Data descriptor:** [Scientific Data paper](https://doi.org/10.1038/sdata.2017.171)

The OU Analyse endpoint currently redirects to the service website, while the UCI entry provides files and lists **CC BY 4.0**. The package comprises relational CSV tables, including VLE daily interaction summaries, assessment definitions/results, student/course metadata. It has no documented per-question response stream for constructing the EdNet-style next-answer target. Use it for course-level outcome experiments after verifying the downloaded README/schema and attribution requirements.

## Access decision log template

Before a new dataset is downloaded (or when EdNet's acquired snapshot is updated), record:

| Field | Value to capture |
|---|---|
| Dataset/version and canonical URL | Exact dataset and snapshot/release |
| Access date and account/approval basis | Public login, PI approval, agreement, or license |
| License/terms | Exact license and additional conditions |
| Intended research use | Noncommercial/commercial, publication, derivative work |
| Modalities and files | Verified file inventory, not title-based assumptions |
| Labels and schema | Exact fields, definitions, missingness and units |
| Identifiers/time | Pseudonymous IDs, session semantics, time zone/order |
| Storage/retention | Approved local or institutional storage and deletion plan |
| Citation/redistribution | Required citation and whether derived/raw data may be shared |

Do not place credentials, access tokens or participant data in the repository.
