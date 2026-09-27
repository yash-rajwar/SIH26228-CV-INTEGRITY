# C3 — Model Security Research

> **Public Research Edition — SIH 2026 PS 26228**  
> **Source artifact:** C3-V2-001  
> **Source packet:** C3-SYN-V2-2026-09-23-01  
> **Research lineage:** C3-PKT-V1-2026-09-23-01 → C3-PKT-V1-RT-2026-09-23-01 → REVERIFY → C3-V2-001 → Public Research Edition  
> **Domain:** C3 — Model Security  
> **Source synthesis date:** 2026-09-23  
> **Public-link verification refresh:** 2026-09-29  
> **Status:** Research / coverage-envelope document. **Not a safety declaration, certification, or production-readiness claim.**

---

## Document Metadata

| Field | Value |
|---|---|
| Project | SIH 2026 PS 26228 — *Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines* |
| C3 responsibility | Model Security |
| Primary model formats in scope | ONNX (`.onnx`), PyTorch weights/checkpoints (`.pt`, `.pth`), TorchScript (`.pt`) where applicable |
| Primary target context | Computer-vision object detection, including YOLO/COCO-oriented workflows |
| Assessment surfaces | Artifact identity, behavioral integrity, safe loading / assessment-process security |
| Access model | Black-box, grey-box, white-box, internal-activation access; refined by a capability vector |
| Offline requirement | Core workflow must operate in an air-gapped environment without external APIs |
| Retraining constraint | Baseline integrity assessment must not require retraining the contributed model |
| Evidence posture | Literature evidence, source/repository inspection, engineering recommendations, and planned experiments are kept separate |
| Project validation posture | The C3 behavioral experiments in this packet have **not** been executed; no universal model-security claim is made |

### Evidence and status vocabulary

This document uses the source packet's status vocabulary:

`BUILD` · `PROTOTYPE` · `DEFER` · `REJECT` · `UNAVAILABLE` · `UNVERIFIABLE` · `PARTIALLY_SUPPORTED` · `SUPPORTED` · `NOT_VERIFIED`

These terms are intentionally narrow:

- **BUILD ≠ IMPLEMENTED.**
- **PROTOTYPE ≠ VALIDATED.**
- **LITERATURE RESULT ≠ PROJECT RESULT.**
- **SOURCE OR REPOSITORY INSPECTION ≠ TEAM EXECUTION.**
- **METHOD EXISTENCE ≠ YOLO VALIDITY.**

The central C3 principle is unchanged:

> **No single detector, and no combination of the currently evaluated methods, establishes universal model safety.**

---

## 1. Research Objective

C3 studies how a contributed computer-vision model artifact can be assessed under declared access, format, runtime, and reference constraints without converting narrow evidence into a global security verdict.

The research separates three questions that must not be collapsed:

1. **Artifact Identity** — Is this the same artifact, or structurally the same kind of artifact, as an independently trusted reference?
2. **Behavioral Integrity** — Does the model behave consistently with a trusted reference on a declared test space, and do selected trigger-oriented probes expose anomalous behavior?
3. **Safe Loading** — Can the assurance system itself parse or execute the submitted artifact without allowing the submitted artifact to compromise the assessor?

These are separate evidence classes. Identity does not prove behavior. Behavioral consistency over a finite battery does not prove the absence of backdoors. Successful parsing does not establish benignness. Safe loading is a prerequisite for trustworthy assessment, not evidence that the model is trustworthy.

A useful public interpretation of C3 is therefore:

```text
ACCESS
  ↓
METHOD AVAILABILITY
  ↓
EVIDENCE CLASS
  ↓
DECLARED LIMITATIONS
  ↓
ANALYST INTERPRETATION
```

---

## 2. C3 Scope and Boundaries

### 2.1 In scope

C3 covers model-security research for submitted model artifacts, including:

- exact-byte model identity;
- structural identity and model fingerprinting;
- reference-relative behavioral comparison;
- backdoor/Trojan-oriented behavioral probes;
- access-dependent detection methods;
- hostile model-file handling;
- safe parsing and loading;
- ONNX external-data security boundaries;
- PyTorch / TorchScript deserialization risk;
- trusted-reference integrity;
- format/runtime/version boundaries;
- quantization-related detection gaps;
- finite behavioral-test limitations;
- negative controls and reproducibility requirements.

The source dossier states that C3 covers **T11 through T15**. The dossier explicitly names and develops **T11**, **T12/T13**, and the safe-loading threat label **T-LOAD**. It does not provide separate public threat-card definitions for T14 and T15; this edition therefore does not invent them.

### 2.2 Out of scope / handoff boundaries

C3 does **not** own:

- dataset integrity and annotation integrity → **C2**;
- final cryptographic provenance-protocol selection → **C4**;
- final assurance semantics, risk calibration, and analyst governance → **C5**;
- final runtime selection, isolation implementation, build authorization, and experiment execution → **C6**;
- mission/threat-context ownership → **C1**.

C3 provides evidence, access conditions, coverage gaps, experiment requirements, and handoff contracts. It does not issue an overall `SAFE`, `CLEAN`, or `BACKDOOR-FREE` verdict.

---

## 3. Problem Statement Requirements Relevant to Model Security

The SIH 2026 problem statement imposes several constraints that directly shape C3.

### 3.1 Explicit requirements

| Requirement | C3 implication |
|---|---|
| Offline / air-gapped operation | Core assessment cannot depend on cloud APIs or remote services. Libraries, fixtures, and reference material required at run time must be packaged locally. |
| Model-agnostic assessment | Format coverage must be reported per tested format/runtime tuple; results cannot be assumed to transfer across ONNX, PyTorch, and TorchScript. |
| COCO / YOLO-oriented input/output context | Behavioral comparison requires a declared detection-output canonicalization. Classification-benchmark evidence does not automatically transfer to object detection. |
| No baseline retraining requirement | A method that requires retraining the trusted baseline is incompatible with the baseline C3 path. |
| Public or team-generated test assets | Trigger fixtures, negative controls, and benchmark inputs must be reproducible and legally usable. |
| Variable access | Methods must state their required access and must degrade to `UNAVAILABLE` when that access is absent. |
| Human-readable evidence and limitations | Every result needs evidence scope, confidence/status, and unsupported-condition metadata. |

### 3.2 Inferred operational requirements

The source packet identifies additional conditions that are logically necessary even when not fully fixed by the problem statement:

- **Trusted reference availability.** The strongest identity and paired-behavior claims require an independently trusted digest, model, or expected-output set.
- **Threshold governance.** False-positive / false-negative operating thresholds are not a C3 invention. C3 supplies raw measurements and coverage metadata; C5 owns calibration and analyst meaning.
- **YOLO variant and exporter definition.** YOLOv5, YOLOv8, YOLOv9 and other variants may differ in detection-head layout, NMS behavior, dynamic-shape handling, opset use, and export/runtime characteristics.
- **Quantization declaration.** FP32, FP16 and INT8 artifacts must not be treated as equivalent assessment targets.
- **Execution-provider declaration.** ONNX Runtime provider choice and framework/runtime versions are part of the evidence envelope.

---

## 4. Access Model

Access is not a cosmetic label. It determines which methods are possible.

| Access mode | Observable | Not guaranteed | Example C3 methods |
|---|---|---|---|
| **Black-box** | Outputs for supplied inputs | Weights, architecture, internal activations, gradients | Behavioral battery; B3D; STRIP-like only if soft outputs are exposed |
| **Grey-box** | Architecture and/or logits; possibly partial metadata | Full gradients, complete internal-state control | Structural fingerprinting; limited metadata inspection |
| **White-box** | Weights, gradients, activation maps, runtime hooks | — | Neural Cleanse; methods needing differentiable model access |
| **INTERNAL-ACTIVATION ACCESS** | Internal activation reads and controlled interventions | Full gradient optimization is not implied | ABS; Activation Clustering needs activation extraction plus data |

A more precise capability vector is retained from the source research:

```text
{
  outputs,
  logits,
  architecture,
  internal_activations,
  weights,
  gradients,
  runtime_hooks
}
```

This vector avoids forcing every real deployment into a coarse black/grey/white category. It is especially useful for ABS and Activation Clustering, whose practical requirement is better expressed as **internal-activation capability** than by an unresolved grey-vs-white label.

### 4.1 Fallback rule

A missing capability does not become positive evidence.

```text
REQUIRED CAPABILITY ABSENT
        ↓
     UNAVAILABLE
        ↓
reported to downstream assurance
        ↓
never mapped to CLEAN
```

**UNAVAILABLE ≠ CLEAN.**

---

## 5. Model Security Surfaces

## 5.1 Artifact Identity

Artifact identity asks whether a submitted file is byte-identical to, or structurally consistent with, an independently trusted reference.

### Exact-byte identity

SHA-256 is a deterministic, format-agnostic identity primitive. A pre-parse digest can be computed before any framework-specific parsing or model execution.

A `MATCH` establishes only:

> The submitted file is byte-for-byte identical to the referenced file represented by the independently stored digest.

It does **not** establish:

- clean training history;
- legitimate weights;
- absence of a backdoor;
- behavioral equivalence to a different reference model;
- global model safety.

A poisoned model can match a digest if the digest was itself generated from that poisoned model.

### Structural identity

A structural fingerprint can normalize and hash fields such as:

- graph/operator inventory;
- graph connectivity;
- input/output signatures;
- tensor shapes;
- dtype manifest;
- parameter-shape metadata;
- selected export metadata.

This may be less sensitive than raw file hashing to benign metadata/export changes, but it introduces a different limitation: **topology is not weights**. A weight-level backdoor can preserve architecture and tensor shape.

### Required semantic boundary

**MATCH ≠ SAFE.**  
**DIFFERENT ≠ MALICIOUS.**

---

## 5.2 Behavioral Integrity

Behavioral integrity asks whether the submitted model responds to a declared set of inputs in a way that is consistent with a trusted reference and whether selected trigger-oriented probes expose anomalous output behavior.

The strongest C3 behavioral design is paired testing:

```text
SAME INPUT
  ├──→ trusted reference model
  └──→ submitted model
            ↓
      canonicalize outputs
            ↓
      compare declared metrics
```

The comparison may include:

- class-confidence behavior;
- detection counts;
- object-class agreement;
- bounding-box coordinates and geometry;
- localization changes;
- object disappearance / injection behavior;
- nuisance-transform stability.

The source packet is explicit that a finite behavioral battery provides **bounded consistency evidence only**.

A model can be trained to behave normally on a known battery and trigger elsewhere. Increasing battery size can improve empirical coverage but cannot convert a finite input set into proof over the full input space.

