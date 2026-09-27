# C1 — Mission, Threat & Operational Context Research

## Document Metadata

| Field | Value |
|---|---|
| **Project** | SIH 2026 — Trustworthy Computer Vision Integrity Assurance |
| **Problem Statement** | PS 26228 — “Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines” |
| **Cell** | C1 |
| **Domain** | Mission / Threat / SIH / Operational Context |
| **Source research version** | `C1-SYNTH-V2-COMPLETE-20260922-01` |
| **Public research edition** | 1.0 |
| **Original research date** | 22 September 2026 |
| **Public-edition verification date** | 29 September 2026 |
| **Document purpose** | Establish the mission, threat, trust-boundary, operational and requirements context that constrains downstream design in C2–C6 |
| **Status** | **Research synthesis for C1; implementation and validation are governed separately by C2–C6.** |

This document is a public-facing restructuring of the C1 research dossier. It preserves the research findings, assumptions, unresolved questions and evidence boundaries of the source material while removing internal competitive strategy and implementation planning that do not belong in a public mission/threat dossier.

C1 does **not** claim that the final project architecture, algorithms, cryptographic protocol, scoring semantics or runtime engineering decisions have been validated merely because candidate approaches were explored during C1 research.

---

## 1. Research Objective

C1 investigates the problem that SIH 2026 PS 26228 is asking the team to solve before downstream cells choose or implement specific mechanisms.

The purpose of C1 is to establish:

- the integrity-assurance problem described by the problem statement;
- the lifecycle over which assurance is required;
- the actors and trust boundaries implied by a multi-contributor pipeline;
- the assets that require protection or assessment;
- the principal threat and failure categories;
- the operational and evaluation constraints that limit possible solutions;
- the distinction between evidence, anomaly, uncertainty and confirmed malicious behaviour;
- the dataset context relevant to later experimental work;
- unresolved assumptions requiring organiser clarification or downstream research; and
- explicit handoffs from mission/threat research into C2–C6.

C1 is therefore the **context and problem-definition layer** of the research programme. It is not the final specification for data-integrity detection, model-security algorithms, provenance cryptography, drift scoring, governance semantics or engineering implementation.

---

## 2. Problem Statement and Mission Context

### 2.1 What PS 26228 asks the team to solve

The available copy of PS 26228 identifies the organisation as the Ministry of Defence, department Indian Army (DGIS), category Software, and theme Blockchain & Cybersecurity [R01].

The problem statement describes computer-vision pipelines that may combine:

- training data from multiple contributors;
- pretrained or vendor-supplied models; and
- inference outputs consumed by downstream systems.

The resulting assurance problem spans the complete data/model/inference lifecycle rather than a single detector or model.

The problem statement identifies risks including mislabelling, duplicated content, out-of-distribution material, trigger-based backdoors, model substitution or modification, hidden model behaviour, and alteration or replay of inference records [R01].

Its central requirement is therefore best interpreted as:

> Build an evidence-based assurance layer around contributed data, supplied models and resulting inference records without assuming that every contributing source is trusted.

This is a **problem interpretation derived directly from the PS**, not a claim that the team has already implemented or validated such a layer.

### 2.2 Why multi-contributor pipelines change the trust problem

A conventional CV pipeline may implicitly assume that the dataset, annotations, model artifact and resulting predictions belong to one controlled environment.

PS 26228 removes that simplifying assumption.

A contributor may supply data, annotations or a trained model. A different system may perform inference. Another process may consume or archive the output. Evidence therefore has to survive transitions between parties and lifecycle stages.

The key question is no longer only:

> “Does the model produce useful predictions?”

The assurance question becomes:

> “What evidence exists that the data, model, configuration and output being examined are the assets that were expected, and what evidence supports any claim that one of them is anomalous, altered or suspicious?”

That distinction is central to the rest of the research.

### 2.3 Evidence-based assurance rather than attack attribution

The PS repeatedly asks for evidence, confidence or severity, limitations, affected assets and recommended dispositions [R01].

C1 therefore treats **integrity evidence** and **attack attribution** as different claims.

A mismatch, anomaly or distributional deviation may justify investigation. It does not, by itself, establish malicious intent, compromise or a particular attack mechanism.

This distinction becomes a project-wide interpretation boundary in Section 8.

---

## 3. Operational Lifecycle

C1 models the assurance problem as the following lifecycle:

```text
CONTRIBUTION
     ↓
DATA / MODEL INGESTION
     ↓
ASSESSMENT
     ↓
INFERENCE
     ↓
EVIDENCE GENERATION
     ↓
ANALYST REVIEW
     ↓
AUDIT / TRACEABILITY
```

### 3.1 Contribution

External or otherwise non-implicitly-trusted sources may provide datasets, annotations, batches, model artifacts or associated metadata.

The contributor identity may be known, partially known or represented only by source/batch metadata.

The existence of contributor metadata matters because the PS explicitly asks that sample-level evidence be aggregated at source level where such metadata is available [R01].

### 3.2 Data and model ingestion

The pipeline receives artifacts that may not yet have been established as trustworthy.

At this stage, an artifact's presence in the system must not be confused with validation of its content or provenance.

File format parsing is itself security-relevant. C1 research identified current PyTorch and ONNX security concerns that make untrusted model loading part of the engineering threat surface rather than merely a file-handling detail [R07][R08][R09].

### 3.3 Assessment

Assessment is the stage at which downstream C2, C3 and C5 mechanisms examine data integrity, model behaviour and distribution shift.

C1 defines what these assessments need to communicate; it does not prescribe their final algorithms.

Where evidence cannot be produced because of access restrictions, missing reference assets or unsupported conditions, the result must remain distinguishable from a clean assessment.

### 3.4 Inference

Inference connects an input, a model and processing configuration to an output.

PS 26228 specifically requires the system to make post-generation substitution, alteration or replay of protected inference records detectable [R01].

The final cryptographic protocol for accomplishing this belongs to C4.

### 3.5 Evidence generation

A finding is meaningful only if the evidence behind it can be inspected.

