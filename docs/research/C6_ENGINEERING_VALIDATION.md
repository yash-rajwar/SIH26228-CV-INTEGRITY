# C6 — Engineering & Validation Research

**SIH 2026 PS 26228 — Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines**

---

## Document Metadata

| Field | Value |
|---|---|
| Domain | C6 — Engineering / Validation |
| Artifact | C6-V2-001 |
| Source status | `C6_V2_DRAFT` |
| Source date | 2026-09-24 |
| Public-document purpose | Engineering reality check, validation plan, evidence boundary, reproducibility record |
| Packet lineage | V1 → RED_TEAM → REVERIFY → V2 Synthesis → C6 V2 |
| Current packet | `C6-CURRENT-PACKET-V2-DOSSIER-2026-09-24-G` |
| Checkpoint 1 | FAIL — carried from prior stages |
| Checkpoint 2 | **NOT PASSED** |
| Build gate | **NOT PASSED** |
| Build authorization | **NONE** |
| Assessment | **PARTIAL / NOT CLEAN** |
| Level C evidence | **NOTHING — no target-host execution** |
| Level D evidence | **NOTHING — no experimental reproduction** |
| Final V2 audit | Pending in the source packet |

### Current Public Status

| Area | Current evidence status |
|---|---|
| Target host | **OPEN — CRITICAL** |
| Build gate | **NOT PASSED** |
| Build authorization | **NONE** |
| Checkpoint 2 | **NOT PASSED** |
| Target execution | **NOT AVAILABLE** |
| Level C evidence | **NOTHING** |
| Level D evidence | **NOTHING** |
| Reproducibility | **NOT YET VALIDATED ON TARGET** |
| Offline closure | **UNVERIFIED ON TARGET** |
| Format coverage | **CONDITIONAL ON EXACT TESTED TUPLE** |
| CPU performance | **UNBENCHMARKED ON TARGET** |
| Hostile-artifact containment | **NOT VALIDATED ON TARGET** |
| Behavioral-detector validation | **UNVERIFIED** |
| Cross-cell contracts | **OPEN** |
| Assessment status | **PARTIAL / NOT CLEAN** |

### Primary Engineering Question

> **Can the proposed integrity-assurance system actually operate within the project's offline, CPU-only, model-agnostic, no-retraining and five-day constraints?**

Every C6 engineering claim is evaluated through that question.

C6 is intentionally conservative. A paper, GitHub repository, documented API, successful package installation, or plausible implementation approach is not equivalent to demonstrated operation on the project target.

---

# 1. C6 Mission and Engineering Scope

C6 is the **Engineering / Validation reality-check cell**.

Its responsibility is to determine whether proposed components can actually:

- accept the intended artifacts;
- safely parse or load untrusted artifacts;
- install and remain operational without network access;
- execute correctly on the permitted CPU-only platform;
- interoperate across the exact supported format/version/runtime combinations;
- invoke the required detector interfaces;
- remain within CPU, RAM and runtime limits;
- contain hostile or malformed inputs;
- produce deterministic, typed outcomes;
- and generate reproducible evidence.

C6 does **not** select:

- C2 data-integrity detectors;
- C3 model-security methods;
- C4 cryptographic architecture;
- C5 assurance semantics;
- or the overall system architecture.

It challenges whether those decisions survive implementation reality.

### C6 validation boundary

```text
ARTIFACT ACCEPTANCE
        ↓
PARSER / LOAD SAFETY
        ↓
ENVIRONMENT CLOSURE
        ↓
RUNTIME CORRECTNESS
        ↓
CROSS-FORMAT PARITY
        ↓
DETECTOR INVOCATION
        ↓
RESOURCE BUDGET
        ↓
EVIDENCE RECORDING
```

A later gate must not be assumed merely because an earlier gate passed.

For example:

```text
PACKAGE INSTALLED
      ≠
RUNTIME EXECUTED
      ≠
OFFLINE CLOSURE PROVEN
      ≠
HOSTILE INPUT CONTAINED
      ≠
OUTPUT CORRECT
      ≠
DETECTOR VALIDATED
```

C6 outputs are **engineering evidence records and gate verdicts**.

They are **not security certifications**.

The meaningful unit of a C6 claim is the exact tested combination of:

```text
ARTIFACT
  +
FORMAT
  +
VERSION
  +
RUNTIME
  +
CONFIGURATION
  +
TARGET PLATFORM
```

Anything outside the demonstrated tuple remains `UNSUPPORTED`, `ASSESSMENT_UNAVAILABLE`, or otherwise explicitly unvalidated.

---

# 2. PS Engineering Requirements

The source packet establishes the following engineering requirements and constraints.

## 2.1 Offline / Air-Gapped Operation

The validation system must be capable of operating without network egress during inference, validation and provenance/result writing.

This is a deployment constraint.

**Offline does not mean secure by itself.**

An air-gapped environment can still contain hostile artifacts, compromised packages, vulnerable parsers, malicious removable media, unsafe local privileges or compromised provenance data.

Therefore:

```text
OFFLINE
   ≠
SECURE
```

Offline behavior itself requires evidence.

A package that *can* be downloaded for offline use is not automatically proven to execute without attempted network access.

## 2.2 Model-Agnostic Integrity Assurance

The system must not assume that every submitted artifact belongs to one framework or format family.

"Model-agnostic" therefore means that the engineering layer must:

- identify the artifact type and relevant version/configuration;
- route only supported combinations into supported validation paths;
- explicitly reject or mark combinations outside those paths;
- and avoid treating unknown artifacts as benign.

Model-agnostic does **not** mean that every conceivable model format is supported.

## 2.3 Target Scope

The claimed project target scope includes:

- COCO / YOLO data or configuration paths;
- PyTorch artifacts;
- TorchScript;
- ONNX;
- and associated runtime/export paths.

C6 reports support only for combinations that are actually tested.

The current packet contains **no target-host execution**, so no format family currently has Level C coverage.

TorchScript arbitrary ingestion is specifically **DEFERRED**.

## 2.4 No Baseline Retraining

C6 operates on as-delivered artifacts.

Training or fine-tuning a replacement baseline is outside the normal validation path.

## 2.5 Reproducible Public or Team-Generated Evidence

Hostile fixtures must be reproducible from public or team-controlled assets.

The engineering plan must not rely on an unavailable proprietary poisoned-model corpus.

## 2.6 Anomaly Is Not Malicious Intent

A hash mismatch, output divergence, unusual weight statistic, parser rejection or detector anomaly does not independently prove malicious activity.

Similarly, absence of a detected anomaly does not establish benign intent.

The engineering layer therefore must not collapse technical observations into unsupported intent labels.

## 2.7 Unavailable Assessment Is Not Clean

A validation path that cannot complete does not produce a positive result.

The following are not equivalent to a successful assessment:

- timeout;
- blocked load;
- missing reference;
- resource exhaustion;
- unsupported artifact variant;
- parser failure;
- unavailable isolation;
- missing dependency;
- or missing cross-cell contract.

## 2.8 Result-State Invariant

The working C6 state vocabulary is:

| State | Engineering meaning |
|---|---|
| `MATCH` | The defined comparison or artifact-identity check matched within its explicitly defined scope. It does not mean benign, correct or trusted. |
| `DIFFERENT` | The compared artifact or output differs under the defined check. It does not establish malicious intent. |
| `UNSUPPORTED` | The artifact, configuration, required containment mechanism or validation route lies outside the supported/tested scope. |
| `ASSESSMENT_UNAVAILABLE` | A meaningful verdict could not be obtained, for example because of timeout, resource termination, missing reference or unavailable required capability. |
| `ERROR` | The validation path encountered an execution, parser, loader or internal failure that prevents a normal result. |

`CLEAN` and `MALICIOUS` are **not C6 primary engineering states**.

The exact authoritative tokens remain an open C5 contract under `DEP-C6-C5-001`.

The invariant is architectural, not merely documentary:

```text
TIMEOUT
BLOCKED LOAD
MISSING REFERENCE
UNSUPPORTED FORMAT
PARSER FAILURE
RESOURCE LIMIT
        ↓
MUST NOT TRANSITION TO
        ↓
CLEAN
```

If another layer later exposes a user-facing positive assurance state, that state must not be derivable from an incomplete or unavailable C6 path.

---

# 3. Engineering Gate Model

C6 treats validation as a sequence of engineering gates rather than a collection of available libraries.

## 3.1 Core Gate Sequence

| Gate | What must be demonstrated | Evidence required | Current status |
|---|---|---|---|
| Artifact acceptance | Artifact is identified, scoped and routed without assuming unsupported format semantics | Frozen artifact definition and acceptance tests | **NOT TARGET-VALIDATED** |
| Parser / load safety | Untrusted input cannot silently force unrestricted parsing/loading in the trusted process | Patched versions, hostile fixtures, isolated execution evidence | **NOT TARGET-VALIDATED** |
| Environment closure | All required packages, native libraries and runtime components exist offline | Clean-room installation plus no-network evidence | **UNVERIFIED** |
| Runtime correctness | Runtime executes the intended artifact and output contract | Target-host execution logs and expected outputs | **UNVERIFIED** |
| Cross-format parity | Source/export paths have matched preprocessing, postprocessing and output semantics | Differential fixtures and parity criteria | **UNVERIFIED / CONDITIONAL** |
| Detector invocation | Required C3 access contract is available and correctly exposed | Interface-level execution evidence | **BLOCKED BY C3 CONTRACT** |
| Resource budget | CPU, RAM and runtime remain inside target bounds | Target benchmarks including peak RSS | **NOT MEASURED** |
| Evidence recording | Results, versions, manifests, hashes and logs are authoritative and reproducible | Deterministic second run and evidence bundle | **NOT PRODUCED** |

## 3.2 Build-Evidence Ladder

```text
SOURCE / PAPER
      ↓
IMPLEMENTATION INSPECTION
      ↓
INSTALL
      ↓
EXECUTE
      ↓
TARGET-HOST TEST
      ↓
EXPERIMENTAL REPRODUCTION
      ↓
BUILD EVIDENCE
```

Code existing upstream does not mean the project has executed it.

Installation does not mean runtime correctness.

One execution does not mean reproducibility.

A smoke test does not mean detector efficacy.

A source-reported result cannot be silently promoted into project evidence.

---

# 4. Evidence Classification

Evidence classification is central to C6 because the current research packet contains substantial external evidence but no target-host execution.

## 4.1 Evidence Levels

| Level | Meaning | What it can support | What it cannot establish |
|---|---|---|---|
| **Level A — SOURCE_REPORTED** | Literature, papers, upstream documentation, upstream repository or public source reports | Research hypotheses, known behavior, candidate selection, expected constraints | Project installation, project execution, target performance or reproducibility |
| **Level B — IMPLEMENTATION_INSPECTED** | API/source/repository/advisory behavior inspected closely enough to establish implementation facts | Prototype design, version-floor decisions, known code-path constraints | Target-host operation, containment or project performance |
| **Level C — Run by C6 on target** | Candidate actually installed/executed on the specified target | Target-specific engineering behavior | Experimental reproduction unless the experiment protocol itself is repeated and controlled |
| **Level D — Experimentally reproduced** | Defined experiment reproduced under controlled conditions with recorded evidence | Project-specific empirical validation within the tested tuple | Universal security or format-family claims |

### Current evidence boundary

**Level C: NOTHING.**

No C6 target-host execution has occurred at any packet stage.

**Level D: NOTHING.**

No C6 experiment has yet been reproduced on the project target.

The central gap is therefore:

```text
LEVEL A / LEVEL B
      ↓
   CURRENT GAP
      ↓
LEVEL C
      ↓
LEVEL D
```

All current `PROTOTYPE` candidates remain on the Level A/B side of that gap.

## 4.2 Claim Status Taxonomy

C6 deliberately preserves distinct claim statuses.

| Status | Meaning |
|---|---|
| `SUPPORTED` | Available source evidence directly supports the bounded claim. |
| `PARTIALLY_SUPPORTED` | Some portion is supported, but scope, target applicability, version range or other qualifiers remain. |
| `CONTRADICTED` | Stronger evidence contradicts the claim as stated. |
| `UNVERIFIABLE` | The required evidence is unavailable in the current packet or target environment. |
| `SOURCE_REPORTED` | Reported by an external source but not reproduced by C6. |
| `IMPLEMENTATION_INSPECTED` | Relevant implementation, API, repository or advisory details were inspected. |
| `REVERIFY_CONFIRMED` | A re-verification pass confirmed a specific primary-source fact. |
| `INFERENCE` | Engineering conclusion derived from available facts but not itself directly demonstrated. |
| `RECOMMENDATION` | Proposed engineering treatment, not a completed implementation. |
| `NOT_SUPPORTED` | The evidence does not justify the claim. |

These states must not be flattened into "verified."

## 4.3 External Research vs Project Evidence

C6 uses the following semantic separation throughout this document:

```text
LITERATURE EVIDENCE
≠
IMPLEMENTATION INSPECTION
≠
PROJECT TARGET EXECUTION
≠
EXPERIMENTAL REPRODUCTION
```

External research can establish:

- known vulnerabilities;
- published limitations;
- documented APIs;
- candidate implementation paths;
- and experimental hypotheses.

It does not prove that the SIH implementation works on its target.

---

# 5. Checkpoint and Build-Gate Status

## 5.1 Current Gate State

**BUILD GATE: NOT PASSED**

**BUILD AUTHORIZATION: NONE**

**CHECKPOINT 2: NOT PASSED**

**ASSESSMENT: PARTIAL / NOT CLEAN**

No candidate currently reaches `BUILD`.

## 5.2 Checkpoint 2 Requirements

Checkpoint 2 requires all of the following before it can pass:

| Prerequisite | Current state |
|---|---|
| Target host specification confirmed | **NOT SATISFIED** |
| Exact version, commit and package/hash freeze completed | **NOT SATISFIED** |
| At least one `PROTOTYPE` candidate demonstrated with Level C target-host evidence | **NOT SATISFIED** |
| Blocking cross-cell dependencies resolved, including `DEP-C6-ALL-001` and at minimum `DEP-C6-C1-001` | **NOT SATISFIED** |

