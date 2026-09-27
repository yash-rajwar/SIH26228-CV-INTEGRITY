# C2 — Data Integrity Research

## Document Metadata

| Field | Value |
|---|---|
| Project | SIH 2026 PS 26228 — *Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines* |
| Problem Statement | PS 26228 |
| Cell | C2 |
| Domain | Data Integrity |
| Research Version | V2 / Artifact lineage C2-V2-001 |
| Research Date | 2026-09-23 |
| Public Research Edition | 2026-09-29 |
| Document Purpose | Public-facing research dossier for the GitHub research repository, evaluator review, and citation from the final SIH research/reference material |
| Status | **C2 research synthesis; implementation and validation remain separately gated.** |

> **Mandatory interpretation rule:** An anomaly, hash match/mismatch, or statistical flag is evidence for review; it is **not proof of malicious intent**. An unavailable assessment result is **not** a clean result.

---

## 1. Research Objective

C2 investigates the integrity of contributed computer-vision datasets and related data artefacts, especially datasets represented through COCO JSON and YOLO text formats. The research separates three different questions that must not be conflated:

1. **Can the contributed data be checked for structural, statistical, duplicate, or image-content anomalies?**
2. **Can those anomalies be represented as reproducible, analyst-reviewable evidence?**
3. **Can malicious intent be proven from those anomalies alone?**

C2 addresses the first two questions where the evidence supports doing so. The third generally falls outside what a data-integrity signal can establish by itself.

C2 therefore treats dataset integrity as a layered evidence problem rather than a binary “safe/unsafe” classification. A structurally invalid annotation can be deterministically identified. An exact duplicate can be deterministically grouped by file hash. A perceptual-hash cluster can establish image similarity relationships. A source-concentration statistic can quantify skew. None of those facts, by itself, establishes why the condition exists.

The core boundary is:

**Anomaly / hash mismatch / statistical flag ≠ proof of malicious intent.**

The current V2 packet records no project-specific detection-rate, false-positive-rate, or wall-clock benchmark for any C2 method. All experiments described below are pre-registered evaluation plans unless explicitly marked otherwise.

---

## 2. C2 Scope and Boundaries

### 2.1 In scope

C2 covers evidence about contributed data, including:

- COCO and YOLO annotation integrity;
- image-file and pixel-level integrity;
- malformed annotation records and hostile-input handling;
- bounding-box, segmentation, and task-specific geometry rules where specified;
- exact duplicate evidence;
- near-duplicate relationship evidence;
- class-distribution and source-stratified statistics;
- joint class co-occurrence and spatial-layout statistics as a prototype;
- acquisition/image-content anomalies;
- contributor/source concentration evidence, subject to identity-assurance limits;
- trigger-related image analysis only where the method and evidence actually support it;
- reproducible, team-controlled corruption/manipulation scenarios for evaluation.

### 2.2 Out of scope

C2 does not own:

- final model-security or model-backdoor conclusions — **C3**;
- cryptographic provenance design and trusted contributor identity — **C4**;
- project-wide assurance semantics, risk scoring, or the final meaning assigned to evidence — **C5**;
- deployment engineering ownership or project-wide runtime validation — **C6**;
- mission/operational domain definition — **C1**.

C2 may produce evidence consumed by those cells, but that is a **handoff/dependency**, not evidence that an integration has been implemented.

### 2.3 Cross-cell handoff summary

| Handoff | C2 provides / requires | Status in current packet |
|---|---|---|
| C2 → C3 | Explicit T05d clean-label coverage gap; possible residual-image evidence stream | Handoff defined; model-level closure not provided by C2 |
| C2 ↔ C4 | Requires Sybil-resistant source identity and provenance-related metadata before reliable T10 interpretation | Critical dependency |
| C2 → C5 | Evidence bundles must preserve states such as `UNASSESSABLE` and `SYBIL-UNRELIABLE` | Dependency defined |
| C2 ↔ C1 | Requires operational domain policy for legitimate variation, burst/video controls, sensor diversity, and analyst review budget | High-priority dependency |
| C2 → C6 | Public boundary identifies build/runtime validation as outside C2 ownership | No formal `DEP-C6-*` identifier exists in the current C2 V2 dossier |

---

## 3. PS Requirements Relevant to C2

| Requirement | C2 interpretation | Consequence |
|---|---|---|
| Offline / air-gapped operation | C2 methods must execute without cloud APIs | Dependencies and model artefacts must be pre-bundled |
| No baseline retraining | Baseline assessment must be data-only or frozen-model-assisted | Training-dependent methods are outside the baseline |
| COCO / YOLO support | Both annotation ecosystems must be handled | Parser and validation rules must be format- and task-aware |
| YOLO task variation | Detection, segmentation, pose, and OBB do not share one identical row structure | M01 scope depends on OQ-V2-007 |
| Model-agnostic constraint | C2 cannot depend on one particular deployed model architecture | Data-only evidence is preferred; frozen-model methods remain optional/prototype |
| Approximately five implementation days | Methods must be tiered by defensibility and dependency | Deterministic floor and relationship evidence are prioritized |
| Human-readable, analyst-reviewable evidence | Outputs must expose the rule, data item, relationship, or statistic behind a flag | Binary “attack detected” outputs are not acceptable substitutes |
| Public/team-controlled assets | Evaluation scenarios must be reproducible and controlled | Synthetic attack fixtures must be team-controlled |
| Reproducible scenarios | Experiment parameters and ground truth must be recorded | Planned experiments require explicit metadata and split discipline |
| Unavailable ≠ clean | Missing evidence cannot be interpreted as absence of risk | C5 ingestion must retain `UNASSESSABLE` states |
| Anomaly ≠ proof of attack | Evidence cannot silently become an intent verdict | All summaries must preserve analyst interpretation boundaries |
| ONNX / PyTorch / TorchScript support | Model-format support is not itself a C2 data-integrity requirement | Relevant only where C2 evidence is handed to model-level analysis |

---

## 4. Data Integrity Model

C2 separates dataset integrity into two primary layers because they expose different failure modes.

```text
DATA CONTRIBUTION
      |
      +--> ANNOTATION INTEGRITY --------+
      |                                 |
      +--> PIXEL / IMAGE INTEGRITY -----+--> C2 EVIDENCE
      |                                 |
      +--> SOURCE / CONTRIBUTOR CONTEXT-+
                                        |
                                        v
                              ANALYST-REVIEWABLE FINDING
```

### 4.1 Annotation Integrity

Annotation integrity concerns the machine-readable records that describe what is present in an image and where it is located. Depending on the task and format, this can include:

- image and annotation identifiers;
- category/class identifiers;
- bounding boxes;
- segmentation polygons or masks;
- `iscrowd` and related COCO fields;
- normalized YOLO coordinates;
- task-specific fields for segmentation, pose, and oriented bounding boxes;
- source/batch metadata where available.

C2 distinguishes **structural validity** from **semantic correctness**. A coordinate can violate a schema or image boundary in a way that is deterministically checkable. A structurally valid box can still surround the wrong object, use the wrong class, or otherwise be semantically incorrect. That latter problem requires additional evidence and is not solved by schema validation.

### 4.2 Pixel / Image Integrity

Pixel/image integrity concerns the actual image bytes and image-derived signals. Relevant checks include:

- exact byte identity through SHA-256;
- perceptual similarity and near-duplicate grouping;
- image acquisition statistics;
- repeated local patterns;
- visible trigger-like patches, textures, or colour shifts where a method can expose them;
- image-content or representation-space anomalies.

Pixel-level analysis is essential because an annotation file can remain perfectly valid while image content is altered.

### 4.3 Why the two layers cannot substitute for each other

A clean annotation record does not prove clean pixels. Clean-label attacks are the clearest example: the label can remain semantically correct while the image is modified to influence later training behavior.

Conversely, an image-level duplicate or acquisition check does not prove that its annotation is correct. A byte-identical image can carry a wrong class ID; a visually ordinary image can have a malformed polygon; a valid JPEG can be paired with the wrong label.

C2 therefore requires evidence to retain the layer from which it originated.

---

## 5. Threat Taxonomy