Evidence may include deterministic integrity measurements, statistical observations, behavioural observations, provenance records or an explicit declaration that an assessment could not be performed.

C1 does not assume that every evidence type has equal strength.

### 3.6 Analyst review

The source research consistently treats the analyst as the decision boundary.

The PS asks for recommended dispositions such as accept, review or quarantine [R01], but it does not by itself define the enforcement semantics of “quarantine.”

C1 therefore treats automated disposition as an open governance question rather than assuming that a detector should automatically block an asset.

### 3.7 Audit and traceability

Findings, evidence, decisions and limitations need sufficient traceability for later review.

The PS explicitly requires a tamper-evident audit trail and a reproducible audit log [R01].

The mechanism used to make that audit trail tamper-evident is a downstream design question.

---

## 4. Actors and Trust Boundaries

The following model reflects actors and components supported by the C1 source and problem statement.

| Actor / component | C1 trust classification | Rationale |
|---|---|---|
| **External data contributor** | UNTRUSTED / CONDITIONAL | Multi-contributor data cannot be assumed clean merely because a source supplied it. |
| **External model contributor / vendor model** | UNTRUSTED / CONDITIONAL | Model substitution, hidden behaviour and modification are explicit PS concerns. |
| **Dataset and model ingestion layer** | CONDITIONAL | It is part of the project-controlled pipeline, but it processes potentially hostile artifacts and therefore forms a security boundary. |
| **Assessment engine** | CONDITIONAL | It is relied upon to produce evidence, but its conclusions remain limited by access, calibration, detector scope and implementation correctness. |
| **Model-processing/runtime environment** | CONDITIONAL | Model parsers and runtimes process untrusted artifacts; C1 identified supply-chain and unsafe-loading risks. |
| **Reference assets / baselines** | CONDITIONAL / TRUST-DEPENDENT | Comparisons are only meaningful when the reference itself has an established provenance or explicitly stated trust assumption. |
| **Inference record** | UNTRUSTED UNTIL VERIFIED | A stored or received output may have been replaced, altered or replayed. |
| **Evidence/audit store** | TRUSTED ONLY UNDER DECLARED CONTROLS | The PS requires tamper evidence; ordinary storage alone does not establish immutability. |
| **Human analyst** | DECISION AUTHORITY | C1 treats the analyst as the consumer of findings and recommendations rather than as another detection algorithm. |
| **Organiser-provided evaluation assets** | UNKNOWN | Exact models, datasets, access levels and compute envelope remain partly unresolved. |

### 4.1 Trust is scoped, not absolute

“Trusted” should not be interpreted as “incapable of failure.”

For example, a project-controlled assessment engine may still produce false positives, false negatives or unavailable results.

Likewise, a reference model is only suitable as an integrity reference if the project can explain why that reference is authoritative for the comparison being performed.

### 4.2 Host compromise is outside the simple artifact model

The source dossier notes that a compromised host could undermine mechanisms operating on that host.

Accordingly, cryptographic integrity of a record does not automatically establish that the computation that generated the record was itself trustworthy.

This is a limitation that must remain visible in C4/C6.

---

## 5. Assurance Surfaces

PS 26228 creates four related but distinct assurance surfaces.

### 5.1 Data

The data surface includes:

- images or other CV inputs;
- annotations and labels;
- contributor and batch metadata;
- duplicate or near-duplicate material;
- unusual or out-of-distribution samples; and
- possible trigger or poisoning artifacts.

The PS specifically identifies trigger injection, label flipping, systematic mislabelling, near-duplicate flooding and OOD insertion [R01].

C2 owns the final methods used to assess these conditions.

### 5.2 Model

The model surface includes supplied model files and behaviour associated with them.

Relevant concerns include:

- substitution of one artifact for another;
- modification of model files;
- backdoor-like behaviour;
- differences between expected and observed behaviour;
- different levels of model access; and
- security risks created by parsing or loading an untrusted model.

The PS permits approaches such as behavioural fingerprinting, trigger search or reconstruction, parameter or activation statistics, and comparison with a reference battery, but it does not mandate one algorithm [R01].

C3 owns final model-assessment methodology.

### 5.3 Inference

The inference surface concerns whether an output can be tied to the input, model and processing configuration that supposedly generated it.

Threats include:

- replacing the input after inference;
- substituting a model identifier;
- changing preprocessing or inference parameters in the record;
- altering predictions;
- replacing one valid record with another; and
- replaying a previously valid record.

C4 owns the final protection and verification protocol.

### 5.4 Provenance and audit

The provenance/audit surface connects the other three surfaces.

A useful provenance record has to answer questions such as:

- Which input was processed?
- Which model or model digest was used?
- Which processing configuration was applied?
- What output was generated?
- Which evidence was produced?
- When was the record created?
- Can alteration or replay be detected?
- What did the analyst decide?
- Which assessments were unsupported or unavailable?

C1 establishes the need for these questions. It does not approve a specific ledger, signature scheme or storage architecture.

---

## 6. Threat and Failure Context

### 6.1 Data threats

| Threat / failure | Affected asset | Why it matters | C1 classification |
|---|---|---|---|
| **Label flipping** | Labels / annotations | Can corrupt the relationship between input content and ground truth. | FACT — named by PS |
| **Systematic mislabelling** | Labels / contributor batches | A source may introduce structured rather than random annotation errors. | FACT — named by PS |
| **Near-duplicate flooding** | Dataset composition | Repeated or slightly modified samples can distort dataset composition or contributor influence. | FACT — named by PS |
| **OOD insertion** | Dataset distribution | Foreign-domain samples may indicate accidental contamination, operational change or deliberate manipulation. | FACT — named by PS |
| **Trigger injection / poisoning** | Images, labels or training relationship | Trigger-associated samples may create hidden model behaviour. | FACT — named by PS |
| **Contributor concentration of anomalies** | Contributor / batch | Multiple sample-level findings from one source may be more informative than isolated flags. | FACT/INFERENCE — source aggregation requested by PS |