### Required semantic boundary

**NOT_DETECTED ≠ ABSENT.**

A behavioral anomaly also does not by itself prove malicious intent. Benign re-export, quantization, fine-tuning, preprocessing drift, or implementation mismatch can produce divergence.

---

## 5.3 Safe Loading

Safe loading is the security boundary of the **assessor**.

A submitted model is not merely an object to inspect; it is potentially hostile input to the assurance system. Unsafe deserialization, path traversal, resource exhaustion, custom operators, or parser/runtime vulnerabilities can compromise the process that is supposed to generate the evidence.

Therefore:

> Model-assessment correctness depends on the integrity of the loading and execution boundary.

The required conceptual order is:

```text
UNTRUSTED MODEL
      ↓
PRE-PARSE HASH
      ↓
QUARANTINE
      ↓
ISOLATED PARSER / LOADER
      ↓
STRUCTURAL PARSE
      ↓
ISOLATED INFERENCE
      ↓
TYPED OUTPUT EXTRACTION
      ↓
OUT-OF-BAND ANALYSIS
```

This is a required architecture/control objective where implementation evidence is absent. It is **not** a claim that the final target host has already been validated.

---

## 6. Threat Taxonomy

| Threat ID / label | Threat | Threat exists? | Detectable by current C3 mechanisms? | Project-validated? |
|---|---|---:|---|---|
| **T11** | Model substitution or modification | Yes | Exact substitution can be detected relative to an independent digest; structural changes may be partially exposed; weight-level changes can bypass topology-only fingerprints | No project experiment executed |
| **T12 / T13** | Trojan / backdoor behavior | Yes | Partially observable through finite behavioral testing and access-dependent research methods | No project YOLO backdoor validation executed |
| **T-LOAD** | Malicious model loading / assessor compromise | Yes | Controlled through architecture and isolation rather than a backdoor detector | Safe-loading experiment not yet executed |

### 6.1 T11 — Model substitution and modification

Two broad cases are distinguished:

1. complete replacement with a different artifact; and
2. internal modification that preserves superficial identity characteristics.

Cryptographic hashing is strong for exact byte identity but weak for the second case if the reference itself is poisoned or if an authorized artifact contains a training-time backdoor.

Benign causes of `DIFFERENT` include:

- re-export;
- exporter/version metadata changes;
- opset changes;
- quantization;
- pruning;
- format conversion.

`DIFFERENT` therefore means byte non-identity, cause unspecified.

### 6.2 T12 / T13 — Trigger-conditioned behavior

Backdoor behavior can include:

- misclassification;
- bounding-box suppression;
- localization change;
- object injection;
- object disappearance;
- geometry manipulation.

The trigger can be:

- static patch;
- spatial marker;
- spectral or texture condition;
- shape condition;
- scene-level relation;
- dynamic multi-object interaction.

A finite black-box detector sees only behavior that is activated inside the exercised input domain.

### 6.3 Dynamic and relational triggers

The source packet highlighted three object-detection attack families as coverage warnings.

- **ShrinkBox** manipulates bounding-box geometry, demonstrating why class-label-only comparison can miss security-relevant behavior.
- **Phantom** uses physical object interactions and NMS-exploited dynamic triggers, demonstrating why static single-object trigger assumptions are incomplete.
- **CIS-BA** uses continuous inter-object interaction conditions, demonstrating why scene-level relations require different fixture design from static patches.

The original dossier treated the numerical results for these papers as unverified. The public-link verification refresh on 2026-09-29 found primary/publication sources for the cited results. Those are **external literature results**, not project benchmarks; details are recorded in Sections 19 and 24.

### 6.4 T-LOAD — hostile model artifacts

Relevant attack surfaces include:

- unsafe pickle deserialization;
- malformed checkpoint structures;
- external-data path escape;
- symlink / hardlink traversal;
- attribute manipulation;
- resource exhaustion;
- unsupported/custom operators;
- runtime/parser vulnerabilities.

Threat existence, mitigation design, and validated mitigation are separate propositions.

---

## 7. Evidence-Backed Research Findings

### 7.1 Safe loading

**Finding F-01 — unsafe/untrusted PyTorch deserialization is a critical assessor risk.**  
PyTorch documentation warns against loading untrusted data, and unrestricted pickle-based checkpoint loading can execute attacker-controlled code. The C3 architecture therefore treats model loading as hostile-input processing, not ordinary application I/O.

**Finding F-02 — `weights_only=True` is a mitigation, not a complete trust boundary.**  
The original packet correctly narrowed this to a version-qualified mitigation. The 2026-09-29 verification refresh additionally confirmed PyTorch advisory **GHSA-63cw-57p8-fm3p / CVE-2026-24747**, with affected versions below the fixed 2.10.0 boundary and patched version 2.10.0. This strengthens the source packet's previously partial version claim. It does **not** remove the requirement for isolation, resource controls, and version pinning.

**Finding F-03 — ONNX external data is a filesystem-security surface.**  
Current ONNX security documentation explicitly documents path traversal, symlink traversal, hardlink attacks, attribute injection, and resource exhaustion, and describes layered path-containment and secure-open defenses.

The original packet additionally asserted that the ONNX checker does not automatically protect `onnxruntime.InferenceSession`. The 2026-09-29 verification refresh did not find a primary ONNX Runtime source establishing the packet's exact runtime/version claim. That portion therefore remains **NOT VERIFIED**. C3 still recommends an independent runtime isolation boundary because checker validation and inference execution are distinct processing stages.

### 7.2 Access corrections

- **STRIP:** original STRIP relies on output-distribution entropy and therefore requires soft probability/logit-like information; hard-label-only access is insufficient for the original formulation.
- **Neural Cleanse:** requires differentiable, gradient-based model access. Earlier "inference-only" wording is rejected.
- **ABS:** requires internal activation read/intervention capability.
- **Activation Clustering:** requires internal activation extraction and data samples; model-only conditions are insufficient for the original workflow.
- **B3D:** is query-based and gradient-free at inference, but C3's YOLO output-abstraction and query-cost questions remain unresolved.

### 7.3 Quantization

External literature reports that INT8 quantization reduced the detection rate of five evaluated backdoor defenses to 0% on CIFAR-10 and GTSRB under the study's BadNet setting while attack success remained above 99%.

This is **classification-domain evidence**.

It does not establish the same result for:

- YOLO;
- COCO detection;
- ONNX;
- TorchScript;
- C3's behavioral battery;
- the project's selected runtime.

**YOLO INT8 transfer = NOT_VERIFIED** until `EXP-C3-06` is executed.

### 7.4 TrojAI scope

The 2026-09-29 verification refresh confirms NIST TrojAI Round 13's published object-detection model levels as:

```text
ssd
fasterrcnn
detr
```

YOLO is not listed in the official Round 13 experimental design. Round 13's trigger taxonomy remains useful as a **fixture-design reference**, but Round 13 detector results are not YOLO validation.

### 7.5 ULP deployment precondition

ULP has a black-box-looking runtime interface but depends on a precomputed pattern/classifier artifact derived from populations of clean and poisoned models. The official ULP repository documents model-population generation at substantial scale.

The current C3 packet does not establish a public, reproducible YOLO/COCO ULP library suitable for direct deployment. Building such a library from scratch conflicts with the project's five-day/no-retraining baseline constraint.

### 7.6 STRIP adaptive-evasion limitation

STRIP-like detection depends on a separable entropy signal. The source packet retains the mechanism-level warning that adaptive behavior can collapse the clean/triggered entropy separation.

The specific **AUROC 0.562** value cited in the internal red-team packet remains **UNVERIFIABLE** in this public edition because the exact primary source location was not established during the verification refresh.

---

## 8. Candidate Methods

## 8.1 C3-RC-01 — SHA-256 Artifact Digest

**Purpose**  
Provide exact byte-level identity evidence before any model parsing or deserialization.

**Threats addressed**  
Exact artifact substitution; unexpected byte modification.

**Access required**  
File-only access. No model parsing, execution, gradients, activations, or architecture access.

**Inputs**  
Submitted model bytes; independently stored trusted reference digest.

**Reference required**  
Yes — an independently trusted digest produced from a separately attested artifact.

**Execution mode**  
Offline, pre-parse.

**Method status**  
**BUILD** as an identity mechanism. BUILD does not mean implemented in the project.

**Evidence basis**  
Standard cryptographic hashing; deterministic and format-agnostic.

**Project-specific evidence**  
No project execution record is needed to establish the semantics of SHA-256 itself, but the project's reference-management and evidence-schema behavior still require implementation and tests.

**Known limitations**

- Match is only byte identity.
- Mismatch does not identify cause.
- Re-export, pruning, quantization, metadata changes, or format conversion cause different hashes.
- A poisoned artifact can still match if the reference digest came from the same poisoned artifact.

**Failure / evasion cases**  
Compromised reference registration; replacement of both artifact and reference; training-time backdoor already present in trusted reference.

**YOLO / COCO applicability**  
Format independent; no YOLO-specific behavior is assessed.

**ONNX / PyTorch / TorchScript applicability**  
Applicable to all as raw files.

**Five-day feasibility**  
High; included in core path.

**Required validation**  
`EXP-C3-01` for controlled-variant behavior and evidence-schema semantics.

**Sources**  
SIH requirement context; PyTorch/ONNX format references; source dossier C3-RC-01.

---

## 8.2 C3-RC-02 — Canonical Structural Fingerprint

**Purpose**  
Provide a secondary model-identity layer based on deterministic normalization of model structure.

**Threats addressed**  
Some architecture substitutions, graph changes, operator changes, incompatible I/O changes.

**Access required**  
Safely isolated structural parsing; architecture/graph visibility. Gradients are not required.

**Inputs**  
Parsed graph/architecture metadata, input/output signatures, tensor-shape and dtype information.

**Reference required**  
Yes — independently stored reference fingerprint for comparative use.

**Execution mode**  
Offline; parser runs inside the safe-loading boundary.

**Method status**  
**PROTOTYPE**.

**Evidence basis**  
ONNX graph/protobuf inspection is technically established; a cross-format YOLO canonicalization scheme is not validated in this packet.

**Project-specific evidence**  
No executed re-export stability study.

**Known limitations**

- Topology-only fingerprints are blind to changed weight values that preserve structure.
- Exporter/opset/version differences can cause benign divergence.
- Adding weight statistics increases modification sensitivity but reduces stability under quantization/fine-tuning.

**Failure / evasion cases**  
Weight-level backdoor with unchanged graph and tensor shapes.

**YOLO / COCO applicability**  
Requires YOLO/export-specific canonicalization and stability testing.