| ID | Threat | Data layer | Mechanism | Current C2 coverage | Key limitation |
|---|---|---|---|---|---|
| **T05** | Trigger-Based / Backdoor Poisoning | Primarily pixels; may interact with labels/model training | A small subset is modified with a trigger such as a patch, texture, or colour offset | T05a/b/c **PARTIALLY_SUPPORTED** through image-analysis prototypes; T05d **UNVERIFIABLE / COVERAGE GAP** | Clean-label, label-consistent attacks can preserve apparently correct annotations and evade current no-retraining/no-reference C2 methods |
| **T06** | Label Flips / Systematic Mislabeling | Annotation | Category IDs/class indices are changed randomly or systematically | **PARTIALLY_SUPPORTED** through M06; M14 is **PROTOTYPE** | Distribution-preserving swaps can evade marginal statistics |
| **T07** | Annotation Defects | Annotation; optionally image+annotation for semantic checks | Malformed coordinates, polygons, missing/invalid fields, semantically wrong boxes or labels | Structural defects **SUPPORTED** through M01 after its fixture gate; semantic checking via M05 remains **PROTOTYPE** | Structurally valid but semantically incorrect records are outside deterministic schema validation |
| **T08** | Exact / Near-Duplicate Flooding | Pixel/file | Repeated or near-identical images inflate counts, bias training, or cause leakage | Exact duplicates **SUPPORTED** through M02; near-duplicate relationships **PARTIALLY_SUPPORTED** through M03-PDQ | Similarity relationships do not establish malicious flooding; calibration is required |
| **T09** | OOD Insertion | Pixel, acquisition, source context | Images differ in domain, scene, resolution, sensor, or acquisition conditions | **PARTIALLY_SUPPORTED** through M06, M15, and optional M04 | Legitimate domain diversity can look anomalous without C1 operational policy |
| **T10** | Contributor / Source Concentration | Source metadata | One source contributes a disproportionate share, or coordinated identities distribute the same effect | **SYBIL-DEFEATABLE** | HHI, entropy, and per-source share are unreliable against identity fragmentation unless C4 supplies Sybil-resistant identity |

### T05d clean-label boundary

No method in the current C2 packet has a verified signal for T05d under the stated no-retraining, no-reference baseline. Generic trigger scans, frozen embeddings, and semantic-alignment checks must not be represented as automatic coverage of clean-label poisoning.

### T10 identity boundary

The structural problem is that concentration metrics operate on the identities they are given. If one real adversarial source can appear as multiple independent identities, source concentration can be diluted. The dossier cites FoolsGold measurements from a federated-learning setting as evidence that Sybil identities can materially alter poisoning behavior, but explicitly does **not** transfer those numerical results to COCO/YOLO object detection.

---

## 6. Evidence-Backed Research Findings

| Finding ID | Finding | Evidence class | Primary source(s) in packet | Project implication |
|---|---|---|---|---|
| **EF-01** | M01 structural validation and M02 exact hashing form the most defensible five-day deterministic floor. M01 remains gated on parser fixtures. | FACT / research synthesis | SRC-01, SRC-02, SRC-03; RED_TEAM MAJ-03 | Prioritize deterministic, traceable checks before probabilistic enrichment |
| **EF-02** | PDQ produces near-duplicate relationship evidence; it is not a validated flooding detector until project FPR-vs-threshold calibration exists. | FACT | SRC-05; RV-02; FACT-V2-009 | Record threshold and output relationships, not a binary poison verdict |
| **EF-03** | T10 contributor concentration is structurally Sybil-defeatable. | FACT with cross-domain literature support | arXiv:1808.04866; arXiv:2602.15671v1; FACT-V2-014 | Reliable T10 interpretation depends on identity assurance, not only statistics |
| **EF-04** | “Trusted metadata” must be explicit. V2 requires `TRUSTED / UNTRUSTED / UNAVAILABLE`; path/filename identity is always `UNTRUSTED`. | FACT / correction | RED_TEAM MAJ-04; CORR-T10-03 | M06 T10 evidence is `SYBIL-UNRELIABLE` unless C4 supplies trusted identity |
| **EF-05** | ClipGrader’s 91% accuracy / 1.8% FPR comes from a trained/adapted setup; the paper reports ~11% accuracy in its unseen-class zero-shot experiment. | FACT / citation correction | SRC-10; RED_TEAM CRIT-01; FACT-V2-010 | SRC-10 is context only for M05; the headline trained numbers are not C2 frozen-mode performance |
| **EF-06** | No C2 method has verified T05d clean-label coverage under the baseline constraints. | FACT / negative evidence | SRC-08, SRC-14; FACT-V2-016 | Preserve a formal coverage gap and handoff to C3/C4 |
| **EF-07** | A version-pinned public COCO subset is not automatically a clean reference. | FACT / rejected assumption | SRC-09; RED_TEAM MAJ-01; CONTRA-V2-003 | M11’s original sourcing strategy is rejected and the method remains blocked |
| **EF-08** | The packet contains no project-specific detection rate, FPR, or timing result for any C2 method. | FACT / project evidence status | FACT-V2-008, -010, -013 | Literature results must remain visually and semantically separate from project evidence |
| **EF-09** | A five-day path is feasible for Tiers 1–2; T05d closure, M11 reference sourcing, and unprepared frozen-model methods are not. | INFERENCE | V2 synthesis §7 | Sequence by dependency and evidence strength |
| **EF-10** | Citation/reverification items remain open, including ClipGrader review status, TellTale object-detection scope, and disputed COCO-noise figures. | FACT / open verification | REVERIFY queue | Reference register is not fully closed |

---

## 7. Method Research

### M01 — Structural / Geometry Validation + Hostile-Input Parser Hardening

**Purpose**  
Validate annotation structure and geometry while hardening the parser against adversarially large or malformed inputs.

**Threats addressed**  
T07 structural/geometry defects; gross T06 schema violations.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
COCO JSON and/or task-appropriate YOLO annotation files plus image dimensions where geometry checks require them.

**Reference requirement**  
No clean dataset reference. Rules derive from the relevant format/task specification.

**C2 status**  
**BUILD AFTER EXP-C2-V1-001 PARSER FIXTURE PASS [P0].**

**Evidence basis**  
COCO API/format semantics, COCO area clarification, and Ultralytics YOLO format documentation.

**Legitimate false-positive conditions**  
Border-touching boxes; valid empty images; task-specific empty segmentation in detection-only contexts; `iscrowd=1`; segmentation/pose/OBB-specific structures; geometry rules applied without determining task variant.

**Known failure / evasion cases**  
Any deliberately structurally valid annotation can evade M01. Clean-label poisoning is a complete blind spot.

**Project-specific evidence**  
No project parser benchmark has been run. Format documentation is not parser validation.

**Five-day feasibility**  
Feasible on Day 1 if the fixture suite passes.

**Current limitation**  
YOLO task variants beyond detection are unresolved. The parser must enforce resource caps such as `MAX_ANNOTATIONS_PER_IMAGE`, `MAX_POLYGON_VERTICES`, and `MAX_FILE_SIZE`.

**Next validation step**  
Run EXP-C2-V1-001 with valid, malformed, boundary, `iscrowd`, empty-segmentation, hostile-size, and YOLO-variant fixtures.

**Sources**  
SRC-01, SRC-02, SRC-03.

**Engineering constraint**  
Do **not** enforce `area = bbox_width × bbox_height`; the packet records the COCO `area` field as segmentation-mask area.

---

### M02 — Exact Cryptographic Hashing (SHA-256)

**Purpose**  
Create deterministic evidence of exact file duplicates.

**Threats addressed**  
T08 exact duplicates.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
Image files.

**Reference requirement**  
None.

**C2 status**  
**BUILD [P0].**

**Evidence basis**  
SHA-256 deterministic hashing property.

**Legitimate false-positive conditions**  
A hash match correctly means the bytes are identical; however, legitimate duplicate content can exist because of burst photography, shared stock imagery, multi-view datasets, or intentionally duplicated assets. Intent is not inferable from the hash alone.

**Known failure / evasion cases**  
Any byte modification changes the hash. Re-encoded or transformed copies therefore fall outside M02.

**Project-specific evidence**  
No project dataset run has been recorded.

**Five-day feasibility**  
Feasible in the deterministic Day 1 tier.

**Current limitation**  
Exact equality only; no near-duplicate semantics.

**Next validation step**  
Run EXP-C2-V1-002 with known duplicate groups and re-saved controls.

**Sources**  
SRC-04.

---

### M03-PDQ — PDQ Perceptual Near-Duplicate Clustering