A critical interpretation boundary is that **OOD or unusual content is not automatically adversarial**. A legitimate change in sensor, terrain, illumination or acquisition condition may also produce distributional deviation.

### 6.2 Model threats

| Threat / failure | Affected asset | Why it matters | C1 classification |
|---|---|---|---|
| **Model substitution** | Model artifact | A different model may be supplied under an expected identity. | FACT — named by PS |
| **Model modification** | Model artifact | Weights or graph structure may differ from the intended artifact. | FACT — named by PS |
| **Hidden/backdoor-like behaviour** | Model behaviour | Routine validation may fail to reveal conditional malicious behaviour. | FACT — named by PS |
| **Benign re-encoding/conversion** | Model artifact | File-level changes may occur without equivalent semantic compromise. | INFERENCE / required control case |
| **Unsafe loading of untrusted model files** | Runtime environment | Parsing/deserialisation may create host security risks independent of model accuracy. | EXTERNAL SECURITY EVIDENCE [R07][R08][R09] |

The benign-conversion case is particularly important: a changed file digest is evidence that bytes differ; it is not sufficient evidence that the model is malicious.

### 6.3 Inference and provenance threats

The PS explicitly identifies replay, replacement and alteration of inference records [R01].

The relevant failure modes include:

- output modification after generation;
- replacing the recorded input;
- replacing or misidentifying the model;
- altering preprocessing or inference configuration;
- replaying an older valid output as if it were new;
- sequence deletion or reordering where sequence semantics exist; and
- presenting an integrity value whose own reference source is attacker-controlled.

The last case is relevant to the ONNX model-hub research: a digest does not form an independent root of trust if the digest and artifact are supplied by the same untrusted source [R08].

### 6.4 Operational and context threats

PS 26228 explicitly mentions distribution changes associated with terrain, season, sensor, illumination and acquisition conditions [R01].

C1 treats these as operational context changes that may be benign.

A detector therefore needs to preserve the distinction between:

1. **material shift was observed**, and
2. **the cause of that shift is malicious**.

The first may be measurable without sufficient evidence for the second.

### 6.5 Audit and evidence failures

A technically correct detector can still produce an inadequate assurance system if:

- findings are stored without supporting evidence;
- unsupported assessments are silently omitted;
- confidence is presented as a probability without calibration;
- audit entries can be altered without detection;
- external benchmark results are presented as project results;
- recommendations are treated as automatic enforcement without a defined policy;
- limitations are absent from the report; or
- an analyst cannot identify the affected asset.

These are governance failures rather than only ML failures.

---

## 7. SIH Requirements and Constraints

| Requirement | What it means for the project | C1 implication | Evidence/source |
|---|---|---|---|
| **Unified assurance scope** | Dataset, model and inference records must be considered together. | C1 must define cross-lifecycle trust boundaries. | PS §2.1–2.3 [R01] |
| **Training-data integrity** | Suspicious samples and contributor behaviour must be assessable. | C2 receives explicit data-threat categories. | PS §2.2.1 [R01] |
| **Model integrity** | Supplied models must be assessed under available access conditions. | C3 must declare access assumptions and limitations. | PS §2.2.2 [R01] |
| **Inference provenance** | Input, model/configuration and output require verifiable binding. | C4 receives the provenance requirement, not a pre-approved protocol. | PS §2.2.3 [R01] |
| **Distribution-shift assessment** | Material deviation from a declared reference distribution must be characterised. | C5 must distinguish observation of shift from unsupported attack attribution. | PS §2.2.4 [R01] |
| **Analyst-facing evidence** | Findings need reason, evidence, confidence/severity, asset and disposition. | The report must remain interpretable by a human reviewer. | PS §2.2.5 [R01] |
| **Tamper-evident audit** | Audit history must expose later alteration. | Mechanism is delegated to C4/C6. | PS §2.2.5 [R01] |
| **Unsupported-condition declaration** | The system must declare attack classes or conditions it does not support. | “Unsupported” and “unavailable” become first-class states. | PS §2.2.5–2.2.6 [R01] |
| **Offline / air-gapped operation** | Evaluation cannot depend on cloud APIs or live internet access. | C6 must package runtime assets and dependencies locally. | PS §2.2.6 [R01] |
| **Dataset-format support** | Common formats including COCO and YOLO must be ingestible. | Dataset choice must not remove format-compatibility obligations. | PS §2.2.6 [R01] |
| **Model-format support** | Organiser-defined formats include ONNX and PyTorch/TorchScript. | C3/C6 must safely handle relevant model formats. | PS §2.2.6 [R01] |
| **No baseline retraining requirement** | Initial integrity assessment cannot depend on retraining contributed models. | Candidate methods requiring retraining cannot be the sole baseline path. | PS §2.2.6 [R01] |
| **Black-box fallback** | White-box-only methods require fallback or explicit unavailable state. | Access level must be reported with each applicable assessment. | PS §2.2.6 [R01] |
| **Public/team-generated evaluation assets** | Real operational military data is not required by the PS. | Reproducible public or synthetic scenarios are valid research assets. | PS §2.3 [R01] |
| **Reproducible scenarios** | Poisoning, backdoor, substitution and tampering cases need repeatable generation/evaluation. | Detailed scenario definitions belong in C2–C6 and the Dataset Card. | PS §2.3 [R01] |
| **Submission artefacts** | Source/setup notes, report schema, reproducible audit log and coverage statement are required. | C1 establishes the evidence obligation; downstream cells produce the artefacts. | PS §2.3 [R01] |

### 7.1 What is not established as an official requirement

The original C1 also contained internal schedules, performance targets and implementation sequencing.

Those are **project planning artifacts**, not official PS requirements unless separately supported.

In particular, the source C1's 36-hour build plan is not treated in this public document as an organiser-mandated time envelope.

---

## 8. Evidence Model and Research Discipline

### 8.1 Evidence classifications

C1 uses the following classifications.

**FACT**  
A statement directly supported by the problem statement, an authoritative specification, an official repository or another identified source.