**ONNX / PyTorch / TorchScript applicability**

- ONNX: strongest conceptual support through explicit graph representation.
- PyTorch weights: architecture extraction may depend on accompanying code/model definition.
- TorchScript: parser-dependent and subject to safe-loading constraints.

**Five-day feasibility**  
Prototype feasible; stability claim not feasible without experiment.

**Required validation**  
`EXP-C3-02`.

**Sources**  
Source dossier C3-RC-02; ONNX graph/runtime documentation.

---

## 8.3 C3-RC-03 — Deterministic Behavioral Battery

**Purpose**  
Measure reference-relative output consistency on a fixed, declared, reproducible input battery.

**Threats addressed**  
Observable trigger-conditioned behavior, selected substitution/modification effects, class/geometry output anomalies.

**Access required**  
Strict black-box output access is sufficient for paired comparison, provided the output representation can be canonicalized.

**Inputs**

- ordinary images;
- background/negative samples;
- nuisance/preprocessing transformations;
- synthetic trigger fixtures;
- geometry-oriented cases;
- benign-modified negative controls.

**Reference required**  
Trusted reference model, or trusted stored reference outputs generated from a verified reference.

**Execution mode**  
Offline, with both submitted-model and reference inference inside controlled runtime boundaries.

**Method status**  
**BUILD (mechanism) / PROTOTYPE (backdoor-specific claims).**

**Evidence basis**  
Differential behavioral testing is established as a general paradigm. Project-specific YOLO backdoor discrimination is not yet demonstrated.

**Project-specific evidence**  
No executed `EXP-C3-03` or `EXP-C3-06`.

**Known limitations**

- finite input space;
- can be overfit/evaded;
- dynamic and relational triggers may fall outside fixture coverage;
- quantization changes behavior;
- canonicalization choices affect comparison;
- reference compromise defeats shared-behavior detection.

**Failure / evasion cases**

- model intentionally trained to agree on the known battery;
- relational trigger not represented in a single-image fixture;
- trigger tied to preprocessing/runtime conditions not present in the battery;
- threshold chosen without adequate benign-negative controls.

**YOLO / COCO applicability**  
Potentially strong, but only after output canonicalization is fixed. Comparison must include bounding-box geometry, not only class labels.

**ONNX / PyTorch / TorchScript applicability**  
Potentially all three through the isolated loader and a common typed output schema.

**Five-day feasibility**  
Core candidate.

**Required validation**  
`EXP-C3-03`; `EXP-C3-06` for INT8.

**Sources**  
SIH PS model-integrity requirement; source dossier C3-RC-03; NIST TrojAI taxonomy as fixture-design input only.

---

## 8.4 C3-RC-04 — STRIP-like Perturbation / Output-Entropy Probe

**Purpose**  
Detect inputs whose model predictions remain unusually stable under intentional perturbation, producing a low-entropy signature.

**Threats addressed**  
Selected trigger-conditioned behaviors that dominate prediction under perturbation.

**Access required**  
Black-box with **soft output** (probabilities/logits or an equivalent continuous detection representation). Hard-label-only access is insufficient for the original STRIP formulation.

**Inputs**  
Candidate image plus a clean reference image pool used for perturbation.

**Reference required**  
A clean reference image pool; not necessarily a reference model.

**Execution mode**  
Offline; repeated inference queries.

**Method status**  
**PROTOTYPE**, blocked until YOLO output representation is declared.

**Evidence basis**  
Original STRIP paper and code establish the classification formulation. YOLO adaptation is not established.

**Project-specific evidence**  
No project STRIP/YOLO run.

**Known limitations**

- entropy representation for multi-box detection is unresolved;
- adaptive evasion can collapse the entropy gap;
- reference-image distribution mismatch can reduce meaning;
- post-NMS entropy cannot observe all pre-NMS candidate-volume or latency signals.

**Failure / evasion cases**  
Adaptive trigger training; benign model with unusually stable outputs; detector representation that discards the signal of interest.

**YOLO / COCO applicability**  
**Not established in the current C3 research packet.**

**ONNX / PyTorch / TorchScript applicability**  
Format-independent in principle if the necessary soft output is exposed; runtime output interface is the binding constraint.

**Five-day feasibility**  
Parallel research spike only; not core path.

**Required validation**  
`EXP-C3-04`.

**Sources**  
STRIP paper and authors' public code; source dossier C3-RC-04.

---

## 8.5 C3-RC-05 — B3D-Style Query-Based Trigger Reconstruction

**Purpose**  
Reverse-engineer candidate trigger patterns through gradient-free model queries.

**Threats addressed**  
Backdoor behaviors recoverable through an optimization objective over model outputs.

**Access required**  
Black-box query access.

**Inputs**  
Queries to the target model; original B3D also discusses clean or synthetic samples.

**Reference required**  
No trusted reference model is inherently required, but an output abstraction and optimization objective are required.

**Execution mode**  
Offline, repeated queries.

**Method status**  
**DEFER**.

**Evidence basis**  
B3D is a published ICCV 2021 black-box method using gradient-free trigger reconstruction.

**Project-specific evidence**  
No YOLO query-cost measurement; no detector-output adaptation executed.

**Known limitations**

- query budget for an 80+ class YOLO model is unknown;
- classification objective does not directly map to a post-NMS set of detections;
- reconstructed patterns are candidate triggers, not proof of malicious training.

**Failure / evasion cases**  
Query budget exhaustion; objective mismatch; benign unusual patterns optimized as candidate triggers.

**YOLO / COCO applicability**  
**Not established in the current C3 research packet.**

**ONNX / PyTorch / TorchScript applicability**  
Potentially format-independent behind a query interface; practical output adaptation unresolved.

**Five-day feasibility**  
Deferred.

**Required validation**  
`EXP-C3-07` is a deferred adaptation experiment.

**Sources**  
Dong et al., ICCV 2021; source dossier C3-RC-05.

---

## 8.6 C3-RC-06 — Neural Cleanse

**Purpose**  
Reverse-engineer small class-targeted triggers through gradient-based optimization and identify anomalous target classes using trigger-size outlier analysis.

**Threats addressed**  
Backdoors whose target class admits an unusually small/easy reconstructed trigger under the method's assumptions.

**Access required**  
White-box, differentiable gradient access.

**Inputs**  
Target model and suitable inputs for the optimization process.

**Reference required**  
No separate trusted model is required by the original method; experiment/input assumptions still apply.

**Execution mode**  
Gradient-based optimization per target class.

**Method status**  
**DEFER**.

**Evidence basis**  
IEEE S&P 2019 publication and the authors' Keras/TensorFlow implementation.

**Project-specific evidence**  
No YOLO implementation, no project runtime benchmark, no ONNX differentiation path, no measured project FPR.

**Known limitations**

- not inference-only;
- expensive per-class optimization;
- original implementation stack differs from project target formats;
- clean-model false positives are possible;
- quantization-domain transfer is unresolved.

**Failure / evasion cases**  
Non-small triggers, distributed triggers, optimization failure, architecture/output mismatch.

**YOLO / COCO applicability**  
Not validated in this packet.

**ONNX / PyTorch / TorchScript applicability**

- PyTorch/TorchScript: possible only with a differentiable implementation and compatible graph/runtime.
- ONNX: differentiability path not established.

**Five-day feasibility**  
Deferred. The source dossier's ">2 days/class" CPU statement is an **inference, not a measured benchmark** and must not be reported as project timing evidence.

**Required validation**  
Before reconsideration: benchmark one YOLO class on target hardware, establish objective compatibility, then measure clean-model FPR and trigger detection.

**Sources**  
Wang et al., IEEE S&P 2019; official Neural Cleanse project/repository; source dossier C3-RC-06.

---

## 8.7 C3-RC-07 — ABS (Artificial Brain Stimulation)

**Purpose**  
Stimulate internal neurons and observe output changes to identify neurons whose controlled activation causes consistent target behavior.

**Threats addressed**  
Backdoors associated with internal activation mechanisms detectable through stimulation.

**Access required**  
**INTERNAL-ACTIVATION ACCESS** — read and intervention.

**Inputs**  
Model with hook/intervention capability and input examples.

**Reference required**  
No separate trusted model required, but architecture instrumentation knowledge is required.

**Execution mode**  
Internal activation probing.

**Method status**  
**DEFER**.

**Evidence basis**  
ACM CCS 2019 publication and public implementation repository.

**Project-specific evidence**  
No YOLO hook map; no project run; no quantified YOLO FPR.

**Known limitations**

- context-dependent candidate-neuron false positives;
- architecture-specific instrumentation;
- unclear general behavior after quantization;
- no stable arbitrary-YOLO hook contract in the packet.

**Failure / evasion cases**  
Backdoors not localized to the probed activation mechanism; inaccessible layers; framework/runtime without intervention hooks.

**YOLO / COCO applicability**  
Not established.

**ONNX / PyTorch / TorchScript applicability**  
Requires runtime hooks; ONNX inference generally does not expose the same intervention model as eager PyTorch without additional instrumentation.

**Five-day feasibility**  
Deferred.

**Required validation**  
Define a YOLO hook map, intervention method, and project-specific false-positive/false-negative experiments.

**Sources**  
Aafer et al., ACM CCS 2019; public ABS repository; source dossier C3-RC-07.

---

## 8.8 C3-RC-08 — Activation Clustering

**Purpose**  
Cluster internal activation representations to identify anomalous sample subpopulations that may correspond to poisoning/backdoor behavior.

**Threats addressed**  
Poisoned subpopulations that form distinguishable internal-representation clusters.

**Access required**  
Internal activations plus data samples.

**Inputs**  
Representative samples passed through the model; internal activation vectors.

**Reference required**  
A separate trusted model is not inherently required, but data is required.

**Execution mode**  
Activation extraction followed by clustering.

**Method status**  
**DEFER**; **UNAVAILABLE** under model-only conditions without usable sample data and activation access.

**Evidence basis**  
Published Activation Clustering research in classification settings.

**Project-specific evidence**  
No YOLO feature-pyramid representation or clustering recipe executed.

**Known limitations**

- natural subpopulations can resemble anomalous clusters;
- domain shift and class imbalance affect clustering;
- "same-label" representation is nontrivial for multi-object images;
- INT8 changes activation geometry.

**Failure / evasion cases**  
Distributed poison effects; poor layer choice; multi-object representation ambiguity.

**YOLO / COCO applicability**  
Not established.

**ONNX / PyTorch / TorchScript applicability**  
Requires accessible internal representations; not a file-only method.

**Five-day feasibility**  
Deferred.