**Purpose**  
Build near-duplicate relationship evidence such as clusters, contact sheets, and Hamming-distance adjacency.

**Threats addressed**  
T08 near duplicates; contextual support for T09.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
Image bytes and a PDQ implementation available offline.

**Reference requirement**  
No clean reference for corpus clustering. A legitimate burst/video control set is required for FPR calibration.

**C2 status**  
**BUILD for relationship evidence [P1]; PROTOTYPE for flooding/poisoning detection claims until EXP-C2-V1-003 produces project calibration data.**

**Evidence basis**  
Meta ThreatExchange PDQ. The packet records 256-bit perceptual hashes and a recommended starting Hamming distance of ≤31, while also recording that the threshold is designer-dependent.

**Legitimate false-positive conditions**  
Burst frames, video sequences, re-saves, compression changes, crops, borders, multi-view capture, flips, resizes, and recolouring can be perceptually close.

**Known failure / evasion cases**  
Unique perturbations with no related original in the corpus can evade relationship matching. PDQ similarity does not establish malicious flooding.

**Project-specific evidence**  
No project COCO/YOLO PDQ run or FPR calibration is recorded.

**Five-day feasibility**  
Feasible on Day 2 if an offline PDQ package and control set are available.

**Current limitation**  
No project-specific threshold has been validated; minimum control-set size is not established.

**Next validation step**  
Run EXP-C2-V1-003 across a threshold range and record FPR, near-duplicate recall, and analyst-budget precision.

**Sources**  
SRC-05; RV-02; FACT-V2-009.

---

### M04 — Frozen Embedding kNN / Clustering

**Purpose**  
Surface corpus-relative representation-space outliers and clusters for analyst review.

**Threats addressed**  
T09; conditional exploratory signal for visible/non-adaptive T05a–c.

**Execution class**  
`FROZEN_MODEL_ASSISTED`.

**Input requirements**  
Images plus a pre-bundled frozen embedding model such as CLIP/DINO and sufficient compute.

**Reference requirement**  
No clean reference for corpus-relative clustering. A validated discriminative model/signal would be required for stronger clean-label claims; none is established.

**C2 status**  
**PROTOTYPE [P1] — corpus-relative/OOD pilot only. No clean-label BUILD claim.**

**Evidence basis**  
Clean-label attack literature and model-embedding reasoning; ClipGrader is context only.

**Legitimate false-positive conditions**  
Rare classes, legitimate sensor/domain shifts, augmentation, ambiguous imagery, and normal intra-class variation.

**Known failure / evasion cases**  
Feature-collision or representation-preserving attacks can remain inside the legitimate embedding manifold.

**Project-specific evidence**  
No COCO/YOLO project benchmark exists.

**Five-day feasibility**  
Conditional. Offline model artefacts must be confirmed by Day 1; otherwise M04 is descoped.

**Current limitation**  
No verified clean-label signal or project-specific detection benchmark.

**Next validation step**  
If artefacts exist, run EXP-C2-V1-008 for OOD utility and EXP-C2-V1-007 only as a clean-label stress-test gate.

**Sources**  
SRC-08, SRC-14, SRC-10 context only.

---

### M05 — Frozen VLM Semantic Alignment

**Purpose**  
Generate analyst-reviewable evidence about image/label semantic alignment.

**Threats addressed**  
T06/T07 semantic issues; conditional T05a cases where a visible change creates annotation inconsistency.

**Execution class**  
`FROZEN_MODEL_ASSISTED`.

**Input requirements**  
Images, annotations, an offline frozen VLM, and a stable class-prompt contract.

**Reference requirement**  
No clean dataset reference.

**C2 status**  
**PROTOTYPE [P1].**

**Evidence basis**  
VLM-assisted annotation-quality literature. ClipGrader is retained **for context only** because its headline performance comes from trained/adapted conditions.

**Legitimate false-positive conditions**  
Ontology ambiguity, small objects, rare classes, preprocessing differences, and legitimate annotator disagreement.

**Known failure / evasion cases**  
A clean-label sample can remain fully semantically consistent with its correct label; semantic alignment then produces no useful signal.

**Project-specific evidence**  
No frozen-mode COCO/YOLO project evaluation exists.

**Five-day feasibility**  
Conditional on pre-bundled offline model artefacts and compute.

**Current limitation**  
The packet explicitly rejects using ClipGrader’s 91%/1.8% figures as evidence for this frozen baseline.

**Next validation step**  
If artefacts exist, define the class-prompt contract and evaluate semantic alignment under controlled annotation defects.

**Sources**  
SRC-10 context only; SRC-09.

---

### M06 — Source-Stratified Class / Image Statistics

**Purpose**  
Quantify class, source, and batch distributions and expose source-specific anomalies.

**Threats addressed**  
T06, T09, and T10 with an explicit Sybil caveat.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
Annotations plus trusted source/batch metadata for any reliable T10 interpretation.

**Reference requirement**  
No clean reference dataset.

**C2 status**  
**BUILD CONDITIONAL [P1] — only with C4 Sybil-resistant identity for reliable T10 outputs.**

**Evidence basis**  
Distribution statistics plus V2 red-team correction on identity trust.

**Legitimate false-positive conditions**  
Real class imbalance, regional/domain specialization, contributor-specific capture context, annotation style, and sampling differences.

**Known failure / evasion cases**  
Clean-label attacks can preserve marginals. Distribution-preserving A↔B swaps can evade marginal-only checks. Sybil identities can fragment source concentration.

**Project-specific evidence**  
No controlled attack experiment or COCO/YOLO benchmark is recorded. The prior 3–5% universal label-flip threshold claim is rejected.

**Five-day feasibility**  
Feasible on Day 3 for statistics; T10 interpretation remains `SYBIL-UNRELIABLE` if identity is not `TRUSTED`.

**Current limitation**  
Requires C4 contract:

`source_identity_status ∈ { TRUSTED, UNTRUSTED, UNAVAILABLE }`

`TRUSTED` requires cryptographic attestation, a cost-of-identity mechanism, and identity-linkage detection. Path/email/filename alone is not sufficient.

**Next validation step**  
Resolve DEP-C4-001/002/003 and run EXP-C2-V1-004 plus EXP-C2-V1-009.

**Sources**  
V1 M06 card; SRC-09; RED_TEAM MAJ-04; CORR-T10-03; FACT-V2-014.

---

### M11 — Trusted Reference Comparison

**Purpose**  
Compare contributed data against an approved clean reference where aligned comparison is meaningful.

**Threats addressed**  
T06, T07, T09 in reference-relative settings.

**Execution class**  
`REFERENCE_DEPENDENT`.

**Input requirements**  
A separately approved reference dataset with contamination controls and distribution-match evidence.

**Reference requirement**  
Yes. This is the defining requirement.

**C2 status**  
**BLOCKED — sourcing strategy REJECTED; clean-reference sourcing unresolved.**

**Evidence basis**  
The V2 packet rejects the proposed public-COCO-subset assumption because public availability does not establish cleanliness.

**Legitimate false-positive conditions**  
Reference contamination, domain mismatch, annotation-style mismatch, and legitimate distribution shift.

**Known failure / evasion cases**  
Without an exact or appropriately matched clean counterpart, many anomalies have no trustworthy reference signal.

**Project-specific evidence**  
Not tested.

**Five-day feasibility**  
Not feasible under current conditions.

**Current limitation**  
M11 remains blocked until all four conditions are defined and satisfied:

1. contamination audit with pass/fail criteria;
2. explicit distribution-match metric;
3. minimum reference size specification;
4. an independent review process completable inside the project window.

**Next validation step**  
Resolve OQ-V2-001/002 and only then design EXP-C2-V1-010.

**Sources**  
SRC-09; RED_TEAM MAJ-01; CONTRA-V2-003.

---

### M14 — Joint Co-Occurrence + Spatial-Layout Statistics

**Purpose**  
Complement marginal statistics with class-pair and spatial-layout relationships.

**Threats addressed**  
T06 distribution-preserving systematic flips where relationships shift; conditional T07 layout anomalies.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
Parsed annotations with sufficient class/source support.

**Reference requirement**  
No clean reference in principle.

**C2 status**  
**PROTOTYPE [P1].**

**Evidence basis**  
Logical complement to M06. The dossier records no primary peer-reviewed source for this exact C2 formulation.