**EXTERNAL LITERATURE RESULT**  
A result reported by a paper, benchmark or external repository. It is evidence about that external evaluation only.

**PROJECT OBSERVATION**  
A result produced by this project through an executed, recorded experiment.

**INFERENCE**  
A reasoned interpretation derived from facts but not literally stated by the source.

**RECOMMENDATION**  
A proposed project treatment or engineering direction that still requires downstream adoption.

**OPEN QUESTION**  
A material issue for which C1 does not have sufficient evidence to assert a final answer.

### 8.2 Current project-evidence status

The final C1 source packet explicitly records:

```text
team_experiments: NONE
```

Accordingly, the public C1 does not present any detection rate, F1 value, false-positive rate, accuracy number or attack-detection result as a result achieved by this project.

Metrics reported by TRACE or other external implementations remain **external results**.

Targets proposed in the original C1 remain **targets**, not observations.

### 8.3 C1-OP-01 — UNAVAILABLE ≠ CLEAN

**Classification: PROJECT INTERPRETATION derived from PS §2.2.6**

```text
UNAVAILABLE ≠ CLEAN
```

The phrase is not treated as a verbatim sentence from the problem statement.

Its basis is the PS requirement that a white-box-dependent assessment must either fall back gracefully or **clearly report that the relevant assessment is unavailable** when only black-box access is present [R01].

Therefore:

- an assessment that could not run is not evidence that an asset is clean;
- unavailable evidence must be exposed rather than silently converted into a pass; and
- downstream reports need an explicit unavailable/unsupported state.

### 8.4 C1-OP-02 — ANOMALY / HASH MISMATCH ≠ PROVEN ATTACK

**Classification: PROJECT INTERPRETATION derived from evidence-based governance requirements**

```text
ANOMALY / HASH MISMATCH ≠ PROVEN ATTACK
```

This is also a C1 interpretation rather than a literal PS sentence.

Its purpose is to prevent the system from converting weak evidence into a stronger claim than the evidence supports.

Examples:

- a different hash establishes different bytes;
- a distribution-shift statistic establishes observed deviation under a defined test;
- an OOD score establishes distance under a particular feature/reference model;
- a behavioural difference establishes divergence under a particular test battery.

None of these observations alone establishes malicious intent.

### 8.5 Confidence is not automatically probability

The original C1 used terms such as confidence, severity and contributor risk.

C1 does not assume that a heuristic score is a calibrated probability.

Where downstream cells produce scores, their semantics, calibration procedure, reference population and limitations must be explicit.

---

## 9. Dataset Context and Research Implication

### 9.1 VisDrone as the primary research direction

The source C1 selected VisDrone2019 as the primary imagery direction because it contains drone-captured scenes with variation in viewpoint, scale, object density, environment, weather and illumination [R02][R03].

The official VisDrone repository describes a broader benchmark containing 10,209 static images and more than 2.6 million annotated bounding boxes captured across multiple cities and drone platforms [R02].

This makes VisDrone useful for research scenarios involving:

- aerial viewpoints;
- small and densely distributed objects;
- illumination and weather variation;
- camera/platform variation; and
- controlled experiments involving object-detection annotations.

This is a **dataset-relevance inference**, not evidence that VisDrone represents actual Indian Army operational data or deployments.

C1 does not claim that VisDrone is an official defence dataset.

### 9.2 COCO as compatibility/reference context

PS 26228 explicitly requires ingestion of common CV dataset formats including COCO and YOLO [R01].

The COCO dataset remains useful as:

- a well-established object-detection reference dataset;
- a source of compatibility tests for COCO JSON handling; and
- the evaluation domain used by the external TRACE work considered during C1 research [R04][R05][R06].

The C1 dataset direction is therefore:

```text
Primary research imagery direction:
    VisDrone / aerial-object-detection context

Secondary compatibility/reference context:
    COCO

Required format coverage:
    COCO-compatible and YOLO-compatible ingestion
```

Dataset imagery and annotation format are separate concerns. VisDrone's native annotations should not be confused with the requirement to support YOLO input; conversion and normalization belong to the dataset pipeline.

### 9.3 Representativeness limitation

VisDrone was collected in civilian urban/suburban environments in China [R02].

It cannot, by itself, establish performance under Indian military terrain, sensors, acquisition chains or mission conditions.

Its value in this project is therefore experimental and contextual, not proof of field representativeness.

### 9.4 Dataset-card boundary

The original C1 contained detailed split counts, download procedures, annotation schemas, attack-generation ideas and offline staging instructions.

Those details should live in a separate Dataset Card / Dataset Research document rather than turning C1 into the dataset implementation specification.

**Detailed dataset metadata and reproducible scenario definitions are maintained separately from the C1 mission/threat dossier.**

---

## 10. Research Findings