**Required validation**  
Define sample source, layer selection, aggregation over multi-scale feature maps, and clean/poisoned ground truth.

**Sources**  
Chen et al., Activation Clustering; source dossier C3-RC-08.

---

## 8.9 C3-RC-09 — ULP (Universal Litmus Patterns)

**Purpose**  
Use learned universal input patterns and model-response classification to distinguish clean from trojaned model populations.

**Threats addressed**  
Backdoor patterns represented by the population used to train the litmus-pattern detector.

**Access required**  
Runtime query access plus a precomputed ULP detector/pattern library.

**Inputs**  
Precomputed ULP patterns, target model outputs.

**Reference required**  
Not a single reference model, but a privileged precomputation process over populations of clean and poisoned models.

**Execution mode**  
Fast runtime querying after expensive precomputation.

**Method status**  
**REJECT V1 MVP**.

**Evidence basis**  
CVPR 2020 paper and official repository.

**Project-specific evidence**  
No YOLO/COCO ULP library established in the C3 packet.

**Known limitations**

- hidden precomputation dependency;
- pattern basis may not cover new trigger families;
- generating a new population is expensive and conflicts with project constraints.

**Failure / evasion cases**  
Trigger outside learned pattern basis; distribution/model-family mismatch.

**YOLO / COCO applicability**  
Not established.

**ONNX / PyTorch / TorchScript applicability**  
Potentially query-based at runtime, but deployment is blocked by missing compatible precomputed assets.

**Five-day feasibility**  
Rejected for V1 MVP.

**Required validation**  
A reproducible YOLO/COCO model population and ULP training/evaluation pipeline would be required before reconsideration.

**Sources**  
Kolouri et al., CVPR 2020; official ULP repository; source dossier C3-RC-09.

---

## 9. Method Status Matrix

| Method | ID | Access | Reference / data dependency | C3 status | Core reason |
|---|---|---|---|---|---|
| SHA-256 digest | C3-RC-01 | File-only | Independent reference digest | **BUILD** | Deterministic exact identity, low cost |
| Structural fingerprint | C3-RC-02 | Structural parse | Reference fingerprint | **PROTOTYPE** | Stability under benign re-export not measured |
| Behavioral battery | C3-RC-03 | Black-box outputs | Trusted reference model or outputs | **BUILD mechanism / PROTOTYPE claims** | Feasible, but YOLO backdoor performance not yet tested |
| STRIP-like | C3-RC-04 | Black-box + soft outputs | Clean perturbation pool | **PROTOTYPE / BLOCKED** | YOLO entropy representation unresolved |
| B3D | C3-RC-05 | Black-box query | Output abstraction; possibly samples | **DEFER** | Query cost and detector objective unresolved |
| Neural Cleanse | C3-RC-06 | White-box gradients | Optimization inputs | **DEFER** | Gradient access, runtime and stack mismatch |
| ABS | C3-RC-07 | Internal activation read/intervention | Instrumentation | **DEFER** | YOLO hook map unresolved |
| Activation Clustering | C3-RC-08 | Internal activations + data | Representative samples | **DEFER / UNAVAILABLE model-only** | Data and YOLO activation representation unresolved |
| ULP | C3-RC-09 | Query + precomputed library | Large precomputed clean/poisoned model population | **REJECT V1 MVP** | Missing YOLO/COCO library; incompatible precomputation cost |

---

## 10. Safe-Loading and Assessment Isolation

### 10.1 Required architecture

The assurance system should treat every submitted model as hostile until the relevant processing steps complete inside a constrained environment.

```text
PRE-PARSE SHA-256
      ↓
QUARANTINE / IMMUTABLE INPUT
      ↓
ISOLATED PARSER OR LOADER
      │
      ├─ no external network
      ├─ no undeclared filesystem writes
      ├─ bounded memory
      ├─ wall-clock timeout
      ├─ bounded CPU/process count
      └─ custom operators denied by default
      ↓
STRUCTURAL PARSE
      ↓
ISOLATED INFERENCE
      ↓
TYPED / SCHEMA-VALIDATED OUTPUT
      ↓
OUT-OF-BAND ANALYSIS
```

No automatic unsafe fallback is permitted. If a safer path is unavailable, the correct result is `UNAVAILABLE`, `UNSUPPORTED`, or `ERROR` according to the schema — not a silent switch to unrestricted loading.

### 10.2 Format-by-format safe-loading status

| Format | Main risk | Safer assessment path | Residual limitation | Current C3 status |
|---|---|---|---|---|
| PyTorch `.pt/.pth` checkpoint/weights | Pickle/unpickling and checkpoint-parser attack surface; version-specific vulnerabilities | Pin an approved PyTorch version; prefer restricted `weights_only=True` where semantically applicable; isolate the loader; restrict filesystem/network/resources | `weights_only=True` is not a standalone sandbox; model may require objects unsupported by restricted loading; parser bugs/DoS remain relevant | **Mitigation supported; isolation required** |
| ONNX `.onnx` | External-data traversal, symlink/hardlink issues, malicious attributes, resource exhaustion, runtime/parser attack surface | Validate external-data containment; reject unsafe paths; isolate parser and inference runtime; deny undeclared custom operators | Current ONNX security docs verify ONNX external-data risks; the source packet's exact ORT-version bypass claim remains not verified | **Path containment supported; ORT-specific version claim NOT_VERIFIED** |
| TorchScript `.pt` | Serialized object/loading attack surface and runtime execution boundary | Treat as hostile; isolate loading and inference; pin runtime | No sandbox-free path was established in the current C3 packet | **Isolation required; safer standalone path not established** |

### 10.3 PyTorch version qualification

The original V2 dossier treated the exact `CVE-2026-24747 / GHSA-63cw-57p8-fm3p` version boundary as only partially supported because the advisory text had not been retrieved.

The 2026-09-29 verification refresh located the official PyTorch GitHub advisory:

- advisory: **GHSA-63cw-57p8-fm3p**;
- CVE: **CVE-2026-24747**;
- vulnerable `weights_only` unpickler behavior documented;
- patched version: **2.10.0**.

This updates the **source-verification status** of that narrow version claim. It does not authorize a build version by itself. C6 must still pin and validate the actual project runtime.

### 10.4 ONNX path containment

Current ONNX documentation describes defense-in-depth for external data, including:

- canonical path containment;
- symlink checks;
- secure file-open strategies;
- hardlink checks;
- external-data attribute validation;
- resource-exhaustion limits.

For C3, the operational rule is:

> All external tensor-data paths must resolve inside the declared model submission directory, and inference must remain inside the runtime isolation boundary.

### 10.5 Safe loading is not model validation

A model that loads successfully may still be substituted, poisoned, backdoored, or behaviorally anomalous.

```text
LOAD SUCCESS ≠ BENIGN
PARSE SUCCESS ≠ SAFE
ISOLATION SUCCESS ≠ MODEL INTEGRITY
```

---

## 11. Reference Integrity

A reference is useful only if its trust is independent of the submission under assessment.

### 11.1 Required properties

A reference digest/model/output set should have:

- a declared origin;
- independent storage or attestation;
- an immutable or controlled update path;
- version and format metadata;
- linkage to exporter/runtime configuration where relevant;
- provenance that is not generated from the current submission.

### 11.2 Self-consistency failure mode

If a contributor can both submit a model and register the corresponding digest as the trusted reference, then:

```text
BACKDOORED MODEL
      ↓
REFERENCE DIGEST GENERATED FROM SAME MODEL
      ↓
SUBMISSION HASH == REFERENCE HASH
      ↓
MATCH
```

The `MATCH` is technically correct but security-weak. It proves self-consistency, not legitimacy.

### 11.3 Reference-relative behavioral limitation

A compromised reference model creates the same problem for paired behavioral testing. If the reference and submitted model share the same backdoor, reference-relative consistency may look normal.

**MATCH ≠ SAFE / GLOBAL IDENTITY.**

---

## 12. Format / Runtime / Interoperability Boundaries

### 12.1 ONNX structural validity is not semantic equivalence

An ONNX model can be structurally valid without being semantically equivalent to a source PyTorch/TorchScript model under the intended preprocessing, exporter settings, opset, execution provider, precision, NMS implementation, or custom-operator behavior.

C3 therefore does not use:

```text
ONNX CHECK PASSED
```

as evidence of:

```text
PYTORCH ↔ ONNX BEHAVIORAL EQUIVALENCE
```

### 12.2 Required format/runtime tuple

Behavioral evidence should be tagged with a tuple similar to:

```text
format
framework/runtime version
exporter version
opset (if ONNX)
execution provider
precision (FP32 / FP16 / INT8)
input shape policy
preprocessing version
NMS implementation/settings
output canonicalization version
custom-operator policy
```

Coverage is only claimed for tuples actually tested.

### 12.3 YOLO output canonicalization

Before behavioral comparison, C3 requires a declared representation of:

- detection heads used;
- confidence threshold;
- NMS threshold and implementation;
- pre-NMS vs post-NMS visibility;
- box coordinate convention;
- class-score representation;
- ordering/alignment of variable-length detections;
- treatment of duplicate/overlapping boxes;
- handling of empty detections.

Without this declaration, results are not reproducible enough for evaluator review.

---

## 13. Quantization and Other Coverage Gaps

### 13.1 Quantization boundary

External classification evidence establishes a meaningful research warning: model quantization can materially alter the behavior of backdoor defenses.

It does not establish C3's YOLO result.

| Proposition | Status |
|---|---|
| INT8 can alter backdoor-defense detection behavior in the cited classification study | **SUPPORTED** |
| The cited study used CIFAR-10 / GTSRB and BadNet-style settings | **SUPPORTED** |
| The cited result automatically applies to YOLO | **NOT_VERIFIED** |
| The cited result automatically applies to ONNX/TorchScript exports | **NOT_VERIFIED** |
| C3's behavioral battery remains effective after INT8 | **NOT_VERIFIED** |
| `EXP-C3-06` is required for project evidence | **REQUIRED** |

### 13.2 Dynamic / relational trigger gap

Static patch batteries do not exhaust the space of trigger conditions.

Relational and interaction-based attacks motivate future fixture categories involving:

- two or more objects;
- relative geometry;
- co-occurrence;
- movement or interaction context;
- NMS-sensitive arrangements.

The correct public claim is:

> C3 identifies this as a coverage gap and fixture-design requirement. It does not claim that the current battery detects every dynamic or relational backdoor.

### 13.3 Pre-NMS / post-NMS visibility

If only post-NMS detections are exposed, then signals that exist only in:

- pre-NMS candidate volume;
- suppressed-box distribution;
- NMS compute behavior;
- internal confidence structure

