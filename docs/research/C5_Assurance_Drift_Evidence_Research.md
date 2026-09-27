# C5 — Assurance, Drift & Evidence Research

## Document Metadata

| Field | Value |
|---|---|
| Project | SIH 2026 PS 26228 — *Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines* |
| Research cell | C5 — Assurance / Risk / Drift / Evidence |
| Public-edition focus | Assurance semantics, drift interpretation, evidence representation, confidence semantics, analyst governance, limitations, and non-claim enforcement |
| Source dossier | `C5_V2_Dossier.docx` |
| Dossier date | 2026-09-23 |
| Public research edition | 2026-09-29 |
| Research lineage | S7OC5_V1 → S8OC5 Red Team → S9OC5 Reverify → C5_V2 |
| Deployment model | Offline / air-gapped |
| Model constraint | Model-agnostic; baseline integrity assessment must not require retraining |
| Target artefacts | COCO/YOLO annotations; ONNX/PyTorch/TorchScript model and inference artefacts, subject to tested format/version/runtime scope |
| C5 status | Semantic/governance core: bounded BUILD authorization; several statistical mechanisms remain PROTOTYPE; deployment readiness is not established |
| Final-readiness dependency | Separate `FINAL_V2_AUDIT` required |
| Public-edition rule | Research specification, recommendation, implementation, execution, and validation are kept distinct |

> **Absolute semantic boundary**
>
> **OBSERVATION ≠ EXPLANATION ≠ ATTRIBUTION**  
> **UNAVAILABLE ≠ CLEAN**  
> **NATURAL SHIFT ≠ MANIPULATION**  
> **DETECTOR AGREEMENT ≠ INDEPENDENT EVIDENCE**  
> **DETECTOR SCORE ≠ COMPROMISE PROBABILITY**
>
> C5 does not produce or imply a probability of compromise or an arbitrary overall risk score.

---

## 1. Research Objective

C5 defines how technical evidence produced elsewhere in the assurance pipeline may be interpreted and presented without exceeding what that evidence establishes. C5 is therefore primarily a **semantic and governance layer**, not a detector-development cell.

C2, C3, and C4 may produce technical detector signals. C5 determines the permissible evidence semantics around those signals: what was observed, whether the observation is applicable to the current artefact and operating conditions, what interpretation is justified, what limitations must accompany it, what cannot be claimed, and which analyst actions are permitted.

The C5 objective is represented by the following flow:

```text
C2 / C3 / C4
      ↓
TECHNICAL SIGNAL
      ↓
EVIDENCE CLASS
      ↓
C5 INTERPRETATION
      ↓
APPLICABILITY / SCOPE
      ↓
LIMITATIONS + NON-CLAIMS
      ↓
ANALYST-FACING FINDING
      ↓
GOVERNED ANALYST ACTION
      ↓
AUDIT RECORD
```

A signal that cannot be safely interpreted is not silently discarded and is not converted into a reassuring result. Lack of interpretability can itself produce an `UNAVAILABLE`, `UNRESOLVED`, `CONFLICTING`, or out-of-scope finding.

---

## 2. C5 Scope and Boundaries

### 2.1 C5 scope

C5 owns the following research responsibilities:

1. **Assurance semantics** — define what downstream findings can establish.
2. **Drift interpretation** — prevent distributional difference from becoming unsupported causal attribution.
3. **Evidence semantics** — distinguish raw observations from interpretation and corroboration.
4. **Confidence representation** — avoid unsupported scalar confidence or compromise probability.
5. **Reference-health interpretation** — make reference quality part of every reference-relative finding.
6. **Scope enforcement** — prevent results from being generalized beyond tested detector/version/runtime/format/operating-condition combinations.
7. **Analyst governance** — define bounded dispositions and required authority.
8. **Limitation-first reporting** — ensure uncertainty and unsupported conditions are visible.
9. **Cannot-Claim enforcement** — prevent known semantic overreach.
10. **Audit semantics** — preserve decisions, overrides, evidence links, and review history.

### 2.2 Absolute C5 boundaries

C5 must not produce or imply:

- probability of compromise;
- arbitrary overall risk score;
- anomaly = attack;
- hash mismatch = malicious tampering;
- unavailable assessment = clean;
- no alert = clean;
- natural shift = manipulation;
- detector count = independent corroboration;
- raw detector statistic = compromise probability;
- validation beyond the exact tested configuration;
- transfer of benchmark calibration to shifted SIH conditions without relevant validation.

These are **semantic safety constraints**, not presentation preferences.

### 2.3 Status vocabulary

| Status | Meaning |
|---|---|
| `BUILD` | Authorized/recommended for implementation within the bounded MVP scope |
| `BUILD (bounded)` | Buildable only within explicit configuration or semantic limits |
| `PROTOTYPE` | Experimental or upstream mechanism; not validated for operational analyst-facing use |
| `DEFER` | Not part of the current build scope |
| `REJECT` | Not accepted for the current design |
| `PROHIBITED` | Violates an absolute C5 boundary |
| `NOT ESTABLISHED` | Evidence is insufficient to support the claim |
| `UNVERIFIED` | Verification required but not performed/documented |
| `CONFIGURATION_REQUIRED` | Mission-owner or deployment authority must supply the value/policy |

**BUILD ≠ implemented.**  
**PROTOTYPE ≠ validated.**  
**RECOMMENDATION ≠ project approval.**

---

## 3. Problem Context

The assurance problem requires the available evidence to distinguish, only where justified, among three broad classes of explanation:

1. legitimate operational distributional change;
2. accidental corruption or unintended processing change;
3. adversarial manipulation.

The central difficulty is that many statistical mechanisms identify **difference**, not **cause**. A detector may establish that an observed sample differs from a reference distribution while remaining unable to establish why that difference arose.

```text
REFERENCE
   ↓
SHIFT DETECTOR
   ↓
DISTRIBUTIONAL DIFFERENCE OBSERVED
   ↓
CAUSE?
   ├── OPERATIONAL
   ├── ACCIDENTAL
   ├── ADVERSARIAL
   └── CANNOT_DETERMINE
```

The `CANNOT_DETERMINE` branch is a valid outcome and must remain visible.

### 3.1 Primary threat surfaces

| ID | Threat surface | C5 relevance |
|---|---|---|
| T-01 | Model-weight manipulation | A changed or anomalous model artefact still requires bounded interpretation; change alone does not establish adversarial cause. |
| T-02 | Annotation poisoning | COCO/YOLO annotation modification can create integrity evidence but causal attribution still requires appropriate evidence. |
| T-03 | Reference contamination | A compromised, stale, or unknown reference can invalidate reference-relative interpretation. |
| T-04 | Audit-trail tampering | Auditability requires tamper evidence and explicit trust boundaries around the chain root, key, storage, archive, and clock. |
| T-05 | Sparse/localized manipulation | Small affected fractions may evade batch-level distributional detectors. |
| T-06 | Score laundering | Hypothesized adaptive behaviour could remain below thresholds; adaptive robustness is not established for the MVP. |
| T-07 | Context-metadata forgery | False sensor, season, acquisition, or other operational context could incorrectly make anomalous evidence appear operationally explained. |

### 3.2 Attribution boundary

No supplied C5 packet contains an SIH-specific labeled adversarial experiment that establishes reliable attribution between ordinary operational drift and malicious manipulation.

Therefore:

```text
DETECTOR FIRED
      ≠
ATTACK DETECTED
```

The allowed progression is:

```text
SIGNAL
  ↓
INTERPRETATION
  ↓
APPLICABILITY / LIMITATION
  ↓
ANALYST ACTION
```

---

## 4. Evidence Semantics

### 4.1 Evidence model

C5 distinguishes four layers that must not be collapsed:

| Layer | Question answered |
|---|---|
| **Raw signal** | What numerical, cryptographic, structural, or behavioural observation did the detector produce? |
| **Interpretation** | What bounded semantic state is consistent with that observation? |
| **Evidence/confidence representation** | How well supported and applicable is that interpretation under the declared scope? |
| **Analyst action** | What governed human disposition is permitted given the finding, limitations, and authority? |

A raw detector value remains a detector-native statistic. For example, a divergence value, p-value, reconstruction error, or digest comparison retains the semantics of that detector. It is not automatically transformed into security probability.

### 4.2 Canonical verified findings

| Claim ID | Canonical finding | Evidence status | Primary packet source |
|---|---|---|---|
| VC-01 | Distribution-shift detection observes distributional difference; it does not identify the cause as operational, accidental, or adversarial. | FACT | S7OC5_V1 §4; S8OC5 §1; S9OC5 |
| VC-02 | A raw detector statistic is detector-native evidence, not a posterior probability of compromise. | FACT | S7OC5_V1 §11 C5-NC-002; S9OC5 |
| VC-03 | Anomaly/hash mismatch ≠ attack; unavailable ≠ clean; no alert ≠ clean. | FACT | S7OC5_V1 §11 C5-NC-005/006/007; S8OC5 §1; S9OC5 |
| VC-04 | Detector count ≠ independent corroboration because detectors may share preprocessing, decoder, embedding, reference, or another common cause. | FACT | S7OC5_V1 §11 C5-NC-004; S8OC5 §2.4/§2.6; S9OC5 |
| VC-05 | Calibration is distribution-specific; benchmark calibration does not automatically transfer to shifted operational conditions. | FACT | S7OC5_V1 §14; S8OC5 §2.8; S9OC5 calibration table |
| VC-06 | Rabanser et al. provides benchmark evidence for dataset-shift methods, not SIH operational performance evidence. | FACT | S7OC5_V1 §14/§16 |
| VC-07 | Conformal prediction provides coverage-style guarantees under stated assumptions such as exchangeability; this is not a generic attack-detection FPR guarantee. | FACT | S7OC5_V1 §14; S8OC5 §5 |
| VC-08 | A hash chain is tamper-evident within a trusted chain, not tamper-proof against root/key/storage/clock/archive attacks. | FACT | S7OC5_V1 §10; S8OC5 C5-RT-MAJ-004 |
| VC-09 | Existing repository/implementation evidence does not establish the required end-to-end SIH format and offline coverage. | FACT | S7OC5_V1 §22 |
| VC-10 | The bounded semantic/governance core is considered feasible for the five-day MVP and authorized for BUILD, subject to stated dependencies. | FACT / bounded recommendation | S7OC5_V1 §19/§25; S8OC5 §1; S9OC5 |