**Legitimate false-positive conditions**  
Natural scene co-occurrence, rare-class sparsity, source-specific capture context, and annotation-tool differences.

**Known failure / evasion cases**  
A carefully constructed attack can preserve joint structure. M14 must not be represented as detecting arbitrary distribution-preserving swaps.

**Project-specific evidence**  
No experiment has been executed.

**Five-day feasibility**  
Feasible as a lightweight Day 3/4 prototype if the corpus provides adequate support.

**Current limitation**  
Minimum class/source support is not established.

**Next validation step**  
Define support criteria and run the relevant arms of EXP-C2-V1-004.

**Sources**  
No primary peer-reviewed literature identified for the exact formulation in the current packet.

---

### M15 — Annotation-Blind Image-Only Pipeline

**Purpose**  
Provide image-only evidence when annotations are missing, hostile, or untrusted.

**Threats addressed**  
T08 through hash/PDQ tiers; T09 through acquisition statistics; conditional T05a–c through a residual repeated-pattern pilot.

**Execution class**  
`DATA_ONLY`.

**Input requirements**  
Image bytes only.

**Reference requirement**  
No clean reference to execute. A heterogeneous clean/control set is needed to quantify FPR.

**C2 status**  
**BUILD for hash/acquisition/PDQ tiers [P1]; PROTOTYPE for residual trigger-scan tier. Residual output is not for security claims.**

**Evidence basis**  
M02/M03 foundations plus an exploratory residual-scan concept.

**Legitimate false-positive conditions**  
Sensor diversity, burst/video sampling, re-saves, watermarks, overlays, uniform textures, grids, and repeated architectural patterns.

**Known failure / evasion cases**  
Invisible, non-repeating, clean-label perturbations can evade entirely.

**Project-specific evidence**  
No project test has been run. The residual tier is unverified for poisoning detection.

**Five-day feasibility**  
Hash/acquisition/PDQ tiers are feasible. Residual analysis is a Day 4 pilot only.

**Current limitation**  
Residual output must be patch/relationship evidence for analyst review, never a “backdoor detected” verdict.

**Next validation step**  
Run EXP-C2-V1-006 with team-controlled visible patches, textures, colour offsets, and clean controls.

**Sources**  
SRC-05; SRC-07.

---

### ObjectLab / Cleanlab — Model-Assisted Label Quality

**Purpose**  
Prioritize potential semantic annotation errors using detector predictions.

**Threats addressed**  
T07 semantic annotation errors.

**Execution class**  
`FROZEN_MODEL_ASSISTED`.

**Input requirements**  
Ground-truth labels plus object-detector predictions.

**Reference requirement**  
No reserved clean dataset is documented, but model predictions are required.

**C2 status**  
**DEFER / OPTIONAL [P1].**

**Evidence basis**  
Cleanlab object-detection workflow and ObjectLab research.

**Legitimate false-positive conditions**  
Detector errors on rare/novel classes, domain mismatch, ambiguous/partial objects.

**Known failure / evasion cases**  
Does not directly detect pixel triggers or model backdoors.

**Project-specific evidence**  
No project run. The packet explicitly corrects earlier assumptions: Cleanlab object detection is not data-only, and ObjectLab is not model-free.

**Five-day feasibility**  
Optional only if an approved offline detector and prediction bundle already exists.

**Current limitation**  
The baseline cannot assume a detector-training path.

**Next validation step**  
Confirm an offline prediction source and format adapter before considering implementation.

**Sources**  
SRC-11, SRC-12, SRC-06.

---

### TellTale — Training-Trajectory Spectrum Analysis

**Purpose**  
Detect poisoned samples using training-loss trajectory information transformed into the spectrum domain.

**Threats addressed**  
T05, including clean-label cases in the source literature.

**Execution class**  
`TRAINING_DEPENDENT`.

**Input requirements**  
Training trajectories; static dataset files alone are insufficient.

**Reference requirement**  
No reserved clean reference is required by the method, but trajectory data is required.

**C2 status**  
**DEFER OUTSIDE BASELINE.**

**Evidence basis**  
NDSS 2025 TellTale paper/repository.

**Legitimate false-positive conditions**  
Not established for COCO/YOLO object detection in the current packet.

**Known failure / evasion cases**  
Applicability to the exact C2 object-detection setting remains unverified.

**Project-specific evidence**  
No project execution. The source reports ≥95.52% detection accuracy and ≤0.61% false-positive rate across its evaluated settings, but the packet does not confirm a COCO/YOLO object-detection evaluation. Those numbers are therefore not admissible as C2 OD performance.

**Five-day feasibility**  
Outside the no-retraining baseline because training-trajectory data is unavailable.

**Current limitation**  
RV-QNT-02 remains open.

**Next validation step**  
Only reconsider if compatible pre-collected traces become available and the source’s OD scope is verified.

**Sources**  
SRC-13; NEW-CLM-004; NEW-QNT-002.

---

## 8. Status Matrix

| Method | Current status | Why | Gate / dependency |
|---|---|---|---|
| M01 | **BUILD AFTER EXP-C2-V1-001** | Deterministic annotation rules are defensible, but parser implementation is not yet validated | Parser fixture pass; YOLO task scope |
| M02 | **BUILD** | Deterministic exact-byte duplicate evidence | Project run still pending |
| M03-PDQ | **BUILD** for relationship evidence / **PROTOTYPE** for flooding detection | Similarity relationship is supported; project FPR threshold is not | EXP-C2-V1-003 |
| M04 | **PROTOTYPE** | Corpus-relative OOD only; no clean-label claim | Offline model artefact + compute |
| M05 | **PROTOTYPE** | Analyst evidence only; trained ClipGrader figures do not transfer | Offline VLM + prompt contract |
| M06 | **BUILD CONDITIONAL** | Statistics are implementable; reliable T10 meaning depends on identity trust | C4 `TRUSTED` identity contract |
| M11 | **BLOCKED** | Proposed clean-reference sourcing strategy rejected | Four reference-quality conditions |
| M14 | **PROTOTYPE** | Complementary statistical idea without project or exact-literature validation | Support threshold + EXP-C2-V1-004 |
| M15 | **BUILD** for hash/acquisition/PDQ; **PROTOTYPE** residual | Image-only fallback is useful; residual poisoning claim unverified | Calibration and controlled residual evaluation |
| ObjectLab / Cleanlab | **DEFER / OPTIONAL** | Requires detector predictions | Approved offline detector/predictions |
| TellTale | **DEFER OUTSIDE BASELINE** | Requires training trajectories | Compatible pre-collected trajectories + scope verification |

“BUILD” in this table is a research disposition, not proof that code has been implemented, executed, or validated.

---

## 9. Five-Day Implementation Feasibility

The V2 packet defines a staged plan. It is a feasibility sequence, not an execution log.

| Day | Planned focus | Methods / activity | Current state |
|---|---|---|---|
| **Day 1** | Deterministic floor | M01 parser/geometry gate; M02 exact hashing | **PLANNED / IMPLEMENTABLE IN PRINCIPLE**; M01 gated by EXP-C2-V1-001 |
| **Day 2** | Relationship evidence | M03-PDQ; M15 hash/PDQ/acquisition evidence | **PLANNED**; flooding claims remain prototype until calibration |
| **Day 3** | Statistical evidence | M06 if identity dependency is satisfied; M14 prototype | **PLANNED / CONDITIONAL** |
| **Day 4** | Synthetic scenarios / residual pilots | M14 scenario arms; M15 residual; optional M04/M05 only if offline artefacts exist | **PLANNED / CONDITIONAL** |
| **Day 5** | Review and evidence handoff | Evidence bundle, analyst workflow, correction register | **PLANNED**; analyst-review validation is an explicit open gap |

### Feasible within five days, subject to gates

- M01 after the Day 1 fixture pass;
- M02;
- M03-PDQ relationship evidence;
- M15 hash/acquisition/PDQ tiers;
- M06 statistics if required source identity is available;
- M14 as a prototype;
- team-controlled synthetic fixture generation;
- evidence bundle generation and analyst review if time is explicitly allocated.

### Not feasible or not justified within the current window

- M11 clean-reference sourcing, audit, and distribution matching;
- closing T05d clean-label coverage;
- TellTale without trajectory data;
- M04/M05 if offline artefacts and compute are not confirmed before implementation begins.