may be unavailable to black-box analysis.

### 13.4 Model-specific export differences

Benign conversion can change:

- numerical precision;
- operator implementation;
- shape handling;
- NMS placement;
- fused operators;
- metadata;
- output ordering.

Negative controls must therefore include benign export/runtime transformations.

---

## 14. Validation and Experiment Plan

No C3 project experiment in this packet is claimed as executed, reproducible, or validated.

### 14.1 Experiment status vocabulary

- **PLANNED** — experiment design exists.
- **EXECUTED** — a run was performed with recorded configuration.
- **REPRODUCIBLE** — another controlled run reproduces the result from documented artifacts/configuration.
- **VALIDATED** — evidence has passed the project's review criteria and supports the stated bounded claim.

The current C3 packet is at **PLANNED** for the experiments below.

| Experiment | Method / surface | Purpose | Required access | Ground truth | Primary metric | Current status |
|---|---|---|---|---|---|---|
| **EXP-C3-01** | SHA-256 identity | Controlled variant suite across identical and benign-modified artifacts | File-only | Known variant provenance | Digest determinism; expected mismatch behavior | **PLANNED / NOT EXECUTED** |
| **EXP-C3-02** | Structural fingerprint | Measure stability across equivalent exports and benign modifications | Structural parse | Known same-source vs modified variants | Collision/divergence rate; benign divergence rate | **PLANNED / NOT EXECUTED** |
| **EXP-C3-03** | Behavioral battery | Compare clean, benign-modified and trigger-bearing YOLO variants | Black-box outputs | Controlled clean/benign/triggered model set | Agreement/divergence; threshold sensitivity; FP/FN counts | **PLANNED / NOT EXECUTED** |
| **EXP-C3-04** | STRIP-like probe | Test one fixed YOLO soft-output representation | Black-box + soft outputs | Clean / trigger / benign-modified cases | AUROC or declared detection rate at declared FPR; entropy-distribution overlap | **PLANNED / BLOCKED BY OUTPUT DEFINITION** |
| **EXP-C3-05** | Safe loading | Stress hostile checkpoints, malformed external-data references and resource-exhaustion fixtures | File + isolated loader | Controlled malicious/malformed fixtures | Blocked execution; filesystem escape; timeout/resource containment | **PLANNED / NOT EXECUTED** |
| **EXP-C3-06** | INT8 behavioral battery | Compare detection behavior before/after INT8 on the same YOLO variants | Black-box outputs | Paired FP32/INT8 controlled variants | Detection-rate change; trigger survival; FP/FN shift | **PLANNED / NOT EXECUTED** |
| **EXP-C3-07** | B3D adaptation | Estimate query cost and feasibility for one YOLO output abstraction | Black-box query | Controlled class/trigger setting | Trigger discovery; queries/class; benign false positives | **DEFERRED / NOT EXECUTED** |

### 14.2 Battery design requirements

The battery should declare coverage across:

- negative/background images;
- representative classes;
- object scales;
- object counts;
- nuisance/preprocessing changes;
- static patch triggers;
- localized triggers;
- injection/disappearance behaviors;
- geometry-sensitive cases;
- benign fine-tuning;
- benign pruning;
- benign re-export;
- INT8 quantization.

### 14.3 Battery size

The source packet intentionally does not prescribe a universal minimum image count.

It gives illustrative Bernoulli-estimation calculations:

- about 96 samples for ±10 percentage-point precision at 95% confidence;
- about 385 for ±5 points;
- about 2,401 for ±2 points;
- about 299 trials for a 95% chance of observing at least one event with 1% prevalence;
- about 459 trials for 99%.

These are **planning calculations**, not project validation criteria. Trigger coverage and stratification can matter more than raw image count.

---

## 15. Project Implementation Evidence

### 15.1 Evidence ladder

C3 distinguishes six evidence levels:

1. **Source inspection** — paper/document/source material reviewed.
2. **Code/repository inspection** — implementation artifacts located and inspected.
3. **Team implementation** — project code written.
4. **Team execution** — project code run under a recorded environment.
5. **Reproducible experiment** — repeatable run with controlled inputs and outputs.
6. **Validated result** — evidence supports a bounded claim after review.

No level may be silently upgraded to the next.

Examples:

- authors' Neural Cleanse repository exists → does **not** mean C3 implemented Neural Cleanse;
- repository inspection → does **not** mean successful execution;
- paper benchmark → does **not** mean SIH YOLO benchmark;
- method mechanism → does **not** mean project validity.

### 15.2 Method evidence table

| Method | Literature / source evidence | Project implementation evidence | Project execution | Project validation |
|---|---|---|---|---|
| SHA-256 | Standard primitive | Not established in this research packet as an executed project module | Not documented | Not required for cryptographic semantics; project workflow still requires tests |
| Structural fingerprint | Conceptually supported; ONNX graph parsing well understood | Prototype design only | No | No |
| Behavioral battery | General differential-testing paradigm supported | Buildable design | No | No |
| STRIP-like | Paper and public code verified | No YOLO adaptation | No | No |
| B3D | ICCV 2021 paper verified | No YOLO adaptation | No | No |
| Neural Cleanse | IEEE S&P paper + official implementation verified | No C3 port | No | No |
| ABS | ACM CCS paper + public repo verified | No YOLO hook implementation | No | No |
| Activation Clustering | Literature verified | No YOLO implementation | No | No |
| ULP | CVPR paper + official repo verified | No YOLO library | No | No |

### 15.3 Current research status snapshot

| Area | Current evidence position |
|---|---|
| Exact-byte identity semantics | Strong / standard |
| Structural fingerprint | Prototype concept; stability unmeasured |
| Behavioral battery mechanism | Buildable; detector claims unvalidated |
| YOLO trigger discrimination | Not project-validated |
| INT8 YOLO coverage | Not verified |
| Safe-loading architecture | Required design; project stress test not executed |
| Cross-format equivalence | Not universally verified |
| White-box/internal-activation methods | Deferred unless capabilities are available |

---

## 16. Five-Day Feasibility

All durations below are planning inferences from the source dossier, not measured project execution times.

| Capability | Feasibility | Dependencies | Current evidence |
|---|---|---|---|
| SHA-256 + artifact triage | **Core MVP feasible** | Independent reference digest; evidence schema | Standard mechanism |
| YOLO output canonicalizer | **Core MVP feasible if output contract is known** | C6 output/runtime contract | Not implemented in packet |
| Paired behavioral battery runner | **Core MVP feasible** | Reference model/outputs; canonicalization | General mechanism only |
| Synthetic trigger + benign-negative fixture set | **Core MVP feasible** | Reproducible fixtures | Planned |
| Isolated loader integration | **Core / prototype boundary** | Runtime versions, sandbox mechanism, resource limits | Required architecture; unexecuted |
| Structural fingerprint | **Prototype candidate** | Safe structural parsing; stability experiment | Unexecuted |
| STRIP-like YOLO | **Prototype / research track** | Soft outputs; entropy representation | Blocked |
| B3D | **Deferred** | Query budget, YOLO objective | Unmeasured |
| Neural Cleanse | **Deferred** | Gradients, compatible implementation, runtime benchmark | Unmeasured on target |
| ABS | **Deferred** | YOLO hook map and intervention | Unavailable without internal access |
| Activation Clustering | **Deferred** | Internal activations + data + clustering recipe | Unavailable in model-only conditions |
| ULP | **Rejected for V1 MVP** | Precomputed YOLO/COCO model-population library | Missing in packet |

### 16.1 Source dossier planning envelope

The source packet estimated a core of approximately **3.25–4.25 days** for:

- hash/triage;
- YOLO canonicalization and behavioral runner;
- synthetic fixtures;
- isolated-loader integration.

That figure is retained as a **planning inference**, not a demonstrated delivery duration.

---

## 17. Limitations and Negative Evidence

## 17.1 Structural limitations

### No universal detector

No method evaluated in the current C3 packet proves model safety for the full YOLO/COCO/ONNX/PyTorch/TorchScript/INT8 space.

### Finite behavioral testing

A finite battery can always miss behavior outside the tested domain. A model can also be intentionally optimized to pass a known battery.

### Dynamic / relational triggers

Single-image static-trigger fixtures do not exhaust scene-level relational triggers.

### Quantization

INT8 changes numerical and internal representation behavior. Classification evidence warns of a serious detection gap, but the project's YOLO transfer remains unverified.

### Access

Methods needing gradients or internal activations become `UNAVAILABLE` when those capabilities are not present.

### Reference trust

Identity and differential behavior inherit the trustworthiness of the reference.

### Format/runtime coverage

Results cannot be generalized across untested framework, exporter, opset, runtime, execution-provider, precision, or custom-operator combinations.

### Canonicalization

YOLO behavioral evidence is not reproducible until output canonicalization is declared.

### Safe loading

Assessor security depends on correct isolation, path containment, version control, timeouts, and resource ceilings.

---

## 17.2 Per-method limitations

### SHA-256

- mismatch is not maliciousness;
- match is not behavioral integrity;
- compromised reference defeats security meaning;
- every benign byte change changes the digest.

### Structural fingerprint

- topology-only design misses weight-only modification;
- stability under benign export differences is unknown;
- weight-statistic extensions trade stability for sensitivity.

### Behavioral battery

- finite and evadable;
- depends on canonicalization and thresholds;
- strongest form depends on a trusted reference;
- dynamic/relational conditions may remain outside coverage.

### STRIP-like

- needs soft outputs;
- clean perturbation pool required;
- adaptive evasion can reduce entropy separation;
- YOLO entropy representation not established;
- post-NMS view can hide upstream signals.

### B3D

- query cost unmeasured for C3 target;
- detector-output objective unresolved;
- recovered pattern is evidence of an optimization result, not proof of a malicious backdoor.

### Neural Cleanse

- gradients required;
- target runtime cost unmeasured;
- classification assumptions may not fit detection heads;
- project FPR not measured;
- INT8 YOLO applicability not established.

### ABS

- internal intervention required;
- candidate-neuron evidence can have context-dependent false positives;
- arbitrary-YOLO hook map unresolved.

### Activation Clustering

- data required;
- activation layer/aggregation choices unresolved for feature pyramids;
- natural subpopulation structure can appear anomalous;
- quantization changes representation geometry.

### ULP

- needs precomputed model-population artifacts;
- no compatible YOLO/COCO library established in the packet;
- pattern basis may fail on out-of-distribution trigger families.

---

## 17.3 Negative evidence — what was not established in the source packet