The research lineage contains zero Level C evidence.

Accordingly, Checkpoint 2 cannot be promoted based on literature quality, source inspection or implementation plausibility.

## 5.3 Security Preconditions

The source packet records the following floors as **mandatory preconditions before BUILD consideration**:

| Component | Minimum / control | Basis | Meaning |
|---|---|---|---|
| PyTorch | **≥ 2.10.0** | CVE-2025-32434 and CVE-2026-24747 lineage | Earlier affected ranges invalidate `weights_only=True` as a sufficient loader control. |
| ONNX | **≥ 1.21.0** | CVE-2026-27489 and CVE-2026-34445 | Earlier external-data handling includes confirmed vulnerability scope. |
| Docker Desktop, if used | **≥ 4.44.3** | CVE-2025-9074 | Required patch floor for the documented Docker Desktop vulnerability. |
| ONNX Runtime | Set `ORT_DISABLE_TELEMETRY=1` **before ORT import/initialization** where applicable | ORT v1.29.0 documentation | Required air-gap precaution; staged binary behavior still requires inspection/testing. |

These are floors, not certifications.

```text
PATCHED VERSION
      +
ISOLATION
      +
VALIDATION
      +
TARGET TESTING
      ≠
COMPLETE SECURITY GUARANTEE
```

---

# 6. Threat / Engineering Problem Context

C6 organizes its engineering threat context into five clusters.

## 6.1 Hostile Artifact Ingestion

Model artifacts are not necessarily passive data.

Relevant attack surfaces include:

- PyTorch serialized checkpoints;
- pickle-derived object reconstruction behavior;
- allowlisted globals/classes/functions;
- TorchScript executable semantics;
- ONNX external-data path resolution;
- external file traversal;
- symbolic-link and hard-link handling where applicable;
- configuration/schema parsing;
- and runtime resource consumption.

The source packet contains confirmed vulnerability evidence showing that loader configuration alone cannot be treated as a complete security boundary.

## 6.2 Dependency and Deployment Closure

An offline wheelhouse can appear complete while runtime dependencies remain absent.

Examples identified in the packet include:

- VC++ runtime requirements;
- `libgomp`;
- oneDNN-related runtime requirements;
- ORT native binaries;
- architecture-specific wheels;
- Python ABI compatibility;
- target OS differences;
- and hidden native dependencies.

A successful `pip install` therefore does not prove that the resulting environment can execute the target workload.

## 6.3 Interoperability False Equivalence

Cross-format validation can falsely signal equivalence if engineering semantics differ.

Relevant causes include:

- treating ONNX structural validity as behavioral equivalence;
- different preprocessing pipelines;
- different letterboxing behavior;
- different postprocessing/NMS behavior;
- dynamic-shape differences;
- output-contract mismatches;
- batch handling;
- and export/runtime defects.

The documented YOLO11/12 `nms=True`, `dynamic=True`, batch>1 problem demonstrates why apparently valid ONNX execution can still produce incorrect validation evidence.

## 6.4 Detector Reliability and Transfer

Neural Cleanse, STRIP, ABS and TABOR originate primarily from research settings that do not automatically map to a YOLO object-detection pipeline.

Open issues include:

- classifier-oriented statistics;
- undefined YOLO adaptation;
- architecture access requirements;
- false-positive behavior;
- scale dependence;
- calibration requirements;
- CPU cost;
- and absence of a qualified clean/poisoned YOLO corpus.

## 6.5 The Assurance System's Own Attack Surface

The assurance layer contains privileged components of its own:

- parser;
- loader;
- isolated worker;
- supervisor;
- manifest authority;
- result writer;
- provenance store;
- dependency bundle.

If an untrusted model can influence authoritative metadata used to validate itself, the trust boundary becomes circular.

---

# 7. Safe Artifact Ingestion

Artifact ingestion is a security boundary.

A public validation system must distinguish **artifact acceptance** from **artifact trust**.

## 7.1 Safe-Loading Pipeline

The intended engineering sequence is:

```text
UNTRUSTED ARTIFACT
        ↓
PRE-LOAD / PRE-PARSE VALIDATION
        ↓
QUARANTINE
        ↓
ISOLATED LOADER / PARSER
        ↓
STRUCTURAL VALIDATION
        ↓
ISOLATED EXECUTION
        ↓
TYPED OUTPUT EXTRACTION
        ↓
VALIDATION RESULT
```

The trusted supervisor should not directly import, deserialize or execute an artifact merely to determine what it contains.

## 7.2 Pre-Load / Pre-Parse Controls

Where applicable, pre-load controls should establish:

- expected artifact type;
- file-set membership;
- manifest relationship;
- version prerequisites;
- file-size/resource limits;
- external-data references;
- path normalization;
- allowed root;
- and unsupported conditions.

These checks reduce risk but do not replace isolation.

## 7.3 Quarantine

Untrusted artifacts should enter a location and process context where they cannot:

- modify the authoritative manifest;
- write provenance;
- alter trusted code;
- gain unrestricted network access;
- or escape into unrelated host filesystem locations.

## 7.4 Isolation as Part of the Boundary

A "safer" loader option is not automatically containment.

The source's PyTorch CVE evidence explicitly contradicts treating `weights_only=True` as a complete boundary.

Similarly, ONNX external-data path validation must happen inside a containment model capable of surviving parser/runtime defects.

---

# 8. PyTorch and TorchScript Validation

## 8.1 `weights_only=True`

`torch.load(..., weights_only=True)` restricts unsupported globals, classes and functions and may require explicit allowlisting.

That is useful engineering behavior.

It is not a complete security boundary.

**C6-CLM-008 is CONTRADICTED:** the assumption that `weights_only=True` alone creates a sufficient hostile-checkpoint boundary is invalidated by:

- CVE-2025-32434 / GHSA-53q9-r3pm-6pq6;
- CVE-2026-24747 / GHSA-63cw-57p8-fm3p.

The packet therefore establishes **PyTorch ≥2.10.0 as a version-floor precondition**, not as proof of safe execution.

## 8.2 Allowlisting and Ultralytics Compatibility

For some Ultralytics `.pt` artifacts, `weights_only=True` may reject `DetectionModel` or other globals unless:

- explicitly allowlisted; or
- architecture reconstruction is performed.

This creates operational pressure to retry with unrestricted loading.

That retry must not happen implicitly.

```text
SAFE LOAD FAILS
      ↓
DO NOT
      ↓
AUTOMATICALLY RETRY WITH weights_only=False
```

`RC-013` rejects this fallback pattern.

## 8.3 Hostile Checkpoints

The proposed validation fixture includes a checkpoint containing a deliberately unsafe serialized object.

The expected validation objective is not "loader returned an error."

The important pass condition is:

- payload does not execute;
- supervisor remains intact;
- unrestricted fallback does not occur;
- and the outcome is recorded as `ERROR`, `UNSUPPORTED` or another authoritative non-positive state.

No C6 target-host execution of this fixture has occurred.

## 8.4 TorchScript

PyTorch's security policy treats TorchScript from unknown sources as executable-code risk.

Arbitrary TorchScript ingestion is therefore **RC-003 — DEFER**.

The blocker is concrete:

> the isolated worker and hostile TorchScript containment have not been demonstrated on the target host.

TorchScript must not be added to public support claims solely because a runtime API exists.

---

# 9. ONNX Structural and Differential Validation

## 9.1 Structural Validity Is Not Semantic Equivalence

The most important ONNX distinction is:

```text
ONNX STRUCTURAL VALIDITY
        ≠
SOURCE / ONNX SEMANTIC EQUIVALENCE
```

A structurally valid graph may still differ because of:

- preprocessing;
- letterboxing;
- tensor shapes;
- output ordering;
- output contract;
- postprocessing;
- NMS;
- export behavior;
- quantization;
- or runtime implementation.

Accordingly:

- **RC-004** concerns ONNX structural checking.
- **RC-005** concerns PyTorch → ONNX differential validation.

The two must remain separate.

## 9.2 RC-004 — Structural Checking

RC-004 is a `PROTOTYPE` candidate.

It can answer bounded questions such as whether an ONNX graph satisfies expected structural/schema constraints.

It cannot by itself produce a semantic `MATCH`.

The graph can pass structural checking while still producing meaningfully different inference behavior.

## 9.3 RC-005 — PyTorch → ONNX Differential Validation

RC-005 remains:

**DEFER — unless C1 declares ONNX interoperability mandatory for the first delivery.**

A credible differential test requires:

- one frozen source artifact;
- one frozen export;
- exact opset;
- exact batch configuration;
- exact preprocessing;
- exact postprocessing;
- defined numeric tolerances;
- per-item output-count assertions;
- and a frozen runtime.

No such project-specific parity run currently exists.

## 9.4 External Data

An ONNX model can store tensor content outside the main `.onnx` file.

Therefore:

```text
HASH(main.onnx)
       ≠
HASH(complete ONNX artifact unit)
```

when external tensor data exists.

C6 records external-data handling as a security and integrity boundary.

Relevant risks include:

- traversal;
- absolute-path references;
- symbolic links;
- hard-link behavior where documented;
- and external-data injection.

The confirmed advisory correction retained by the dossier is:

- CVE-2026-27489 / GHSA-3r9x-f23j-gc73;
- CVE-2026-34445 / GHSA-538c-55jv-c5g9.

The earlier `CVE-2026-34447` attribution is **NOT SUPPORTED** by the inspected primary advisories and must not be restored into the public claim set.

The source retains **ONNX ≥1.21.0** as the precondition floor.

That floor does not remove the need for containment and path validation.

---

# 10. YOLO / Ultralytics Reproducibility

"YOLO" is not a single reproducible artifact.

A credible C6 support claim must identify the actual test tuple.

## 10.1 Required YOLO Test Tuple

A frozen tuple should include, where applicable:

| Parameter | Required record |
|---|---|
| Ultralytics | Exact release and/or exact commit |
| Model | Exact model variant |
| Source artifact | Hash |
| Export path | Exact command/API path |
| Opset | Resolved numeric value |
| Batch | Exact export and validation value |
| Dynamic shapes | Exact setting |
| NMS | Exact setting |
| Image size | Exact setting |
| Preprocessing | Exact implementation/configuration |
| Postprocessing | Exact implementation/configuration |
| Runtime | Exact ORT/runtime version |
| Target | OS, CPU architecture, Python ABI |
| Exported artifact | Hash |

`ultralytics/ultralytics:main` is not a reproducibility pin.

## 10.2 Opset Resolution

The dossier records that `opset=None` uses an exporter-selected supported opset.

That behavior is not enough for reproducibility.

The resolved numeric opset must be recorded in the evidence bundle.

## 10.3 Batch + NMS + Dynamic Export Risk

C6-SRC-022 documents a configuration-specific problem affecting YOLO11/12 ONNX export:

```text
nms=True
+
dynamic=True
+
runtime batch > 1
```

In the documented case, valid detections were produced only for batch index 0.

The reported issue included a severe validation metric collapse under the affected setup.

This is not a universal claim about every YOLO release or every ONNX export.

It is a warning tied to the documented version/configuration path.

The engineering implication is mandatory:

- assert output count for every batch item;
- freeze the version containing any claimed fix;
- do not infer correctness from issue closure;
- and use batch=1 or an explicitly validated export maximum until the frozen tuple proves otherwise.

---

# 11. Offline Environment Closure

Offline deployment is broader than package installation.

## 11.1 Closure Model

```text
WHEELS AVAILABLE
      ↓
HASHES VERIFIED
      ↓
--no-index INSTALL
      ↓
NATIVE DEPENDENCIES PRESENT
      ↓
IMPORTS SUCCEED
      ↓
RUNTIME EXECUTES
      ↓
NO NETWORK ACCESS
      ↓
SECOND CLEAN-ROOM RUN
      ↓
OFFLINE CLOSURE EVIDENCE
```

Therefore:

```text
PACKAGE INSTALLATION SUCCESS
        ≠
OFFLINE DEPLOYMENT PROOF
```

## 11.2 Wheelhouse

### What it solves

A wheelhouse can stage Python packages for installation using mechanisms such as:

```text
pip install --no-index --find-links <wheelhouse>
```

It is the lowest-overhead packaging approach retained as a `PROTOTYPE` candidate.

### What it does not solve

A Python wheelhouse does not automatically capture every host dependency.

The dossier specifically identifies risks around:

- VC++ runtimes;
- `libgomp`;
- oneDNN;
- ORT native libraries;
- Python ABI;
- platform tags;
- architecture;
- and other system dependencies.

### Required offline test

The BUILD gate requires:

- exact target;
- empty package cache;
- `--no-index`;
- frozen dependency set;
- package hashes;
- native ABI inspection;
- monitored network activity;
- and a second clean-room run.

## 11.3 Conda-Pack

`RC-015` is **DEFER**.

Official conda-pack documentation establishes that:

- the source and target OS must match;
- environments are not generally relocatable in the unrestricted sense;
- after `conda-unpack`, moving the environment again is unsupported.

Its status is not "insecure."

Its C6 problem is that target OS/architecture is unknown and the additional packaging path does not currently remove a critical five-day blocker.

## 11.4 Docker

`RC-016` is **DEFER**.

Docker provides useful packaging properties:

- image-level dependency bundling;
- deterministic image transport;
- offline image tarball transfer;
- environment consistency.

Those advantages do not establish isolation adequacy.

The dossier retains CVE-2025-9074 as a confirmed example showing that container isolation assumptions can fail.

If Docker is reconsidered, the source requires:

- Docker Desktop ≥4.44.3 for the cited vulnerability;
- restricted Engine API exposure;
- least privilege;
- target daemon-policy confirmation;
- patched runtime;
- and a trust model in which the authoritative supervisor remains outside the hostile-model container boundary.

C6 does **not** state "Docker is insecure."

It states that Docker availability alone is insufficient evidence for the required isolation claim.

---

# 12. CPU / ORT Runtime Validation

The deployment constraint is CPU-only.