### Recommended five-day boundary

The packet recommends measuring and documenting the T05d gap rather than spending the implementation window implying closure that the current evidence cannot support.

---

## 10. Evaluation Plan

**Execution status:** all experiments below are **PRE-REGISTERED; NONE is recorded as executed in the current packet.**

| Experiment | Method | Purpose | Ground truth | Metric | Offline feasibility | Current execution status |
|---|---|---|---|---|---|---|
| EXP-C2-V1-001 | M01 | Parser conformance on valid, malformed, boundary, hostile, and YOLO-variant fixtures | Known synthetic fixture validity/invalidity | Per-rule binary pass/fail | Yes | **NOT RUN** |
| EXP-C2-V1-002 | M02, M15 hash | Exact-duplicate recall across originals, exact copies, and re-saves | Known duplicate groups | Recall/precision of exact duplicate pairs; separate re-save behavior | Yes | **NOT RUN** |
| EXP-C2-V1-003 | M03-PDQ | Calibrate Hamming-distance threshold using bursts, video controls, re-saves, crops, rotations, compression variants | Known near-duplicate relationships plus legitimate burst controls | FPR-vs-threshold table; precision@K for analyst budget | Yes, with team control set | **NOT RUN** |
| EXP-C2-V1-004 | M06, M14 | Evaluate random/systematic label flips across 0.1/0.5/1/3/5/10% arms and varied priors | Known modified annotations | Detection rate by arm; FPR on unmodified data; no universal threshold claim | Yes | **NOT RUN** |
| EXP-C2-V1-005 | M01 | Evaluate geometry defects and task-aware edge cases | Known defective records | Per-rule detection rate; structural vs semantic cases separated | Yes | **NOT RUN** |
| EXP-C2-V1-006 | M15 residual | Evaluate visible patch/texture/colour-offset patterns with clean controls | Team-controlled trigger patterns | Precision@K for repeated patterns | Yes, with generated images | **NOT RUN** |
| EXP-C2-V1-007 | M04/M05 claim gate | Clean-label stress test across 0.1/0.5/1/5% arms | Team-controlled Turner/Narcissus-style examples | Detection rate by arm; FPR on unmodified subset; `UNVERIFIABLE` if no signal | Conditional on pre-available adversarial tooling | **NOT RUN** |
| EXP-C2-V1-008 | M04, M15 acquisition | Evaluate OOD evidence against legitimate domain/sensor variation controls | Known OOD insertions plus legitimate diversity controls | FPR on legitimate diversity; top-K utility | Conditional on offline model artefacts | **NOT RUN** |
| EXP-C2-V1-009 | M06 T10 | Compare single-source concentration with 2/4/8-Sybil synthetic identity fragmentation | Team-generated contributor identities and known allocation | Threshold behavior by arm; explicit `SYBIL-UNRELIABLE` reporting | Yes, identity assumptions required | **NOT RUN** |
| EXP-C2-V1-010 | M11 | Test when reference contamination or mismatch should force `UNASSESSABLE` | Deliberately contaminated vs approved clean reference | Correct `UNASSESSABLE` behavior | Not feasible in current window | **NOT RUN** |

No planned poisoning percentage, threshold, or test arm in this table should be presented as an observed project result.

---

## 11. Dataset / Test-Asset Requirements

C2 distinguishes four different objects:

- **Dataset:** the contributed or evaluation corpus being assessed.
- **Test scenario:** the controlled condition under which a method is exercised.
- **Ground truth:** the known status required to score the test.
- **Derived attack fixture:** a reproducibly modified asset created to instantiate a scenario.

### Required asset classes

| Asset class | Why it is required | Examples from the current plan |
|---|---|---|
| Parser fixtures | Validate M01 before BUILD promotion | `iscrowd=1`, empty segmentation, boundary boxes, negative/out-of-bounds/zero-area cases, hostile sizes, YOLO variants |
| Exact duplicate groups | Validate M02 | Original plus byte-identical copies |
| Near-duplicate controls | Calibrate M03-PDQ | Burst/video frames, re-saves, crops, rotation, compression variants |
| Legitimate variation controls | Estimate false positives | Sensor changes, domain shifts, augmentations, resaves |
| Label-flip fixtures | Evaluate M06/M14 | Known random/systematic flips at pre-registered rates |
| Geometry-defect fixtures | Evaluate M01 rule behavior | Negative, zero, out-of-bounds, missing, overlap/task-aware cases |
| Trigger-pattern controls | Evaluate M15 residual pilot | Visible patches, textures, colour offsets plus clean images |
| OOD insertion scenarios | Evaluate M04/M15 acquisition evidence | Known OOD additions with legitimate-diversity controls |
| Source/contributor metadata | Evaluate M06/T10 | Trusted vs untrusted source IDs; synthetic Sybil allocations |
| Reference contamination/mismatch fixtures | Evaluate M11 if unblocked | Deliberately contaminated and distribution-mismatched reference sets |

A public dataset must not be labelled “clean” merely because it is public. The rejected M11 COCO-subset assumption is retained as a negative research result.

**Detailed dataset metadata, licensing, exact splits, derived subsets, and reproducible scenario definitions are maintained separately in the project Dataset Card.**

---

## 12. Reproducibility

The current packet defines reproducibility requirements; it does **not** claim that reproducibility has already been demonstrated.

Every executed C2 experiment should record, at minimum:

- random seed;
- dataset identifier and version;
- software/library version;
- hardware and runtime environment;
- attack/corruption parameters;
- ground-truth labels or fixture manifest;
- calibration/reference split;
- held-out evaluation split;
- exact metric definitions;
- execution date;
- method ID;
- experiment ID;
- evidence bundle/result identifier;
- method-specific thresholds, including the exact PDQ Hamming threshold where applicable.

### Split discipline

The packet requires that calibration, attack generation, and held-out evaluation roles do not silently overlap. In particular:

- an image used to tune a PDQ threshold must not silently become held-out evaluation evidence;
- an asset used to generate an attack fixture must be traceable as such;
- reference data, if M11 is ever unblocked, must have a separately auditable role;
- any manually reviewed subset must record who reviewed it and under what review contract.

### Evidence bundle contract

C2 evidence should include:

- method ID;
- experiment ID where applicable;
- evidence type, such as `STRUCTURAL_FLAG`, `NEAR_DUPLICATE_CLUSTER`, or `DISTRIBUTION_ANOMALY`;
- confidence/status label such as `DETERMINISTIC`, `PROTOTYPE`, or `ANALYST_REVIEW_REQUIRED`;
- `UNASSESSABLE` or `SYBIL-UNRELIABLE` when applicable;
- the exact underlying record, relationship, rule, or statistic needed for analyst review.

**Current state:** reproducibility requirements are defined. Reproducibility has not yet been demonstrated by executed C2 experiments.

---

## 13. Limitations and Negative Evidence

| ID | Limitation | Affected scope |
|---|---|---|
| LIM-V2-001 | T05d clean-label poisoning remains an **UNVERIFIABLE COVERAGE GAP** under the no-retraining/no-reference baseline | All tiers |
| LIM-V2-002 | T10 concentration evidence is **SYBIL-DEFEATABLE** without C4 identity assurance | M06 / T10 |
| LIM-V2-003 | Distribution-preserving label swaps can evade M06 marginals; M14 is only a prototype partial signal | T06 |
| LIM-V2-004 | PDQ threshold/FPR is unevaluated for the project population | M03-PDQ, M15 PDQ |
| LIM-V2-005 | No project-specific detection-rate evidence exists; quantitative literature claims come from other domains, trained/adapted setups, or unverified sources | All methods |
| LIM-V2-006 | M01 remains contingent on parser fixture validation and hostile-input hardening | M01 |
| LIM-V2-007 | M04/M05 require pre-bundled offline model artefacts and compute that are not yet confirmed | M04, M05 |
| LIM-V2-008 | M11 is blocked because no approved clean reference has been sourced | M11 |
| LIM-V2-009 | Day 5 human analyst-review workflow validation is not yet allocated in the earlier plan | All evidence outputs |
| LIM-V2-010 | OOD evidence cannot distinguish attack from legitimate domain variation without C1 policy | M06 T09, M15 acquisition, M04 |
| LIM-V2-011 | YOLO segmentation/pose/OBB parser behavior is untested | M01 |
| LIM-V2-012 | FL-domain Sybil results do not transfer quantitatively to COCO/YOLO object detection | T10 analysis |