### 4.3 Partially supported claims

**PS-01 — Temperature scaling.** Temperature scaling has benchmark support under i.i.d. conditions, while calibration can degrade under distribution shift. Transfer to SIH conditions is not established. Analyst-facing temperature-scaled confidence is therefore rejected for the MVP.

**PS-02 — `failing-loudly` repository.** A research repository and benchmark pipeline exist, but the C5 packet does not establish a pinned commit, lockfile, wheelhouse, SIH-format capability, or air-gapped installation test.

**PS-03 — `torch-two-sample`.** Two-sample functionality exists, but offline/native build dependencies are unresolved in the packet.

**PS-04 — F5 operational-drift semantics.** `OPERATIONAL-DRIFT-CONSISTENT` can be considered only when context is authenticated. Authenticated context still does not prove exclusive causal explanation. A `CONFIRMED` sub-state requires mission-owner definition.

**PS-05 — Six-state disposition taxonomy.** The disposition model is coherent, but authority assignments for `CONTAIN/HOLD` and `OVERRIDE` remain deployment configuration, not verified organizational policy.

---

## 5. Drift and Shift Taxonomy

V2-C5-A defines six shift categories. Across all six, the current evidence is insufficient to claim that the detector itself can reliably distinguish routine shift from manipulation.

| Shift type | Operational meaning | Statistical signature | Possible detector signals | Distinguishable from manipulation? | Analyst-facing interpretation | Required context / metadata | Limitation |
|---|---|---|---|---|---|---|---|
| **Terrain change** | Change in geographical/scene environment | Covariate change in pixel, embedding, feature, class-prior, or spatial distributions | BBSD, KS, MMD, reconstruction error | **NO** | `SHIFT-CONSISTENT`; cause remains `CANNOT_DETERMINE` | Labeled operational terrain envelope and appropriate reference | No SIH terrain-vs-adversarial labeled experiment exists |
| **Seasonal / weather variation** | Seasonal appearance, precipitation, colour-temperature, or related temporal change | Illumination/colour/precipitation artefacts and temporal covariate shift | BBSD, KS, MMD, reconstruction error, pixel-level mechanisms | **NO** | `SHIFT-CONSISTENT`; do not infer manipulation or benignity | Authenticated season/weather context plus relevant labeled ground truth | Operational context is not itself causal proof |
| **Sensor hardware change** | Different sensor characteristics or acquisition device | Resolution, dynamic range, spectral response, noise-signature change; possible shared-preprocessing effects | Potentially all dependent detectors | **NO** | `OUT_OF_SCOPE` where sensor is outside validated reference scope; co-firing is not independent corroboration | Sensor identity, version, preprocessing and reference provenance | Common preprocessing can cause multiple detectors to co-fire |
| **Illumination / viewing-angle change** | Lighting, shadow, viewpoint or apparent surface change | Brightness, contrast, shadow, albedo or feature-distribution change | BBSD, KS, MMD, reconstruction error | **NO** | `SHIFT-CONSISTENT`; benign-cause review before escalation | Authenticated acquisition/illumination context | Illumination is a documented common-cause counterexample |
| **Acquisition protocol / processing change** | Compression, resizing, framing, serialization or processing-pipeline change | Compression artefacts, resolution/framing differences, digest changes | Hash/digest mechanisms and batch distribution detectors | **NO** | `INTEGRITY-CHANGE-CONSISTENT` may be appropriate; F7 required before escalation | Processing/configuration provenance | Benign conversion can alter digests; mismatch ≠ attack |
| **Adversarial / malicious shift** | Targeted alteration of data/model/annotations or related behaviour | Potential distribution shift, weight perturbation, annotation changes; may be sparse/subtle | Potentially all mechanisms, but sparse alterations may remain below batch thresholds | **CANNOT_DETERMINE** | Maximum bounded state is `MANIPULATION-CONSISTENT`, only after its policy gate is defined | Mission-owner evidence threshold plus security-specific corroborating evidence | State does not confirm compromise; adaptive/sparse robustness not established |

### 5.1 Governing interpretation

For every row above:

```text
OBSERVED SHIFT
      ↓
SHIFT-CONSISTENT
      ↓
CAUSE NOT ESTABLISHED
      ↓
CANNOT_DETERMINE
```

unless additional, independent, in-scope evidence justifies a more specific bounded state.

No ambiguity is converted into a security verdict.

---

## 6. Natural Shift vs Manipulation

Natural operational variation explicitly considered in the C5 source includes terrain, season/weather, sensor hardware, illumination/viewing angle, and acquisition/processing changes.

These conditions matter because an operational shift may create detector behaviour similar to that produced by manipulation.

The C5 packet does **not** document the SIH-specific operating envelope for these variables sufficiently to establish natural-shift false-positive rate. Consequently:

- no project-level natural-shift FPR may be reported as established;
- no detector threshold may be promoted as an attack/benign separator based only on benchmark evidence;
- no natural-shift detector firing may be described as proof of manipulation;
- no absence of detector firing may be described as proof of clean status.

The unresolved causal question remains:

```text
DISTRIBUTIONAL DIFFERENCE
           ↓
      WHY DID IT OCCUR?
       /      |       \
operational accidental adversarial
       \      |       /
        CANNOT_DETERMINE
```

The system may attach authenticated context and describe a finding as **consistent with** operational drift. It must not convert that context into exclusive proof that manipulation did not occur.

---

## 7. Reference Health and Scope

### 7.1 Why reference health is part of the evidence

A reference-relative mechanism is meaningful only to the extent that its reference remains appropriate, identifiable, and sufficiently trusted for the declared scope.

The C5 reference-health states are:

| State | Meaning |
|---|---|
| `HEALTH_VERIFIED` | Reference has passed the defined provenance/health procedure for the relevant scope |
| `HEALTH_UNVERIFIED` | Reference exists, but its health has not been established by the required procedure |
| `CONTAMINATION_SUSPECTED` | Evidence suggests the reference may itself be contaminated |
| `STALE_SUSPECTED` | Reference may no longer represent the intended operational distribution |
| `UNAVAILABLE` | Required reference cannot validly be used |

C5 recommends that unknown reference health must not produce `CLEAN` or silently permit a reference-relative `SHIFT-CONSISTENT` conclusion. Where the dependency invalidates interpretation, the appropriate semantic result is `UNAVAILABLE`.

### 7.2 Scope representation

The structured scope representation is:

```text
VALIDATED_SCOPE(
    detector_id,
    detector_version,
    loader_runtime,
    format,
    operating_condition,
    reference_version
)
```

with additional states:

```text
PARTIAL_SCOPE
OUT_OF_SCOPE
UNAVAILABLE
```

`VALIDATED_SCOPE` does not transfer automatically to a different model loader, runtime, format, detector version, operating condition, or reference version.

### 7.3 Current reference status

No provenance-backed SIH reference distribution is established in the C5 packet. Until such a reference is documented, findings that depend on it must expose `HEALTH_UNVERIFIED` or `UNAVAILABLE` as appropriate.

---

## 8. Confidence Representation

V2-C5-B replaces scalar confidence collapse with a **Structured Finding**. It explicitly rejects a standalone score, p-value, flag, or free-floating `HIGH/MEDIUM/LOW` label as the primary analyst confidence representation.

### 8.1 Raw signal

A raw signal is the detector-native output:

```text
KS statistic
MMD statistic
reconstruction error
digest comparison result
another detector-native value
```

It answers: **what was measured?**

### 8.2 Interpretation

Interpretation maps the raw observation to a bounded semantic state such as:

```text
STABLE
SHIFT-CONSISTENT
INTEGRITY-CHANGE-CONSISTENT
MANIPULATION-CONSISTENT
CONFLICTING
UNRESOLVED
UNAVAILABLE
```

It answers: **what interpretation is justified by the available rule and evidence?**

### 8.3 Confidence / evidence class

C5 confidence is not an unexplained scalar. It consists of structured evidence concerning:

- how the detection state was derived;
- whether the mechanism is applicable;
- detector and version identity;
- reference identity and health;
- calibration status;
- dependency/common-cause information;
- limitations and non-claims.

It answers: **how bounded and applicable is this interpretation?**

### 8.4 Analyst action

Analyst action is a governed disposition, not a model confidence label. It answers: **what may an authorized analyst do with the finding?**

This separation prevents a common semantic failure:

```text
RAW SCORE 0.73
      ↓
"73% COMPROMISED"     ← PROHIBITED
```

---

## 9. Detector Dependency and Corroboration

### 9.1 Detector count is not corroboration

Multiple detectors may share:

- preprocessing;
- decoder logic;
- embeddings;
- reference distributions;
- input artefacts;
- loaders/runtimes;
- sensor dependencies;
- upstream failure causes.

Consequently:

```text
DETECTOR A FIRED
+
DETECTOR B FIRED
≠
TWO INDEPENDENT PIECES OF EVIDENCE
```

A shared illumination change, sensor transition, decoder defect, preprocessing fault, or contaminated reference could cause several mechanisms to co-fire.

### 9.2 Dependency gate

The engineering recommendation is that a semantic state equivalent to `CORROBORATED MULTI-CHANNEL` must not be emitted until detector dependency has actually been tested and distinctness established.

A field equivalent to:

```text
dependency_metric_tested = TRUE
```

must be a required gate rather than optional metadata if such corroboration language is implemented.

### 9.3 Rejected universal independence threshold

An earlier proposal treated:

```text
r < 0.7
```

as an independence gate.

C5 V2 rejects this as a universal theorem. No SIH-specific dependency experiment establishes a universal numerical independence threshold. The replacement is a **configurable dependency-testing requirement**, with the actual method and acceptance criteria to be justified for the relevant detector pair and operating context.

---

## 10. Calibration and Distribution Shift

### 10.1 C5 calibration position

C5 does not recommend an analyst-facing calibration mechanism for V2 because no calibration study under the actual SIH operating conditions has been documented.

The required calibration representation is therefore explicit:

```text
CALIBRATED(
    dataset_id,
    operating_conditions,
    metric,
    N,
    date
)

or

UNCALIBRATED

or

CALIBRATION_UNKNOWN
```