No C6 candidate has yet been benchmarked on the project target CPU.

## 12.1 ORT CPU Path

`RC-008 — CPU-only ONNX Runtime execution` remains `PROTOTYPE`.

The upstream CPU path is documented.

Project-level evidence is absent.

## 12.2 Telemetry

ORT v1.29.0 documentation records POSIX telemetry support in telemetry-enabled builds and the `ORT_DISABLE_TELEMETRY=1` control.

For the project:

```text
ORT_DISABLE_TELEMETRY=1
```

must be set **before ORT import/initialization** where the control is applicable.

That does not prove that the staged binary is telemetry-free.

Binary/build inspection and a no-network target test remain required.

## 12.3 Architecture-Specific Behavior

The dossier preserves a re-verification report concerning ORT Issue #29613 and Linux/aarch64 behavior involving CPU FlashAttention being silently disabled under some conditions.

The affected-release scope remains an informational open question.

Therefore x86-64 and aarch64 must not be treated as interchangeable benchmark targets.

## 12.4 Required Resource Evidence

Any CPU runtime claim should record at minimum:

- cold-start latency;
- warm-run latency;
- peak RSS;
- CPU architecture;
- CPU model/core count;
- input shape;
- batch;
- runtime version;
- provider;
- failure/timeout limits;
- and fallback-provider behavior.

No target performance claim is currently authorized.

---

# 13. Isolation and Sandboxed Worker

`RC-011` exists because the trusted supervisor should not directly process hostile model artifacts.

## 13.1 Supervisor / Worker Separation

```text
                 TRUSTED SUPERVISOR
                /       |        \
               /        |         \
      policy/gates   evidence    provenance
             |
             v
       ISOLATED WORKER
       /      |       \
    parse    load     execute
      \       |       /
       typed result only
             |
             v
      TRUSTED SUPERVISOR
```

The worker should contain:

- parsing;
- model loading;
- external-data resolution;
- and potentially unsafe runtime operations.

The supervisor should retain authority over:

- timeouts;
- resource limits;
- final state emission;
- evidence records;
- manifests;
- and provenance.

## 13.2 Required Containment Tests

Before BUILD consideration, the isolated worker must be tested against at least the hostile behaviors defined by the source:

| Hostile worker attempt | Required outcome |
|---|---|
| `socket.connect()` | Network action contained; supervisor survives |
| `open('/etc/shadow')` or equivalent protected-file probe | Access prevented by containment; supervisor survives |
| Infinite loop | Worker terminated; supervisor survives |
| `bytearray(10**10)` or equivalent memory exhaustion | Worker constrained/terminated; supervisor survives |

The result must be `ASSESSMENT_UNAVAILABLE`, `ERROR`, `UNSUPPORTED`, or another explicitly non-positive state.

It must never become `CLEAN`.

## 13.3 Target Dependency

The source currently assumes Landlock/seccomp as possible Linux controls.

Whether Landlock is available depends on:

- kernel version;
- Landlock ABI;
- deployment policy;
- and permitted host controls.

No target isolation mechanism has been validated.

If the required containment cannot be implemented on the target, paths requiring hostile parsing/loading must remain `UNSUPPORTED`.

---

# 14. Manifest, Hash and Artifact-Unit Boundaries

## 14.1 Hashing Scope

C6 retains SHA-256 serialized-byte identity as a deterministic integrity primitive.

Its semantics are deliberately narrow.

```text
SHA-256 MATCH
      ↓
BYTE IDENTITY
WITH RESPECT TO THE DEFINED ARTIFACT UNIT
```

It does **not** establish:

- semantic equivalence;
- model correctness;
- benign behavior;
- contributor trust;
- or malicious intent.

## 14.2 Artifact Unit

The exact artifact unit is owned by the C4 contract under `DEP-C6-C4-001`.

C6 must not decide the cryptographic architecture independently.

For ONNX with external tensor storage, the integrity unit cannot silently be reduced to the main `.onnx` file.

Potential components include, depending on the C4 definition:

- main model file;
- external tensor data;
- model configuration;
- dataset annotation;
- associated metadata.

The exact list must be frozen before hashing code becomes authoritative.

## 14.3 Manifest Authority

An artifact under test must not control the metadata against which it is validated.

The circular-trust failure is:

```text
MODEL / CONTRIBUTOR
        ↓
WRITES OWN MANIFEST
        ↓
VALIDATOR TRUSTS MANIFEST
        ↓
VALIDATOR COMPARES MODEL
AGAINST MODEL-CONTROLLED DATA
```

That does not establish an independent integrity boundary.

The intended authority separation is:

```text
INDEPENDENT TRUSTED AUTHORITY
        ↓
AUTHORITATIVE MANIFEST
        ↓
TRUSTED SUPERVISOR
        ↓
COMPARES
        ↓
UNTRUSTED ARTIFACT UNIT
```

A model or worker that processed the model must not be allowed to overwrite its authoritative manifest path.

---

# 15. Candidate Engineering Methods

`PROTOTYPE` means the evidence supports attempting implementation.

It does **not** mean the candidate is implemented, target-tested or BUILD-authorized.

No candidate currently reaches `BUILD`.

## RC-001 — Generic Multi-Format Adapter

**Purpose:** Route multiple target artifact families through format-specific validation paths without pretending that all formats share identical semantics.

**Engineering role:** Model-agnostic dispatch and typed adaptation layer.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** `DEP-C6-ALL-001`, `DEP-C6-C1-001`, `DEP-C6-C2-001`, and format-specific runtime contracts.

**Target format/runtime:** Conditional across the frozen COCO/YOLO, PyTorch, TorchScript and ONNX scope.

**Offline status:** `UNKNOWN`

**CPU status:** `CONDITIONAL`

**Current disposition:** **PROTOTYPE**

**Why considered:** Required if the system is to expose explicit supported/unsupported paths rather than assume one framework.

**Why not BUILD:** No target-host execution, mandatory format set is unresolved, and individual adapters inherit their own safety/runtime gates.

**Blocker:** Target specification plus C1 mandatory-format closure.

**False-positive risks:** No method-specific quantitative FP analysis exists in the dossier; adapter misclassification could yield an inappropriate route or unsupported outcome.

**False-negative risks:** No project experiment exists; unsupported variants must not be accepted through overly broad family matching.

**Evidence available:** Format-specific upstream documentation only; no dedicated target implementation evidence.

**Five-day implications:** **HIGH risk** because every included format expands testing and dependency scope.

**Sources:** Format-specific C6 registry sources including C6-SRC-001, -003, -005, -006 and -011; no dedicated RC-001 execution evidence.

## RC-002 — PyTorch `weights_only=True` Safe-Loading

**Purpose:** Reduce unrestricted deserialization behavior when handling PyTorch checkpoints.

**Engineering role:** PyTorch hostile-artifact loading gate inside containment.

**Evidence class:** `IMPLEMENTATION_INSPECTED`

**Dependencies:** PyTorch ≥2.10.0; RC-011 isolation; explicit allowlisting policy; hostile fixture.

**Target format/runtime:** PyTorch serialized checkpoint path.

**Offline status:** `LIKELY`, not target-proven.

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Documented API with explicit restricted-loading semantics and lower integration cost than reconstructing every model via a new serialization format.

**Why not BUILD:** `weights_only=True` has known historical bypasses; no patched target run or hostile checkpoint containment test exists.

**Blocker:** Target PyTorch version, explicit DetectionModel handling, RC-011 containment and proof that no unrestricted fallback occurs.

**False-positive risks:** Legitimate Ultralytics models can be rejected because required globals are not allowlisted, creating false `UNSUPPORTED` pressure.

**False-negative risks:** Vulnerable/unpatched loader behavior could execute hostile code without a rejection path.

**Evidence available:** `torch.load` docs plus two PyTorch security advisories.

**Five-day implications:** **MEDIUM risk**; foundational for any PyTorch path.

**Sources:** C6-SRC-002, C6-SRC-009, C6-SRC-010; Reverify C6-CLM-042 context.

## RC-003 — TorchScript Arbitrary Ingestion

**Purpose:** Validate arbitrary TorchScript artifacts.

**Engineering role:** TorchScript model-ingestion path.

**Evidence class:** `IMPLEMENTATION_INSPECTED`

**Dependencies:** Validated isolated worker; target containment mechanism; hostile TorchScript fixture.

**Target format/runtime:** TorchScript.

**Offline status:** `UNKNOWN`

**CPU status:** `CONDITIONAL`

**Current disposition:** **DEFER**

**Why considered:** TorchScript is part of the claimed target format family.

**Why not BUILD:** PyTorch policy treats unknown TorchScript as executable-code risk and the required worker boundary is not demonstrated.

**Blocker:** Isolated worker not demonstrated on target; hostile TorchScript containment not executed.

**False-positive risks:** Legitimate artifact may be marked unsupported where safe containment is unavailable.

**False-negative risks:** Uncontained execution could permit hostile behavior outside the intended validator boundary.

**Evidence available:** PyTorch security policy inspection.

**Five-day implications:** **CRITICAL risk**; ordered behind RC-011.

**Sources:** C6-SRC-011.

## RC-004 — ONNX Structural Checking

**Purpose:** Validate bounded ONNX graph/schema structure.

**Engineering role:** Structural layer in the ONNX validation chain.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** ONNX ≥1.21.0; RC-011 external-data containment; exact opset/runtime.

**Target format/runtime:** ONNX.

**Offline status:** `LIKELY`, not proven on target.

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Low-complexity deterministic validation layer.

**Why not BUILD:** No offline target execution, no external-data containment test and no target wheel closure.

**Blocker:** ONNX wheel/runtime closure plus isolated external-data validation.

**False-positive risks:** A structurally valid graph can still be semantically altered; treating structural PASS as a positive semantic verdict would be false assurance.

**False-negative risks:** Structural checking intentionally does not detect every behavioral change; this is a scope limitation rather than a promised detector failure.

**Evidence available:** ONNX concepts and external-data documentation.

**Five-day implications:** **MEDIUM risk**.

**Sources:** C6-SRC-006, C6-SRC-007.

## RC-005 — PyTorch → ONNX Differential Validation

**Purpose:** Compare source-model and exported-ONNX behavior under matched semantics.

**Engineering role:** Cross-format semantic parity gate.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** `DEP-C6-C1-001`; frozen source/export; preprocessing and postprocessing parity; ORT; output criteria.

**Target format/runtime:** PyTorch source vs ONNX export.

**Offline status:** `UNKNOWN`

**CPU status:** `CONDITIONAL`

**Current disposition:** **DEFER unless C1 declares ONNX mandatory**

**Why considered:** Required to avoid confusing structural graph validity with semantic equivalence.

**Why not BUILD:** No project parity run, exact export tuple or matching preprocessing contract exists.

**Blocker:** C1 mandatory-format decision plus batch/NMS and preprocessing alignment.

**False-positive risks:** Letterbox/preprocessing mismatch can produce false `DIFFERENT` on an otherwise equivalent export.

**False-negative risks:** Quantization/postprocessing delta below the comparison threshold could allow an altered artifact to pass.

**Evidence available:** PyTorch ONNX verification documentation plus Ultralytics issue evidence.

**Five-day implications:** **HIGH risk; +5h** in the source plan if mandatory.

**Sources:** C6-SRC-022, C6-SRC-023, C6-SRC-025.

## RC-006 — Ultralytics YOLO Path

**Purpose:** Establish one reproducible YOLO/Ultralytics artifact and export/runtime path.

**Engineering role:** Concrete YOLO implementation path rather than format-family generalization.

**Evidence class:** `IMPLEMENTATION_INSPECTED`

**Dependencies:** Frozen Ultralytics version/commit, model variant, export flags, opset, NMS/batch configuration.

**Target format/runtime:** Exact frozen Ultralytics YOLO tuple.

**Offline status:** `LIKELY`, unproven.

**CPU status:** `YES` for planned path.

**Current disposition:** **PROTOTYPE**

**Why considered:** Likely project artifact family and shortest path to a concrete demo tuple.

**Why not BUILD:** `main` is not a reproducibility pin and no frozen export/run tuple exists.

**Blocker:** Commit/version freeze and explicit testing of Issue #23647 conditions.

**False-positive risks:** Export or preprocessing mismatch can create false divergence.

**False-negative risks:** Silent batch/output defects can create apparently valid output while omitting detections.

**Evidence available:** Exporter source and issue inspection.

**Five-day implications:** **MEDIUM risk** if reduced to one exact tuple.

**Sources:** C6-SRC-003, C6-SRC-022, C6-SRC-023.

## RC-007 — Generic Offline Wheelhouse

**Purpose:** Stage required Python packages for no-index installation.

**Engineering role:** Primary offline dependency-delivery path.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** Exact target OS/arch/Python ABI; lockfile; hashes; native dependencies.

**Target format/runtime:** Project Python environment.

**Offline status:** `LIKELY`, target closure unproven.

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Lower complexity than alternate environment/container packaging.

**Why not BUILD:** Native/system dependency closure and zero-network behavior have not been demonstrated.

**Blocker:** Clean-room target installation with native ABI closure.

**False-positive risks:** Successful package installation may be mistaken for deployability.

**False-negative risks:** Missing native dependency can fail only at import/runtime after apparently successful staging.

**Evidence available:** pip documentation and source-reported native-dependency concerns.

**Five-day implications:** **MEDIUM risk** and prerequisite for almost every Python candidate.

**Sources:** C6-SRC-012; C6-CLM-046 lineage context.

## RC-008 — CPU-Only ONNX Runtime Execution

**Purpose:** Execute ONNX artifacts using a CPU-only runtime path.

**Engineering role:** ONNX runtime layer.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** ORT package/native closure, telemetry control, architecture-specific benchmark.

**Target format/runtime:** ONNX Runtime CPU.

**Offline status:** `LIKELY`, not demonstrated.

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Required practical execution path for CPU-only ONNX validation.

**Why not BUILD:** No target CPU benchmark or no-network binary test.

**Blocker:** Target architecture, telemetry inspection, peak-RSS benchmark and provider verification.