| ID | Finding | Classification | Evidence/source | Project implication |
|---|---|---|---|---|
| — | PS 26228 is a lifecycle integrity-assurance problem spanning data, models and inference outputs. | FACT | PS §2.1–2.3 [R01] | The project cannot be reduced to a single poisoning detector or model scanner. |
| — | Trust cannot be assumed for every contributing source. | FACT | PS §2.1 [R01] | Contributor/source identity and evidence aggregation matter. |
| — | Training-data threats explicitly include trigger injection, label flipping, systematic mislabelling, near-duplicate flooding and OOD insertion. | FACT | PS §2.2.1 [R01] | C2 must define supported and unsupported coverage for these conditions. |
| — | Model assessment must adapt to available access and state its assumptions and limitations. | FACT | PS §2.2.2 and §2.2.6 [R01] | C3 must distinguish white-box, limited-access and black-box conditions. |
| — | Protected inference records require cryptographic linkage to input, model/configuration and output, with replay controls. | FACT | PS §2.2.3 [R01] | C4 must define a verifiable provenance protocol. |
| — | Distribution shift can arise from legitimate operational conditions as well as suspicious manipulation. | FACT + INFERENCE | PS §2.2.4 [R01] | C5 must not equate measured drift with proven attack. |
| C1-OP-01 | UNAVAILABLE ≠ CLEAN. | PROJECT INTERPRETATION | Derived from PS §2.2.6 [R01] | Unsupported assessments must remain visible. |
| C1-OP-02 | ANOMALY / HASH MISMATCH ≠ PROVEN ATTACK. | PROJECT INTERPRETATION | Derived from PS evidence/governance language [R01] | Claims must not exceed evidence. |
| — | Analyst-readable reasons, evidence, confidence/severity, affected asset and disposition are part of the required output. | FACT | PS §2.2.5 [R01] | Assurance semantics matter as much as detector output. |
| — | A tamper-evident audit trail and explicit unsupported-condition declaration are required. | FACT | PS §2.2.5 [R01] | Coverage and traceability must be first-class artefacts. |
| — | Offline/air-gapped operation materially constrains dependencies and architecture. | FACT | PS §2.2.6 [R01] | C6 must eliminate live cloud/API dependencies from evaluation. |
| — | Loading contributed models creates a software-security surface in addition to an ML-integrity surface. | EXTERNAL SECURITY EVIDENCE | PyTorch/ONNX advisories and ONNX Assurance Case [R07][R08][R09] | C6 must handle model parsing/loading defensively. |
| — | TRACE provides relevant external research on test-time backdoor detection for object detection. | EXTERNAL LITERATURE RESULT | CVPR 2025 paper/repository [R05][R06] | C3 may evaluate it as a candidate method; its published metrics are not project results. |
| — | VisDrone is a reasonable aerial-imagery research direction but not evidence of military representativeness. | INFERENCE | VisDrone sources [R02][R03] | Dataset limitations must remain explicit. |
| — | No team-executed benchmark result was recorded in the C1 source packet. | PROJECT STATUS | Source C1 packet | All performance claims remain unvalidated until downstream experiments execute. |
| — | C1 does not approve downstream algorithm selection. | PROJECT STATUS | Source C1 packet | Candidate mechanisms remain subject to C2–C6. |

---

## 11. Open Questions and Unresolved Assumptions

The source C1 contained several questions that remained open even though its headline status used phrases such as “all gaps closed.”

They are preserved here.

| ID | Question | Current status | Conservative project treatment | Owner / downstream dependency |
|---|---|---|---|---|
| **VQ-03** | What model access level will be available during evaluation? | **OPEN** | Support explicit access declarations and avoid depending solely on white-box methods. | Organiser / C3 / C6 |
| **VQ-04** | Will inference records be organiser-supplied or generated by the team's pipeline? | **OPEN** | Keep provenance model capable of representing either origin until clarified. | C4 / C6 |
| **VQ-05** | Is there an organiser-defined provenance field schema beyond the PS wording? | **OPEN** | Treat the PS-required binding elements as the minimum context, not a final schema. | Organiser / C4 |
| **VQ-06** | Is the objective integrity only, or also source authentication / trusted-key identity? | **OPEN** | Do not infer authentication requirements from integrity wording alone. | Organiser / C4 |
| **VQ-07** | What does “quarantine” mean operationally during judging? | **OPEN** | Treat quarantine as a recommended disposition until enforcement semantics are defined. | Organiser / C5 / C6 |
| **VQ-08** | Which benign operational shift cases will be evaluated? | **OPEN** | Maintain benign controls covering plausible acquisition/illumination changes without claiming organiser equivalence. | C5 |
| **VQ-09** | What compute and memory envelope will be available in the air-gapped environment? | **OPEN** | Do not make GPU availability a prerequisite for the entire workflow. | Organiser / C6 |
| **VQ-10** | What evidence threshold will the organiser consider sufficient for a demonstrated finding? | **OPEN** | Report detector evidence and FP/FN behaviour transparently rather than hiding thresholds. | C2–C5 |
| **VQ-13** | Are earlier reference lists/examples in the PS mandatory or advisory? | **OPEN** | Do not interpret research examples as mandatory algorithms without explicit language. | Organiser / all cells |
| **VQ-14** | Which PyTorch/ONNX versions will be available in the evaluation environment? | **OPEN** | C6 must verify safe supported versions and retain isolation controls. | Organiser / C6 |

### 11.1 Questions closed within C1

| ID | C1 treatment |
|---|---|
| **VQ-01** | The PS text used by C1 was obtained and incorporated into the source research. |
| **VQ-11** | C1-OP-01 and C1-OP-02 were defined as project-wide evidence-discipline rules. |
| **VQ-12** | C1 treats the required coverage statement as the place to declare supported classes, assumptions, limitations and unsupported conditions. |
| **VQ-15** | The TRACE repository's documented YOLOv5 dependency commit was verified in the external repository [R06]. |

Closing these questions does **not** close VQ-03 through VQ-14 listed above.

---

## 12. Contradictions and Research Evolution

C1 evolved over several research passes. Some earlier positions were stronger than the evidence ultimately justified.

These changes are retained explicitly rather than erased.