A bare:

```text
CALIBRATED = TRUE
```

is insufficient.

### 10.2 External literature evidence

**EXTERNAL LITERATURE EVIDENCE — NOT SIH OPERATIONAL VALIDATION**

Guo et al. show the usefulness of temperature scaling on benchmark classification settings.

Ovadia et al. evaluate predictive uncertainty under distribution shift and report that traditional post-hoc calibration can degrade under shift.

Rabanser et al. evaluate methods for detecting dataset shift and provide benchmark evidence for two-sample-testing approaches; this does not establish causal attack attribution or SIH operational performance.

These sources justify research interest in calibration and shift detection. They do **not** establish:

```text
benchmark result
      =
SIH operational validation
```

### 10.3 Conformal prediction

The current C5 treatment is similarly bounded. Conformal methods may offer coverage-style guarantees under stated assumptions such as exchangeability. They are not represented as:

- attack detectors;
- generic security false-positive guarantees;
- guaranteed adversarial-detection mechanisms.

No specific conformal-prediction paper is named in the C5 source registry, so this public edition does not introduce a new literature citation and attribute it to the original packet.

---

## 11. Candidate Methods

### Semantic Governance Core

**Purpose.** Convert heterogeneous detector evidence into bounded, analyst-facing findings without collapsing uncertainty into a scalar.

**What evidence it consumes.** C2/C3/C4 adapter outputs, detector-native semantics, version identifiers, scope metadata, reference information, dependency information, and operational context.

**What it can establish.** A structured semantic interpretation, applicability status, mandatory limitations, non-claims, and permitted workflow state.

**What it cannot establish.** Whether compromise actually occurred merely because an anomaly or shift exists.

**Dependencies.** Frozen C2/C3/C4 adapter contract; mission-owner policy fields; reference-health information.

**Current status.** `BUILD`.

**Project-specific evidence.** The architecture is coherent across the V1, Red Team, and Reverify packets. No independent implementation execution is recorded.

**Limitations.** Correctness remains dependent on upstream evidence quality and configuration.

**Five-day feasibility.** Primary five-day MVP deliverable if upstream interfaces freeze early.

**Analyst-facing role.** Core semantic layer.

**Sources.** S7OC5_V1 §19/§25; S8OC5 §1; S9OC5.

### Reference Health + Scope Enforcement

**Purpose.** Prevent reference-relative evidence from being treated as valid when the reference or operating scope is unknown.

**What evidence it consumes.** Reference identity/version/digest, provenance, health state, detector/version/runtime/format, and operating condition.

**What it can establish.** Whether a result is interpretable within declared scope.

**What it cannot establish.** That a reference is clean without the defined verification procedure.

**Dependencies.** OQ-02 reference-trust procedure and C2/C3/C4 coverage metadata.

**Current status.** `BUILD`.

**Project-specific evidence.** Required by C5's reference-health correction and structured finding schema.

**Limitations.** SIH reference provenance and health procedure remain unresolved.

**Five-day feasibility.** Included in Day 1 schema work and subsequent rule enforcement.

**Analyst-facing role.** Mandatory applicability and reference-health disclosure.

**Sources.** S8OC5 C5-RT-CRIT-006; S9OC5; CC-23.

### Structured Finding Card

**Purpose.** Represent confidence and interpretation without scalar collapse.

**What evidence it consumes.** Detection rule, raw signal, applicability, reference health, calibration state, limitations, and non-claims.

**What it can establish.** A transparent evidence package identifying how the interpretation was derived.

**What it cannot establish.** Security probability or unsupported severity.

**Dependencies.** Frozen finding schema and UI enforcement.

**Current status.** `BUILD`.

**Project-specific evidence.** V2-C5-B provides the schema and mandatory limitation/non-claim blocks.

**Limitations.** Upstream evidence fields must be available and correctly populated.

**Five-day feasibility.** Included in Day 3.

**Analyst-facing role.** Primary analyst-facing evidence representation.

**Sources.** V2-C5-B; S7OC5_V1 §11; S8OC5 C5-RT-CRIT-002.

### Six-State Analyst Disposition Workflow

**Purpose.** Convert findings into governed human actions while preserving uncertainty.

**What evidence it consumes.** Finding state, applicability, reference health, authenticated context where relevant, rationale, analyst identity, and authority.

**What it can establish.** Which workflow disposition is recorded.

**What it cannot establish.** Clean status, confirmed compromise, or causal truth merely from a disposition.

**Dependencies.** Mission-owner authority mapping and identity binding.

**Current status.** `BUILD`.

**Project-specific evidence.** Six canonical disposition states are defined in V2-C5-C.

**Limitations.** `CONTAIN/HOLD` and `OVERRIDE` authority remain configurable.

**Five-day feasibility.** Included in Day 3.

**Analyst-facing role.** Governance workflow.

**Sources.** V2-C5-C; S7OC5_V1 §9; S8OC5 C5-RT-MAJ-006.

### Hash-Chained Audit Trail

**Purpose.** Make disposition history and evidence linkage tamper-evident within a trusted chain.

**What evidence it consumes.** Finding IDs, case IDs, analyst/disposition records, supporting evidence references, previous event hash, and canonical serialized event content.

**What it can establish.** Whether the recorded chain verifies against its stored root and predecessor links.

**What it cannot establish.** Truth of detector evidence or protection against root/key/storage/clock/archive substitution.

**Dependencies.** Canonical serialization, trusted root/key handling, trusted clock, analyst identity, storage policy.

**Current status.** `BUILD`.

**Project-specific evidence.** V2-C5-D defines 14 mandatory fields and chain verification.

**Limitations.** Root, key, clock, storage, and archive trust remain explicit boundaries.

**Five-day feasibility.** Implementation Day 3; verification Day 5.

**Analyst-facing role.** Traceability and second-level review trigger.

**Sources.** S7OC5_V1 §10; S8OC5 C5-RT-MAJ-004/005.

### Benign-Cause Checklist (F7)

**Purpose.** Require plausible documented benign explanations to be examined before escalation.

**What evidence it consumes.** Asset/change context such as processing change, recompression, resolution/framing changes, serialization change, sensor/illumination context, and other source-supported operational metadata.

**What it can establish.** That a known benign explanation has or has not been considered.

**What it cannot establish.** That an event is benign, safe, or non-adversarial.

**Dependencies.** Context provenance and appropriate evidence.

**Current status.** `BUILD`.

**Project-specific evidence.** Required for digest/processing-change scenarios and tested conceptually by T05.

**Limitations.** Checklist completion is not causal proof.

**Five-day feasibility.** Included in governance/rule-engine scope.

**Analyst-facing role.** Escalation gate.

**Sources.** C5 method matrix; V2-C5-A acquisition/processing row; T05.

### Override-Pattern Governance Advisory

**Purpose.** Identify patterns in repeated analyst overrides that may require governance review.

**What evidence it consumes.** Override events, finding class, timestamps/time window, analyst/reviewer records.

**What it can establish.** That the configured review trigger has been reached.

**What it cannot establish.** Malicious analyst behaviour or unsafe operation merely from override count.

**Dependencies.** Mission-owner threshold and time window.

**Current status.** `BUILD (bounded)`.

**Project-specific evidence.** Second-level review trigger is specified; `>50` is only a proposed criterion.

**Limitations.** No operationally validated threshold exists.

**Five-day feasibility.** Bounded advisory is part of the semantic/governance core.

**Analyst-facing role.** Governance advisory, not security scoring.

**Sources.** V2-C5-C §C.3; CC-29; OQ-13.

### BBSD / KS / MMD Detector Harness

**Purpose.** Experimentally measure distributional difference relative to a reference.

**What evidence it consumes.** Reference and target samples plus detector-specific representation/statistical configuration.

**What it can establish.** Under tested conditions, whether statistical evidence indicates distributional difference according to the selected test.

**What it cannot establish.** Cause of the difference, compromise, or SIH operational FPR without project validation.

**Dependencies.** Trusted reference, operating-envelope ground truth, tested implementation, dependency packaging.

**Current status.** `PROTOTYPE`.

**Project-specific evidence.** External benchmark support exists; SIH natural-shift FPR is unmeasured.

**Limitations.** Not analyst-facing as a security finding until required project validation exists.

**Five-day feasibility.** Explicitly outside five-day BUILD validation scope.

**Analyst-facing role.** None in the MVP security path.

**Sources.** Rabanser et al.; S7OC5_V1 §14/§16; S9OC5.

### Conformal Prediction Module

**Purpose.** Explore coverage-based uncertainty representation under its stated statistical assumptions.

**What evidence it consumes.** Exact C5 implementation/data contract is **not established in the current C5 research packet**.

**What it can establish.** Coverage-style properties only under applicable assumptions and a valid implementation.

**What it cannot establish.** Attack detection, generic security FPR, or adversarial-detection guarantees.

**Dependencies.** Exchangeability assumptions, valid calibration/reference data, and implementation-specific conditions.

**Current status.** `PROTOTYPE — upstream only`.

**Project-specific evidence.** No SIH operational validation.

**Limitations.** Distribution shift and adversarial conditions can undermine the assumptions on which coverage statements rely.

**Five-day feasibility.** Excluded from five-day BUILD scope.

**Analyst-facing role.** None in the MVP security-finding path.

**Sources.** S7OC5_V1 §14/§16; S8OC5 §5.

### MANIPULATION-CONSISTENT Gating Logic

**Purpose.** Define the maximum bounded semantic state that may be emitted when evidence satisfies an explicitly configured security-evidence rule.

**What evidence it consumes.** Security-relevant evidence, dependency-aware corroboration, applicability information, and mission-owner threshold/policy.

**What it can establish.** That observed evidence satisfies the defined `MANIPULATION-CONSISTENT` rule.

**What it cannot establish.** Confirmed compromise or malicious intent.

**Dependencies.** OQ-03 mission-owner threshold and supporting evidence contract.

**Current status.** `PROTOTYPE — mission-owner threshold required`.

**Project-specific evidence.** State exists; emission policy remains unresolved.

**Limitations.** Until the threshold is defined, safe emission is unavailable.

**Five-day feasibility.** State-machine logic may be prototyped; operational use is blocked.

**Analyst-facing role.** None until gate closure.