**False-positive risks:** Blocked telemetry or dependency initialization could be misinterpreted as model failure.

**False-negative risks:** Silent provider fallback could make the wrong execution path appear valid.

**Evidence available:** ORT install/release documentation; architecture issue reported in lineage.

**Five-day implications:** **MEDIUM risk**.

**Sources:** C6-SRC-001, C6-SRC-008, C6-SRC-024 and Reverify C6-CLM-041 context.

## RC-009 — Activation-Space / Feature Extraction

**Purpose:** Expose or compare intermediate features for detector-oriented integrity methods.

**Engineering role:** Potential interface for C3 methods requiring activations.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** `DEP-C6-C3-001`; portable activation mapping; resource budget.

**Target format/runtime:** Potential PyTorch / ORT / TorchScript paths.

**Offline status:** `UNKNOWN`

**CPU status:** `UNKNOWN`

**Current disposition:** **DEFER**

**Why considered:** Some model-security detectors may require more than final outputs.

**Why not BUILD:** Intermediate representations are not proven portable and CPU/RAM cost is unknown.

**Blocker:** C3 access contract plus target benchmark.

**False-positive risks:** Cross-format activation mismatch may look like artifact divergence.

**False-negative risks:** Inaccessible or non-equivalent layers may omit the signal expected by a detector.

**Evidence available:** Source-reported method descriptions only.

**Five-day implications:** **CRITICAL risk**.

**Sources:** No dedicated normalized C6-SRC mapping in the current registry.

## RC-010a — Neural Cleanse

**Purpose:** Investigate trigger-inversion/backdoor detection as a possible behavioral/model-security component.

**Engineering role:** Candidate backdoor-detection method, not deterministic integrity baseline.

**Evidence class:** `IMPLEMENTATION_INSPECTED`

**Dependencies:** Legacy framework chain or modern port; qualified clean/poisoned corpus; YOLO adaptation; target benchmark.

**Target format/runtime:** Original classifier-oriented implementation; YOLO adaptation absent.

**Offline status:** `PROBLEMATIC`

**CPU status:** `CONDITIONAL`; categorical impossibility is `NOT_SUPPORTED`.

**Current disposition:** **DEFER**

**Why considered:** Established academic backdoor-detection approach.

**Why not BUILD:** Legacy Keras/TF stack, documented false positives, scale-related failures, no YOLO statistic/adaptation and no qualified corpus.

**Blocker:** Detection validity and integration, not a proven universal CPU impossibility.

**False-positive risks:** Source-reported threshold-2 experiment classified 6 of 10 clean MobileNet models as backdoored.

**False-negative risks:** Scale-dependent trigger inversion failure; YOLO behavior unverified.

**Evidence available:** Repository inspection plus later research evidence.

**Five-day implications:** **CRITICAL risk**.

**Sources:** C6-SRC-014; Reverify arXiv 2104.15129v1.

## RC-010b — ABS

**Purpose:** Investigate activation-based backdoor screening.

**Engineering role:** Candidate behavioral/model-security detector.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** Activation access, C3 access contract, CPU benchmark.

**Target format/runtime:** Activation-access model path.

**Offline status:** `UNKNOWN`

**CPU status:** `UNKNOWN`

**Current disposition:** **DEFER**

**Why considered:** Published backdoor-analysis method.

**Why not BUILD:** No implementation/target execution, no YOLO-scale CPU benchmark and required activation access is unresolved.

**Blocker:** `DEP-C6-C3-001` and target benchmarking.

**False-positive risks:** Not quantified for the target model family in the packet.

**False-negative risks:** Not quantified for the target model family in the packet.

**Evidence available:** Paper-level evidence only.

**Five-day implications:** **CRITICAL risk**.

**Sources:** C6-SRC-016.

## RC-010c — TABOR

**Purpose:** Investigate optimization-based trigger/backdoor analysis.

**Engineering role:** Candidate model-security detector.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** Model access, optimization budget, target CPU benchmark.

**Target format/runtime:** Research implementation assumptions; YOLO target not validated.

**Offline status:** `UNKNOWN`

**CPU status:** `UNKNOWN`

**Current disposition:** **DEFER**

**Why considered:** Published trigger-analysis approach.

**Why not BUILD:** Source-reported only; optimization cost and YOLO-scale CPU behavior untested.

**Blocker:** C3 access contract and target benchmark.

**False-positive risks:** Not quantified for the target model family.

**False-negative risks:** Not quantified for the target model family.

**Evidence available:** Paper-level evidence only.

**Five-day implications:** **CRITICAL risk**.

**Sources:** C6-SRC-017.

## RC-011 — Sandboxed / Isolated Worker

**Purpose:** Contain hostile parsing, deserialization and runtime behavior outside the trusted supervisor.

**Engineering role:** Core process/security boundary.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** Target OS/kernel, Landlock/seccomp or permitted equivalent, supervisor IPC design.

**Target format/runtime:** All parser-touching artifact paths.

**Offline status:** `LIKELY`

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Required because safer loader options alone do not provide complete containment.

**Why not BUILD:** No target isolation mechanism has been implemented or hostile-tested.

**Blocker:** `DEP-C6-ALL-001`, especially target kernel and permitted isolation.

**False-positive risks:** Legitimate processing may become `UNSUPPORTED` if required host controls are unavailable.

**False-negative risks:** Incomplete containment could let hostile behavior reach the supervisor or host.

**Evidence available:** Landlock documentation and vulnerability-driven engineering requirement.

**Five-day implications:** **HIGH risk** and a prerequisite for several other candidates.

**Sources:** C6-SRC-013; C6-CLM-TH-010 lineage claim.

## RC-012 — Manifest / Hash Layer

**Purpose:** Establish deterministic serialized-byte identity over the agreed artifact unit.

**Engineering role:** Pre-parse integrity input and evidence record.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** `DEP-C6-C4-001`, `DEP-C6-C4-002`; independent manifest authority.

**Target format/runtime:** All defined artifact units.

**Offline status:** `CONFIRMED` mechanically; complete artifact semantics remain unresolved.

**CPU status:** `YES`

**Current disposition:** **PROTOTYPE**

**Why considered:** Lowest-complexity deterministic integrity primitive.

**Why not BUILD:** Artifact-unit definition and C4 hash/provenance contract remain open; no project mutation suite has executed.

**Blocker:** C4 artifact-unit and output-format decisions.

**False-positive risks:** Incorrect artifact-unit definition can produce misleading comparison outcomes.

**False-negative risks:** If external tensor data is omitted, modified ONNX data can still leave the main-file hash unchanged. SHA-256 collision is architecturally possible but not treated as the operational concern here.

**Evidence available:** Project constraint plus ONNX external-data evidence.

**Five-day implications:** **LOW risk** relative to other candidates.

**Sources:** C6-SRC-007; C6-CLM-031 and C6-CLM-032.

## RC-013 — Automatic Unsafe Fallback

**Purpose:** Represents a failure pattern rather than an acceptable validation method.

**Engineering role:** Negative design rule.

**Evidence class:** `SOURCE_REPORTED` / implementation behavior context.

**Dependencies:** Applies across loaders, worker isolation and execution-provider selection.

**Target format/runtime:** Any path capable of silently degrading security assumptions.

**Offline status:** N/A

**CPU status:** N/A

**Current disposition:** **REJECT**

**Why considered:** Real compatibility pressure can trigger fallback paths.

**Why not BUILD:** A silent transition to less-restricted loading or unisolated execution invalidates the claimed trust boundary.

**Blocker:** Not applicable; the behavior is forbidden.

**False-positive risks:** May make an unsupported artifact appear successfully validated.

**False-negative risks:** Can bypass the very control intended to contain malicious behavior.

**Evidence available:** Ultralytics compatibility behavior and C6 trust-boundary analysis.

**Five-day implications:** Must be excluded from implementation from the outset.

**Sources:** Reverify C6-CLM-042 / Issue #19824 context.

## RC-014 — Safetensors + JSON Configuration

**Purpose:** Explore a non-pickle tensor-storage path.

**Engineering role:** Alternative serialization/input strategy.

**Evidence class:** `IMPLEMENTATION_INSPECTED`

**Dependencies:** Architecture definition, state-dict mapping, inference-equivalence test.

**Target format/runtime:** Tensor storage plus model reconstruction.

**Offline status:** `LIKELY`

**CPU status:** `YES`

**Current disposition:** **DEFER**

**Why considered:** Avoids pickle-based tensor serialization.

**Why not BUILD:** Tensor storage alone does not reconstruct a complete YOLO deployment artifact.

**Blocker:** YOLO architecture/state-dict mapping and equivalence implementation absent.

**False-positive risks:** Mapping mismatch could make a correct tensor set appear invalid.

**False-negative risks:** Incorrect architecture reconstruction could produce superficially loadable but semantically wrong execution.

**Evidence available:** Safetensors implementation/repository inspection.

**Five-day implications:** **HIGH risk** without prior YOLO-specific mapping work.

**Sources:** C6-SRC-019.

## RC-015 — Conda-Pack Offline Bundle

**Purpose:** Package a Conda environment for offline transfer.

**Engineering role:** Alternative deployment packaging.

**Evidence class:** `SOURCE_REPORTED` / documentation inspected.

**Dependencies:** Matching OS/architecture, source package cache, fixed deployment location/process.

**Target format/runtime:** Conda Python environment.

**Offline status:** `UNKNOWN` on target.

**CPU status:** `YES`

**Current disposition:** **DEFER**

**Why considered:** Can bundle a fuller Python environment than a simple wheelhouse.

**Why not BUILD:** Exact target is unknown and relocation constraints add risk without resolving the main blocker.

**Blocker:** Target OS/architecture not supplied.

**False-positive risks:** Archive creation can be mistaken for target deployability.

**False-negative risks:** Relocation or platform mismatch may appear only after transfer.

**Evidence available:** Official conda-pack documentation.

**Five-day implications:** **HIGH risk** as an alternate packaging track.

**Sources:** C6-SRC-020.

## RC-016 — Docker Image Tarball

**Purpose:** Transport a prebuilt environment as an offline container image.

**Engineering role:** Alternative packaging and possible containment layer.

**Evidence class:** `SOURCE_REPORTED` with reverify-confirmed vulnerability evidence.

**Dependencies:** Target Docker policy/runtime, patched version, daemon configuration, supervisor trust separation.

**Target format/runtime:** Docker container runtime.

**Offline status:** `UNKNOWN` on target.

**CPU status:** `YES`

**Current disposition:** **DEFER**

**Why considered:** Strong dependency-packaging convenience and offline image transport.

**Why not BUILD:** Target daemon policy and isolation adequacy are unverified; cited vulnerability requires patch floor and hardening.

**Blocker:** Target Docker availability/policy plus isolation test.

**False-positive risks:** Successful container launch can be mistaken for sufficient sandboxing.

**False-negative risks:** Runtime/daemon trust-boundary weakness can permit escape from intended containment.

**Evidence available:** Docker image transport docs and confirmed CVE-2025-9074.

**Five-day implications:** **HIGH risk** and additional scope.

**Sources:** C6-SRC-021; Reverify C6-CLM-040.

## RC-017 — Weight-Space Statistical Anomaly

**Purpose:** Search model weights for statistical anomalies relative to an expected baseline/family.

**Engineering role:** Optional heuristic integrity signal.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** Clean baseline or comparable model family; calibration and thresholding.

**Target format/runtime:** Weight-access path.

**Offline status:** `LIKELY`

**CPU status:** `YES`

**Current disposition:** **DEFER**

**Why considered:** Potentially lower-compute signal than full behavioral search.

**Why not BUILD:** No clean baseline, no project FPR and no demonstrated separation on the target family.

**Blocker:** Baseline/corpus and empirical threshold.

**False-positive risks:** Fine-tuning, quantization or legitimate training differences can shift statistics.

**False-negative risks:** Subtle or distributed backdoors may not produce separable weight statistics.

**Evidence available:** Literature/source-reported only; no dedicated project benchmark.

**Five-day implications:** **MEDIUM risk**, but unnecessary for deterministic MVP.

**Sources:** No dedicated normalized C6-SRC entry in the current registry.

## RC-018 — STRIP Minimal Subset

**Purpose:** Explore perturbation/entropy-based backdoor detection.

**Engineering role:** Optional behavioral detector.

**Evidence class:** `SOURCE_REPORTED`

**Dependencies:** YOLO-specific statistic, calibration corpus, target benchmark.

**Target format/runtime:** Originally classifier softmax outputs; YOLO adaptation undefined.

**Offline status:** `UNKNOWN`

**CPU status:** `CONDITIONAL`

**Current disposition:** **DEFER**

**Why considered:** Published black-box method with attractive low-access assumptions.

**Why not BUILD:** Bounding-box output does not directly provide the original entropy statistic; later research shows setting/attack dependence; no calibration corpus exists.

**Blocker:** Undefined YOLO statistic and unavailable qualified calibration data.

**False-positive risks:** Entropy distributions may overlap for clean/backdoored cases under some settings.

**False-negative risks:** Source-specific or setting-dependent attacks may evade separation.

**Evidence available:** Original STRIP paper plus later USENIX failure analysis.

**Five-day implications:** **HIGH risk**.

**Sources:** C6-SRC-015; Reverify USENIX Tang et al.

## RC-019 — Simplified Deterministic MVP

**Purpose:** Build the smallest independently testable validation vertical slice.

**Engineering role:** Five-day MVP candidate.

**Evidence class:** `SOURCE_REPORTED` composite.

**Dependencies:** RC-002, RC-004 where applicable, RC-007, RC-011, RC-012 plus open cell contracts.

**Target format/runtime:** One exact frozen team/public artifact tuple.

**Offline status:** `LIKELY`, not demonstrated.

**CPU status:** `YES` in the planned bounded scope.

**Current disposition:** **PROTOTYPE**

**Why considered:** Hash → schema → safe/isolated load → smoke execution → bounded states → evidence recording is easier to validate deterministically than speculative behavioral detection.

**Why not BUILD:** Every component still lacks target evidence and multiple prerequisites are open.