### Explicitly unsupported claims

The current research does **not** support:

- Cleanlab/ObjectLab as data-only or model-free methods;
- TellTale as a static dataset scanner without training trajectories;
- ClipGrader’s 91%/1.8% trained/adapted figures as frozen-mode C2 performance;
- a universal 3–5% label-flip detection threshold;
- a universal COCO annotation-error percentage;
- applying federated LLM/QA poisoning ASR numbers directly to COCO/YOLO object detection;
- M01 BUILD promotion before EXP-C2-V1-001 passes;
- reliable M06 T10 outputs before C4 supplies Sybil-resistant identity;
- any inference that an unexecuted assessment produced a clean result.

### Negative evidence retained as research output

- No primary source in the current packet establishes a universal 3–5% object-detection label-flip threshold.
- No primary source in the current packet establishes the previously cited universal 24.0–24.6% COCO annotation-error rate.
- No C2 method has a verified T05d signal under the baseline constraints.
- No project-specific C2 FPR, detection-rate, or timing benchmark is recorded.
- No cited repository has been executed as project evidence.
- No project COCO/YOLO dataset benchmark is recorded.

---

## 14. Contradictions, Corrections and Research Evolution

### 14.1 Resolved V2 corrections

| Topic | Earlier statement | V2 correction / later finding | Current treatment |
|---|---|---|---|
| M01 status | BUILD [P0] | Format documentation is not parser validation | BUILD only after EXP-C2-V1-001 fixture pass |
| M03-PDQ scope | BUILD CONDITIONAL | No project FPR calibration exists | BUILD for relationships; PROTOTYPE for flooding detection |
| M11 sourcing | Public COCO subset proposed as reference | Public COCO contains annotation noise and is not automatically clean | Sourcing strategy REJECTED; M11 BLOCKED |
| T10 coverage | PARTIALLY_SUPPORTED | Concentration metrics are structurally Sybil-defeatable | `SYBIL-DEFEATABLE`; outputs unreliable without identity assurance |
| M06 trusted metadata | “Trusted contributor metadata” undefined | Explicit trust enum and Sybil-resistance requirements introduced | `TRUSTED / UNTRUSTED / UNAVAILABLE`; path/filename always untrusted |
| ClipGrader in M05 | Cited without sufficient qualification | Headline metrics come from trained/adapted setup; zero-shot unseen-class result is much weaker | SRC-10 context only; no imported performance claim |

### 14.2 Unresolved contradictions / verification issues

| Topic | Earlier / competing statement | Current evidence | Current treatment |
|---|---|---|---|
| Sybil quantitative transferability | FL results show strong Sybil amplification | Structural relevance is credible; quantitative OD transfer is unverified | Keep numbers source-scoped; validate only through project experiment |
| COCO annotation-noise percentage | Prior 24.0–24.6% figure; alternative 2.8% figure | Former provenance unresolved; latter pending RV-QNT-04 | No universal COCO error-rate claim |
| ClipGrader review status | ICLR 2025 status/reproduction questioned | Pending RV-QNT-01 | Do not use review-status claim until verified |
| TellTale OD scope | Multi-modal/non-classification result reported | COCO/YOLO object-detection evaluation not confirmed in current packet | Keep metrics out of C2 OD claims pending RV-QNT-02 |

### 14.3 Packet consistency observations

The V2 quality-gate narrative says “14 explicit limitations” while the actual limitation register enumerates `LIM-V2-001` through `LIM-V2-012` (12 IDs). This public edition preserves the enumerated register rather than inventing two missing limitations.

The quality-gate narrative also summarizes seven cross-domain dependencies as “4 to C4, 1 to C3, 1 to C1, 1 to C5,” while the dependency table actually contains 3 C4 IDs, 2 C3 IDs, 1 C1 ID, and 1 C5 ID. This public edition preserves the actual dependency table.

These are document-consistency observations, not new research claims.

---

## 15. Open Questions

| ID | Question | Dependency | Priority | Current status |
|---|---|---|---|---|
| OQ-V2-001 | Is a trusted clean reference available, and who owns sourcing/approval? | M11 | High | Open |
| OQ-V2-002 | What minimum reviewed reference size is acceptable once domain/classes are known? | M11 | High | Open |
| OQ-V2-003 | Will C4 provide Sybil-resistant authenticated contributor/batch linkage in the V1/V2 window? | M06 T10 | Critical | Open |
| OQ-V2-004 | Which exact offline model artefacts are available for M04/M05/ObjectLab-style analysis? | Optional Tier 4 | High | Open |
| OQ-V2-005 | What analyst review budget `K` is acceptable for top-K evidence triage? | All output tiers | High | Open |
| OQ-V2-006 | What legitimate variation controls are available for PDQ calibration? | EXP-C2-V1-003 | High | Open |
| OQ-V2-007 | Which YOLO task variants beyond detection must be supported? | M01 | High | Open |
| OQ-V2-008 | Are synthetic T05 scenarios fully team-controlled and reproducible? | EXP-C2-V1-007 | Critical | Open |
| OQ-V2-009 | Do FL-domain Sybil scaling results transfer quantitatively to COCO/YOLO contributor settings? | M06 / EXP-C2-V1-009 | Medium | Open |
| OQ-V2-010 | Does TellTale include COCO/YOLO object-detection evaluation in the full NDSS paper? | TellTale | Medium | Open / RV-QNT-02 |
| OQ-V2-011 | What is the exact origin of the rejected 24.0–24.6% COCO noise figure in the V1 packet? | Citation integrity | High | Open / CRIT-03 |
| OQ-V2-012 | Was ClipGrader rejected at ICLR 2025 and does independent reproduction exist? | M05 source classification | Medium | Open / RV-QNT-01 |
| OQ-V2-013 | What exact methodology/population supports the alternative 2.8% COCO error figure? | Optional reference point | Low | Open / RV-QNT-04 |
| OQ-V2-014 | Is C4 identity assurance path-derived or cryptographically attested? | M06 T10 | Critical | Open |

---

## 16. Cross-Cell Dependencies

| DEP ID | Handoff / dependency | C2 impact if unresolved | Required by | Criticality |
|---|---|---|---|---|
| DEP-C4-001 | C4 supplies `source_identity_status ∈ {TRUSTED, UNTRUSTED, UNAVAILABLE}` with the V2 trust requirements | M06 T10 remains `SYBIL-UNRELIABLE` | Day 3 | Critical |
| DEP-C4-002 | C4 confirms path/filename-derived identity is never `TRUSTED` | Prevents false confidence in T10 analysis | Day 1 design contract | Critical |
| DEP-C4-003 | C4 specifies cost-of-identity and linkage-detection approach | EXP-C2-V1-009 Sybil arms cannot be meaningfully designed without it | Day 2 | High |
| DEP-C3-001 | C3 owns model-level T05d clean-label coverage | T05d remains a data-level coverage gap in C2 | Architecture gate | Critical |
| DEP-C3-002 | Clarify ownership of M15 residual trigger-scan evidence | Prevents double-counting or an assurance gap | Architecture gate | Medium |
| DEP-C1-001 | C1 defines legitimate burst/video behavior, expected sensor/domain changes, and analyst review budget `K` | PDQ/OOD evidence remains hard to operationalize | Before Day 2 calibration | High |
| DEP-C5-001 | C5 preserves `UNASSESSABLE` and `SYBIL-UNRELIABLE`; absence of evidence must not become “clean” | Prevents incorrect assurance weighting | Architecture gate | High |

No formal `DEP-C6-*` item appears in the current C2 V2 dependency table. C6 is therefore treated here as a scope boundary for build/runtime validation rather than an implemented or formally registered integration.

---

## 17. References

The references below retain the source IDs used in the C2 packet. URLs are public authoritative/project pages where available. Access date for this public edition: **2026-09-29**.

### [R01 / Project context] Smart India Hackathon

**Organization:** Ministry of Education / AICTE / MoE Innovation Cell — Smart India Hackathon  
**Title:** Smart India Hackathon public programme portal  
**Year:** 2026 programme context  
**URL:** https://www.sih.gov.in/  
**Use in C2:** Problem-statement context. The current C2 packet itself remains the authoritative source for the C2-specific interpretation of PS requirements.