| Topic | Earlier position in C1 | Later evidence / boundary | Current C1 interpretation |
|---|---|---|---|
| **Research status** | “Research complete,” “all gaps closed,” “unconditional advance.” | The same final packet lists ten open VQs and records `team_experiments: NONE`. | Research synthesis is mature enough for downstream work, but operational questions and implementation validation remain open. |
| **Blockchain** | Hyperledger Fabric was described as a key differentiator and effectively mandatory because the SIH theme is Blockchain & Cybersecurity. | The PS requires a **tamper-evident audit trail** but does not explicitly require blockchain [R01]. | Blockchain remains a candidate provenance/audit mechanism. Theme classification alone does not establish a mandatory implementation mechanism. Final treatment belongs to C4/C6. |
| **HMAC provenance** | The source C1 proposed HMAC-SHA256 as the primary inference-record protection mechanism. | The PS requires hashes, signatures and replay controls but does not mandate HMAC [R01]. Later provenance work is responsible for final cryptographic selection. | HMAC is historical candidate research, not C1 approval of the final protocol. |
| **Authentication semantics** | Earlier C1 assumptions leaned toward integrity-only + shared-secret HMAC. | VQ-06 remains open and the PS wording does not fully define contributor authentication/trusted-key semantics. | C4 must explicitly decide identity, key ownership, verifier trust and signature/MAC semantics. |
| **Risk scoring** | Earlier C1 contained contributor risk aggregation and overall “risk score” examples. | The PS asks for source-level aggregation and calibrated risk/confidence in scoped contexts, but this does not establish an arbitrary universal compromise probability. | Scoped evidence/confidence may be valid; an overall global risk score is not approved by C1. Final assurance semantics belong to C5. |
| **Anomaly handling** | Some early scenario text used CRITICAL/QUARANTINE outcomes as expected detector outputs. | C1-OP-02 requires evidence to remain distinct from attack attribution; VQ-07 leaves enforcement semantics open. | Severity/disposition must be evidence-based and policy-defined; anomalies are not automatically attacks. |
| **VisDrone relevance** | C1 stated that VisDrone directly matched Indian Army/DGIS operational conditions. | VisDrone is a civilian research dataset collected in China and does not establish military representativeness [R02]. | VisDrone is an aerial-imagery research choice, not evidence of actual deployment conditions. |
| **Model-file hashing** | Hash mismatch was used in some scenarios as strong tamper evidence. | Benign conversion or serialization changes can also change bytes. | Hashing is strong evidence of byte identity/non-identity, not proof of malicious semantic modification. |
| **36-hour plan** | A complete 36-hour implementation schedule was included. | C1 does not contain authoritative organiser evidence that 36 hours is an official PS constraint. | Treat it as internal planning and move it to engineering/project-management material. |
| **ONNX patch state** | On 22 September, C1 recorded `1.21.0rc1` as the available mitigation path. | Current upstream status should be checked by C6 before implementation. | C6 should resolve and pin the current stable safe version at build time instead of copying the old C1 pin mechanically. |

This evolution is intentional. Research quality improves when later evidence narrows earlier claims rather than when earlier claims are silently deleted.

---

## 13. Cross-Cell Handoffs

| From C1 | Handoff to | Why it matters |
|---|---|---|
| PS §2.2.1 data-threat categories | **C2 — Data Integrity** | Defines which data threats require explicit coverage analysis. |
| Multi-contributor/source context | **C2 — Data Integrity** | Establishes why contributor/batch aggregation matters. |
| Dataset-context research | **C2 / Dataset Card** | Provides the VisDrone/COCO rationale without dictating final preprocessing or attack-generation design. |
| Model substitution/backdoor context | **C3 — Model Integrity** | Defines the classes of model concern that assessment should address. |
| Access-level uncertainty and black-box fallback requirement | **C3 — Model Integrity** | Prevents white-box-only research from being presented as universal coverage. |
| External TRACE research | **C3 — Model Integrity** | Provides a candidate research baseline without converting TRACE results into team results. |
| Required input/model/configuration/output linkage | **C4 — Provenance / Cryptography** | Defines what provenance must protect. |
| Replay/replacement/alteration threat context | **C4 — Provenance / Cryptography** | Defines security properties without pre-selecting HMAC, asymmetric signatures or blockchain. |
| Audit/tamper-evidence requirement | **C4 / C6** | Requires a verifiable audit mechanism and durable evidence handling. |
| Terrain/season/sensor/illumination context | **C5 — Drift / Assurance Semantics** | Establishes why benign operational change must be separated from attack attribution. |
| C1-OP-01 and C1-OP-02 | **C2–C6** | Defines common evidence semantics across the system. |
| Analyst-facing fields and disposition context | **C5 / C6** | Defines what evidence must be visible to a reviewer. |
| Air-gap/offline requirement | **C6 — Engineering** | Determines packaging, dependency, logging and runtime architecture constraints. |
| PyTorch/ONNX unsafe-loading research | **C6 — Engineering** | Requires safe handling/isolation of contributed model artifacts. |
| Open VQ-03 and VQ-09 | **Organiser / C3 / C6** | Model access and compute envelope can materially affect feasible evaluation paths. |

**Handoff ≠ implementation approval.**

A mechanism appearing in historical C1 research does not become final merely because it was passed downstream.

---

## 14. Limitations

### 14.1 No project benchmark evidence in C1

The C1 source packet records no team-executed experiments.

Accordingly, C1 cannot establish:

- project F1;
- project precision or recall;
- false-positive or false-negative rates;
- project AUROC;
- project attack-detection coverage;
- project throughput;
- runtime performance;
- successful air-gapped deployment;
- successful blockchain deployment; or
- successful reproduction of TRACE.

Those require downstream evidence.

### 14.2 External results are not project results

TRACE results belong to TRACE's published/repository evaluation [R05][R06].

BackdoorBench, NIST TrojAI and any other external benchmark similarly provide literature or tooling context, not validation of this project's system [R10][R11].

### 14.3 Dataset representativeness is limited

VisDrone is useful for aerial object-detection experimentation but is not evidence of:

- Indian Army sensor characteristics;
- border or battlefield terrain;
- operational classification policy;
- defence collection procedures; or
- real DGIS deployment conditions.

### 14.4 Exact organiser evaluation assets remain unknown

C1 does not establish the exact:

- organiser-provided model;
- organiser-provided dataset;
- model access level;
- GPU availability;
- memory limit;
- inference-record schema;
- trusted-key model; or
- quarantine/enforcement semantics.

### 14.5 Coverage remains detector-specific

No detector considered by C1 should be described as universally detecting:

- every poisoning attack;
- every backdoor;
- every OOD condition;
- every semantic manipulation;
- every model substitution;
- every adversarially constructed duplicate; or
- every provenance attack.

Unsupported classes must be declared.

### 14.6 Software validation is not equivalent to safe execution

The ONNX Security Assurance Case states that semantic validation utilities are best-effort and that untrusted model handling retains important limitations [R09].

Model-file validation therefore cannot be treated as a substitute for runtime isolation and resource controls.