**Blocker:** Target host plus C1/C2/C4/C5 contracts and isolation availability.

**False-positive risks:** An incorrect state-machine transition could mislabel timeout/unsupported conditions; component-specific FP risks also propagate.

**False-negative risks:** Deterministic checks do not cover every behavioral integrity threat; behavioral-layer FN risks remain outside this MVP.

**Evidence available:** Composite of current C6 sources; no target run.

**Five-day implications:** **MEDIUM risk**, but lowest credible integration scope.

**Sources:** Composite; no dedicated C6-SRC entry.

---

# 16. Method Status Matrix

| RC | Method | Evidence Class | Current Status | Main Dependency | Main Blocker |
|---|---|---|---|---|---|
| RC-001 | Generic multi-format adapter | SOURCE_REPORTED | **PROTOTYPE** | C1 format scope | Format/target contracts not frozen |
| RC-002 | PyTorch `weights_only` safe-loading | IMPLEMENTATION_INSPECTED | **PROTOTYPE** | RC-011 + PyTorch ≥2.10.0 | No hostile target execution; unsafe fallback risk |
| RC-003 | TorchScript arbitrary ingestion | IMPLEMENTATION_INSPECTED | **DEFER** | RC-011 | Isolated worker not demonstrated |
| RC-004 | ONNX structural checking | SOURCE_REPORTED | **PROTOTYPE** | ONNX ≥1.21.0 + RC-011 | External-data containment untested |
| RC-005 | PyTorch→ONNX differential | SOURCE_REPORTED | **DEFER unless C1 mandates** | C1 + RC-006/008 | Frozen parity tuple absent |
| RC-006 | Ultralytics YOLO path | IMPLEMENTATION_INSPECTED | **PROTOTYPE** | Version/commit freeze | `main` not reproducible; batch/NMS gate untested |
| RC-007 | Offline wheelhouse | SOURCE_REPORTED | **PROTOTYPE** | Target OS/ABI | Native closure unproven |
| RC-008 | CPU-only ORT | SOURCE_REPORTED | **PROTOTYPE** | Target architecture | No CPU/RSS/network benchmark |
| RC-009 | Activation-space extraction | SOURCE_REPORTED | **DEFER** | C3 access contract | Portability/resource cost unknown |
| RC-010a | Neural Cleanse | IMPLEMENTATION_INSPECTED | **DEFER** | Corpus + adaptation | Legacy stack + efficacy limitations |
| RC-010b | ABS | SOURCE_REPORTED | **DEFER** | C3 access + CPU | No target benchmark |
| RC-010c | TABOR | SOURCE_REPORTED | **DEFER** | C3 access + CPU | No target benchmark |
| RC-011 | Sandboxed worker | SOURCE_REPORTED | **PROTOTYPE** | Target kernel/policy | Isolation mechanism not demonstrated |
| RC-012 | Manifest/hash layer | SOURCE_REPORTED | **PROTOTYPE** | C4 artifact unit | Hash scope unresolved |
| RC-013 | Automatic unsafe fallback | SOURCE_REPORTED | **REJECT** | N/A | Violates trust boundary |
| RC-014 | Safetensors + JSON config | IMPLEMENTATION_INSPECTED | **DEFER** | YOLO mapping | Architecture/state-dict mapping absent |
| RC-015 | Conda-pack | SOURCE_REPORTED | **DEFER** | Target OS/arch | Portability constraints |
| RC-016 | Docker image tarball | SOURCE_REPORTED | **DEFER** | Target Docker policy | Isolation/hardening not tested |
| RC-017 | Weight-space statistics | SOURCE_REPORTED | **DEFER** | Clean baseline | FPR/separation unknown |
| RC-018 | STRIP subset | SOURCE_REPORTED | **DEFER** | YOLO statistic/corpus | Adaptation/calibration absent |
| RC-019 | Deterministic MVP | SOURCE_REPORTED | **PROTOTYPE** | All core deterministic gates | Composite target evidence absent |

**BUILD: none.**

---

# 17. Deterministic MVP

RC-019 is the smallest C6 path considered credible for the five-day engineering window.

Its intended shape is:

```text
ARTIFACT
   ↓
DEFINED ARTIFACT UNIT + HASH
   ↓
SCHEMA / STRUCTURAL VALIDATION
   ↓
SAFE / ISOLATED LOAD
   ↓
BOUNDED SMOKE EXECUTION
   ↓
TYPED RESULT STATE
   ↓
EVIDENCE RECORD
```

The advantage is not that this pipeline detects every model-integrity threat.

It does not.

Its advantage is that each layer can be given a deterministic pass/fail condition.

The MVP should therefore emphasize:

- artifact identity;
- schema/structural validity;
- loader/runtime containment;
- successful bounded execution;
- correct state semantics;
- and reproducible evidence.

Behavioral backdoor detectors should not be added merely to make the prototype appear more sophisticated if their transfer, corpus and error rates cannot be meaningfully validated.

### Smoke-test boundary

A 10-image or similar execution test can demonstrate:

- runtime executes;
- outputs are returned;
- the pipeline integrates at a basic level.

It cannot establish:

- false-positive rate;
- true-positive rate;
- attack-detection rate;
- robustness;
- detector generalization;
- or production efficacy.

```text
SMOKE TEST
    ≠
DETECTOR EFFICACY EVALUATION
```

---

# 18. Rejected / Deferred Methods

## 18.1 REJECT — Automatic Unsafe Fallback

**RC-013 is rejected.**

Examples of prohibited implicit transitions include:

```text
weights_only=True fails
        ↓
silent retry
        ↓
weights_only=False
```

or:

```text
isolated worker unavailable
        ↓
silent retry
        ↓
trusted supervisor executes model
```

or:

```text
expected execution provider fails
        ↓
silent alternate provider
        ↓
result treated as equivalent
```

Any such behavior changes the trust model without changing the reported assurance state.

That is unacceptable.

## 18.2 DEFER — TorchScript Arbitrary Ingestion

**RC-003 — DEFER**

Reason:

- unknown-source TorchScript carries executable semantics;
- isolated worker is still only a prototype;
- hostile containment is not target-demonstrated.

## 18.3 DEFER — ONNX Differential Validation

**RC-005 — DEFER unless C1 declares it mandatory**

Reason:

- source/export tuple not frozen;
- preprocessing alignment not tested;
- batch/output assertions not implemented;
- documented YOLO batch/NMS issue must be handled explicitly.

Structural checking alone must never be reinterpreted as semantic parity.

## 18.4 DEFER — Neural Cleanse

**RC-010a — DEFER**

Preserved reasons:

- Keras 2.2.2 / TensorFlow 1.10-era implementation chain;
- source-supported false-positive evidence;
- scale-dependent limitations;
- no defined YOLO object-detection adaptation;
- no qualified clean/poisoned YOLO corpus.

The dossier specifically rejects the stronger claim that Neural Cleanse has been proven categorically impossible on CPU within five days.

That claim is `NOT_SUPPORTED` because no target CPU benchmark has occurred.

## 18.5 DEFER — ABS / TABOR

**RC-010b / RC-010c — DEFER**

Both remain source-reported only.

They require access patterns and compute behavior that have not been demonstrated on the target model family or CPU.

## 18.6 DEFER — STRIP

**RC-018 — DEFER**

Reasons:

- original statistic assumes classifier-oriented output behavior;
- YOLO output adaptation is undefined;
- calibration corpus is absent;
- later research demonstrates setting-dependent and attack-dependent failures.

The original STRIP results and later failure evidence are both retained rather than averaged into a universal conclusion.

## 18.7 DEFER — Safetensors

**RC-014 — DEFER**

Safetensors removes pickle from the tensor-storage layer.

It does not automatically reconstruct the complete YOLO architecture or map arbitrary state dictionaries into a validated model.

That integration does not currently exist in the packet.

## 18.8 DEFER — Conda-Pack

**RC-015 — DEFER**

Reason:

- exact target OS/architecture unknown;
- relocation constraints are documented;
- no target deployment run exists.

## 18.9 DEFER — Docker

**RC-016 — DEFER**

Reason:

- target daemon policy unknown;
- patch/hardening assumptions not verified;
- supervisor/container trust split untested;
- no target isolation experiment exists.

## 18.10 DEFER — Activation and Weight-Space Methods

**RC-009 and RC-017 — DEFER**

The former lacks a cross-format activation contract and resource benchmark.

The latter lacks an appropriate baseline and empirical separation evidence.

---

# 19. Evidence and Implementation Status

## 19.1 Installation / Execution Evidence

| Method | Evidence class | Install tested | Run tested | Offline confirmed | Notes |
|---|---|---|---|---|---|
| RC-001 Generic adapter | SOURCE_REPORTED | NO | NO | NO | Format-level concept only |
| RC-002 PyTorch safe-loading | IMPLEMENTATION_INSPECTED | NO | NO | NO | API/advisories inspected |
| RC-003 TorchScript ingestion | IMPLEMENTATION_INSPECTED | NO | NO | NO | Security policy inspected |
| RC-004 ONNX structural check | SOURCE_REPORTED | NO | NO | NO | ONNX docs inspected |
| RC-005 ONNX differential | SOURCE_REPORTED | NO | NO | NO | Verification docs inspected |
| RC-006 Ultralytics YOLO | IMPLEMENTATION_INSPECTED | NO | NO | NO | Exporter inspected; commit unfrozen |
| RC-007 Wheelhouse | SOURCE_REPORTED | NO | NO | NO | pip mechanics documented |
| RC-008 ORT CPU | SOURCE_REPORTED | NO | NO | NO | ORT documentation/release inspected |
| RC-009 Activation-space | SOURCE_REPORTED | NO | NO | NO | Research-level only |
| RC-010a Neural Cleanse | IMPLEMENTATION_INSPECTED | NO | NO | NO | Legacy dependency chain inspected |
| RC-010b ABS | SOURCE_REPORTED | NO | NO | NO | Paper only |
| RC-010c TABOR | SOURCE_REPORTED | NO | NO | NO | Paper only |
| RC-011 Sandboxed worker | SOURCE_REPORTED | NO | NO | NO | Landlock docs inspected |
| RC-012 Manifest/hash | SOURCE_REPORTED | NO | NO | **CONFIRMED mechanically only** | Hashing itself requires no network; authoritative artifact scope unresolved |
| RC-013 Unsafe fallback | SOURCE_REPORTED | N/A | N/A | N/A | Rejected behavior |
| RC-014 Safetensors | IMPLEMENTATION_INSPECTED | NO | NO | NO | Storage semantics inspected; YOLO mapping absent |
| RC-015 Conda-pack | SOURCE_REPORTED | NO | NO | NO | Portability caveats inspected |
| RC-016 Docker tarball | SOURCE_REPORTED | NO | NO | NO | Vulnerability and transport evidence inspected |
| RC-017 Weight-space statistics | SOURCE_REPORTED | NO | NO | NO | No benchmark |
| RC-018 STRIP | SOURCE_REPORTED | NO | NO | NO | Original and later research inspected |
| RC-019 Deterministic MVP | SOURCE_REPORTED | NO | NO | NO | Composite path; all gaps remain |

## 19.2 Evidence Gap

The current project state is:

```text
SOURCE_REPORTED
      +
IMPLEMENTATION_INSPECTED
      ↓
NO TARGET EXECUTION
      ↓
NO EXPERIMENTAL REPRODUCTION
```

This is why no BUILD claim is authorized.

## 19.3 Source Quality-Gate Carry-Forward

| Quality area | Source dossier assessment |
|---|---|
| Scope discipline | PASS |
| Evidence traceability | PASS |
| Re-verification of major claims | PASS |
| Implementation inspection | PASS |
| Limitations visibility | PASS |
| Red-team / disconfirming evidence | PASS |
| Five-day feasibility | **NEEDS_REVIEW** |
| Evaluation ground truth | **NEEDS_REVIEW** |
| Contradictions / uncertainty | PASS |
| Cross-cell dependency visibility | PASS |

The two `NEEDS_REVIEW` areas remain unresolved because planning and proposed ground truth have not been validated on the actual target.

---

# 20. False-Positive / False-Negative Risks

No numerical rates are invented below.

| Method | False-positive risk | False-negative risk | Evidence status |
|---|---|---|---|
| RC-002 | Legitimate `DetectionModel` may be rejected under restricted loading, creating pressure for an unsafe fallback | Vulnerable/unpatched loader may allow hostile behavior to execute | Implementation/advisory evidence; no target test |
| RC-004 | Structural PASS may be misinterpreted as semantic PASS | Structural checker intentionally does not detect every behavioral alteration | Documentation-backed scope; no target test |
| RC-005 | Preprocessing/letterbox mismatch can produce false `DIFFERENT` | Quantization/postprocessing differences below threshold can permit altered output to appear equivalent | Source-reported; no project parity test |
| RC-008 | Blocked telemetry/native-init problem may produce an `ERROR` unrelated to model correctness | Silent provider/runtime fallback may accept the wrong inference path | Source-reported; no target benchmark |
| RC-010a | Source-reported threshold-2 experiment classified 6/10 clean MobileNet models as backdoored | Trigger inversion can fail at larger scales; YOLO behavior is unvalidated | External research only |
| RC-012 | Incorrect artifact-unit definition can create misleading comparison outcomes | External data omitted from the hash unit can allow altered tensor data to escape the comparison | Design/source evidence; no mutation suite run |
| RC-018 | Clean/backdoored output statistics may overlap | Setting- or attack-specific behavior may evade STRIP separation | Original plus later research |
| RC-019 | Incorrect state transition could treat timeout/unsupported behavior as a positive result | Deterministic MVP does not cover all behavioral integrity threats | Architectural risk; no experimental evidence |

---

# 21. Unsupported Conditions

The following conditions have **not** been tested and must remain visible.