**Sources.** S8OC5 C5-RT-CRIT-001; S9OC5; OQ-03.

### F5 Confirmed/Inferred Drift Semantics

**Purpose.** Distinguish contextual operational-drift interpretation from unsupported causal attribution.

**What evidence it consumes.** Drift signal plus independently authenticated operational context.

**What it can establish.** A bounded operational-drift-consistent interpretation when the required context conditions are met.

**What it cannot establish.** Exclusivity of operational cause.

**Dependencies.** Context authentication and mission-owner definition of any `CONFIRMED` sub-state.

**Current status.** `PROTOTYPE — context authentication gate`.

**Project-specific evidence.** Partial support only.

**Limitations.** Authenticated context ≠ causal proof.

**Five-day feasibility.** Prototype semantics may be encoded; deployment use remains configuration-dependent.

**Analyst-facing role.** Conditional only after gate closure.

**Sources.** PS-04; OQ-06.

### Sequential Drift Adaptation / Reference Learning

**Purpose.** Update a reference as operational distributions change.

**What evidence it consumes.** Exact safe adaptation contract is **not established in the current C5 research packet**.

**What it can establish.** Not established for the current project.

**What it cannot establish.** That an adapted reference has not normalized malicious or contaminated drift.

**Dependencies.** Validated anchor and contamination-detection procedure.

**Current status.** `DEFER`.

**Project-specific evidence.** No validated anchor or contamination procedure is documented.

**Limitations.** Drift creep and reference contamination.

**Five-day feasibility.** Outside MVP.

**Analyst-facing role.** None.

**Sources.** C5 V2 §7.4.

### Pass-Through Raw-Signal Mode

**Purpose.** Preserve access to raw detector evidence when semantic dependency metadata is unavailable.

**What evidence it consumes.** Raw detector output.

**What it can establish.** Only the underlying detector-native observation.

**What it cannot establish.** Interpreted risk, corroboration, causal attribution, or clean status.

**Dependencies.** Minimal detector availability.

**Current status.** `DEFER — fallback only`.

**Project-specific evidence.** Retained solely as a fallback.

**Limitations.** High analyst burden and alert fatigue; lacks interpretive context.

**Five-day feasibility.** Technically simple but not preferred.

**Analyst-facing role.** Exceptional fallback.

**Sources.** C5 V2 §7.5.

### Quantitative Fusion / Meta-Classifier

**Purpose.** Aggregate detector outputs into a combined scalar or learned meta-decision.

**What evidence it consumes.** Multiple detector outputs.

**What it can establish.** No defensible project-level security conclusion under current evidence.

**What it cannot establish.** Valid combined compromise probability or risk score when dependency structure is unknown.

**Dependencies.** Detector independence/dependency model, valid training/calibration evidence.

**Current status.** `REJECT`.

**Project-specific evidence.** Common-cause/dependency failure mode makes the scalar uninterpretable.

**Limitations.** Violates C5's semantic boundary when used as an undefendable security score.

**Five-day feasibility.** Not applicable; rejected.

**Analyst-facing role.** None.

**Sources.** FM-03; C5 V2 §7.2.

### Temperature Scaling as Analyst Confidence

**Purpose.** Produce calibrated predictive confidence through temperature scaling.

**What evidence it consumes.** Exact project data contract is **not established in the current C5 research packet**; external literature uses model outputs plus calibration data.

**What it can establish.** Benchmark calibration improvements under the conditions tested by the cited literature.

**What it cannot establish.** Calibration under arbitrary SIH distribution shift.

**Dependencies.** SIH-specific calibration study.

**Current status.** `REJECT for MVP`.

**Project-specific evidence.** No SIH calibration study exists.

**Limitations.** Attractive numerical precision may be mistaken for security confidence.

**Five-day feasibility.** Not part of MVP analyst confidence.

**Analyst-facing role.** None.

**Sources.** Guo et al.; Ovadia et al.; PS-01.

### Compromise Probability / Overall Risk Score

**Purpose.** Would numerically summarize compromise or security risk.

**What evidence it consumes.** No valid evidence contract exists because the output itself violates the C5 boundary.

**What it can establish.** Nothing permitted by C5.

**What it cannot establish.** Probability of compromise or true overall risk from the available evidence.

**Dependencies.** Not applicable.

**Current status.** `REJECT — PROHIBITED`.

**Project-specific evidence.** Explicit absolute boundary.

**Limitations.** Any such output would create unsupported semantics.

**Five-day feasibility.** Not applicable.

**Analyst-facing role.** Prohibited.

**Sources.** PS-R-08; CC-28.

### Learned Deep Ensembles

**Purpose.** Use multiple trained models to improve predictive uncertainty estimation.

**What evidence it consumes.** Exact project evidence contract is **not established in the current C5 research packet**.

**What it can establish.** Not established for C5.

**What it cannot establish.** A permissible project capability without violating retraining constraints.

**Dependencies.** Training multiple models.

**Current status.** `REJECT for MVP`.

**Project-specific evidence.** Conflicts with the no-baseline-retraining constraint and five-day scope.

**Limitations.** Retraining requirement.

**Five-day feasibility.** Outside permitted scope.

**Analyst-facing role.** None.

**Sources.** C5 V2 §7.3.

---

## 12. Method Status Matrix

| Method / Component | Evidence status | V2 status | Dependency | Why |
|---|---|---|---|---|
| Semantic Governance Core | Verified architecture / packet-supported | `BUILD` | C2/C3/C4 contract | Core bounded semantic layer |
| Reference Health + Scope Enforcement | Required control | `BUILD` | Reference provenance and coverage data | Reference-relative evidence is invalid without scope/health |
| Structured Finding Card | Verified design | `BUILD` | Frozen schema | Prevents scalar collapse |
| Six-State Analyst Disposition Workflow | Proposed, coherent | `BUILD` | Mission-owner authority | Makes `UNAVAILABLE/NO DECISION` explicit |
| Hash-Chained Audit Trail | Required control | `BUILD` | Root/key/clock/storage trust | Provides bounded tamper evidence |
| Benign-Cause Checklist (F7) | Required control | `BUILD` | Context evidence | Prevents premature escalation |
| Override-Pattern Governance Advisory | Bounded | `BUILD (bounded)` | Mission-owner threshold | Threshold cannot be invented |
| BBSD / KS / MMD harness | Benchmark-supported; SIH FPR unmeasured | `PROTOTYPE` | SIH reference and ground truth | Internal only pending project validation |
| Conformal Prediction | Conditional coverage | `PROTOTYPE — upstream only` | Statistical assumptions | Not a security-finding mechanism |
| MANIPULATION-CONSISTENT gate | State defined, threshold unresolved | `PROTOTYPE` | Mission-owner threshold | Unsafe to emit before policy is defined |
| F5 Confirmed/Inferred Drift | Partially supported | `PROTOTYPE` | Context authentication | Context does not prove cause |
| Sequential reference adaptation | No validated anchor | `DEFER` | Safe adaptation procedure | Drift-creep/contamination risk |
| Pass-through raw signal | Technically simple | `DEFER — fallback` | Detector availability | High interpretation burden |
| Quantitative fusion/meta-classifier | Dependency problem | `REJECT` | Independence model | Produces undefendable scalar |
| Temperature Scaling for analyst confidence | External benchmark support only | `REJECT for MVP` | SIH calibration validation | Calibration may degrade under shift |
| Compromise probability / overall risk score | Boundary violation | `PROHIBITED` | — | Explicit C5 constraint |
| Learned deep ensembles | Conflicts with retraining constraint | `REJECT for MVP` | Retraining | Outside project constraints |

---

## 13. Semantic Governance Core

The selected five-day semantic/governance core contains seven components.

### 13.1 Structured Finding schema

Provides the canonical separation among detection, interpretation, applicability, raw evidence, reference health, limitations, and non-claims.

### 13.2 Evidence normalizer

Consumes C2/C3/C4 adapter output and maps detector-specific fields to a versioned evidence contract without changing their native meaning.

The normalizer must preserve:

```text
detector identity
detector version
native statistic semantics
threshold/test rule
format/runtime
reference identity
operating condition
dependency information
```

### 13.3 Structured rule engine

Applies explicit rules for:

- semantic-state derivation;
- common-cause handling;
- contradictions;
- reference-health propagation;
- applicability/scope;
- dependency-aware corroboration.

Rules must be identifiable by rule ID.

### 13.4 Limitation-first rendering

The source recommends that `LIMITATIONS` be rendered before detection status in analyst-facing UI. This prevents visually dominant alerts from obscuring critical caveats.

### 13.5 Hash-chained audit trail

Every disposition and state-changing governance event is linked into an auditable chain, with a separate chain-verification operation.

### 13.6 Benign-cause checklist

Known benign explanations must be checked before escalation where relevant, especially for processing/digest changes and operational shifts.

### 13.7 Override-pattern advisory

Repeated override behaviour may trigger governance review when a mission-owner-defined threshold and time window are reached.

### 13.8 Engineering implications

The C5 source derives several concrete implementation rules:

**Schema enforcement over documentation.** A forbidden semantic claim must be prevented by schema/API rules rather than merely discouraged in prose.

**Limitation-first rendering.** Limitations cannot be hidden in footnotes.

**Mandatory override rationale.** Empty `override_rationale` must be rejected, not merely warned about.

**Dependency-tested corroboration.** Corroboration language requires evidence of detector distinctness.

**UNAVAILABLE as first-class state.** Missing evidence cannot be converted into a reassuring state.

**Explicit configuration gaps.** Unresolved authority fields must remain `CONFIGURATION_REQUIRED`.

**Offline packaging contract.** Runtime dependencies require pinned artefacts/hashes before offline deployability is claimed.

**Out-of-band audit-root protection.** The system cannot self-certify the root of its own audit chain.

---

## 14. Structured Finding Schema

The V2-C5-B schema is the primary confidence representation.