### [R02 / SRC-01] COCO API

**Organization:** COCO / cocodataset  
**Title:** COCO API  
**Repository:** GitHub  
**URL:** https://github.com/cocodataset/cocoapi  
**Use in C2:** COCO annotation structure and parser semantics.

### [R03 / SRC-02] COCO `area` semantics

**Organization:** COCO API maintainers  
**Title:** `"area" in annotations` — cocoapi issue #36  
**Repository:** GitHub issue  
**URL:** https://github.com/cocodataset/cocoapi/issues/36  
**Relevant location:** Maintainer response identifying `area` as segmentation area.  
**Use in C2:** FACT-V2-003; prevents incorrect `bbox_width × bbox_height` validation.

### [R04 / SRC-03] Ultralytics YOLO detection format

**Organization:** Ultralytics  
**Title:** Object Detection Datasets Overview — Ultralytics YOLO Format  
**Documentation:** Ultralytics Docs  
**URL:** https://docs.ultralytics.com/datasets/detect/  
**Use in C2:** YOLO detection rows, normalized `xywh`, and zero-based class IDs.

### [R05 / SRC-04] SHA-256 standard

**Organization:** National Institute of Standards and Technology (NIST)  
**Title:** FIPS 180-4 — Secure Hash Standard (SHS)  
**Year:** 2015 update to FIPS 180-4  
**URL:** https://csrc.nist.gov/pubs/fips/180-4/upd1/final  
**Use in C2:** SHA-256 exact-content hashing basis. Hash equality establishes identical digest output for the processed bytes; it does not establish intent.

### [R06 / SRC-05] Meta ThreatExchange PDQ

**Organization:** Meta / ThreatExchange  
**Title:** PDQ perceptual hashing  
**Repository:** GitHub  
**URL:** https://github.com/facebook/ThreatExchange/tree/main/pdq  
**Relevant location:** PDQ README matching guidance.  
**Use in C2:** M03-PDQ and M15. The recommended starting distance threshold is treated as advisory and must be calibrated for the project population.

### [R07 / SRC-06] Cleanlab releases

**Organization:** Cleanlab  
**Title:** cleanlab release history  
**Repository:** GitHub  
**URL:** https://github.com/cleanlab/cleanlab/releases  
**Use in C2:** Version/dependency record, including v2.9.0 in the V2 packet.

### [R08 / SRC-07] BadDet

**Authors:** Shih-Han Chan, Yinpeng Dong, Jun Zhu, Xiaolu Zhang, Jun Zhou  
**Title:** *BadDet: Backdoor Attacks on Object Detection*  
**Venue / archive:** arXiv  
**Year:** 2022  
**URL:** https://arxiv.org/abs/2205.14497  
**Use in C2:** Object-detection backdoor context and M15 counterexample framing.

### [R09 / SRC-08] Label-Consistent Backdoor Attacks

**Authors:** Alexander Turner, Dimitris Tsipras, Aleksander Madry  
**Title:** *Label-Consistent Backdoor Attacks*  
**Venue:** NeurIPS 2019 / arXiv  
**Year:** 2019  
**URL:** https://arxiv.org/abs/1912.02771  
**Use in C2:** T05d clean-label threat model and M04/M05 evasion boundary.

### [R10 / SRC-09] Noise-Aware Evaluation of Object Detectors

**Authors:** Jeffri Murrugarra Llerena, Claudio R. Jung  
**Title:** *Noise-Aware Evaluation of Object Detectors*  
**Venue:** WACV 2025  
**Year:** 2025  
**URL:** https://openaccess.thecvf.com/content/WACV2025/html/Llerena_Noise-Aware_Evaluation_of_Object_Detectors_WACV_2025_paper.html  
**Use in C2:** Evidence that COCO annotation noise exists; basis for rejecting “public COCO subset = clean reference.” The paper is not treated as establishing a universal COCO error rate.

### [R11 / SRC-10] ClipGrader — context only for M05

**Authors:** Hong Lu, Yali Bian, Rahul C. Shah  
**Title:** *ClipGrader: Leveraging Vision-Language Models for Robust Label Quality Assessment in Object Detection*  
**Archive:** arXiv / ICLR 2025 submission record  
**Year:** 2025  
**URL:** https://arxiv.org/abs/2503.02897  
**Use in C2:** **CONTEXT ONLY**. The packet records 91% accuracy / 1.8% false-positive rate for the trained/adapted COCO setup and approximately 11% accuracy in an unseen-class zero-shot experiment. These are not C2 frozen-mode performance results.

### [R12 / SRC-11] Cleanlab object-detection tutorial

**Organization:** Cleanlab  
**Title:** *Finding Label Errors in Object Detection Datasets*  
**Documentation:** cleanlab stable documentation  
**URL:** https://docs.cleanlab.ai/stable/tutorials/object_detection.html  
**Use in C2:** Confirms object-detection label-quality analysis requires labels and model predictions.

### [R13 / SRC-12] ObjectLab

**Authors:** Ulyana Tkachenko, Aditya Thyagarajan, Jonas Mueller  
**Title:** *ObjectLab: Automated Diagnosis of Mislabeled Images in Object Detection Data*  
**Venue:** ICML 2023 Data-centric Machine Learning Research workshop / arXiv  
**Year:** 2023  
**URL:** https://arxiv.org/abs/2309.00832  
**Use in C2:** Confirms ObjectLab uses a trained object detector; not model-free.

### [R14 / SRC-13] TellTale

**Authors:** Yansong Gao, Huaibing Peng, Hua Ma, Zhi Zhang, Shuo Wang, Rayne Holland, Anmin Fu, Minhui Xue, Derek Abbott  
**Title:** *Try to Poison My Deep Learning Data? Nowhere to Hide Your Trajectory Spectrum!*  
**Venue:** NDSS Symposium 2025  
**Year:** 2025  
**URL:** https://www.ndss-symposium.org/ndss-paper/try-to-poison-my-deep-learning-data-nowhere-to-hide-your-trajectory-spectrum/  
**Repository:** https://github.com/MPaloze/Telltale  
**Use in C2:** TellTale method basis. C2 retains the training-trajectory dependency and does not import its aggregate metrics as COCO/YOLO object-detection project evidence.

### [R15 / SRC-14] Clean-Label Backdoor Attacks: A Survey

**Authors:** Lior Yasur, Tzvi Lederer, Lior Rokach, Yisroel Mirsky  
**Title:** *Clean-Label Backdoor Attacks: A Survey*  
**Venue:** IEEE Access, Vol. 14  
**Year:** 2026  
**DOI:** https://doi.org/10.1109/ACCESS.2026.3689684  
**Use in C2:** Clean-label attack taxonomy/evasion context. The survey concerns clean-label backdoor research and does not itself establish C2 project detection performance.

### [R16 / FACT-V2-013] Federated instruction-tuning backdoor study

**Authors:** Haodong Zhao, Jinming Hu, Gongshen Liu  
**Title:** *Revisiting Backdoor Threat in Federated Instruction Tuning from a Signal Aggregation Perspective*  
**Archive:** arXiv:2602.15671  
**Year:** 2026  
**URL:** https://arxiv.org/abs/2602.15671  
**Use in C2:** Source-scoped LLM/NLP federated-learning context only. Quantitative poisoning results are not transferred to COCO/YOLO object detection.

### [R17 / FACT-V2-014] FoolsGold

**Authors:** Clement Fung, Chris J. M. Yoon, Ivan Beschastnikh  
**Title:** *Mitigating Sybils in Federated Learning Poisoning*  
**Archive:** arXiv:1808.04866  
**Year:** 2018  
**URL:** https://arxiv.org/abs/1808.04866  
**Use in C2:** Sybil-amplification evidence in federated learning. C2 uses the structural lesson, not the reported percentages as OD project benchmarks.

### Open reference verification queue

| Queue ID | Target | Open issue | Current treatment |
|---|---|---|---|
| RV-QNT-01 | ClipGrader ICLR/OpenReview record and independent reproduction | Review/reproduction status | Keep source as context; do not make review-status claim until closed |
| RV-QNT-02 | Full NDSS TellTale paper | Whether COCO/YOLO object detection is evaluated | Do not use aggregate metrics as OD evidence |
| RV-QNT-03 | V1 packet | Origin of 24.0–24.6% COCO-noise figure | Figure remains rejected |
| RV-QNT-04 | ar5iv noisy-label source | Methodology/population behind 2.8% figure | Do not use as universal rate |
| RV-T10-03 | ACM DOI 10.1145/3701100.3701119 | Transferability of truth-discovery aggregation to C2 contributor aggregation | Open |
| RV-T10-04 | MDPI participation-heterogeneity paper | Transferability of Sybil scaling setup to object detection | Open |