| Unsupported / unassessed condition | Why unsupported |
|---|---|
| Clean-room offline installation on a specific target | No target host supplied |
| CPU performance of any candidate on the target CPU | No target benchmark |
| Peak-RSS compliance | No target benchmark |
| Hostile containment on the intended target mechanism | Isolation not implemented/tested |
| PyTorch → ONNX semantic parity for a project model | No frozen differential run |
| YOLO-scale Neural Cleanse efficacy | No corpus, adaptation or benchmark |
| YOLO STRIP false-positive rate | No YOLO statistic or calibration set |
| Docker isolation adequacy | No target Docker policy/runtime test |
| Conda-pack behavior on target | Target OS/architecture unknown |
| TorchScript hostile ingestion | Worker containment absent |
| ORT zero-egress behavior for staged binary | Binary/network test not performed |
| Full multi-format support | No exact set of tested tuples exists |

The engineering rule is:

> **What has not been tested must be shown.**

---

# 22. Evaluation and Ground-Truth Strategy

The current dossier defines constructable fixtures and experiments.

They are **proposed evaluation procedures**, not completed project experiments.

## 22.1 Candidate Ground-Truth Assets

The packet identifies or proposes:

- a frozen team/public YOLO artifact — **currently UNVERIFIED in packet**;
- COCO/YOLO sample images and labels — offline source still to be confirmed;
- a known-good reference artifact;
- a byte-mutated model;
- malformed schema/config fixtures;
- a hostile PyTorch checkpoint;
- ONNX external-data traversal fixtures;
- clean/poisoned YOLO pairs — **currently UNVERIFIED**;
- format/configuration mismatch cases;
- timeout/resource-exhaustion fixtures.

## 22.2 Evaluation Matrix

| Test | Fixture | Ground truth | Expected result | Pass criterion | Current status |
|---|---|---|---|---|---|
| Byte-level tamper | Known-good artifact with one controlled byte/bit mutation | Artifact differs from reference | `DIFFERENT` | Mutation reliably changes hash within defined artifact unit | **PROPOSED — NOT EXECUTED** |
| Schema malformation | Required COCO/YOLO/config field removed | Fixture is structurally invalid for declared schema | `UNSUPPORTED` or defined structural rejection | Deterministic rejection without positive assurance state | **PROPOSED — NOT EXECUTED** |
| Hostile checkpoint | Controlled `.pt` containing unsafe serialized behavior | Fixture attempts unsafe behavior | `ERROR` / `UNSUPPORTED`; no payload execution | Payload does not execute; no unrestricted fallback; supervisor survives | **PROPOSED — NOT EXECUTED** |
| ONNX traversal | External data references traversal/absolute/symlink path | Path must be outside allowed artifact boundary | `UNSUPPORTED` / `ERROR` | External file is not read; worker remains contained | **PROPOSED — NOT EXECUTED** |
| Resource exhaustion | Infinite loop / excessive allocation fixture | Assessment cannot safely complete | `ASSESSMENT_UNAVAILABLE` | Worker is terminated; supervisor and evidence writer survive | **PROPOSED — NOT EXECUTED** |
| Timeout | Intentionally non-terminating bounded test | Runtime exceeds defined limit | `ASSESSMENT_UNAVAILABLE` | Timeout never converts into positive state | **PROPOSED — NOT EXECUTED** |
| ONNX batch/NMS check | Frozen YOLO11/12 export under documented affected configuration | Every input requires corresponding output accounting | `DIFFERENT` / `UNSUPPORTED` if per-item contract fails | Output-count assertion detects missing batch items | **PROPOSED — NOT EXECUTED** |
| ONNX structural vs semantic separation | Structurally valid but behaviorally changed graph | Structure valid; behavior differs | Structural sub-check passes; semantic layer remains distinct | Structural success never becomes semantic `MATCH` by itself | **PROPOSED — NOT EXECUTED** |
| Clean-room offline closure | Empty-cache target plus local bundle only | No external dependency/network should be needed | Successful bounded execution | Install/import/run succeed with monitored zero egress | **PROPOSED — NOT EXECUTED** |
| Reproducibility rerun | Same frozen tuple on cleaned environment | Same configuration and fixture set | Same typed results/log schema | Second run reproduces evidence deterministically within defined nondeterminism bounds | **PROPOSED — NOT EXECUTED** |

## 22.3 Minimum Candidate-Specific Validation

### RC-002

Required evidence:

- PyTorch ≥2.10.0;
- adversarial checkpoint;
- no payload execution;
- explicit allowed globals;
- no `weights_only=False` fallback.

### RC-004

Required evidence:

- structural check executes;
- external-data scope validated;
- structural sub-result kept separate from semantic result.

### RC-008

Required evidence:

- cold/warm execution timings;
- peak RSS;
- correct CPU provider;
- telemetry control applied;
- monitored no-network behavior.

### RC-011

Required evidence:

- socket attempt;
- protected-file access attempt;
- infinite loop;
- OOM-style allocation;
- supervisor survival.

### RC-012

Required evidence:

- mutate main model file;
- mutate external tensor file;
- mutate configuration;
- mutate dataset annotation;
- confirm each defined artifact-unit change results in `DIFFERENT`;
- confirm unchanged unit results in `MATCH`.

### RC-019

Required evidence:

- the core hostile fixtures;
- one complete offline run;
- second reproducibility run;
- deterministic state semantics;
- no positive state for timeout, error, unsupported or containment failure.

## 22.4 Minimum Demo Boundary

The source proposes one fixed team/public YOLO artifact plus:

- pre-parse manifest;
- COCO/YOLO structural validation;
- safe/isolated loading;
- bounded 10-image smoke execution;
- byte tamper;
- malformed schema;
- hostile checkpoint;
- path traversal;
- resource exhaustion.

This is an integration demo.

The 10-image portion remains a **smoke test**, not a detector-efficacy benchmark.

---

# 23. Reproducibility Requirements

A vague statement such as "supports YOLO" is not reproducible.

A useful evidence tuple must record enough information for another engineer to repeat the experiment.

## 23.1 Required Reproducibility Record

| Category | Required evidence |
|---|---|
| Artifact | File names, artifact-unit members and cryptographic hashes |
| Source model | Exact model identifier and hash |
| Framework | Exact package version |
| Repository-based dependency | Exact commit hash |
| Ultralytics | Exact release/commit, not `main` |
| ONNX | Exact ONNX version |
| ORT | Exact runtime version/build |
| PyTorch | Exact version |
| Export | Command/API path and all flags |
| Opset | Resolved numeric value |
| Batch | Export and validation batch |
| NMS | Exact setting |
| Dynamic shapes | Exact setting |
| Preprocessing | Resize/letterbox/normalization procedure |
| Postprocessing | Thresholding/NMS/output interpretation |
| Python | Exact CPython version |
| OS | Exact OS/release |
| Architecture | x86-64, aarch64, etc. |
| CPU | Target CPU identity |
| RAM | Available target RAM |
| Kernel | Version where isolation depends on kernel support |
| Isolation | Mechanism and configuration |
| Dependency bundle | Lockfile and package hashes |
| Native dependencies | Versions/install state |
| Network | Evidence that run occurred without egress |
| Logs | Deterministic schema plus timestamps/run ID as applicable |
| Fixtures | Hashes and construction procedure |
| Result vocabulary | Exact state tokens and transition rules |

The principle is:

> A reproducible test tuple is more meaningful than a broad claim that a format family is "supported."

---

# 24. Five-Day Feasibility

The five-day estimate in the source is a planning model.

It is not measured implementation time.

## 24.1 Task Plan

| Task | Engineering work | Approx. hours | Dependency | Risk | Status |
|---|---|---:|---|---|---|
| 1 | C1–C5 interface closure: mandatory formats, access contract, provenance/hash contract, result vocabulary | 3 | All open cell dependencies | **CRITICAL** | **BLOCKED** |
| 2 | Freeze target host and isolation policy: OS, architecture, Python, CPU, RAM, kernel, permitted sandbox | 2 | DEP-C6-ALL-001 | **CRITICAL** | **BLOCKED** |
| 3 | Freeze package versions/commits/hashes: PyTorch ≥2.10.0, ONNX ≥1.21.0, ORT, Ultralytics | 2 | Task 2 | HIGH | NOT STARTED |
| 4 | Build wheelhouse and clean-room install harness; `--no-index`; native ABI check | 5 | Target freeze | HIGH | NOT STARTED |
| 5 | Define artifact unit and implement pre-parse manifest/hash | 3 | DEP-C6-C4-001 / C4-002 | HIGH | BLOCKED |
| 6 | COCO/YOLO schema/static validation | 3 | DEP-C6-C2-001 | MEDIUM | BLOCKED |
| 7 | Isolated worker + safe-loading preflight | 7 | Target isolation availability | **CRITICAL** | BLOCKED |
| 8 | Deterministic smoke runner and state machine | 3 | DEP-C6-C5-001 | HIGH | BLOCKED |
| 9 | Synthetic hostile fixtures and containment tests | 4 | Worker + fixtures | HIGH | NOT STARTED |
| 10 | Cross-cell handoff validation | 2 | DEP-C6-ALL-002 and cell contracts | HIGH | BLOCKED |
| 11 | Clean-room rerun and evidence bundle | 3 | All prior tasks | HIGH | NOT STARTED |
| 9A — conditional | PyTorch→ONNX differential validation with matched preprocessing, batch/output assertions | +5 | DEP-C6-C1-001 | HIGH | DEFERRED UNLESS MANDATORY |

### Planning totals

| Scenario | Planning estimate |
|---|---:|
| ONNX differential not mandatory | **37h** |
| ONNX differential mandatory | **42h** |

These are **planning estimates only**.

They are not achieved timings.

## 24.2 Critical Path

```text
TARGET HOST
    ↓
VERSION / ABI FREEZE
    ↓
OFFLINE DEPENDENCY CLOSURE
    ↓
ISOLATION
    ↓
SAFE LOAD / PARSE
    ↓
DETERMINISTIC EXECUTION
    ↓
HOSTILE FIXTURES
    ↓
CROSS-CELL HANDOFF
    ↓
REPRODUCIBLE EVIDENCE
```

The largest uncertainty is the target host.

Unknown values can invalidate downstream assumptions about:

- native libraries;
- Python ABI;
- package wheels;
- kernel features;
- Landlock;
- seccomp;
- ORT builds;
- Docker;
- Conda;
- and memory behavior.

The source estimates that a target-host surprise could consume **6–12 hours of unplanned recovery**.

That is itself an inference, not a measured delay.

## 24.3 Most Likely Blocker per Core Prototype

| Candidate | Primary anticipated blocker |
|---|---|
| RC-002 | Silent/implicit unrestricted compatibility fallback |
| RC-004 | ONNX floor/external-data fixture and containment closure |
| RC-006 | Unfrozen Ultralytics commit and untested batch/NMS tuple |
| RC-007 | Hidden native ABI dependency |
| RC-008 | Staged ORT build behavior and architecture-specific resource use |
| RC-011 | Landlock or equivalent unavailable on target |
| RC-012 | Artifact-unit definition unresolved |
| RC-019 | Any upstream gate failure invalidating the vertical slice |

---

# 25. Engineering Implications

## 25.1 ONNX

Structural and semantic validation must remain separate.

```text
STRUCTURAL PASS
      ≠
SEMANTIC MATCH
```

## 25.2 ONNX External Data

External-data references belong inside the containment boundary.

Paths must be validated before loading.

## 25.3 PyTorch

The PyTorch version floor must be checked before any untrusted checkpoint load.

`weights_only=True` remains a loader restriction, not a complete security boundary.

## 25.4 Unsafe Fallback

No silent switch to unrestricted deserialization, unisolated execution or an unexpected runtime provider is permitted.

## 25.5 CPU

Behavioral detectors cannot be committed as project capabilities until target CPU and RAM behavior is measured.

## 25.6 Offline Deployment

Package-level closure is insufficient.

The final evidence must include native dependencies and monitored no-network execution.

## 25.7 Manifest Authority

The artifact under validation cannot be authoritative for the manifest used to validate it.

## 25.8 Result States

`UNSUPPORTED`, `ASSESSMENT_UNAVAILABLE` and `ERROR` must remain explicit.

They must not be visually or semantically collapsed into a positive result.

## 25.9 Supervisor / Worker Boundary

Hostile artifact parsing and model loading should occur outside the trusted supervisor.

The supervisor should own:

- policy;
- final state;
- manifests;
- evidence;
- provenance.

## 25.10 Supply-Chain Staging

Offline wheels should be hash-pinned against the authoritative pre-staging source set.

Offline transfer alone does not protect against substitution after the bundle is created.

## 25.11 Offline Bundle Size

The dossier records an **INFERENCE**, not a measurement, that a realistic Python-wheel bundle for a stack containing patched PyTorch, ONNX, ORT CPU, pinned Ultralytics, pycocotools and dependencies may be on the order of **2–5 GB**, before model artifacts, fixtures and additional native components.

The exact size must be measured after package freeze.

No bundle-size claim should be treated as final until `pip download` or equivalent staging is actually run.

---

# 26. Cross-Cell Dependencies

| Dependency | Owning / supplying cell | Required input | Why C6 needs it | Blocking effect | Status |
|---|---|---|---|---|---|
| **DEP-C6-ALL-001** | All cells / project environment | Target OS, CPU architecture, CPython, RAM, kernel, permitted isolation mechanism | Determines ABI, packaging, benchmark and containment feasibility | Blocks nearly all Level C work | **OPEN — CRITICAL** |
| **DEP-C6-ALL-002** | C6 produces; C1/C4/C5 consume | Installed versions, bundle hash, containment logs, resource measurements, state outputs | Required downstream as validation evidence | Cannot exist before execution | **NOT YET PRODUCIBLE** |
| **DEP-C6-C1-001** | C1 | Mandatory format list and whether ONNX interoperability is required in first delivery | Determines demonstration scope and +5h differential task | Blocks final critical path definition | **OPEN — CRITICAL** |
| **DEP-C6-C2-001** | C2 | Artifact intake/sanitation boundary and COCO/YOLO annotation scope | Prevents duplicated or missing validation responsibility | Blocks schema/intake implementation | **OPEN** |
| **DEP-C6-C3-001** | C3 | Exact detector access mode: outputs, logits, weights, activations, gradients, baseline, architecture, search budget | Determines whether C6 can expose required data under CPU/runtime constraints | Blocks RC-009/010/018 integration decisions | **OPEN** |
| **DEP-C6-C4-001** | C4 | Authoritative artifact-integrity unit per model format | Required before C6 can hash the correct set of bytes/files | Blocks RC-012 implementation | **OPEN** |
| **DEP-C6-C4-002** | C4 | Hash algorithm/output encoding/field schema; SHA-256 currently assumed in C6 research | C6 must not silently select C4's cryptographic contract | Blocks authoritative manifest output | **OPEN** |
| **DEP-C6-C5-001** | C5 | Authoritative result-state tokens and semantics | Required for the implementation state machine | Blocks final result emission contract | **OPEN** |