```yaml
FINDING_STATE:
  - STABLE
  - SHIFT-CONSISTENT
  - INTEGRITY-CHANGE-CONSISTENT
  - MANIPULATION-CONSISTENT
  - CONFLICTING
  - UNRESOLVED
  - UNAVAILABLE

DETECTION_STATUS:
  - UNASSESSED
  - DERIVED_FROM_RULE:<rule_id>

INTERPRETATION_STATUS:
  one_of: FINDING_STATE

APPLICABILITY_STATUS:
  - VALIDATED_SCOPE(
      detector_id,
      detector_version,
      loader_runtime,
      format,
      operating_condition,
      reference_version
    )
  - PARTIAL_SCOPE
  - OUT_OF_SCOPE
  - UNAVAILABLE

RAW_SIGNAL:
  raw_value: detector-native statistic
  signal_type: detector-native signal type
  signal_semantics: plain-language detector meaning
  threshold_or_test_rule: exact applied rule
  reference_id: required where applicable
  reference_version: required where applicable
  reference_digest: required where applicable

  calibration_status:
    - CALIBRATED(dataset_id, conditions, metric, N, date)
    - UNCALIBRATED
    - CALIBRATION_UNKNOWN

  NOT_A_PROBABILITY_OF_COMPROMISE: mandatory

REFERENCE_HEALTH:
  - HEALTH_VERIFIED
  - HEALTH_UNVERIFIED
  - CONTAMINATION_SUSPECTED
  - STALE_SUSPECTED
  - UNAVAILABLE

LIMITATIONS:
  mandatory: true
  rendering: FIRST

NON_CLAIMS:
  source: V2-C5-E Cannot-Claim Registry
  mandatory: true
```

The source also expects the broader assurance workflow to preserve the affected asset, linked evidence, and resulting analyst action. Exact integration-level field names beyond the frozen V2-C5-B core are not established in the current C5 packet and should be frozen with C6 rather than invented here.

No arbitrary severity or security score is introduced.

---

## 15. Analyst Disposition Registry

V2-C5-C defines six canonical analyst dispositions. Authority assignments remain configurable where the packet has not established organizational policy.

| Disposition | Meaning | Required evidence / condition | Authority status | Must not imply | Audit behaviour |
|---|---|---|---|---|---|
| `ACCEPT` | Accept finding as usable within declared scope | Interpretable state; not out of scope; reference health acknowledged; limitations reviewed | `[CONFIGURABLE: L1]` | Clean status or absence of manipulation | Record reason and original/final state |
| `ACCEPT WITH CONTEXT` | Accept with independently documented operational context | All `ACCEPT` conditions plus authenticated context and identified source | `[CONFIGURABLE: L1]` | Causal proof or exclusion of manipulation | Attach context evidence |
| `ESCALATE` | Route for higher-level review | `MANIPULATION-CONSISTENT`, `CONFLICTING`, `UNRESOLVED`, unexplained, or mission-defined consequential evidence | L1 may escalate; reviewer configurable | Resolution | Preserve escalation reason/reviewer/outcome |
| `CONTAIN / HOLD` | Place affected artefact on operational hold | Escalation conditions plus mission-authorized containment | `[CONFIGURABLE: L2/mission-authorized]` | Confirmed compromise or confirmed clean | Record containment reason and authority |
| `OVERRIDE` | Explicitly replace system-derived interpretation or recommended disposition | Mandatory non-empty override rationale; original state remains immutable | `[CONFIGURABLE: senior authority]` | Erasure of original finding | Record replacement, rationale, reviewer, outcome |
| `UNAVAILABLE / NO DECISION` | Required assessment cannot validly be completed | Unknown reference, out-of-scope condition, unsupported detector/format, missing ground truth, or equivalent blocker | System or analyst may invoke | Clean, unchanged, or resolved status | Record unavailable cause |

### 15.1 Second-level review triggers

Second-level review is triggered when one of the following source-defined conditions occurs:

- the configured recurring-override threshold/time window is reached;
- `MANIPULATION-CONSISTENT` or escalated evidence is overridden without required reviewer signature;
- `CHAIN_VERIFICATION_FAILED` occurs;
- reference health degrades after dependent findings have been issued;
- a finding is issued against `OUT_OF_SCOPE` or `UNAVAILABLE` conditions;
- an `ACCEPT` disposition is attempted on out-of-scope/unavailable evidence without documented mission authorization.

The source's earlier `>50 override events` value remains only a **PROPOSED CRITERION / NOT VALIDATED THRESHOLD**.

---

## 16. MANIPULATION-CONSISTENT Gating

`MANIPULATION-CONSISTENT` is a bounded semantic state. It is not equivalent to:

```text
ATTACK DETECTED
CONFIRMED COMPROMISE
MALICIOUS CONTRIBUTOR
```

The state can only mean that evidence satisfies a defined, in-scope rule describing evidence as consistent with manipulation.

### Required gate

Before the state may be emitted operationally, the mission owner must define the evidence threshold/policy identified by OQ-03.

Until that happens:

```text
MANIPULATION-CONSISTENT
=
NOT SAFELY EMITTABLE
```

The implementation may prototype the state machine, but the analyst-facing state remains gated.

### Additional constraints

Even after a threshold is defined:

1. applicability must be established;
2. reference health must be represented;
3. common-cause detector dependencies must be considered;
4. the required security-specific evidence must be identified;
5. limitations and non-claims remain mandatory;
6. the state still does not equal confirmed compromise.

---

## 17. Benign-Cause Checklist

The F7 Benign-Cause Checklist is a **semantic governance control**, not an “attack filter.”

Its purpose is to stop an integrity or anomaly signal from being escalated solely because it appears suspicious.

Source-supported benign/contextual explanations include:

| Evidence condition | Required check before escalation | Semantic effect |
|---|---|---|
| Digest/hash mismatch | Recompression, format conversion, serialization or processing change | Mismatch may remain `INTEGRITY-CHANGE-CONSISTENT`; attack attribution prohibited |
| Distribution shift | Terrain, season/weather, sensor, illumination/viewing angle, acquisition change | `SHIFT-CONSISTENT`; causal branch may remain `CANNOT_DETERMINE` |
| Multi-detector co-fire | Shared preprocessing, decoder, embedding, reference or sensor dependency | Do not count alerts as independent evidence |
| Sensor transition | Check validated reference/scope for current sensor | May become `OUT_OF_SCOPE` |
| Operational explanation supplied | Verify context provenance/authentication | May support contextual interpretation; does not prove exclusivity |
| Known benign format conversion | Preserve evidence that the conversion occurred | T05 expects checklist execution before escalation |

Checklist completion does not establish benignity. It establishes only that documented alternative explanations were considered.

---

## 18. Audit Trail Specification

V2-C5-D defines a hash-chained audit record with 14 mandatory fields.

### 18.1 Mandatory fields

```yaml
event_id: UUID
finding_id: UUID
case_id: mission_case_identifier

timestamp_utc:
  status: UNVERIFIED_TIME until trusted clock is defined

analyst_id:
  status: IDENTITY_UNBOUND until authentication is defined

disposition: one_of_six_canonical_states
stated_reason: mandatory_non_empty
original_finding_state: immutable
final_state: state_after_disposition
supporting_evidence_refs: list
audit_schema_version: version
previous_event_id: previous_UUID_or_null
prev_event_hash: SHA256(previous_canonical_event)
event_hash: SHA256(current_canonical_event)
```

### 18.2 Additional fields for `OVERRIDE`

```yaml
override_flag: true
original_finding_state: immutable
replacement_state: required
override_rationale: mandatory_non_empty
reviewer_id: required when policy requires
outcome: required
```

### 18.3 Additional fields for `ESCALATE`

```yaml
escalation_reason: required
reviewer_id_when_assigned: recorded
outcome_when_closed: recorded
```

### 18.4 Additional fields for `CONTAIN/HOLD`

```yaml
containment_reason: required
authority_identity: authorizing_role_id
reviewer_id: required
outcome: recorded
```

### 18.5 Tamper-evidence mechanism

C5 recommends SHA-256 over deterministic canonical serialization of mandatory event fields.

Each event stores:

```text
previous_event_id
prev_event_hash
event_hash
```

A chain-verification operation recomputes and verifies the links. Any mismatch raises:

```text
CHAIN_VERIFICATION_FAILED
```

and triggers second-level review.

### 18.6 Auditability ≠ proof of truth

A valid chain means that the recorded history is internally consistent relative to the trusted root and stored chain.

It does **not** prove:

- that the underlying detector was correct;
- that the analyst's explanation was correct;
- that the chain root is authentic;
- that the signing key was uncompromised;
- that privileged storage was not substituted;
- that the clock was trustworthy;
- that an archive was not replaced.

### 18.7 Retention and trust gaps

Retention duration, legal-hold trigger, deletion authority, and preservation obligations remain `CONFIGURATION_REQUIRED`.

`timestamp_utc` remains `UNVERIFIED_TIME` until a trusted clock is defined.

`analyst_id` and `reviewer_id` remain `IDENTITY_UNBOUND` until identity authentication is established.

---

## 19. Cannot-Claim Registry

V2-C5-E is the definitive C5 Cannot-Claim Registry for V2 and C6 handoff.

| ID | C5 cannot claim |
|---|---|
| **CC-01** | That a distribution shift means an attack or manipulation occurred |
| **CC-02** | That a raw anomaly statistic such as `0.73` is a compromise probability |
| **CC-03** | That a p-value is attack probability or compromise confidence |
| **CC-04** | That N detector alerts constitute N independent pieces of evidence |
| **CC-05** | That a hash mismatch proves malicious tampering |
| **CC-06** | That no alert proves the system or model is clean |
| **CC-07** | That an unavailable assessment is equivalent to no detected change |
| **CC-08** | That benchmark results such as MNIST/CIFAR evidence prove SIH aerial-CV operational effectiveness |
| **CC-09** | That temperature scaling is calibrated under arbitrary operational shift |
| **CC-10** | That conformal-prediction coverage is a generic attack-detection FPR guarantee |
| **CC-11** | That a universal BBSD/KS/MMD batch-size minimum exists |
| **CC-12** | That a cited research repository proves air-gapped deployability |
| **CC-13** | That a cited repository proves COCO/YOLO or ONNX/PyTorch/TorchScript coverage |
| **CC-14** | That natural and adversarial causes can always be separated from distribution statistics alone |
| **CC-15** | That adaptive/sparse adversarial robustness has been established by the five-day MVP |
| **CC-16** | That an inferred environmental shift is the same as independently confirmed operational drift |
| **CC-17** | That `r < 0.7` establishes detector independence |
| **CC-18** | That the natural-shift FPR is established or low for SIH |
| **CC-19** | That calibration under shift has been validated for SIH operating conditions |
| **CC-20** | That detector agreement constitutes corroboration before dependency testing |
| **CC-21** | That `MANIPULATION-CONSISTENT` is equivalent to confirmed compromise |
| **CC-22** | That documented operational context proves exclusivity of cause |
| **CC-23** | That reference health is clean or trusted absent a `HEALTH_VERIFIED` procedure |
| **CC-24** | That hash chaining prevents root replacement, key compromise, or privileged storage substitution |
| **CC-25** | That an L1/L2/L3 authority hierarchy is verified organizational policy |
| **CC-26** | That a retention duration has been defined; retention remains `CONFIGURATION_REQUIRED` |
| **CC-27** | That EU AI Act Article 9 mandates specific C5 audit fields |
| **CC-28** | That an overall risk score can be computed or reported |
| **CC-29** | That FPR <5%, ECE within 2×, >50% time reduction, >60% benign-cause recognition, >30% safer override, or >50-event threshold are validated SIH results |
| **CC-30** | That `VALIDATED` applies beyond the exact detector version, loader/runtime, format, operating condition, and reference version actually tested |