| Search target | Packet result |
|---|---|
| Validated public YOLO/COCO ULP precomputed library | Not established |
| CPU-only Neural Cleanse YOLO timing on target hardware | Not measured |
| Validated YOLO feature-pyramid Activation Clustering recipe | Not established |
| Arbitrary-YOLO ABS hook map | Not established |
| B3D query budget for an 80+ class YOLO detector | Not measured |
| YOLO post-NMS entropy representation for STRIP | Not established |
| Project evidence for INT8 backdoor detection | Not executed |
| Project safe-loader stress-test evidence | Not executed |

The original packet also listed several external-source items as not retrieved. Some of those were resolved in the 2026-09-29 public-link verification refresh; those changes are recorded in Section 19.

---

## 18. Semantic Prohibitions

These are output-schema constraints, not slogans.

```text
UNAVAILABLE  → NEVER → CLEAN
DIFFERENT    → NEVER → MALICIOUS
MATCH        → NEVER → SAFE / GLOBAL IDENTITY
NOT_DETECTED → NEVER → ABSENT
```

### 18.1 UNAVAILABLE ≠ CLEAN

A method that could not run due to missing access provides no positive evidence. The unavailable state must survive downstream processing.

### 18.2 DIFFERENT ≠ MALICIOUS

A digest or fingerprint mismatch means non-identity under the declared comparison. Benign causes remain possible.

### 18.3 MATCH ≠ SAFE / GLOBAL IDENTITY

A hash match proves only byte equality to the selected reference. It says nothing about whether that reference contains malicious behavior.

### 18.4 NOT_DETECTED ≠ ABSENT

A detector's failure to flag an anomaly is bounded by the detector's input space, access mode, runtime, threshold, and threat coverage.

### 18.5 Permitted result vocabulary

**Identity-oriented results**

`MATCH / DIFFERENT / SUSPICIOUS / UNAVAILABLE / UNSUPPORTED / ERROR / PARTIAL-REFERENCE-ABSENT`

Every `DIFFERENT` should carry a semantic note equivalent to:

> Byte non-identity. Cause unspecified. Not a maliciousness verdict.

**Behavioral results**

`CONSISTENT / DIVERGENT / THRESHOLD-NOT-MET / UNAVAILABLE`

`UNAVAILABLE` is terminal evidence for that method; it must not be rewritten as a positive state.

---

## 19. Contradictions, Corrections and Research Evolution

The research lineage intentionally preserves changes introduced by red-team and re-verification work.

| Topic | Earlier claim / position | Later evidence / correction | Current public-research status |
|---|---|---|---|
| Neural Cleanse access | Described in early material as inference-only / black-box | Method requires gradient-based differentiable access | **Corrected: white-box gradients required** |
| STRIP access | Over-broad black-box label | Original method relies on output-distribution entropy | **Corrected: black-box with soft output; hard-label-only unsupported** |
| `weights_only=True` | Treated as safer loading, exact 2026 fixed-version boundary not independently retrieved | PyTorch advisory GHSA-63cw-57p8-fm3p was located in the 2026-09-29 refresh and identifies patched version 2.10.0 | **Source-status update: exact boundary now externally verified; isolation still required** |
| ONNX external-data risks | Path risks and checker/runtime separation described; exact ORT version not verified | Current ONNX docs verify external-data threat classes and defense layers; no primary ORT source was found for the packet's exact runtime/version assertion | **Partially supported; ORT-specific claim remains NOT_VERIFIED** |
| INT8 transfer | Classification result risked being read as general detector result | Study scope is CIFAR-10/GTSRB classification | **YOLO/ONNX/TorchScript transfer NOT_VERIFIED** |
| TrojAI Round 13 model list | Packet said YOLO not listed but exact primary page had not been retrieved | NIST Round 13 documentation now verified; `MODEL_LEVELS = ['ssd','fasterrcnn','detr']` | **Source-status update: exact non-YOLO list now verified** |
| STRIP adaptive AUROC | Red-team cited AUROC 0.562 | Exact primary location still not established | **UNVERIFIABLE numeric; mechanism-level warning retained** |
| ShrinkBox numeric claim | 96% ASR, 4% poisoning treated as unverified | arXiv abstract for 2507.18656 reports those figures for YOLOv9m/KITTI | **External literature result now source-verified; not project evidence** |
| Phantom numeric claim | >90% ASR treated as unverified | CVPR 2026 paper text reports >90% in most settings and 99% on COCO+YOLOv5 mislocalization | **External literature result now source-verified; not project evidence** |
| CIS-BA numeric claim | >97% treated as unverified | arXiv abstract 2512.14158 reports >97% under complex environments | **External literature result now source-verified; not project evidence** |
| Phantom NMS-latency-specific claim | Internal red-team packet asserted a latency/entropy relation | The verified Phantom 2026 source establishes NMS-exploited dynamic triggers, but this refresh did not establish the exact latency/no-entropy wording used by C3-CLM-013 | **C3-CLM-013 remains UNVERIFIABLE** |
| Neural Cleanse citation pointer | Source packet included an arXiv pointer while also identifying the IEEE S&P paper | Public refresh verified the canonical IEEE S&P 2019 publication and official project page | **Reference normalized to primary publication; evidence scope unchanged** |

Research evolution is not a weakness in the dossier. It records where earlier assumptions were challenged and narrowed.

---

## 20. Open Questions

### 20.1 P0 — must be resolved before C3 evidence can be treated as project validation

| ID | Question | Dependency | Priority | Current status |
|---|---|---|---|---|
| **OQ-P0-01** | Does the C3 behavioral path distinguish clean vs backdoored YOLO models before and after INT8? | EXP-C3-06 | P0 | Open |
| **OQ-P0-02** | What exact PyTorch, ONNX Runtime and execution-provider versions are approved for the project? | C6 runtime contract | P0 | Open |
| **OQ-P0-03** | What exact external-data/path behavior is present in the C6-approved ONNX Runtime version? | C6 + primary ORT evidence | P0 | Open |
| **OQ-P0-04** | What isolation boundary is required in addition to restricted PyTorch loading on the final host? | C6 architecture | P0 | Open; C3 requires isolation in its trust model |
| **OQ-P0-05** | What is the exact YOLO output canonicalization for STRIP-like entropy and for behavioral comparison? | C6 output contract | P0 | Open |
| **OQ-P0-06** | What battery size and stratification are justified once the trigger-search strategy is frozen? | C3/C5/C6 | P0 | Open |
| **OQ-P0-07** | Which geometry-only backdoor behaviors can pass class-label/mAP-oriented checks? | Fixture design + EXP-C3-03 | P0 | Open; ShrinkBox motivates the question |
| **OQ-P0-08** | How is the trusted reference protected from poisoning, staleness, or compromised registration? | C4 provenance + governance | P0 | Open |

### 20.2 P1 — should be resolved before deferred methods are reconsidered

| ID | Question | Dependency | Priority | Current status |
|---|---|---|---|---|
| **OQ-P1-09** | What black-box output information is guaranteed: labels, confidences, logits, pre-NMS candidates, post-NMS detections? | C6 | P1 | Open |
| **OQ-P1-10** | What query budget does B3D require per YOLO class? | Benchmark | P1 | Open |
| **OQ-P1-11** | How often do benign re-export/pruning/quantization changes trigger structural or behavioral divergence? | EXP-C3-02 / 03 | P1 | Open |
| **OQ-P1-12** | Can hostile artifacts force DoS or unintended filesystem access even when arbitrary code execution is blocked? | EXP-C3-05 | P1 | Open |
| **OQ-P1-13** | What is the primary-source location for the adaptive STRIP AUROC 0.562 claim? | External source re-verification | P1 | Open |
| **OQ-P1-14** | Do all specific ShrinkBox/Phantom/CIS-BA claims used by future fixtures remain reproducible beyond the source papers? | External replication / project fixtures | P1 | Literature claims located; project replication open |

---

## 21. Cross-Cell Dependencies

### 21.1 C1 — access scenario / operational assumptions

**Dependency:** C3 needs the actual assessment access profile and mission/runtime assumptions. C1 context must not be translated into unearned model access.

### 21.2 C2 — data and annotation context

**Handoff:** C2 may provide information about dataset integrity, trigger-like samples, source metadata, and test fixtures. C3 does not duplicate C2's data-integrity methods.

### 21.3 C4 — provenance and reference identity

**DEP-C3-C4-001**  
Carry the pre-parse digest with format and reference-source metadata.

**DEP-C3-C4-002**  
Carry the versioned structural-fingerprint schema and computed fields where available.

**DEP-C3-C4-003**  
Preserve the identity vocabulary and semantic note for `DIFFERENT`.

**DEP-C3-C4-004**  
Carry behavioral coverage metadata: battery ID, preprocessing, access mode, trigger families, negative controls, unsupported conditions, runtime and precision.

### 21.4 C5 — calibration and analyst meaning

**DEP-C3-C5-001**  
Receive raw behavioral counts, battery definition, trigger strata and negative controls for threshold calibration.

**DEP-C3-C5-002**  
Treat `UNAVAILABLE` as a distinct assurance condition, not as `CLEAN`.

**DEP-C3-C5-003**  
Receive quantization status and whether evidence was generated on FP32/FP16/INT8.

**DEP-C3-C5-004**  
Receive dynamic/relational-trigger coverage gaps as explicit residual-risk metadata.

### 21.5 C6 — runtime and execution

**DEP-C3-C6-001 — runtime contract**  
C6 must define:

- approved PyTorch version;
- approved ONNX Runtime version;
- execution provider;
- isolation mechanism;
- filesystem policy;
- network policy;
- memory/CPU/process limits;
- wall-clock timeout;
- custom-operator policy.

**DEP-C3-C6-002 — YOLO output contract**  
C6 must define the available output surface needed by behavioral and STRIP-like methods.

**DEP-C3-C6-003 — experiment execution**  
C6 must provide the controlled runtime/environment needed to execute `EXP-C3-01` through `EXP-C3-06`.

**DEP-C3-C6-004 — deferred-method contracts**  
If deferred methods are revisited, C6 must provide the required hooks, gradients, query budgets, data and runtime benchmarking.

These are **dependencies / handoffs**, not claims of integration or approval.

---

## 22. Reproducibility and Evidence Requirements

Every project result should record enough metadata to answer:

- What exact artifact was tested?
- What hash identifies it?
- What format and version was used?
- What runtime and execution provider was used?
- What access capabilities were available?
- What preprocessing was applied?
- What output canonicalization version was applied?
- What dataset/fixture set was used?
- What ground truth was known?
- What thresholds were applied and how were they calibrated?
- What negative controls were included?
- What resource limits and isolation controls were active?
- Was the run repeated?
- Are logs, environment manifests and outputs available?