Until `DEP-C6-ALL-001` and `DEP-C6-C1-001` are resolved, the source authorizes **no BUILD claim**.

---

# 27. Contradictions, Corrections and Research Evolution

The C6 research record intentionally retains corrections.

The evolution is:

```text
V1
 ↓
RED TEAM
 ↓
REVERIFY
 ↓
V2 SYNTHESIS
 ↓
C6 V2
```

Stronger evidence was allowed to overturn earlier assumptions.

| Topic | Earlier claim | New evidence / correction | Current treatment |
|---|---|---|---|
| `weights_only=True` as a complete security boundary | Early wording treated restricted loading as sufficient | CVE-2025-32434 and CVE-2026-24747 show bypasses | RC-002 remains **PROTOTYPE**; require PyTorch ≥2.10.0 + isolation + hostile tests |
| ONNX structural validity as semantic equivalence | Structural checker success was treated as meaningful interoperability proof | ONNX/PyTorch verification evidence shows structural validity does not prove parity | Structural and differential layers remain separate |
| ONNX CVE-2026-34447 attribution | Red-team branch cited CVE-2026-34447 with inconsistent version scope | REVERIFY located CVE-2026-27489 and CVE-2026-34445; the 34447 attribution was not supported | Use confirmed advisories; keep ONNX ≥1.21.0 floor |
| PyTorch 2.10.0 as both affected and fixed | Branch wording stated 2.10.0 was affected and patched | Re-verification established affected versions below 2.10.0 and 2.10.0 as fixing release | Floor remains **PyTorch ≥2.10.0** |
| STRIP original performance vs later reliability work | Original paper reported low FAR under its tested conditions | Later research demonstrates setting/attack-dependent failures | Preserve both; no YOLO claim without adapted statistic and corpus |
| Neural Cleanse CPU impossibility | Critique extrapolated to categorical CPU impossibility within five days | No target benchmark exists | Categorical impossibility is `NOT_SUPPORTED`; method remains DEFER for other evidence-backed reasons |
| Conda-pack / Docker as BUILD candidates | Earlier branch treated them more favorably | Portability, target-policy and vulnerability/isolation evidence remained unresolved | Both corrected to **DEFER** |

This evolution is a strength of the research process only insofar as the corrections remain visible.

---

# 28. Open Questions

## 28.1 Architecture-Critical

### OQ-AC-001

What is the exact target:

- OS;
- CPU architecture;
- CPython version;
- RAM;
- kernel;
- Landlock ABI;
- seccomp availability;
- permitted isolation mechanism?

This blocks Tasks 2, 3, 4 and 7 and maps to `DEP-C6-ALL-001`.

### OQ-AC-002

Does C1 require ONNX export/interoperability in the first five-day delivery?

If yes, RC-005 enters the critical path and the source planning estimate increases by 5h.

### OQ-AC-003

What is the authoritative C5 state vocabulary?

Are the exact tokens:

`MATCH / DIFFERENT / UNSUPPORTED / ASSESSMENT_UNAVAILABLE / ERROR`

or does C5 require additional states?

### OQ-AC-004

Is Landlock available and permitted on the target kernel?

If not, what equivalent isolation mechanism is allowed?

If no acceptable containment mechanism exists, paths requiring hostile model loading must remain `UNSUPPORTED`.

## 28.2 MVP-Critical

### OQ-MV-001

What exact artifact does C2 hand to C6, and what sanitation has already occurred?

### OQ-MV-002

What access does each C3 detector require?

If intermediate activations are required through ORT, can the frozen runtime expose them in a reproducible supported way?

### OQ-MV-003

What exact provenance/hash schema does C4 define?

C6 must not silently create a conflicting cryptographic contract.

### OQ-MV-004

Does the staged ORT binary have telemetry enabled in its build configuration?

### OQ-MV-005

Does the frozen Ultralytics version used by the project contain the relevant fix for Issue #23647 under the project's exact export tuple?

Issue closure alone is insufficient.

### OQ-MV-006

Which qualified clean/poisoned YOLO pairs and synthetic attack artifacts physically exist for evaluation?

## 28.3 Informational

### OQ-IN-001

Is CVE-2026-34447 a distinct confirmed ONNX advisory beyond CVE-2026-27489 and CVE-2026-34445?

The current primary-source inspection did not support the earlier attribution.

### OQ-IN-002

What is the exact closure status and affected-release range of ORT Issue #29613?

This becomes relevant if the target is Linux/aarch64.

### OQ-IN-003

What YOLO-specific entropy or prediction-set statistic would be used for a STRIP adaptation?

### OQ-IN-004

What experiment battery size and statistical acceptance criterion will the SIH evaluator accept as meaningful bounded behavioral evidence?

---

# 29. False-Assumption Alerts

These are engineering lessons established or preserved by the dossier.

| False assumption | Correct engineering interpretation |
|---|---|
| **"pip installable" means offline deployable** | Python package installation does not establish native ABI closure, runtime operation or zero network access. |
| **`weights_only=True` is a complete security boundary** | It is a useful restricted loader mode, but known vulnerabilities show that isolation and patched versions remain necessary. |
| **ONNX structural PASS means semantic equivalence** | Structural validity and source/export behavioral parity are separate claims. |
| **Hash MATCH means benign** | A hash establishes byte identity only with respect to the defined artifact unit. |
| **Hash DIFFERENT means malicious** | Difference establishes change, not intent. |
| **Docker exists, therefore isolation is safe** | Runtime version, daemon policy, privileges and containment behavior must be validated. |
| **Offline means secure** | Air-gapping removes a network dependency; it does not remove malicious files, vulnerable parsers or local compromise. |
| **Timeout means clean because no attack was detected** | Timeout means assessment could not complete. |
| **Blocked load means clean** | A blocked load is an unavailable/unsupported assessment path. |
| **Unsupported format means clean** | Unsupported means no valid assessment was produced. |
| **A 10-image smoke test validates a detector** | It only demonstrates bounded runtime/integration behavior. |
| **Ultralytics `main` is reproducible** | A branch name can change; exact commit/version must be frozen. |
| **PyTorch 2.10.0 is affected by CVE-2026-24747** | The re-verification treatment records 2.10.0 as the fixing release. |
| **CVE-2026-34447 is confirmed ONNX evidence in this packet** | The inspected primary advisories did not support that attribution. |

---

# 30. Limitations and Negative Evidence

## 30.1 Target Limitation

No target host specification was supplied.

This remains the single most important engineering blocker.

It affects:

- Python ABI;
- package compatibility;
- CPU performance;
- memory;
- kernel features;
- isolation;
- native libraries;
- ORT;
- Docker;
- Conda;
- and offline packaging.

## 30.2 CPU Limitation

No target CPU benchmark has been performed.

No behavioral detector should therefore be described as target-feasible or target-infeasible solely from the current C6 evidence.

## 30.3 Isolation Limitation

No containment mechanism has been validated on the target.

Landlock availability is unresolved.

## 30.4 Format Limitation

Coverage is conditional on exact:

- format;
- version;
- export path;
- opset;
- runtime;
- preprocessing;
- postprocessing;
- and target platform.

No blanket YOLO or ONNX support claim is justified.

## 30.5 Corpus Limitation

No qualified clean/poisoned YOLO corpus exists in the packet.

This blocks meaningful efficacy evaluation of several behavioral methods.

## 30.6 Differential-Validation Limitation

No project-specific PyTorch→ONNX differential run has been performed.

## 30.7 Deployment Limitation

Offline dependency closure is not proven on the target.

## 30.8 Security Limitation

Known loader/runtime vulnerabilities require patch floors and isolation, but satisfying those prerequisites does not establish complete security.

## 30.9 Behavioral-Detector Limitation

Academic results from classifier settings do not automatically transfer to object-detection outputs.

## 30.10 Engineering Uncertainty

Native libraries, ABI, runtime build flags, target architecture and isolation details remain unresolved until the target host is defined.

## 30.11 Negative-Evidence Register

| Investigated assumption/method | Evidence-backed problem |
|---|---|
| `weights_only=True` as sole security boundary | Known PyTorch vulnerabilities invalidate it as a complete boundary |
| Ultralytics compatibility fallback | Unrestricted loading behavior can occur under compatibility pressure and must not be silently accepted |
| ONNX structural check as semantic proof | Contradicted |
| YOLO11/12 ONNX `nms=True`, `dynamic=True`, batch>1 path | Documented silent missing-detection behavior for non-first batch elements in the cited configuration |
| Neural Cleanse | Legacy dependency chain, false-positive evidence, scale limitations, no YOLO adaptation, no qualified corpus |
| STRIP | Classifier statistic, later reliability concerns, no YOLO statistic/calibration |
| ABS / TABOR | Source-reported only; no CPU benchmark or C3 access contract |
| Safetensors as drop-in YOLO deployment | Tensor storage does not provide architecture reconstruction/state mapping |
| Conda-pack as verified target deployment | Target/platform and relocation assumptions unresolved |
| Docker as unconditional isolation boundary | Confirmed vulnerability history plus unverified target runtime/policy |
| TorchScript in first MVP | Executable semantics plus no validated containment |
| CVE-2026-34447 ONNX attribution | Not supported by inspected primary advisories |
| "PyTorch 2.10.0 is affected" | Rejected by REVERIFY treatment; 2.10.0 is the retained fixing floor |

---

# 31. Claim / Source Index

The following table preserves the normalized claim rows present in the C6 V2 source.

| Claim ID | Claim | Status | Evidence / Source | Version | Impact |
|---|---|---|---|---|---|
| **C6-CLM-001** | No target host was supplied; installation/offline/performance claims are not target-validated. | `UNVERIFIABLE` | Target absent in all packet stages | N/A | DI-SCHEDULE / DI-OFFLINE / DI-SECURITY |
| **C6-CLM-002** | ONNX opset semantics are graph-attached and operator/domain-version specific. | `SUPPORTED` | C6-SRC-006 | ONNX 1.24.0 | DI-INTEROP |
| **C6-CLM-003** | Ultralytics export `opset=None` uses the latest supported opset at export time. | `PARTIALLY_SUPPORTED` | C6-SRC-003 | `main`; commit not frozen | DI-INTEROP |
| **C6-CLM-004** | ORT CPU installation is documented through `pip install onnxruntime`. | `SUPPORTED` | C6-SRC-001 | Current docs | DI-OFFLINE |
| **C6-CLM-005** | Blanket claim that ORT CPU initialization never performs network activity is not established. | `UNVERIFIABLE` | C6-SRC-001 / C6-SRC-008 | Requires binary test | DI-OFFLINE |
| **C6-CLM-006** | ORT v1.29.0 documents POSIX telemetry; `ORT_DISABLE_TELEMETRY=1` disables it. | `PARTIALLY_SUPPORTED` | C6-SRC-008 | v1.29.0 | DI-OFFLINE / DI-SECURITY |
| **C6-CLM-007** | `weights_only=True` restricts unsupported globals/classes/functions and may require allowlisting. | `SUPPORTED` | C6-SRC-002 | PyTorch stable | DI-SECURITY |
| **C6-CLM-008** | `weights_only=True` is a complete security boundary for hostile checkpoints. | `CONTRADICTED` | C6-SRC-009 / C6-SRC-010 | CVE-2025-32434 / CVE-2026-24747 | DI-SECURITY |
| **C6-CLM-009** | CVE-2025-32434 affected PyTorch ≤2.5.1 even with `weights_only=True`; patched 2.6.0. | `PARTIALLY_SUPPORTED` | C6-SRC-009 | GHSA-53q9-r3pm-6pq6 | DI-SECURITY |
| **C6-CLM-010** | GHSA-63cw-57p8-fm3p / CVE-2026-24747 affects PyTorch <2.10.0; patched in 2.10.0. | `PARTIALLY_SUPPORTED` | C6-SRC-010 | GHSA-63cw-57p8-fm3p | DI-SECURITY |
| **C6-CLM-011** | PyTorch treats untrusted models as executable-code risk; TorchScript from unknown sources is executable code. | `PARTIALLY_SUPPORTED` | C6-SRC-011 | Current policy | DI-SECURITY |
| **C6-CLM-012** | ONNX external-data references create a filesystem attack surface including traversal/symlink/hardlink concerns. | `PARTIALLY_SUPPORTED` | C6-SRC-007 | ONNX 1.24.0 security | DI-SECURITY |
| **C6-CLM-015** | pycocotools 2.0.11 was released 2025-12-15; wheels exist across multiple platform tags. | `SUPPORTED` | C6-SRC-018 | 2.0.11 | DI-OFFLINE |
| **C6-CLM-020** | A successful ONNX graph check proves PyTorch/ONNX semantic equivalence. | `CONTRADICTED` | C6-SRC-006 / C6-SRC-025 | ONNX 1.24.0 / PyTorch verification docs | DI-INTEROP |
| **C6-CLM-022** | YOLO11/12 ONNX export with `nms=True`, `dynamic=True` can silently return detections only for batch index 0. | `PARTIALLY_SUPPORTED` | C6-SRC-022 | Issue #23647, 2026-02-12 | DI-INTEROP |
| **C6-CLM-024** | Neural Cleanse official implementation requires Keras 2.2.2 / TF 1.10-era stack. | `PARTIALLY_SUPPORTED` | C6-SRC-014 | IMPLEMENTATION_INSPECTED | DI-SCHEDULE |
| **C6-CLM-027** | STRIP is a published black-box perturbation/entropy method; YOLO transfer and small-subset power are unverified. | `PARTIALLY_SUPPORTED` | C6-SRC-015 | 2019 paper | DI-VALIDATION |
| **C6-CLM-028** | A pip wheelhouse with `--no-index` can be staged; package-level closure does not prove native/system ABI closure. | `PARTIALLY_SUPPORTED` | C6-SRC-012 | pip 26.2.1 | DI-OFFLINE |
| **C6-CLM-031** | SHA-256 over serialized bytes establishes byte identity, not semantic equivalence or malicious intent. | `PARTIALLY_SUPPORTED` | Project constraint | N/A | DI-INTEGRITY |
| **C6-CLM-032** | ONNX main-file hashing alone is insufficient when tensor data resides in external files. | `PARTIALLY_SUPPORTED` | C6-SRC-007 | ONNX 1.24.0 | DI-INTEGRITY |
| **C6-CLM-034** | No current C6 evidence establishes a BUILD-ready end-to-end stack. | `UNVERIFIABLE` | Absence of Level C evidence | N/A | DI-SCHEDULE / DI-SECURITY |
| **C6-CLM-043** | Conda-pack environments are not generally relocatable; post-unpack relocation is unsupported. | `PARTIALLY_SUPPORTED` | C6-SRC-020 | conda-pack 0.8.1 | DI-OFFLINE |
| **Reverify C6-CLM-036** | ONNX GHSA-3r9x-f23j-gc73 / CVE-2026-27489 and GHSA-538c-55jv-c5g9 / CVE-2026-34445 support the retained external-data security floor; CVE-2026-34447 was not supported by inspected primary advisories. | `PARTIALLY_SUPPORTED` | Primary ONNX advisories | GHSA-3r9x / GHSA-538c | DI-SECURITY |
| **Reverify C6-CLM-040** | Docker CVE-2025-9074 is confirmed; container isolation is not unconditional. | `PARTIALLY_SUPPORTED` | Reverify C6-SRC-021 | Docker security announcement | DI-SECURITY |
| **Reverify C6-CLM-041** | ORT Issue #29613 reports silent disabling of CPU FlashAttention on Linux/aarch64. | `PARTIALLY_SUPPORTED` | C6-SRC-008 + reported ORT issue | v1.29.0 context | DI-CPU |
| **Reverify C6-CLM-042** | Some Ultralytics `.pt` checkpoints loaded with `weights_only=True` reject `DetectionModel` unless allowlisted or reconstructed. | `PARTIALLY_SUPPORTED` | C6-SRC-019 + Issue #19824 context | IMPLEMENTATION_INSPECTED | DI-INTEROP |