---

## 18. Claim / Source Index

### 18.1 V2 fact register

| Claim ID | Claim | Status | Evidence type | Primary source | Exact location |
|---|---|---|---|---|---|
| FACT-V2-001 | COCO annotations include IDs, category, segmentation, area, bbox, `iscrowd` | SUPPORTED | External format documentation | SRC-01 / R02 | COCO API / annotation format |
| FACT-V2-002 | COCO bbox convention is `[x_min, y_min, width, height]` in pixel space | SUPPORTED | External format documentation | SRC-01; SRC-03 | COCO/format documentation |
| FACT-V2-003 | COCO `area` is segmentation area, not bbox width × height | SUPPORTED; earlier claim contradicted | Primary-source issue clarification | SRC-02 / R03 | cocoapi issue #36 maintainer reply |
| FACT-V2-004 | YOLO detection uses `class cx cy w h`, normalized to [0,1], zero-based class IDs | SUPPORTED | Official documentation | SRC-03 / R04 | Ultralytics detection dataset format |
| FACT-V2-005 | cleanlab v2.9.0 release record and dependency change | SUPPORTED | Repository release record | SRC-06 / R07 | cleanlab releases page |
| FACT-V2-006 | Cleanlab OD requires labels + model predictions; not data-only | SUPPORTED correction | Official documentation | SRC-11 / R12 | “Format data, labels, and model predictions” |
| FACT-V2-007 | ObjectLab uses a trained object detector; not model-free | SUPPORTED correction | Research paper | SRC-12 / R13 | Abstract/method description |
| FACT-V2-008 | TellTale requires training trajectories; not a static dataset scanner | SUPPORTED correction | Research paper/repository | SRC-13 / R14 | Method description / trajectory collection |
| FACT-V2-009 | PDQ is a perceptual hash with Hamming matching; ≤31 is advisory/designer-dependent | SUPPORTED | Official repository documentation | SRC-05 / R06 | PDQ README matching guidance |
| FACT-V2-010 | ClipGrader headline figures come from trained/adapted use; zero-shot unseen-class performance is much lower | SUPPORTED but scope-limited | Research paper | SRC-10 / R11 | Main results + zero-shot grading section |
| FACT-V2-011 | No primary source in the packet establishes a universal 3–5% OD label-flip threshold | NOT_SUPPORTED earlier claim | Negative evidence | No primary source found | Exact location not established in current source packet |
| FACT-V2-012 | No primary source in the packet establishes a universal 24.0–24.6% COCO error rate | NOT_SUPPORTED earlier claim | Negative evidence | SRC-09; RV-QNT-03 | Exact source provenance unresolved |
| FACT-V2-013 | Federated instruction-tuning poisoning results cited in V2 belong to LLM/NLP FL context | SOURCE-SCOPED | External literature result | R16 | arXiv paper abstract/experimental sections cited in packet |
| FACT-V2-014 | FoolsGold packet figures show strong Sybil amplification in its FL setting | SUPPORTED in source domain | External literature result | R17 | FoolsGold experimental results cited in packet |
| FACT-V2-015 | SHA-256 supports deterministic exact-content digest comparison; intent is not inferable | SUPPORTED | Standard + inference boundary | SRC-04 / R05 | FIPS 180-4 plus C2 interpretation |
| FACT-V2-016 | No C2 method has a verified T05d signal under no-retraining/no-reference baseline | UNVERIFIABLE / COVERAGE GAP | Research synthesis / negative evidence | SRC-08, SRC-14 | C2 V2 threat/method analysis |

### 18.2 Major finding register

| Finding ID | Status | Primary source basis | Exact location / note |
|---|---|---|---|
| EF-01 | FACT | SRC-01, SRC-02, SRC-03; RED_TEAM MAJ-03 | Deterministic-floor synthesis; M01 gate retained |
| EF-02 | FACT | SRC-05; RV-02; FACT-V2-009 | PDQ relationship-vs-detector boundary |
| EF-03 | FACT / critical escalation | R17; R16; FACT-V2-014 | Sybil structural limitation; quantitative transfer restricted |
| EF-04 | FACT / correction | RED_TEAM MAJ-04; CORR-T10-03 | Trust enum introduced in V2 |
| EF-05 | FACT / citation correction | R11; RED_TEAM CRIT-01; FACT-V2-010 | ClipGrader performance-scope correction |
| EF-06 | FACT / coverage gap | R09; R15; FACT-V2-016 | T05d boundary |
| EF-07 | FACT / rejected assumption | R10; RED_TEAM MAJ-01 | COCO-subset clean-reference assumption rejected |
| EF-08 | FACT / project status | V2 implementation-evidence section | No project benchmark exists |
| EF-09 | INFERENCE | V2 feasibility synthesis | Five-day feasibility by tier |
| EF-10 | FACT / open verification | REVERIFY queue | Citation register not fully closed |

---

## 19. Research Lineage and Internal Document Traceability

### 19.1 Research lineage

The C2 V2 dossier records the following lineage:

```text
V1 research packet
      |
      v
REVERIFY / Stage 8
      |
      v
RED_TEAM / Stage 9
      |
      v
V2 synthesis
      |
      v
C2-V2-001 dossier
      |
      v
Public Research Edition
```

The purpose of the later stages was not to cosmetically strengthen the earlier research. They were used to challenge claims, narrow source applicability, reject unsupported thresholds, expose missing dependencies, and change method status where the evidence required it.

### 19.2 Current packet disposition

The source dossier records **CHECKPOINT 2: PASS WITH CONDITIONS**. This is a research checkpoint, not architecture approval.

Conditions carried into this public edition include:

- M01 promotion depends on EXP-C2-V1-001;
- M03 flooding claims depend on EXP-C2-V1-003;
- C4 identity contracts are required before reliable M06/T10 use;
- C1 operational policy is required before PDQ/OOD evidence becomes actionable;
- open citation/reverification items must be resolved before the register is treated as final;
- Day 5 analyst-review workflow must be explicitly allocated and validated;
- T05d and Sybil limitations remain documented cross-cell dependencies, not hidden omissions.

### 19.3 V1 → V2 status evolution

- **M01:** BUILD [P0] → **BUILD AFTER EXP-C2-V1-001 PARSER FIXTURE PASS [P0]**
- **M03-PDQ:** BUILD CONDITIONAL → **BUILD for relationship evidence / PROTOTYPE for flooding detection**
- **M06:** generic “trusted metadata” condition → **BUILD CONDITIONAL on C4 `TRUSTED` identity; T10 otherwise `SYBIL-UNRELIABLE`**
- **T10:** PARTIALLY_SUPPORTED → **SYBIL-DEFEATABLE**
- **M11 sourcing:** PROPOSED public COCO subset → **REJECTED sourcing strategy; M11 BLOCKED**
- **SRC-10 in M05:** unqualified source → **CONTEXT ONLY**
- **COCO `area` rule:** earlier bbox-area assumption → **CONTRADICTED and corrected**
- **Cleanlab data-only assumption:** → **NOT_SUPPORTED**
- **ObjectLab model-free assumption:** → **CONTRADICTED**
- **TellTale static-scanner assumption:** → **NOT_SUPPORTED**
- **Federated poisoning metrics:** → **source-scoped to their FL/LLM setting**

Open correction-register items carried forward in the source packet are `C2-CORR-001`, `-002`, `-004`, `-005`, `-008`, `-010`, and `-011`; they require experiment evidence before closure.

### 19.4 Final public interpretation

The present research supports a defensible deterministic baseline, relationship evidence for duplicates/near-duplicates, conditional statistical analysis, and a reproducible evaluation plan. It does **not** support a claim that all data poisoning is detectable, that clean-label poisoning is solved, that contributor concentration is reliable without identity assurance, that a public dataset is clean by default, or that planned experiments are already project results.

**Final status:** this is a public C2 research synthesis. Implementation, experiment execution, analyst review, cross-cell dependency closure, and final architecture approval remain separately gated.