### 22.1 Minimum evidence record

```yaml
artifact:
  sha256: ...
  format: ...
  precision: ...
  reference_id: ...
runtime:
  framework: ...
  version: ...
  execution_provider: ...
  isolation_profile: ...
access:
  outputs: true/false
  logits: true/false
  architecture: true/false
  internal_activations: true/false
  weights: true/false
  gradients: true/false
  runtime_hooks: true/false
behavioral_test:
  battery_id: ...
  preprocessing_version: ...
  output_canonicalization_version: ...
  trigger_families: [...]
  negative_controls: [...]
result:
  state: ...
  metrics: ...
  unsupported_conditions: [...]
  semantic_note: ...
```

This is a documentation schema example, not a claim that the project has implemented it.

---

## 23. Claim / Source Index

The table preserves the original C3 claim IDs and adds the result of the 2026-09-29 public-source verification where that verification materially changed source status.

| Claim ID | Claim | Original packet status | Public verification status | Evidence type | Primary source | Exact location |
|---|---|---|---|---|---|---|
| **C3-CLM-001** | `weights_only=True` is version-qualified; a 2026 vulnerability affected restricted loading and was fixed at 2.10.0 | PARTIALLY_SUPPORTED | **SUPPORTED for CVE/version boundary** | Official security advisory | R04 | Advisory Summary; Affected versions; Patched versions |
| **C3-CLM-002** | ONNX external-data handling has path/filesystem risks; packet additionally asserted an ORT InferenceSession-specific bypass/version condition | PARTIALLY_SUPPORTED | **SUPPORTED for ONNX external-data threats; NOT_VERIFIED for exact ORT claim** | Official ONNX docs + unresolved ORT detail | R05, R06 | Threat Model; Defense Layers; Protected Entry Points; exact ORT locator not established |
| **C3-CLM-003** | INT8 caused 0% detection for five evaluated defenses in the cited classification study while ASR stayed >99% | SUPPORTED in classification scope | **SUPPORTED in stated paper scope; NOT_VERIFIED for YOLO** | Academic preprint | R07 | Abstract |
| **C3-CLM-004** | STRIP needs soft outputs; adaptive entropy overlap can defeat separation; AUROC 0.562 cited internally | PARTIALLY_SUPPORTED / numeric UNVERIFIABLE | **Mechanism supported; AUROC 0.562 remains UNVERIFIABLE** | Paper + unresolved adaptive-evasion source | R08, R09 | STRIP formulation; exact AUROC source location not established |
| **C3-CLM-005** | Neural Cleanse requires gradient-based access; early inference-only wording was wrong | PARTIALLY_SUPPORTED | **SUPPORTED at method-design level** | Primary paper/project | R10, R11 | Trigger reverse-engineering / optimization method |
| **C3-CLM-006** | B3D is black-box/query-based and gradient-free; YOLO query cost/interface unverified | PARTIALLY_SUPPORTED | **SUPPORTED for method access; YOLO adaptation NOT_VERIFIED** | ICCV paper | R14 | Abstract; method sections |
| **C3-CLM-007** | TrojAI Round 13 model set does not list YOLO | UNVERIFIABLE exact list | **SUPPORTED** | NIST official documentation | R18 | Round 13 Experimental Design; `MODEL_LEVELS` |
| **C3-CLM-008** | ABS uses internal activation intervention; false-positive behavior is context-dependent | PARTIALLY_SUPPORTED | **PARTIALLY_SUPPORTED** | ACM paper / implementation | R12, R13 | Method description; exact universal-FPR statement not established |
| **C3-CLM-009** | ShrinkBox: 96% ASR on YOLOv9m with 4% poisoning in cited setting | UNVERIFIABLE | **SUPPORTED as external literature result** | arXiv primary preprint | R19 | Abstract |
| **C3-CLM-010** | Phantom: >90% ASR in most cited settings | UNVERIFIABLE | **SUPPORTED as external literature result** | CVPR 2026 paper | R20 | Results text in publication |
| **C3-CLM-011** | CIS-BA: >97% attack success in cited setting | UNVERIFIABLE | **SUPPORTED as external literature result** | arXiv primary preprint | R21 | Abstract |
| **C3-CLM-012** | STRIP can fail when clean/trigger entropy distributions overlap | PARTIALLY_SUPPORTED | **PARTIALLY_SUPPORTED** | Literature mechanism | R08 | Exact adaptive-evasion source from packet not established |
| **C3-CLM-013** | Phantom increases NMS latency without altering post-NMS entropy | UNVERIFIABLE | **UNVERIFIABLE** | Internal packet claim | R20 relevant to NMS exploitation, but not sufficient for exact claim | Exact source location not established |
| **C3-CLM-014** | STRIP requires a clean perturbation pool and distribution compatibility matters | PARTIALLY_SUPPORTED | **PARTIALLY_SUPPORTED** | STRIP literature | R08, R09 | Clean-image perturbation design; exact distribution-match wording not established |
| **C3-CLM-015** | Activation Clustering requires activation vectors from samples; model file alone is insufficient | PARTIALLY_SUPPORTED | **SUPPORTED at method-design level** | Academic paper | R15 | Method description / abstract |
| **C3-CLM-016** | Neural Cleanse AUC >0.8 on cited classification benchmarks | UNVERIFIABLE exact value | **UNVERIFIABLE in this edition** | Academic paper | R10 | Exact table/locator not established in current verification |
| **C3-CLM-017** | STRIP AUC 0.801 / 0.486 in cited malware evaluation | UNVERIFIABLE | **UNVERIFIABLE** | Source not established | — | Exact location not established in current packet |
| **C3-CLM-018** | ABS-filter 0.80 detection for filter triggers / patch limitation | UNVERIFIABLE | **UNVERIFIABLE** | Source not established | R12 context only | Exact location not established |
| **C3-CLM-019** | Activation Clustering F1 0.34/0.14 in cited non-YOLO settings | UNVERIFIABLE | **UNVERIFIABLE** | Source not established | R15 context only | Exact location not established |
| **C3-CLM-020** | B3D exact detection figures from classification benchmarks | UNVERIFIABLE exact values | **Primary B3D paper located; exact packet figures not promoted here** | ICCV paper | R14 | Published evaluation tables; packet-specific figure mapping not re-audited |
| **C3-CLM-021** | ULP reported classification performance and requires population-derived precomputation | Exact AUC unverified; prerequisite supported | **Precomputation requirement supported; exact packet AUC not promoted** | CVPR paper + official repo | R16, R17 | Paper method; repository training instructions |
| **CLM-V-001** | Unsafe/untrusted pickle-based `torch.load` can execute code | FACT | **SUPPORTED** | PyTorch docs/advisories | R02, R03, R04 | `torch.load` warning; serialization security; advisory |
| **CLM-V-007** | Old V1 claim that YOLO was included in TrojAI Round 13 | CONTRADICTED | **CONTRADICTED, primary source now verified** | NIST official docs | R18 | `MODEL_LEVELS` |
| **CLM-V-008** | TrojAI Round 13 includes misclassification/evasion/localization/injection trigger taxonomy | SUPPORTED | **SUPPORTED** | NIST official docs | R18 | Round 13 Experimental Design |

---

## 24. References

The references below prioritize official problem-statement sources, official framework/security documentation, primary advisories, original papers, and official research repositories.

### [R01] SIH 2026 Problem Statement

**Organization:** SIH 2026 / Ministry of Defence (Indian Army DGIS listing)  
**Title:** *SIH26228 — Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines*  
**Year:** 2026  
**Relevant location:** Problem Description; Model Integrity; Constraints  
**URL:** https://sih2026.vuce.in/ps/SIH26228  
**Verified:** 2026-09-29

### [R02] PyTorch `torch.load` documentation

**Organization:** PyTorch  
**Title:** *torch.load*  
**Relevant location:** Security warning for untrusted sources; `weights_only` parameter  
**URL:** https://docs.pytorch.org/docs/stable/generated/torch.load.html  
**Verified:** 2026-09-29

### [R03] PyTorch Serialization Semantics

**Organization:** PyTorch  
**Title:** *Serialization semantics*  
**Relevant location:** `torch.load` with `weights_only=True`  
**URL:** https://docs.pytorch.org/docs/stable/notes/serialization.html  
**Verified:** 2026-09-29  
**Source-packet note:** The original dossier cited PyTorch 2.13 documentation; this public edition uses the stable documentation link plus the version-specific security advisory below.

### [R04] PyTorch Security Advisory

**Organization:** PyTorch / GitHub Security Advisory  
**Title:** *Loading a malicious PyTorch checkpoint with weights_only=True can result in arbitrary code execution*  
**Advisory:** GHSA-63cw-57p8-fm3p  
**CVE:** CVE-2026-24747  
**Relevant location:** Summary; Affected versions; Patched versions  
**URL:** https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p  
**Verified:** 2026-09-29

### [R05] ONNX External Data Security

**Organization:** ONNX  
**Title:** *External Data Security*  
**Relevant location:** Threat Model; Defense Layers; Protected Entry Points; External Data Attribute Validation  
**URL:** https://onnx.ai/onnx/repo-docs/ExternalDataSecurity.html  
**Verified:** 2026-09-29

### [R06] ONNX IR External-Data Security Model

**Organization:** ONNX  
**Title:** *Security Model for External Data in onnx-ir*  
**Relevant location:** path containment; hardlink handling; known limitations  
**URL:** https://onnx.ai/ir-py/security.html  
**Verified:** 2026-09-29

### [R07] Pandey & Ye — Quantization Blindspots

**Authors:** Rohan Pandey, Eric Ye  
**Title:** *Quantization Blindspots: How Model Compression Breaks Backdoor Defenses*  
**Venue:** arXiv:2512.06243  
**Year:** 2025  
**Relevant location:** Abstract; experimental scope in paper  
**URL:** https://arxiv.org/abs/2512.06243  
**Verified:** 2026-09-29  
**Scope note:** External classification benchmark — not a project YOLO benchmark.

### [R08] Gao et al. — STRIP

**Authors:** Yansong Gao, Chang Xu, Derui Wang, Shiping Chen, Damith C. Ranasinghe, Surya Nepal  
**Title:** *STRIP: A Defence Against Trojan Attacks on Deep Neural Networks*  
**Venue:** ACSAC 2019 / arXiv:1902.06531  
**Year:** 2019  
**URL:** https://arxiv.org/abs/1902.06531  
**Verified:** 2026-09-29

### [R09] STRIP Public Implementation