### Additional Lineage Claim Identifiers

The source narrative also references lineage identifiers that are not represented as complete normalized rows in the source's main claim/source-index table, including:

- `C6-CLM-023` — preprocessing/letterbox mismatch context;
- `C6-CLM-025` — categorical Neural Cleanse CPU-intractability claim marked `NOT_SUPPORTED`;
- `C6-CLM-039` — later STRIP reliability evidence;
- `C6-CLM-044` — air-gapped operation is not itself a security guarantee;
- `C6-CLM-046` — ORT/native-dependency closure context;
- `C6-CLM-TH-010` — assurance system's own attack surface;
- `C6-CLM-TH-012` — evaluator/statistical acceptance question.

This public rewrite does not fabricate missing source/version/index fields for those identifiers.

---

# 32. References

## Reference Registry

| Reference | Authors / organization | Title / venue / repository | Year / version | Why it matters | URL | Relevant claims / methods |
|---|---|---|---|---|---|---|
| **[R01 / C6-SRC-001]** | Microsoft / ONNX Runtime | ONNX Runtime — Install documentation | Current in source packet | Establishes documented CPU installation path | https://onnxruntime.ai/docs/install/ | C6-CLM-004, C6-CLM-005, RC-008 |
| **[R02 / C6-SRC-002]** | PyTorch Project | `torch.load` API documentation | Stable; accessed by source 2026-09-24 | Restricted-loader semantics and allowlisting | https://pytorch.org/docs/stable/generated/torch.load.html | C6-CLM-007, RC-002 |
| **[R03 / C6-SRC-003]** | Ultralytics | `ultralytics/engine/exporter.py` | Repository `main`; commit not frozen | Export implementation and opset-resolution behavior | https://github.com/ultralytics/ultralytics/blob/main/ultralytics/engine/exporter.py | C6-CLM-003, RC-006 |
| **[R04 / C6-SRC-004]** | Netron project | Netron repository | Accessed 2026-09-24 | Format-inspection capability referenced in research packet | https://github.com/lutzroeder/netron | Research context |
| **[R05 / C6-SRC-005]** | COCO / cocodataset project | COCO API — PythonAPI | Repository | COCO annotation tooling/format context | https://github.com/cocodataset/cocoapi/tree/master/PythonAPI | RC-001, schema/evaluation context |
| **[R06 / C6-SRC-006]** | ONNX Project | ONNX Concepts — opset and domain semantics | ONNX 1.24.0 in source | Establishes versioned operator/opset semantics and structural scope | https://onnx.ai/onnx/intro/concepts.html | C6-CLM-002, C6-CLM-020, RC-004 |
| **[R07 / C6-SRC-007]** | ONNX Project | External Data Security | ONNX 1.24.0 in source | External-data path/security and artifact-unit implications | https://onnx.ai/onnx/repo-docs/ExternalDataSecurity.html | C6-CLM-012, C6-CLM-032, RC-004, RC-012 |
| **[R08 / C6-SRC-008]** | Microsoft / ONNX Runtime | ONNX Runtime v1.29.0 release | 2026-08-12 | Telemetry/build behavior and ORT release context | https://github.com/microsoft/onnxruntime/releases/tag/v1.29.0 | C6-CLM-005, C6-CLM-006, RC-008 |
| **[R09 / C6-SRC-009]** | PyTorch Project | GHSA-53q9-r3pm-6pq6 — `weights_only=True` RCE / CVE-2025-32434 | Published 2025-04-17 | Demonstrates that restricted PyTorch loading was bypassable in affected versions | https://github.com/pytorch/pytorch/security/advisories/GHSA-53q9-r3pm-6pq6 | C6-CLM-008, C6-CLM-009, RC-002 |
| **[R10 / C6-SRC-010]** | PyTorch Project | GHSA-63cw-57p8-fm3p / CVE-2026-24747 | Published 2026-01-26 | Establishes later `weights_only` security floor | https://github.com/pytorch/pytorch/security/advisories/GHSA-63cw-57p8-fm3p | C6-CLM-008, C6-CLM-010, RC-002 |
| **[R11 / C6-SRC-011]** | PyTorch Project | PyTorch Security Policy | Current in source packet | Treats unknown models/TorchScript as executable-code risk | https://github.com/pytorch/pytorch/security/policy | C6-CLM-011, RC-003 |
| **[R12 / C6-SRC-012]** | Python Packaging Authority / pip | `pip download` documentation | pip 26.2.1 in source | Wheelhouse/offline staging mechanics | https://pip.pypa.io/en/stable/cli/pip_download/ | C6-CLM-028, RC-007 |
| **[R13 / C6-SRC-013]** | Linux kernel documentation | Landlock userspace API | Current kernel docs in source | Candidate Linux isolation mechanism | https://docs.kernel.org/userspace-api/landlock.html | RC-011, OQ-AC-004 |
| **[R14 / C6-SRC-014]** | Bolun Wang / Neural Cleanse project | Neural Cleanse implementation repository | Repository inspected 2026-09-24 | Confirms legacy framework dependency chain | https://github.com/bolunwang/backdoor | C6-CLM-024, RC-010a |
| **[R15 / C6-SRC-015]** | Gao et al. | STRIP: black-box perturbation/entropy backdoor detection | 2019 | Original STRIP method and assumptions | https://arxiv.org/abs/1902.06531 | C6-CLM-027, RC-018 |
| **[R16 / C6-SRC-016]** | Liu et al. | ABS paper | CCS 2019 / arXiv record | Activation-based candidate method | https://arxiv.org/abs/1912.02771 | RC-010b |
| **[R17 / C6-SRC-017]** | Guo et al. | TABOR paper | 2019 | Optimization-based trigger-analysis candidate | https://arxiv.org/abs/1908.01763 | RC-010c |
| **[R18 / C6-SRC-018]** | pycocotools project / PyPI | pycocotools package | 2.0.11; source records 2025-12-15 release | Platform/package dependency evidence | https://pypi.org/project/pycocotools/ | C6-CLM-015 |
| **[R19 / C6-SRC-019]** | safetensors project | safetensors repository | Accessed 2026-09-24 | Tensor-storage semantics and alternate serialization evaluation | https://github.com/safetensors/safetensors | RC-014; Reverify C6-CLM-042 context |
| **[R20 / C6-SRC-020]** | conda-pack project | conda-pack documentation | 0.8.1 | Documents relocation and OS constraints | https://conda.github.io/conda-pack/ | C6-CLM-043, RC-015 |
| **[R21 / C6-SRC-021]** | Docker | Docker image save/load documentation and security announcements | Current in source packet | Offline image transport plus CVE-2025-9074 context | https://docs.docker.com/reference/cli/docker/image/save/ ; https://docs.docker.com/security/security-announcements.md | Reverify C6-CLM-040, RC-016 |
| **[R22 / C6-SRC-022]** | Ultralytics | Issue #23647 — ONNX models exported with `nms=True` produce incorrect results when batch size >1 | Opened 2026-02-12 | Configuration-specific YOLO11/12 ONNX silent-output defect | https://github.com/ultralytics/ultralytics/issues/23647 | C6-CLM-022, RC-005, RC-006 |
| **[R23 / C6-SRC-023]** | Ultralytics | Issue #26269 | Branch-reported in S8OC6; not independently retrieved in source packet | Non-square `.pt`/ONNX divergence context | https://github.com/ultralytics/ultralytics/issues/26269 | C6-CLM-023 context, RC-005 |
| **[R24 / C6-SRC-024]** | Microsoft / ONNX Runtime | ORT Issue #28231 | Opened 2026-04-26 | Platform-specific memory-growth context | https://github.com/microsoft/onnxruntime/issues/28231 | Runtime-risk context |
| **[R25 / C6-SRC-025]** | PyTorch Project | ONNX verification documentation | Updated 2025-08-29 in source | Differential-verification tooling and structural/semantic separation | https://docs.pytorch.org/docs/main/onnx_verification.html | C6-CLM-020, RC-005 |
| **[R26 / Reverify GHSA-3r9x-f23j-gc73]** | ONNX Project | CVE-2026-27489 advisory | Accessed 2026-09-24 | Symlink-traversal PoC and external-data security-floor evidence | https://github.com/onnx/onnx/security/advisories/GHSA-3r9x-f23j-gc73 | Reverify C6-CLM-036 |
| **[R27 / Reverify GHSA-538c-55jv-c5g9]** | ONNX Project | CVE-2026-34445 advisory | Accessed 2026-09-24 | External-data injection evidence and version-floor context | https://github.com/onnx/onnx/security/advisories/GHSA-538c-55jv-c5g9 | Reverify C6-CLM-036 |
| **[R28 / Reverify USENIX Tang et al.]** | Tang et al. | STRIP reliability/failure evaluation | USENIX Security 2021 | Demonstrates setting-dependent and attack-dependent STRIP limitations | https://www.usenix.org/system/files/sec21-tang-di.pdf | C6-CLM-039 context, RC-018 |
| **[R29 / Reverify arXiv 2104.15129v1]** | Authors not normalized in the C6 registry | Stealthy Backdoors paper | 2021 | Neural Cleanse false-positive/scale evidence used in C6 | https://arxiv.org/html/2104.15129v1 | C6-CLM-024, RC-010a |

---

# 33. C6 Research Conclusion

C6 defines the engineering conditions under which this project can make defensible validation claims.

It does **not** certify arbitrary models, arbitrary YOLO variants, arbitrary ONNX graphs, arbitrary PyTorch checkpoints or arbitrary runtimes.

The meaningful support boundary is an exact tested tuple:

```text
ARTIFACT
   +
FORMAT
   +
VERSION
   +
RUNTIME
   +
CONFIGURATION
   +
TARGET PLATFORM
```

A claim outside that tuple must remain:

```text
UNSUPPORTED
```

or:

```text
ASSESSMENT_UNAVAILABLE
```

until corresponding evidence exists.

The current research record therefore remains intentionally incomplete in implementation terms:

- **BUILD GATE: NOT PASSED**
- **BUILD AUTHORIZATION: NONE**
- **CHECKPOINT 2: NOT PASSED**
- **ASSESSMENT: PARTIAL / NOT CLEAN**
- **LEVEL C TARGET-HOST EVIDENCE: NOTHING**
- **LEVEL D EXPERIMENTAL REPRODUCTION: NOTHING**
- multiple candidates remain **PROTOTYPE**;
- multiple candidates remain **DEFERRED**;
- automatic unsafe fallback remains **REJECTED**;
- target-host information remains the critical blocker;
- cross-cell contracts remain open;
- offline closure is unverified;
- target CPU performance is unmeasured;
- isolation is unvalidated;
- and the 37h / 42h schedule remains a planning estimate rather than achieved engineering evidence.

The strongest C6 contribution is therefore not a claim that everything builds.

It is a disciplined boundary between:

```text
WHAT EXISTS IN RESEARCH
        ↓
WHAT HAS BEEN INSPECTED
        ↓
WHAT COULD REASONABLY BE PROTOTYPED
        ↓
WHAT HAS ACTUALLY RUN ON THE TARGET
        ↓
WHAT HAS BEEN EXPERIMENTALLY REPRODUCED
        ↓
WHAT MAY FINALLY SUPPORT A BUILD CLAIM
```

At the current stage, the last three transitions remain open.

That distinction is the basis for trustworthy engineering validation.