### 14.7 Intent is generally not directly observable

C1 focuses on integrity and assurance evidence.

A suspicious artifact may originate from:

- malicious activity;
- accidental corruption;
- annotation error;
- legitimate conversion;
- operational drift;
- contributor process differences; or
- unsupported conditions.

Where intent cannot be established, the report should not invent it.

---

## 15. Reproducibility and Research Traceability

### 15.1 Source hierarchy

C1 uses the following source priority:

1. official organiser/government/standards material;
2. original peer-reviewed academic publications;
3. official dataset or software repositories;
4. official security advisories;
5. secondary technical material;
6. external implementation/repository intelligence.

External competitor implementations are not used as authoritative evidence for this project's performance or security claims in this public edition.

### 15.2 Problem-statement source limitation

The C1 source used the SIH26228 page hosted at `sih2026.vuce.in`.

That site identifies itself as a community-maintained, unofficial archive rather than an official Government of India/SIH host [R01].

The text is retained because it is the complete PS text used by the original C1 research, but the public dossier does not mislabel the mirror itself as an official government publication.

Where an authoritative official copy is made stably available, the repository should replace or supplement R01 with that source while preserving the archived research lineage.

### 15.3 Reproducibility expectations

Later experimental documents should record, as applicable:

- dataset name and exact version;
- source URL;
- source file/checksum;
- train/validation/test selection;
- derived-scenario generation procedure;
- random seed;
- model file/checksum;
- model access level;
- preprocessing configuration;
- detector version;
- detector parameters/thresholds;
- ground-truth labels;
- environment/dependency lock;
- hardware/compute context;
- raw findings;
- TP/FP/FN definitions;
- resulting metrics;
- unsupported conditions; and
- deviations from the documented procedure.

C1 research alone does not claim that those experimental artefacts already exist.

### 15.4 Status terminology

The project should prefer terms such as:

- **SUPPORTED**
- **PARTIALLY SUPPORTED**
- **EXTERNAL RESULT**
- **PROJECT OBSERVATION**
- **INFERENCE**
- **RECOMMENDATION**
- **UNVERIFIED**
- **UNAVAILABLE**
- **OPEN QUESTION**
- **DEFERRED**
- **REJECTED**

Terms such as “fully secure,” “attack-proof,” “detects all attacks,” or “fully validated” require evidence that C1 currently does not possess.

---

## 16. References

URLs below were checked during preparation of this public edition where web verification was available.

### [R01] SIH 2026 Problem Statement PS 26228 — community archive

**Title:** Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines  
**Organisation shown in archived statement:** Ministry of Defence — Indian Army (DGIS)  
**Problem ID:** SIH26228  
**Relevant locations:** §2.1 Background; §2.2.1–§2.2.6; §2.3 Expected Solution  
**Status:** Unofficial community-maintained mirror of SIH problem statements; not treated as the authoritative host itself  
**URL:** https://sih2026.vuce.in/ps/SIH26228  
**Accessed:** 2026-09-29

### [R02] VisDrone / AISKYEYE Team, Tianjin University

**Title:** VisDrone Dataset  
**Repository:** Official VisDrone dataset repository  
**Relevant material:** dataset overview; capture conditions; static-image/video benchmark description; object classes and annotations  
**URL:** https://github.com/VisDrone/VisDrone-Dataset  
**Accessed:** 2026-09-29

### [R03] Pengfei Zhu et al.

**Title:** VisDrone-DET2019: The Vision Meets Drone Object Detection in Image Challenge Results  
**Venue:** ICCV Workshops, 2019  
**Relevant material:** VisDrone object-detection benchmark composition and evaluation protocol  
**URL:** https://openaccess.thecvf.com/content_ICCVW_2019/papers/VISDrone/Du_VisDrone-DET2019_The_Vision_Meets_Drone_Object_Detection_in_Image_Challenge_ICCVW_2019_paper.pdf  
**Accessed:** 2026-09-29

### [R04] COCO Consortium

**Title:** COCO — Common Objects in Context  
**Dataset / benchmark:** Microsoft COCO  
**Relevant material:** dataset overview; object detection dataset and evaluation resources  
**URL:** https://cocodataset.org/  
**Accessed:** 2026-09-29

### [R05] Hangtao Zhang et al.

**Title:** Test-Time Backdoor Detection for Object Detection Models  
**Venue:** IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2025  
**Pages:** 24377–24386  
**Relevant material:** TRACE methodology and external evaluation results  
**URL:** https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Test-Time_Backdoor_Detection_for_Object_Detection_Models_CVPR_2025_paper.html  
**Accessed:** 2026-09-29

### [R06] TRACE Authors

**Title:** TRACE — Test-Time Backdoor Detection for Object Detection Models  
**Repository:** Official code repository accompanying the CVPR 2025 paper  
**Relevant material:** YOLOv5/COCO setup, released checkpoints, test workflow, repository-reported evaluation results  
**URL:** https://github.com/Rookie143/Trace  
**Accessed:** 2026-09-29

### [R07] PyTorch Project

**Title:** Loading a malicious PyTorch checkpoint with `weights_only=True` can result in arbitrary code execution  
**Advisory:** GHSA-63cw-57p8-fm3p / CVE-2026-24747  
**Relevant material:** affected versions, patched versions, malicious checkpoint threat  
**URL:** https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p  
**Accessed:** 2026-09-29

### [R08] ONNX Project

**Title:** Trust Check Bypass in `onnx.hub.load()` via `silent=True`  
**Advisory:** GHSA-hqmj-h5c6-369m / CVE-2026-28500  
**Relevant material:** repository trust warning bypass and attacker-controlled manifest/hash problem  
**URL:** https://github.com/onnx/onnx/security/advisories/GHSA-hqmj-h5c6-369m  
**Accessed:** 2026-09-29

### [R09] ONNX Project