---

## 20. Failure and Fallback Rules

V2-C5-F applies a semantic fail-closed rule: absence of sufficient evidence must not silently become a positive or clean result.

### 20.1 Governing rule

```text
IF legitimate-shift ground truth is unavailable,
THEN do not promote a shift-vs-attack distinction method to BUILD
as an operational attribution mechanism.

ALWAYS communicate what cannot be distinguished.

NEVER replace missing evidence with "clean."

NEVER produce an arbitrary overall risk score.
```

### 20.2 Failure mapping

| Failure / uncertainty condition | Required semantic behaviour |
|---|---|
| Missing required evidence | `UNAVAILABLE` or `UNRESOLVED`; identify missing evidence |
| Reference unavailable | `REFERENCE_HEALTH = UNAVAILABLE`; invalidate dependent reference-relative interpretation |
| Reference health unknown | `HEALTH_UNVERIFIED`; do not imply trust or clean status |
| Detector unavailable | Report assessment unavailable; do not substitute “no anomaly” |
| Dependency information missing | Do not claim independent corroboration; raw-signal fallback may be used if necessary |
| Conflicting detector signals | Emit `CONFLICTING`; do not automatically resolve the contradiction |
| Unsupported format/runtime/version | `OUT_OF_SCOPE` or `UNAVAILABLE` as appropriate |
| Operating condition outside tested scope | Do not extend `VALIDATED_SCOPE` |
| Context unauthenticated | Do not emit confirmed operational-drift semantics |
| Plausible benign explanation | Apply F7 before escalation; do not automatically mark benign |
| Required ground truth absent | Preserve `CANNOT_DETERMINE` for causal distinction |
| Authority missing | Do not execute authority-bound disposition; keep configuration requirement visible |
| Empty override rationale | Reject override |
| Audit-chain verification failure | Raise `CHAIN_VERIFICATION_FAILED` and trigger review |

---

## 21. Evaluation and Test Suite

### 21.1 Ground-truth requirements

Before C5 permits a quantitative project claim, the associated experiment must identify:

```text
calibration dataset version
evaluation dataset version
ground-truth / label source
sensor condition
terrain condition
season/weather condition
illumination condition
acquisition condition
detector version
loader/runtime
format
sample size
metric
evaluation date
reference version
declared-condition result
shifted-condition result
experiment identifier
```

### 21.2 Proposed evaluation criteria

Every value below remains a **PROPOSED CRITERION**, not an achieved metric.

| Criterion | Current status | Required before promotion |
|---|---|---|
| FPR < 5% under natural shift | `PROPOSED CRITERION` | Exact SIH operating distribution, labeled natural shifts, N, ground truth, experiment ID |
| ECE within 2× of uncalibrated baseline | `PROPOSED CRITERION` | Calibration dataset/version/conditions/metric/N/date |
| >50% analyst-time reduction | `PROPOSED CRITERION` | Controlled workflow study and defined baseline |
| >60% benign-cause recognition | `PROPOSED CRITERION` | Labeled benign-cause set and adjudication procedure |
| >30% reduction in unsafe override acceptance | `PROPOSED CRITERION` | Controlled override study and defined safety criterion |
| >50 override events before advisory | `PROPOSED / NOT VALIDATED THRESHOLD` | Mission-owner policy and operational validation |
| `r < 0.7` detector-independence gate | `REJECTED` | Replace with justified dependency-testing requirement |

### 21.3 Required MVP test suite

The source specifies T01–T08 but does not document their execution. They therefore remain **specified tests, not executed project results**.

| Test | Purpose | Expected semantic result | Current project status |
|---|---|---|---|
| **T01 Natural-shift control** | Inject known natural-shift samples | Detector may fire, but causal interpretation remains `CANNOT_DETERMINE` | Specified; execution evidence not present |
| **T02 Common-cause / shared-decoder fault** | Introduce a shared dependency fault | `CORROBORATED MULTI-CHANNEL` must **not** be emitted | Specified; execution evidence not present |
| **T03 Contradiction state** | Produce conflicting detector outputs | Emit `CONFLICTING`; do not silently resolve | Specified; execution evidence not present |
| **T04 Reference contamination** | Use a known contaminated reference | Propagate `CONTAMINATION_SUSPECTED` to dependent findings | Specified; execution evidence not present |
| **T05 Hash benign cause** | Apply known-benign format conversion | F7 benign-cause gate executes before escalation | Specified; execution evidence not present |
| **T06 Sparse alteration** | Inject 1–5% frame-level alteration | A `STABLE` result must still expose sparse-detection limitation | Specified; execution evidence not present |
| **T07 Override rejection** | Submit override with empty rationale | Override rejected | Specified; execution evidence not present |
| **T08 Audit chain verification** | Corrupt one audit-chain link | `CHAIN_VERIFICATION_FAILED` raised | Specified; execution evidence not present |

---

## 22. Five-Day Feasibility

The five-day estimate is an **INFERENCE / RECOMMENDATION**, not evidence that the work has already been completed. It is conditional on a fast C2/C3/C4 interface freeze and on avoiding end-to-end validation of a new statistical detector during the same period.

| Day | C5 capability | Deliverable | Dependency | Status |
|---|---|---|---|---|
| **Day 1** | Freeze adapter contract; define finding schema, detector registry, reference-health and scope states | Versioned evidence contract | C2/C3/C4 interface freeze; mission-owner input | Recommended plan; not execution evidence |
| **Day 2** | Evidence normalization; structured rule engine; common-cause and contradiction handling | Posture/semantic engine | Day-1 contract | Recommended plan; not execution evidence |
| **Day 3** | Structured finding UI/data model; six-state dispositions; limitation-first rendering; hash-chain audit | Analyst/governance layer | Frozen schema and authority placeholders | Recommended plan; not execution evidence |
| **Day 4** | T01–T06 reproducible failure/evidence tests | Evidence/failure test suite | Test artefacts and reference data | Recommended plan; tests not recorded as executed |
| **Day 5** | Offline packaging; chain verification; UI regression; workflow test; claim/non-claim review; coverage matrix | Bounded MVP package | Offline artefacts/hashes; coverage information | Recommended plan; completion not established |

The estimate becomes unreliable if the same five-day period must also be used to:

- discover/redesign upstream interfaces;
- create the SIH natural-shift ground truth from scratch;
- perform SIH statistical validation from scratch.

BBSD/KS/MMD and conformal-prediction validation are explicitly outside the five-day BUILD scope.

---

## 23. Project Implementation Evidence

### 23.1 Evidence-status separation

C5 distinguishes:

```text
RESEARCH SPECIFICATION
        ≠
RECOMMENDATION
        ≠
ARCHITECTURE
        ≠
IMPLEMENTATION
        ≠
EXECUTED TEST
        ≠
VALIDATED RESULT
```

The dossier states that no repository was independently inspected, no code was run, and no completed SIH experiment was recorded in the supplied C5 packet.

### 23.2 Packet-reported implementation evidence

| Evidence ID | Packet claim | Packet status | V2 public status |
|---|---|---|---|
| C5-I-001 | `failing-loudly` repository exists and contains a benchmark pipeline | `PARTIALLY_SUPPORTED` | Packet-reported research reference; not independently verified as project implementation |
| C5-I-002 | `torch-two-sample` provides two-sample-test functionality | `PARTIALLY_SUPPORTED` | Packet-reported; offline/native build closure not established |
| C5-I-003 | COCO/YOLO and ONNX/PyTorch/TorchScript coverage | `NOT_SUPPORTED` | No tested format/version/runtime matrix |
| C5-I-004 | Air-gapped installation of dependencies | `UNVERIFIABLE` | No pinned lockfile/wheelhouse/artifact-hash/network-isolation evidence |

### 23.3 Current V2 packet status

```text
BOUNDED BUILD AUTHORIZED
  semantic/governance core

PROTOTYPE
  BBSD/KS/MMD harness
  conformal module
  MANIPULATION-CONSISTENT gating
  F5 drift semantics

REJECT
  compromise probability
  overall risk score
  quantitative fusion
  analyst-facing temperature scaling
  learned deep ensembles

DEFER
  sequential drift adaptation
  pass-through raw-signal mode

DETECTOR EFFECTIVENESS
  NOT ESTABLISHED

GOVERNANCE CONFIGURATION
  PENDING

DEPLOYMENT READINESS
  NOT ESTABLISHED

C5 → C6 HANDOFF
  READY SUBJECT TO P0 GATE CLOSURE
```

### 23.4 P0 gates — before V2 freeze

The current packet requires closure of `C5-RT-COR-001` through `C5-RT-COR-007` plus `C5-RT-COR-013`. The current packet explicitly names:

| Gate | Requirement |
|---|---|
| C5-RT-COR-001 | Stop-rule non-equivalence wording |
| C5-RT-COR-002 | Detection-confidence derivation rule |
| C5-RT-COR-003 | Corroborated multi-channel dependency gate |
| C5-RT-COR-004 | Granular `VALIDATED_SCOPE` representation |
| C5-RT-COR-005 | Mission-owner `MANIPULATION-CONSISTENT` threshold |
| C5-RT-COR-006 | Reference-health procedure and provenance |
| C5-RT-COR-013 | C2/C3/C4 interface-contract freeze |
| Additional mandatory enforcement | Limitation rendering and prohibited-override behaviour |