**Organization / author account:** garrisongys  
**Title:** *STRIP — source code for the ACSAC paper*  
**Repository:** GitHub  
**URL:** https://github.com/garrisongys/STRIP  
**Verified:** 2026-09-29

### [R10] Wang et al. — Neural Cleanse

**Authors:** Bolun Wang, Yuanshun Yao, Shawn Shan, Huiying Li, Bimal Viswanath, Haitao Zheng, Ben Y. Zhao  
**Title:** *Neural Cleanse: Identifying and Mitigating Backdoor Attacks in Neural Networks*  
**Venue:** IEEE Symposium on Security and Privacy  
**Year:** 2019  
**DOI:** 10.1109/SP.2019.00031  
**Primary publication/project page:** https://people.cs.uchicago.edu/~ravenben/publications/abstracts/backdoor-sp19.html  
**Verified:** 2026-09-29

### [R11] Neural Cleanse Official Implementation

**Authors / project:** Bolun Wang et al.  
**Repository:** GitHub  
**URL:** https://github.com/bolunwang/backdoor  
**Verified:** 2026-09-29  
**Implementation note:** Repository states Keras with TensorFlow backend.

### [R12] Aafer et al. — ABS

**Authors:** Yousra Aafer, Wenbo Guo, Aravind Nagesh, He Wang, Xiangyu Zhang  
**Title:** *ABS: Scanning Neural Networks for Back-doors by Artificial Brain Stimulation*  
**Venue:** ACM CCS 2019  
**DOI:** 10.1145/3319535.3363216  
**URL:** https://doi.org/10.1145/3319535.3363216  
**Verified:** 2026-09-29

### [R13] ABS Public Implementation

**Project:** ABS  
**Repository:** GitHub  
**URL:** https://github.com/naiyeleo/ABS  
**Verified:** 2026-09-29

### [R14] Dong et al. — B3D

**Authors:** Yinpeng Dong, Xiao Yang, Zhijie Deng, Tianyu Pang, Zihao Xiao, Hang Su, Jun Zhu  
**Title:** *Black-Box Detection of Backdoor Attacks With Limited Information and Data*  
**Venue:** ICCV 2021  
**Pages:** 16482–16491  
**URL:** https://openaccess.thecvf.com/content/ICCV2021/html/Dong_Black-Box_Detection_of_Backdoor_Attacks_With_Limited_Information_and_Data_ICCV_2021_paper.html  
**Verified:** 2026-09-29

### [R15] Chen et al. — Activation Clustering

**Authors:** Bryant Chen, Wilka Carvalho, Nathalie Baracaldo, Heiko Ludwig, Benjamin Edwards, Taesung Lee, Ian Molloy, Biplav Srivastava  
**Title:** *Detecting Backdoor Attacks on Deep Neural Networks by Activation Clustering*  
**Venue:** arXiv:1811.03728 / later SafeAI workshop context  
**Year:** 2018/2019  
**URL:** https://arxiv.org/abs/1811.03728  
**Verified:** 2026-09-29

### [R16] Kolouri et al. — Universal Litmus Patterns

**Authors:** Soheil Kolouri, Aniruddha Saha, Hamed Pirsiavash, Heiko Hoffmann  
**Title:** *Universal Litmus Patterns: Revealing Backdoor Attacks in CNNs*  
**Venue:** CVPR 2020  
**Pages:** 301–310  
**URL:** https://openaccess.thecvf.com/content_CVPR_2020/html/Kolouri_Universal_Litmus_Patterns_Revealing_Backdoor_Attacks_in_CNNs_CVPR_2020_paper.html  
**Verified:** 2026-09-29

### [R17] Universal Litmus Patterns Official Repository

**Project:** UMBCvision / Universal-Litmus-Patterns  
**Repository:** GitHub  
**URL:** https://github.com/UMBCvision/Universal-Litmus-Patterns  
**Verified:** 2026-09-29

### [R18] NIST TrojAI Round 13

**Organization:** National Institute of Standards and Technology (NIST)  
**Title:** *object-detection-feb2023 — Round 13*  
**Relevant location:** About; Experimental Design; `MODEL_LEVELS`; trigger types  
**URL:** https://pages.nist.gov/trojai/docs/object-detection-feb2023.html  
**Verified:** 2026-09-29

### [R19] Shahzad et al. — ShrinkBox

**Authors:** Muhammad Zaeem Shahzad, Muhammad Abdullah Hanif, Bassem Ouni, Muhammad Shafique  
**Title:** *ShrinkBox: Backdoor Attack on Object Detection to Disrupt Collision Avoidance in Machine Learning-based Advanced Driver Assistance Systems*  
**Venue:** arXiv:2507.18656  
**Year:** 2025  
**URL:** https://arxiv.org/abs/2507.18656  
**Verified:** 2026-09-29  
**Scope note:** External literature result — not a project benchmark.

### [R20] Huo et al. — Phantom

**Authors:** Tianlin Huo, Dongchuan Ran, Ranjie Duan, Yao Zhu, Peilun Du, Ningbo Yao, Huanqian Yan, Xu Han, Qiang Yun, Yuzheng Tan, Yang Bao, Yuan He  
**Title:** *Phantom: Physical Object Interactions as Dynamic Triggers for NMS-Exploited Backdoors*  
**Venue:** CVPR 2026  
**Pages:** 27906–27915  
**URL:** https://openaccess.thecvf.com/content/CVPR2026/html/Huo_Phantom_Physical_Object_Interactions_as_Dynamic_Triggers_for_NMS-Exploited_Backdoors_CVPR_2026_paper.html  
**Verified:** 2026-09-29  
**Scope note:** External literature result — not a project benchmark.

### [R21] Zhao et al. — CIS-BA

**Authors:** Shuxin Zhao, Bo Lang, Nan Xiao, Yilang Zhang  
**Title:** *CIS-BA: Continuous Interaction Space Based Backdoor Attack for Object Detection in the Real-World*  
**Venue:** arXiv:2512.14158  
**Year:** 2025  
**URL:** https://arxiv.org/abs/2512.14158  
**Verified:** 2026-09-29  
**Scope note:** External literature result — not a project benchmark.

### Internal lineage sources retained for traceability

The public edition was derived from the C3 research lineage:

- **SRC-C3-BOOT** — C3 session/bootstrap research context.
- **SRC-S7OC3** — V1 research packet.
- **SRC-S8OC3** — red-team review.
- **SRC-S9OC3** — re-verification dispositions.
- **SRC-C3-CRIT** — internal C3 critical analysis on ULP deployment prerequisites.

These internal lineage items are not presented as public external references and no private filesystem paths, credentials, prompt text, or team-only workflow instructions are included here.

---

## 25. C3 Research Conclusion

C3 establishes a bounded model-security research framework built around three non-substitutable surfaces: **artifact identity, behavioral integrity, and safe loading**.

The strongest current conclusions are narrow and technically useful:

- exact-byte hashing is a strong identity primitive when the reference is independently trusted;
- structural fingerprinting can add identity context but does not detect weight-only backdoors by itself;
- a deterministic behavioral battery is a practical black-box mechanism for bounded reference-relative evidence, but its YOLO backdoor claims remain prototype-level until controlled experiments are executed;
- STRIP-like, B3D, Neural Cleanse, ABS, Activation Clustering, and ULP each have access, runtime, data, or deployment prerequisites that prevent them from being treated as universal fallback detectors;
- classification-domain literature, including quantization studies, must not be silently promoted into YOLO/COCO project results;
- dynamic and relational trigger research demonstrates important fixture and coverage gaps;
- safe loading is a prerequisite to credible assessment because the submitted model file can attack the assessor itself;
- `UNAVAILABLE`, `DIFFERENT`, `MATCH`, and `NOT_DETECTED` require explicit semantic constraints so downstream systems cannot convert narrow evidence into unsupported security conclusions.

The project still requires controlled execution of `EXP-C3-01` through `EXP-C3-06`, a frozen YOLO output canonicalization, a C6 runtime/isolation contract, independently governed references through C4, and C5 calibration/analyst semantics.

C3 therefore does **not** conclude that model security is solved, that all backdoors are detectable, or that any submitted model can be certified safe. Its contribution is a transparent coverage envelope: what can be assessed, under what access and runtime conditions, with what evidence, and with which unresolved limitations.

---

# Appendix A — Public Current Packet Snapshot

```text
C3 PUBLIC RESEARCH STATUS
══════════════════════════════════════════════════════════════

Source Artifact:     C3-V2-001
Source Packet:       C3-SYN-V2-2026-09-23-01
Public Refresh:      2026-09-29

SHA-256
  Status:            BUILD (mechanism)
  Evidence:          Exact byte identity only
  Semantic limit:    MATCH ≠ SAFE

Behavioral Battery
  Status:            BUILD (mechanism)
                     PROTOTYPE (backdoor-specific claims)
  Preconditions:     YOLO output canonicalization
                     trusted reference
                     negative controls
  Semantic limit:    NOT_DETECTED ≠ ABSENT

Structural Fingerprint
  Status:            PROTOTYPE
  Gap:               re-export stability not measured
                     weight-only modification can bypass topology-only hash

STRIP-like
  Status:            PROTOTYPE / BLOCKED
  Access:            soft outputs required
  Gap:               YOLO entropy representation unresolved

B3D
  Status:            DEFER
  Gap:               query budget + YOLO objective unresolved

Neural Cleanse
  Status:            DEFER
  Access:            white-box gradients
  Gap:               target runtime / YOLO adaptation unmeasured

ABS
  Status:            DEFER
  Access:            internal activation read/intervention
  Gap:               YOLO hook map unresolved

Activation Clustering
  Status:            DEFER
  Access:            internal activations + data
  Model-only:        UNAVAILABLE

ULP
  Status:            REJECT V1 MVP
  Gap:               compatible precomputed YOLO/COCO population library
                     not established in current packet

SAFE LOADING
  PyTorch:           version pinning + restricted loading where applicable
                     + isolation
  ONNX:              path containment + parser/runtime isolation
  TorchScript:       isolation required; safer standalone path not established

QUANTIZATION
  Classification
  literature:        supported in cited study scope
  YOLO transfer:     NOT_VERIFIED

SEMANTIC PROHIBITIONS
  UNAVAILABLE        ≠ CLEAN
  DIFFERENT          ≠ MALICIOUS
  MATCH              ≠ SAFE / GLOBAL IDENTITY
  NOT_DETECTED       ≠ ABSENT

PROJECT VALIDATION
  EXP-C3-01..06:     PLANNED / NOT EXECUTED
  Universal safety:  NOT CLAIMED

══════════════════════════════════════════════════════════════
```