**Title:** ONNX Security Assurance Case  
**Version:** 1.2  
**Date:** August 2026  
**Relevant material:** general scope and assurances; best-effort semantic validation; malicious-model threat model; untrusted-input limitations  
**URL:** https://onnx.ai/onnx/repo-docs/AssuranceCase.html  
**Accessed:** 2026-09-29

### [R10] National Institute of Standards and Technology (NIST)

**Title:** TrojAI — Trojans in Artificial Intelligence  
**Programme:** NIST Information Technology Laboratory  
**Relevant material:** model-Trojan threat context and evaluation resources  
**URL:** https://www.nist.gov/itl/ai/trojai  
**Accessed:** 2026-09-29

### [R11] SCLBD

**Title:** BackdoorBench: A Comprehensive Benchmark of Backdoor Learning  
**Repository / benchmark:** BackdoorBench  
**Relevant material:** backdoor-learning attack/defence benchmark context; dataset/model scope  
**URL:** https://github.com/SCLBD/BackdoorBench  
**Accessed:** 2026-09-29

---

## 17. Claim / Source Traceability

| Claim ID / source anchor | Claim | Type | Primary source | Exact location |
|---|---|---|---|---|
| **PS §2.1** | Multi-contributor CV pipelines create risks across data, model and inference stages. | FACT | [R01] | §2.1 Background |
| **PS §2.2.1** | Data-integrity scope includes trigger injection, label manipulation, near-duplicate flooding and OOD insertion. | FACT | [R01] | §2.2.1 |
| **PS §2.2.2** | Model assessment must reflect the available access level and declare confidence/limitations. | FACT | [R01] | §2.2.2 |
| **PS §2.2.3** | Inference provenance must bind input, model/configuration and output and make alteration/replay detectable. | FACT | [R01] | §2.2.3 |
| **PS §2.2.4** | Distribution shift includes terrain, season, sensor, illumination and acquisition changes. | FACT | [R01] | §2.2.4 |
| **PS §2.2.5** | Findings require reasons/evidence and the system requires a tamper-evident audit trail and coverage declaration. | FACT | [R01] | §2.2.5 |
| **PS §2.2.6** | Evaluation must operate offline and unsupported white-box methods must expose black-box unavailability/fallback. | FACT | [R01] | §2.2.6 |
| **C1-OP-01** | UNAVAILABLE ≠ CLEAN. | PROJECT INTERPRETATION | [R01] | Derived from §2.2.6; phrase is not claimed as verbatim PS text |
| **C1-OP-02** | ANOMALY / HASH MISMATCH ≠ PROVEN ATTACK. | PROJECT INTERPRETATION | [R01] | Derived from PS evidence/governance language; phrase is not claimed as verbatim PS text |
| **VisDrone context** | VisDrone provides drone-captured scenes with broad variations useful for aerial-object-detection research. | EXTERNAL DATASET FACT | [R02][R03] | R02 repository overview; R03 dataset/challenge description |
| **TRACE** | TRACE is an external CVPR 2025 method for test-time backdoor detection in object-detection models. | EXTERNAL LITERATURE RESULT | [R05][R06] | R05 abstract/experiments; R06 README |
| **CVE-2026-24747** | Untrusted PyTorch checkpoint loading affected versions prior to the stated patched release. | EXTERNAL SECURITY FACT | [R07] | “Affected versions,” “Patched versions,” “Description” |
| **CVE-2026-28500** | `onnx.hub.load(..., silent=True)` could bypass repository trust warnings and rely on attacker-controlled manifest integrity information. | EXTERNAL SECURITY FACT | [R08] | Advisory “What's the issue” / impact |
| **ONNX assurance limitation** | ONNX semantic checking is best-effort and untrusted model handling retains important limitations. | EXTERNAL SECURITY FACT | [R09] | “General scope and assurances” and “Threat Model” |
| **Project metrics** | C1 contains no team-executed benchmark results. | PROJECT STATUS | Source C1 packet | `research_completed → team_experiments: NONE` |
| **Downstream selection** | C1 does not approve final downstream algorithms. | PROJECT STATUS | Source C1 packet | `checkpoint_decision → downstream_algorithm_selection: NOT_APPROVED_BY_C1` |

---

## 18. C1 Research Conclusion

C1 establishes the problem and evidence boundaries for SIH 2026 PS 26228.

The research supports the following conclusions:

1. The problem is a **multi-surface CV integrity-assurance problem**, not merely a model-accuracy or poisoning-detection task.
2. Data, model, inference and provenance/audit surfaces must be considered as connected parts of one lifecycle.
3. Contributed assets cannot be assumed trustworthy merely because their source is known.
4. Findings need analyst-readable evidence, stated limitations and explicit handling of unsupported or unavailable assessments.
5. Distributional or behavioural anomaly is not, by itself, evidence of malicious intent.
6. Offline operation, multiple dataset/model formats, no mandatory baseline retraining and black-box fallback materially constrain the engineering design.
7. VisDrone is a defensible aerial-imagery research direction, while COCO remains useful for compatibility and external-reference work; neither dataset should be presented as operational military ground truth.
8. External research such as TRACE, NIST TrojAI and BackdoorBench can inform downstream methodology but does not constitute project validation.
9. Untrusted model loading creates software-security risks that C6 must address independently of model-integrity detection.
10. The final source C1 contained **no team-executed experiments**, so proposed metrics, scenarios and architectures remain unvalidated until downstream evidence is produced.

C1 does **not** establish the final:

- data-integrity detector set;
- model-integrity algorithm;
- cryptographic protocol;
- blockchain requirement;
- HMAC/asymmetric-signing decision;
- distribution-shift algorithm;
- global assurance/risk-score semantics;
- quarantine/enforcement policy;
- model access level;
- compute envelope; or
- achieved project performance.

Those questions are either open or intentionally handed to C2–C6.

The appropriate C1 status is therefore:

> **Research synthesis complete for the mission/threat/operational domain; downstream implementation, experimentation and validation remain separate obligations.**

Uncertainty is not a defect in this conclusion. Making the boundary between established evidence, inference, recommendation and unresolved questions explicit is itself part of trustworthy assurance research.