The source's checkpoint text refers to `-001` through `-007`; a distinct descriptive label for `C5-RT-COR-007` is not independently established in the current C5 dossier and is therefore not invented here.

### 23.5 P1 gates — before deployment

- natural-shift FPR measurement;
- SIH calibration validation;
- target format/version/runtime coverage matrix;
- air-gapped lockfile, package hashes, and network-isolation evidence;
- authenticated context;
- trusted clock;
- authority mapping and identity binding;
- retention/legal-hold policy;
- audit-root/key protection;
- adaptive-adversary robustness assessment.

### 23.6 V2 dossier quality gates

The source's V2 quality gate records PASS or conditional PASS for scope, evidence discipline, verification disclosure, implementation bounding, limitations, red-team correction handling, feasibility framing, evaluation framing, uncertainty, cross-domain dependencies, boundary compliance, and inclusion of V2-C5-A through V2-C5-F.

A quality-gate PASS applies to the **dossier**, not deployment authorization.

`FINAL_V2_AUDIT` remains required.

---

## 24. Limitations and Negative Evidence

### 24.1 Statistical and epistemic limitations

- Distributional change cannot currently be attributed reliably to operational, accidental, or adversarial cause without appropriate labeled ground truth.
- SIH natural-shift FPR has not been measured.
- Calibration validity under SIH operational shift has not been established.
- Batch-level shift mechanisms may miss sparse/localized changes.
- Detector co-firing may arise from shared preprocessing, decoders, embeddings, reference data, or other common causes.
- Conformal coverage assumptions are not guaranteed under adversarial conditions or arbitrary distribution shift.
- Adaptive-adversary robustness is not established.
- `MANIPULATION-CONSISTENT` is not confirmed compromise.

### 24.2 Reference limitations

- No project-wide SIH trusted reference distribution has been established in the current C5 evidence.
- Reference provenance and health-verification procedure remain open.
- A contaminated or stale reference can undermine every dependent detector interpretation.
- A reference match is not equivalent to clean status.

### 24.3 Governance and operational limitations

- Authority hierarchy for `CONTAIN/HOLD` and `OVERRIDE` is configurable.
- Retention duration is not defined.
- Trusted-clock source is not defined.
- Analyst/reviewer authentication mechanism is not established.
- Audit-chain root/key protection protocol remains unspecified in project evidence.
- Override-pattern/alert-fatigue threshold is unvalidated.
- Severity/consequence mapping is mission-owner dependent.

### 24.4 Coverage limitations

- COCO/YOLO and ONNX/PyTorch/TorchScript coverage has not been established through a complete tested format/version/runtime matrix.
- Air-gapped deployability remains unverified until dependency artefacts are pinned, hashed, packaged, and tested without network access.
- `VALIDATED_SCOPE` cannot be extrapolated between detector versions, runtimes, formats, operating conditions, or reference versions.

### 24.5 Negative evidence

| Capability/claim | Status |
|---|---|
| SIH aerial-CV natural-shift FPR | `NOT MEASURED` |
| SIH calibration validity under shift | `NOT ESTABLISHED` |
| Full required format/version/runtime coverage | `NOT SUPPORTED / UNVERIFIED` |
| Adaptive/sparse adversarial robustness | `NOT ESTABLISHED` |
| Air-gapped dependency installation | `UNVERIFIED` |
| Operationally validated quantitative thresholds | `NOT ESTABLISHED` |
| Automatic attack attribution from shift | `NOT ESTABLISHED` |
| True compromise probability | `PROHIBITED` |

These limitations are findings, not omissions.

---

## 25. Contradictions, Corrections and Research Evolution

| Topic | Earlier treatment | Later correction | Current treatment |
|---|---|---|---|
| **CON-01 — Conformal prediction** | PROTOTYPE and potentially analyst-facing in an alternatives branch | Red-team/reverify treatment narrowed use | Experimental/upstream only; not an analyst-facing security finding |
| **CON-02 — BBSD/KS/MMD** | Stronger BUILD language in V1 alternatives | SIH natural-shift FPR found to be unmeasured | Harness remains `PROTOTYPE`; reference-health control itself may be built |
| **CON-03 — Detection HIGH/MEDIUM/LOW** | Free-floating `Detection: HIGH` | Criticized as unjustified scalar/category | Use `UNASSESSED` or `DERIVED_FROM_RULE:<rule_id>` |
| **CON-04 — Shift/attack equivalence** | Earlier wording equated shift with attack and raw score with compromise probability | Identified as boundary violation | Explicit non-equivalence is mandatory |
| **CON-05 — Hash-chain assurance** | “Tamper-evident within trusted chain” without explicit attack surfaces | Trust-boundary omissions identified | Root, key, storage, clock and archive limitations must be stated |
| **CON-06 — `r < 0.7` independence gate** | Proposed despite acknowledgement that it was not a universal theorem | No SIH dependency experiment resolves a universal threshold | Universal gate rejected; configurable dependency testing required |

The research lineage is intentionally retained:

```text
V1
 ↓
RED TEAM
 ↓
REVERIFY
 ↓
V2
```

The purpose of this lineage is to preserve correction history rather than erase earlier overclaims.

---

## 26. Open Questions

| ID | Question | Priority | Dependency | Current status |
|---|---|---|---|---|
| OQ-01 | What are the exact C2/C3/C4 schemas, native score semantics, versions, shared preprocessing and reference dependencies? | P0 | C2/C3/C4 | **OPEN** |
| OQ-02 | What procedure declares a reference trusted, who supplies it, and how is contamination/staleness handled? | P0 | Operations / mission owner | **OPEN** |
| OQ-03 | What evidence threshold/policy defines `MANIPULATION-CONSISTENT`? | P0 | Mission owner | **OPEN — blocks emission** |
| OQ-04 | What is the SIH natural-shift operating envelope and corresponding detector FPR/power? | P0 | Dataset/operations/experiments | **OPEN** |
| OQ-05 | What exact rule derives detection confidence? | P0 | C5/C6/mission owner | **OPEN** |
| OQ-06 | Who supplies and authenticates operational context metadata? | P0 | Operations | **OPEN** |
| OQ-07 | Who may contain, override, and release holds? | P1 | Mission owner | `CONFIGURATION_REQUIRED` |
| OQ-08 | What are retention duration, legal-hold trigger, deletion authority, and preservation obligations? | P1 | Governance | `CONFIGURATION_REQUIRED` |
| OQ-09 | What protects audit root/key; what trusted clock and analyst-authentication mechanism are used? | P1 | Operations/security | **OPEN** |
| OQ-10 | Which exact COCO/YOLO and ONNX/PyTorch/TorchScript format/version/loader/runtime combinations are tested? | P1 | C2/C3/C4/C6 | **OPEN** |
| OQ-11 | What pinned lockfile, prebuilt artefacts, hashes, and license records establish offline deployment? | P1 | C6/build engineering | **OPEN** |
| OQ-12 | What mission-owner severity/consequence mapping is permitted? | P1 | Mission owner | `CONFIGURATION_REQUIRED` |
| OQ-13 | What override-count/time-window threshold should trigger governance review? | P1 | Mission owner | `CONFIGURATION_REQUIRED` |
| OQ-14 | Has calibration been evaluated under SIH-specific shift conditions? | P1 | Evaluation team | **OPEN / NOT ESTABLISHED** |

Unanswered questions are not removed from the public edition because they define the boundary between research specification and deployable assurance.

---

## 27. Cross-Cell Dependencies

### C2 / C3 / C4 → C5

C5 requires:

- exact output schemas;
- detector-native score semantics;
- detector and implementation versions;
- preprocessing dependencies;
- decoder/embedding dependencies where applicable;
- reference dependencies;
- tested operating conditions;
- detector dependency graph;
- COCO/YOLO and ONNX/PyTorch/TorchScript coverage matrix.

These are a **P0 blocker** for evidence normalization, scope enforcement, and corroboration semantics.

### Mission Owner → C5

C5 requires:

- `MANIPULATION-CONSISTENT` evidence threshold/policy;
- authority hierarchy;
- containment/release authority;
- override governance;
- severity/consequence mapping;
- retention/legal-hold policy;
- override-pattern advisory threshold.

These are deployment/governance dependencies rather than values C5 may invent.

### Operations → C5

C5 requires:

- trusted reference provenance;
- reference-health procedure;
- authenticated operational context;
- trusted time;
- analyst identity binding;
- audit-root/key handling;
- offline dependency state.

### C5 → C6

C5 hands off:

```text
Structured Finding schema
Governance specification
Cannot-Claim Registry
Mandatory boundary constraints
Reference-health semantics
Disposition rules
Audit schema
UI semantic-lint requirements
```

The source records C5→C6 as handoff-ready subject to P0 closure.

**Handoff ≠ implementation completion.**

---

## 28. Reproducibility and Evidence Requirements

### 28.1 Reproducibility record

Every promoted experimental claim should identify, at minimum:

| Category | Required evidence |
|---|---|
| Dataset | Name, version, source, digest where applicable |
| Ground truth | Label/adjudication source |
| Environment | Sensor, terrain, season, illumination, acquisition conditions |
| Detector | ID and exact version |
| Runtime | Loader/runtime/library versions |
| Format | Exact dataset/model artefact format/version |
| Reference | ID, version, digest, provenance, health state |
| Test rule | Exact threshold/statistical rule |
| Sample size | N |
| Metric | Exact metric and calculation |
| Date | Evaluation date |
| Experiment | Unique experiment/test ID |
| Conditions | Declared baseline and shifted conditions |
| Result | Raw result plus limitations and scope |

### 28.2 Offline reproducibility

Before air-gapped deployability is claimed, the package should contain:

```text
pinned dependency versions
offline artefacts / wheels where required
cryptographic hashes
license records
installation procedure
network-isolation test
reproducible test commands
coverage matrix
```

Repository existence or successful installation on an internet-connected machine is not evidence of air-gapped deployability.

### 28.3 Reference provenance

A reference record should be sufficiently identifiable to support:

```text
reference_id
reference_version
reference_digest
source/provenance
declared operating conditions
health-assessment state
health-assessment evidence
assessment date
```

The final procedure remains dependent on OQ-02.

---

## 29. Claim / Source Index

### 29.1 Verified claims

| Claim ID | Claim | Status | Evidence type | Source(s) | Exact location |
|---|---|---|---|---|---|
| VC-01 | Shift detection establishes difference, not cause | Supported | Packet fact | S7OC5_V1; S8OC5; S9OC5 | S7OC5_V1 §4; S8OC5 §1 |
| VC-02 | Raw statistic is not compromise probability | Supported | Packet fact | S7OC5_V1; S9OC5 | S7OC5_V1 §11 C5-NC-002 |
| VC-03 | Anomaly/hash mismatch ≠ attack; unavailable/no alert ≠ clean | Supported | Packet fact | S7OC5_V1; S8OC5; S9OC5 | S7OC5_V1 §11 C5-NC-005/006/007 |
| VC-04 | Detector count ≠ independent evidence | Supported | Packet fact | S7OC5_V1; S8OC5; S9OC5 | S7OC5_V1 §11 C5-NC-004; S8OC5 §2.4/§2.6 |
| VC-05 | Calibration is distribution-specific | Supported | Packet + literature | S7OC5_V1; S8OC5; S9OC5 | S7OC5_V1 §14; S8OC5 §2.8 |
| VC-06 | Rabanser evidence is benchmark evidence, not SIH validation | Supported | Literature classification | S7OC5_V1 | §14/§16 |
| VC-07 | Conformal coverage ≠ generic attack FPR | Supported | Packet/literature interpretation | S7OC5_V1; S8OC5 | §14; S8OC5 §5 |
| VC-08 | Hash chain has root/key/storage/clock/archive trust boundaries | Supported | Packet fact | S7OC5_V1; S8OC5 | §10; C5-RT-MAJ-004 |
| VC-09 | Existing implementation evidence does not establish full format/offline capability | Supported | Packet implementation evidence | S7OC5_V1 | §22 |
| VC-10 | Bounded semantic/governance core is feasible/BUILD-oriented | Supported as bounded recommendation | Research architecture | S7OC5_V1; S8OC5; S9OC5 | §19/§25; S8OC5 §1 |

### 29.2 Other registries and evidence classes

| Claim / Registry ID | Type | Current treatment | Primary source classification | Exact location |
|---|---|---|---|---|
| PS-01–PS-05 | Partially supported | Retained with limitations | V1 + Red Team + Reverify | Group index in C5_V2; individual exact locations vary |
| CON-01–CON-06 | Contradiction / resolution | Five resolved, one unresolved | V1 + Red Team + Reverify | C5_V2 §10 |
| FM-01–FM-10 | Failure-mode registry | Referenced by C5 synthesis | V1 / Red Team / Reverify | Exact individual wording not reproduced in current C5_V2 packet |
| CC-01–CC-30 | Cannot-claim registry | Definitive V2 registry | All packet stages | V2-C5-E |
| NS-01–NS-14 | Not-to-be-assumed registry | Preserved as claim class | V1 / Red Team / Reverify | Exact individual wording not reproduced in current C5_V2 packet |
| OQ-01–OQ-14 | Open questions | Open/configuration-dependent | All packet stages | C5_V2 §15 |
| V2-C5-A | Drift taxonomy | Current V2 semantic specification | Fact / inference | V2-C5-A |
| V2-C5-B | Confidence specification | Current V2 recommendation | Recommendation | V2-C5-B |
| V2-C5-C | Disposition registry | Current V2 recommendation | Recommendation | V2-C5-C |
| V2-C5-D | Audit specification | Current V2 recommendation | Recommendation | V2-C5-D |
| V2-C5-E | Cannot-Claim Registry | Current V2 fact registry | Fact | V2-C5-E |
| V2-C5-F | Failure/fallback rules | Current V2 recommendation | Boundary / recommendation | C5_V2 §9.4 |
| C5-I-001–004 | Implementation evidence | Packet-reported only | Project implementation evidence | S7OC5_V1 §22 |

### 29.3 Source classification

| Source | Classification | Role |
|---|---|---|
| S7OC5_V1 | Primary V1 research source | Original method research, semantics, evidence registry, implementation evidence |
| S8OC5 | Red-team correction source | Boundary corrections, dependency critique, attack paths, calibration critique |
| S9OC5 | Reverify source | Reverified statuses and post-red-team synthesis; no new primary experiment |
| C5_V2 | V2 synthesis | Current bounded C5 specification |
| Rabanser et al. | External benchmark literature | Dataset-shift benchmark evidence |
| Guo et al. | External benchmark literature | Neural-network calibration evidence |
| Ovadia et al. | External benchmark literature | Uncertainty/calibration under shift |
| C5-I-* | Packet-reported implementation evidence | Must not be confused with independent execution |
| V2 recommendations | Recommendation | Build guidance, not implementation evidence |
| C5 inferences | Inference | Feasibility/architecture reasoning, not measured result |

---

## 30. References

### 30.1 Project and organiser source

**[R01] Smart India Hackathon 2026 — SIH26228.**  
*Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines.*  
Organization: Ministry of Defence; Department: Indian Army (DGIS).  
Relevant to C5: distribution-shift assessment, confidence/limitations, offline operation, common CV formats, model agnosticism, audit/reporting requirements.

Official SIH portal: <https://sih.gov.in/sih2026PS>

### 30.2 External academic literature

**[R02] Stephan Rabanser, Stephan Günnemann, Zachary C. Lipton.**  
*Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift.*  
Advances in Neural Information Processing Systems 32, NeurIPS 2019.  
Relevant to C5: benchmark dataset-shift detection and two-sample-testing evidence.  
**Classification:** External literature evidence; **not SIH operational validation**.

<https://proceedings.neurips.cc/paper/2019/hash/846c260d715e5b854ffad5f70a516c88-Abstract.html>

**[R03] Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger.**  
*On Calibration of Modern Neural Networks.*  
Proceedings of the 34th International Conference on Machine Learning, PMLR 70, 2017.  
Relevant to C5: temperature scaling and neural-network calibration.  
**Classification:** External benchmark literature; **not SIH calibration validation**.

<https://proceedings.mlr.press/v70/guo17a.html>

**[R04] Yaniv Ovadia, Emily Fertig, Jie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua Dillon, Balaji Lakshminarayanan, Jasper Snoek.**  
*Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift.*  
Advances in Neural Information Processing Systems 32, NeurIPS 2019.  
Relevant to C5: empirical uncertainty/calibration behaviour under dataset shift.  
**Classification:** External benchmark literature; **not SIH operational validation**.

<https://proceedings.neurips.cc/paper/2019/hash/8558cb408c1d76621371888657d2eb1d-Abstract.html>

### 30.3 Research software references

**[R05] `failing-loudly` research repository.**  
Code accompanying Rabanser et al.'s dataset-shift study.  
Relevant to C5 as a research reference only. Repository existence does not establish SIH format coverage or offline deployment.

<https://github.com/steverab/failing-loudly>

**[R06] `torch-two-sample`.**  
PyTorch library implementing several two-sample tests, including MMD.  
Relevant to C5 as a research/prototyping reference. C5 does not treat repository availability as proof of air-gapped installation.

<https://github.com/josipd/torch-two-sample>

### 30.4 Legal / standards reference appearing in the packet

**[R07] European Union. Regulation (EU) 2024/1689 — Artificial Intelligence Act, Article 9.**  
Relevant only because the C5 source discussed a possible Article 9 relationship. Current verification does not establish that Article 9 mandates the specific C5 audit fields defined in this dossier.

<https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689>

### 30.5 Internal research packet sources

**S7OC5_V1 — V1 Research Packet.**  
Primary V1 source for drift taxonomy, C5-NC-001–016, C5-I-001–004, audit design, evaluation concepts, contradictions, and the original semantic layer.

**S8OC5 — Red Team + Attack Packet.**  
Primary correction source for C5-RT-CRIT, C5-RT-MAJ and C5-RT-COR findings, attack paths, dependency critique, calibration critique, and conformal-prediction critique.

**S9OC5 — Reverify Verdict.**  
Post-red-team verification of claim statuses, quantitative-claim classification, calibration/drift findings, FPR status, security evidence, and implementation/coverage status.

No public URLs for S7OC5_V1, S8OC5, or S9OC5 are established in the current C5 packet; none are invented here.

No specific conformal-prediction publication is named in the current C5 source registry, so this public edition does not fabricate a conformal reference.

---

## 31. C5 Research Conclusion

C5 does not primarily detect; it governs how technical detector evidence is interpreted, bounded, disclosed, and acted upon.

Its central research conclusion is that a distributional difference is an **observation**, not an explanation or attribution. Natural operational changes and manipulation can produce overlapping statistical signatures, and the current SIH packet does not establish a project-level procedure that universally separates them.

Confidence therefore cannot responsibly be reduced to an unexplained scalar. The C5 design uses structured findings that preserve detector-native evidence, applicability, reference health, calibration status, limitations, non-claims, and the rule by which an interpretation was derived.

Reference health is part of the finding, not an invisible assumption. Detector agreement is not automatically independent evidence. A hash mismatch is not automatically malicious. A valid audit chain is not proof that the underlying detector or decision was correct. An unavailable assessment is not a clean result.

Analyst actions are governed through explicit dispositions, mandatory rationale, authority controls, immutable original findings, and an auditable decision trail. `MANIPULATION-CONSISTENT` remains a bounded semantic state and is not safely emit-able until the mission-owner threshold/policy is defined.

The five-day BUILD recommendation applies to the semantic/governance core, not to new SIH-specific statistical detector validation. Natural-shift FPR, calibration under SIH shift, target-format coverage, offline dependency closure, reference provenance, context authentication, authority hierarchy, retention, audit-root protection, and several operational thresholds remain unresolved or configuration-dependent.

Accordingly, C5's assurance strength does not come from turning uncertainty into a number or an attack verdict. It comes from preserving the distinction between what the evidence **shows**, what it **may mean**, where it **applies**, what it **cannot establish**, and what governed action an analyst may take.

`FINAL_V2_AUDIT` remains required before final architecture or deployment readiness can be claimed.
