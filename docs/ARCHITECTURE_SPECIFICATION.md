# 09_ARCHITECTURE_SPECIFICATION_SIH26228.md

## SIH 2026 · PS 26228
### Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines

**Stage:** Stage 10 — Architecture Specification
**Document class:** Implementation-ready architecture blueprint. NOT a technology-stack decision. NOT an implementation authorization. NOT a validation record.
**Status:** APPROVED ARCHITECTURE SPECIFIED — see Section 1.
**Produced by:** Principal Systems Architect
**Input artifacts:**
- `08_ARCHITECTURE_DECISION_PACKET_SIH26228.md` — approved architecture decision (project-owner verbal approval 2026-09-25; approval block requires document update)
- `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` — binding reuse decisions
- `04_MASTER_RESEARCH_BIBLE_SIH26228__1__new.md` — highest-authority research foundation

**Governing invariants (absolute — no exception throughout this document):**
```
UNAVAILABLE ≠ CLEAN
NOT_ASSESSED ≠ CLEAN
DEFERRED_IN_SCOPE ≠ CLEAN
anomaly ≠ malicious intent
hash match ≠ safe ≠ semantically equivalent ≠ causal execution proof (PF-002)
finite test coverage ≠ global backdoor absence
detector count ≠ independent corroboration
raw detector score ≠ compromise probability
ANOMALY ≠ PROVEN ATTACK
```

---

# 1. ARCHITECTURE STATUS / APPROVAL

## 1.1 Approval record

```
═══════════════════════════════════════════════════════════════════════
ARCHITECTURE APPROVAL

APPROVED ARCHITECTURE:
Option A — Deterministic Integrity Spine
Full name: Deterministic Integrity Spine + Signed Evidence Governance
           + Offline-First Supervisor-Worker Architecture
As defined in: 05_ARCHITECTURE_OPTIONS_SIH26228.md (improved v2)
As justified in: 08_ARCHITECTURE_DECISION_PACKET_SIH26228.md

PROJECT-OWNER DECISION: APPROVED
Confirmation method: Verbal in-session confirmation, 2026-09-25
NOTE: The approval block in 08_ARCHITECTURE_DECISION_PACKET_SIH26228.md
      must be updated with this date before that document is archived.

ARCHITECTURE CHANGE CONTROL: ACTIVE (see Section 22)
═══════════════════════════════════════════════════════════════════════
```

## 1.2 What this specification does

This document translates the approved architecture decision into a precise, layered blueprint that eliminates architectural ambiguity. Implementation teams must follow this specification; they must not invent major interfaces, behaviors, or schemas. Gaps and open items are explicitly named; they must not be filled silently.

## 1.3 What this specification does NOT do

- It does NOT authorize implementation. Implementation requires Stage 11 (MVP Implementation Plan) to be produced and approved first.
- It does NOT name final library versions (except hard constraints already established by research: `weights_only=True`, PyTorch ≥2.10.0 floor from XREG-005).
- It does NOT resolve P1 blocking conditions (PRE-01 through PRE-09). Those remain open.
- It does NOT constitute validation evidence for any capability.

## 1.4 Rejection of non-approved alternatives

The following are permanently excluded from this specification. Any implementation agent proposing to include them triggers the architecture change-control process:

- Option B behavioral battery (deferred; DEFERRED_IN_SCOPE at MVP)
- Option C Method Registry / Schema Registry / Config Manager (deferred; post-MVP refactoring targets)
- Blockchain / DLT integration (deferred; GAP-009 pending)
- Aggregate risk score, compromise probability, overall assurance score (ABSOLUTELY PROHIBITED)
- First-box-only label analysis (replaced by all-box structural/geometry validation)
- Fail-open audit chain handling (replaced by fail-closed with ERROR record)
- R01 Fabric client (unconditionally excluded)
- R01 aggregate risk score module (unconditionally excluded)
- Automatic unsafe fallback in PyTorch loading (RC-013 REJECTED)

---

# 2. SYSTEM BOUNDARY

## 2.1 What belongs inside the assurance system

The assurance system boundary contains:

| Layer | Components inside boundary |
|---|---|
| Ingestion | Asset submission interface; format detection; manifest authority |
| C2 — Data Integrity | All-box COCO/YOLO structural/geometry validator (M01); SHA-256 exact duplicate detector (M02); source-concentration statistics (M06); image-level hash floor (M15 hash tier) |
| C3 — Model Security | Model artifact-unit resolver; model SHA-256 identity hasher (REQ-05); ONNX structural validator with path-containment check; safe-loading gate worker (PyTorch weights_only, no fallback) |
| C4 — Provenance/Cryptography | Provenance record builder; signing module; hash-chained audit chain writer |
| C5 — Assurance/Interpretation | Evidence aggregator; C5 finding schema validator; structured finding producer; DEFERRED_IN_SCOPE emitter; T05d non-claim enforcer; UNAVAILABLE propagation enforcer |
| Governance | Reference manager; capability declaration; schema validator |
| Persistence | SQLite evidence store (supervisor-only writes); signed audit log; reference registry |
| Analyst interface | Read-only CLI; evidence export; Dashboard (MVP value feature); Evidence Explorer (MVP value feature); Audit Timeline (MVP value feature); Evidence Bundle Export (MVP value feature); Pipeline Visualization (MVP value feature; time-permitting) |
| Test infrastructure | Hostile fixture suite; synthetic attack generator; validation scenario runner |

## 2.2 What is external to the system

| External element | Relationship |
|---|---|
| Contributed data assets (images, annotation files) | Input — untrusted until assessed |
| Submitted model artifacts (ONNX, PyTorch, TorchScript) | Input — untrusted until assessed |
| Inference records (if organizer-supplied — GAP-011) | Input — untrusted until bound |
| Reference artifacts (if/when established) | Input — enters reference manager only; trust status governed by reference-health protocol R0–R7 |
| Analyst identity / authentication | External — not currently established; policy decision pending (OQ-017) |
| Trusted clock source | External — not currently established (AF-003 open) |
| External checkpoint / tail completeness witness | Deferred — not in MVP |
| Blockchain / distributed ledger | Deferred — GAP-009 pending |
| PDQ near-duplicate component | Deferred — post-MVP spike required |

## 2.3 Explicit out-of-scope items

The following are not supported by this architecture at MVP. Each must appear in the system's capability declaration as explicitly out of scope, not merely absent:

- Behavioral model consistency battery (M07 class) — emits DEFERRED_IN_SCOPE
- PDQ near-duplicate relationship detection (M03-PDQ) — emits DEFERRED_IN_SCOPE
- Statistical drift / OOD detection (M04, M05) — emits DEFERRED_IN_SCOPE
- Reference-relative data comparison (M11) — emits REFERENCE_UNAVAILABLE / BLOCKED until R0–R7 complete
- Activation-space analysis, Neural Cleanse, B3D, ABS, Activation Clustering — emits DEFERRED_IN_SCOPE
- TorchScript ingestion — emits DEFERRED_IN_SCOPE (isolated worker not yet demonstrated on target)
- External tail completeness / checkpoint witness — emits COMPLETENESS_UNAVAILABLE
- Sybil-resistant contributor identity authentication — emits SYBIL_UNRELIABLE (external identity mechanism not established)
- T05d clean-label poisoning detection — emits permanent NON_CLAIM (undetectable under current baseline)

---

# 3. TRUST MODEL

## 3.1 Trusted entities

| Entity ID | Entity | Trust basis | What it is trusted to do |
|---|---|---|---|
| TE-01 | Supervisor process | OS process boundary; runs as privileged service account | Read/write evidence store; hold signing key; write audit chain; control manifest authority |
| TE-02 | Schema validator (supervisor-coded) | Statically compiled into supervisor | Enforce evidence schema; reject noncompliant records before persistence |
| TE-03 | Reference manager | Supervisor component | Manage reference health states; enforce R0–R7 gates; emit REFERENCE_UNAVAILABLE |
| TE-04 | Signing module | Supervisor component; holds private key | Produce provenance binding signatures; maintain sequence state |
| TE-05 | Evidence store (SQLite, local) | Supervisor-only write path; OS ACL-enforced | Persist evidence records, findings, audit events |
| TE-06 | Signing key / HMAC key | Pre-provisioned before operation; stored outside submission pipeline | Cryptographic root of trust for provenance binding |

## 3.2 Untrusted inputs

| Input type | Untrusted because | Entry point |
|---|---|---|
| Contributed data assets | Unknown provenance; may contain hostile content | Ingestion gate → data worker subprocess |
| Submitted model artifacts | May be hostile checkpoints, path-traversal payloads, or resource-exhaustion triggers | Ingestion gate → model worker subprocess |
| Organizer-supplied inference records | Unverified until bound | Ingestion gate → C4 binding only |
| Worker process outputs | Workers are untrusted; their raw output must be schema-validated before supervisor accepts | Supervisor ← worker IPC channel; schema-validated before acceptance |
| Format metadata (filenames, annotation contributor fields) | Self-asserted; Sybil-defeatable | Parsed by workers; identity quality set to UNTRUSTED by default |

## 3.3 Trust anchors

| Anchor ID | Anchor | Location | Compromise consequence |
|---|---|---|---|
| TA-01 | Signing private key (Ed25519) or HMAC secret | Supervisor-accessible key store; not accessible to workers | All provenance bindings unverifiable; requires key rotation and re-signing |
| TA-02 | Supervisor schema validator code | Statically compiled; not runtime-loadable | Noncompliant evidence records could enter store |
| TA-03 | Evidence store OS ACL | OS-level write permission on evidence store directory | Evidence records could be externally tampered |
| TA-04 | Reference health state | Reference manager internal state; not updatable by workers | False HEALTH_VERIFIED could enable invalid reference-relative claims |

Note: XREG-002 (HMAC vs. Ed25519) remains OPEN. If HMAC is selected, TA-01 is a shared secret rather than an asymmetric private key; this changes the non-repudiation property of provenance bindings. If Ed25519 is selected, key generation, storage, and rotation must be explicitly planned in Stage 11.

## 3.4 Trust defaults

| Field | Default value | Promotion condition |
|---|---|---|
| Contributor identity quality | UNTRUSTED | External authenticated identity mechanism (not currently established) |
| Reference health | UNAVAILABLE | R0–R7 gates completed for the declared reference/scope/time |
| Assessment status for any field | UNAVAILABLE / NOT_ASSESSED | Active assessment successfully completes on target host |
| SYBIL_UNRELIABLE flag on T10 | TRUE | C4-supplied TRUSTED identity state received |

---

# 4. TRUST BOUNDARIES

## Boundary B1 — Ingestion gate (external → internal)

| Property | Specification |
|---|---|
| What crosses | Asset file paths; asset metadata; submission manifest |
| Who controls external side | Contributor / organizer |
| Who controls internal side | Supervisor ingestion module |
| Validation required | Manifest integrity; format detection; path normalization; no path traversal into system directories |
| Security property | External assets must not reach any trusted component directly; they enter only through the worker subprocess boundary (B2) |
| Failure behavior | INGESTION_ERROR → evidence record with ERROR status; no asset enters assessment pipeline |

## Boundary B2 — Supervisor / Worker subprocess boundary (trusted → untrusted processing)

| Property | Specification |
|---|---|
| What crosses inbound | Normalized asset path; task specification; resource limits |
| What crosses outbound | Raw assessment result (structured JSON); must be schema-validated before supervisor accepts |
| Who controls supervisor side | Supervisor process (TE-01) |
| Who controls worker side | Worker subprocess (untrusted) |
| Validation required | Schema validation of worker output before any persistence; resource limit enforcement (timeout, memory cap, file-descriptor cap) |
| Security property | Workers cannot write to evidence store, audit chain, or signing key; signing key is inaccessible outside supervisor process; IPC channel is output-only from worker perspective |
| Failure behavior | Worker timeout → LOAD_ERROR / ASSESSMENT_ERROR → propagates to C5 UNAVAILABLE; no CLEAN result; no hang permitted |
| Isolation mechanism | OS subprocess (Python `subprocess` or equivalent); specific isolation mechanism is CONDITIONAL on target host (GAP-001 PRE-01 BLOCKING) |

## Boundary B3 — Evidence store write boundary (supervisor → persistence)

| Property | Specification |
|---|---|
| What crosses | Schema-validated evidence records; findings; audit events; provenance records |
| Who controls | Supervisor (TE-01) exclusively |
| Validation required | Schema validation passes; required fields present; no aggregate risk score field |
| Security property | OS ACL restricts write access to supervisor process account only; no worker can write to evidence store path |
| Failure behavior | Write failure → ERROR logged in audit chain; no silent data loss; no corrupt record accepted |

## Boundary B4 — Analyst read boundary (evidence store → analyst interface)

| Property | Specification |
|---|---|
| What crosses | Evidence records, findings, provenance records, audit events (read-only) |
| Who controls | Analyst interface (CLI, Dashboard) |
| Validation required | Read-only queries only; no evidence-store write path from analyst interface |
| Security property | Analyst interface cannot modify evidence records or audit chain; export is a copy, not a transfer |
| Failure behavior | Missing record → UNAVAILABLE displayed, not hidden |

## Boundary B5 — Signing key boundary (supervisor → signing module)

| Property | Specification |
|---|---|
| What crosses | Evidence record bytes to be signed; returns signature |
| Who controls | Supervisor-only; signing module is a supervisor component |
| Validation required | Key availability confirmed before signing; key material never passed to worker |
| Security property | Workers never receive key material; signing can only be triggered by supervisor code paths |
| Failure behavior | Key unavailable → signing deferred; SIGNING_UNAVAILABLE recorded; no unsigned record silently treated as signed |

---

# 5. END-TO-END LIFECYCLE

The approved dataflow follows this sequence. Each step is described in detail in Section 6 (Component Architecture).

```
[1] SUBMISSION
    Contributor / organizer supplies:
    - data assets (COCO/YOLO annotated images)
    - model artifacts (ONNX, PyTorch, TorchScript)
    - inference records (if organizer-supplied — GAP-011 PENDING)
    - submission manifest
         ↓
[2] INGESTION GATE
    Supervisor: format detection → path normalization → manifest hashing
    → contributor identity set to UNTRUSTED by default
    → asset-unit definition applied (SP-002 BLOCKING)
         ↓
[3] CAPABILITY DECLARATION
    Supervisor: for each asset × method combination:
    → APPLICABLE / UNSUPPORTED / UNAVAILABLE / DEFERRED_IN_SCOPE
    → DEFERRED_IN_SCOPE records emitted immediately for all out-of-scope methods
    → REFERENCE_UNAVAILABLE emitted for all reference-relative methods
         ↓
[4] DATA ASSESSMENT (C2) — worker subprocess(es)
    W-C2a: All-box COCO/YOLO structural/geometry validation (M01)
    W-C2b: SHA-256 exact duplicate detection (M02)
    W-C2c: Source-concentration statistics (M06) — SYBIL_UNRELIABLE default
    W-C2d: Image-level hash floor (M15 hash tier)
    → Each worker produces a raw assessment result (structured JSON)
    → Supervisor schema-validates each result
    → COVERAGE_GAP_CLEAN_LABEL NON_CLAIM required on every C2 record
    → Evidence records written to store by supervisor
         ↓
[5] MODEL ASSESSMENT (C3) — worker subprocess(es)
    W-C3a: Artifact-unit resolver → ARTIFACT_UNIT_AMBIGUOUS if unit undefined
    W-C3b: SHA-256 model artifact identity (REQ-05)
    W-C3c: ONNX structural validator + external-data path containment
    W-C3d: Safe-loading gate (PyTorch weights_only=True, no fallback)
    → access_mode non-nullable in every C3 evidence bundle header
    → COVERAGE_GAP_CLEAN_LABEL NON_CLAIM required on every C3 record
    → Behavioral battery emits DEFERRED_IN_SCOPE (reference UNAVAILABLE)
    → Evidence records written to store by supervisor
         ↓
[6] PROVENANCE BINDING (C4)
    Supervisor:
    → Canonicalize evidence record(s) (SP-003 vocabulary contract BLOCKING)
    → Build provenance record: artifact digest + evidence record digest + timestamp + sequence state
    → Add PF-002 non-claim (digest matching ≠ causal execution proof)
    → Sign record (signing module — XREG-002 BLOCKING)
    → Append to hash-chained audit trail (fail-closed)
    → Write signed provenance record to evidence store
         ↓
[7] ASSURANCE INTERPRETATION (C5)
    Supervisor (C5 interpretation rule engine):
    → Consume C2 evidence, C3 evidence, C4 binding outcomes
    → Map to five-layer finding:
      {DETECTION_STATUS, INTERPRETATION_STATUS, APPLICABILITY_STATUS,
       RAW_SIGNAL, REFERENCE_HEALTH, LIMITATIONS, NON_CLAIMS}
    → UNAVAILABLE propagates without conversion
    → C6 ERROR → C5 UNAVAILABLE/NO_DECISION (no compression)
    → No scalar risk score emitted at any path
    → Multi-detector DEPENDENCY_DECLARATION field set
    → Write C5 structured finding to evidence store
         ↓
[8] ANALYST INTERFACE
    Read-only CLI and/or Dashboard:
    → Display findings with UNAVAILABLE, DEFERRED_IN_SCOPE, NOT_ASSESSED visible
    → Evidence Explorer: finding → evidence record → source asset → hash → audit event
    → Audit Timeline: lifecycle events in sequence
    → Evidence Bundle Export: structured ZIP
    → Pipeline Visualization: execution state only (no assurance confidence)
         ↓
[9] AUDIT
    → Every supervisor action emits an audit event (hash-chained, fail-closed)
    → Analyst disposition recorded as an audit event if/when analyst acts
    → Audit trail readable via analyst interface (read-only)
    → COMPLETENESS_UNAVAILABLE if tail completeness witness absent
```

---

# 6. COMPONENT ARCHITECTURE

## COMP-SUP — Supervisor Orchestrator

| Field | Specification |
|---|---|
| **Component ID** | COMP-SUP |
| **Name** | Supervisor Orchestrator |
| **Responsibility** | Sole authority over evidence store writes, signing key, manifest, and audit chain. Receives and schema-validates all worker outputs. Orchestrates the end-to-end pipeline. Emits DEFERRED_IN_SCOPE records directly. Enforces all schema invariants. |
| **Inputs** | Submission manifest; asset paths; worker raw assessment results (via IPC); analyst actions |
| **Outputs** | Schema-validated evidence records (written to store); provenance records; audit events; structured findings; DEFERRED_IN_SCOPE records; UNAVAILABLE propagation events; analyst interface data |
| **Dependencies** | COMP-SCHEMA (schema validator); COMP-SIGN (signing module); COMP-STORE (evidence store); COMP-REF (reference manager); COMP-AUDIT (audit chain writer); COMP-C5 (C5 interpretation engine) |
| **Trust level** | Trusted (TE-01) |
| **Failure behavior** | Worker failure → ASSESSMENT_ERROR in evidence record → C5 UNAVAILABLE; evidence store write failure → ERROR in audit chain; signing failure → SIGNING_UNAVAILABLE in record; no silent failure |
| **Security requirements** | Signing key accessible only to supervisor process; OS ACL restricts evidence store path; no worker code may execute in supervisor process context; no runtime module loading from submitted assets |
| **Evidence produced** | Orchestration audit event per pipeline run; worker-result acceptance/rejection events |
| **Consumers** | COMP-C5 (reads evidence records); COMP-IFACE (reads from evidence store) |
| **Interface** | Internal: direct function calls to COMP-SIGN, COMP-STORE, COMP-SCHEMA, COMP-C5; IPC (subprocess pipe or temp-file handoff) to/from workers |

## COMP-SCHEMA — Schema Validator

| Field | Specification |
|---|---|
| **Component ID** | COMP-SCHEMA |
| **Name** | Schema Validator |
| **Responsibility** | Validates every worker output and every evidence record against the evidence schema before persistence. Rejects records missing required fields. Specifically enforces: COVERAGE_GAP_CLEAN_LABEL present on C2 AND C3 records; access_mode non-nullable on C3 records; no risk_score or aggregate_assurance field at any path; DEPENDENCY_DECLARATION present when multiple detectors fire; PF-002 non-claim present on all provenance records. |
| **Inputs** | Raw worker output (JSON); evidence records before persistence |
| **Outputs** | VALID / INVALID + rejection reason |
| **Dependencies** | Frozen schema definition (requires SP-003 vocabulary contract — PRE-04 BLOCKING) |
| **Trust level** | Trusted (supervisor component) |
| **Failure behavior** | Schema violation → record rejected → SCHEMA_VIOLATION event in audit chain; rejected record does not enter evidence store |
| **Security requirements** | Schema definition is statically compiled or loaded from a trusted location at startup; not overrideable by submitted assets |
| **Evidence produced** | Audit event for each rejection |
| **Consumers** | COMP-SUP |
| **Interface** | Synchronous validation call within supervisor process |

## COMP-W-C2A — Data Structural Validator Worker

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C2A |
| **Name** | Data Structural Validator Worker (M01) |
| **Responsibility** | All-box COCO/YOLO structural and geometry validation. Checks every annotation box (not only the first). Validates format-specific field presence, coordinate geometry, class-ID range, area computation consistency (no invalid `area = bbox_w × bbox_h` assumption), task-variant field completeness. Rejects or flags malformed inputs rather than skipping. |
| **Inputs** | Asset path (annotation file); format declaration (COCO or YOLO); task-variant declaration; resource limits |
| **Outputs** | Raw evidence record: per-violation type, per-box location, structural pass/fail, LIMITATIONS, NON_CLAIMS including COVERAGE_GAP_CLEAN_LABEL |
| **Dependencies** | R27 COCO API (ADOPT/ADAPT, BSD license, C extension pre-staged); YOLO parser (REIMPLEMENT); resource caps (timeout, memory limit) |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Timeout → ASSESSMENT_ERROR; malformed input → FORMAT_VIOLATION evidence record; out-of-scope task variant → DEFERRED_IN_SCOPE |
| **Security requirements** | Subprocess isolation; no file-system writes outside assigned temp directory; no network access; resource capped |
| **Evidence produced** | C2 structural evidence record per asset |
| **Consumers** | COMP-SUP (receives via IPC, schema-validates, writes to COMP-STORE) |
| **Interface** | Subprocess invocation; output via stdout JSON or named temp file |

## COMP-W-C2B — Exact Duplicate Detector Worker

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C2B |
| **Name** | Exact Duplicate Detector Worker (M02) |
| **Responsibility** | SHA-256 exact duplicate detection across the submitted corpus. Produces per-file digests and exact-match pairs. No near-duplicate detection (deferred). No flooding attribution claim. |
| **Inputs** | Asset file paths; resource limits |
| **Outputs** | Per-file SHA-256 digest; exact-duplicate pair list; LIMITATIONS (exact only, no near-duplicate), NON_CLAIMS |
| **Dependencies** | Python stdlib `hashlib` (no external package); resource caps |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Timeout or resource exhaustion → ASSESSMENT_ERROR |
| **Security requirements** | Subprocess isolation; no network; resource capped; large-corpus denial-of-service risk mitigated by timeout |
| **Evidence produced** | C2 exact-duplicate evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation; output via stdout JSON or named temp file |

## COMP-W-C2C — Source Concentration Worker

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C2C |
| **Name** | Source Concentration Statistics Worker (M06) |
| **Responsibility** | Computes HHI (Herfindahl-Hirschman Index), Shannon entropy, and per-source share from contributor/batch metadata. Outputs raw statistics only — no aggregate risk score. Sets SYBIL_UNRELIABLE=TRUE by default. Promotes to SYBIL_UNRELIABLE=FALSE only if C4 supplies TRUSTED identity state (not currently established). |
| **Inputs** | Contributor/source metadata fields; C4 identity trust state (TRUSTED / UNTRUSTED / UNAVAILABLE — default UNTRUSTED) |
| **Outputs** | HHI, entropy, per-source share counts; SYBIL_UNRELIABLE flag; identity_quality field; LIMITATIONS, NON_CLAIMS |
| **Dependencies** | Python stdlib math; no external package |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Missing metadata → identity_quality=UNAVAILABLE; SYBIL_UNRELIABLE=TRUE maintained regardless |
| **Security requirements** | Subprocess isolation; contributor metadata treated as untrusted strings |
| **Evidence produced** | C2 concentration evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-W-C2D — Image-Level Hash Worker

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C2D |
| **Name** | Image-Level Hash Worker (M15 hash tier) |
| **Responsibility** | SHA-256 hash per image file (byte identity only). Optionally FFT peak measurement as a secondary signal. COVERAGE_GAP_CLEAN_LABEL must appear in every record. No backdoor or attack attribution claim. |
| **Inputs** | Image file paths; resource limits |
| **Outputs** | Per-image SHA-256 digest; optional FFT peak measure; COVERAGE_GAP_CLEAN_LABEL NON_CLAIM; LIMITATIONS |
| **Dependencies** | Python stdlib `hashlib`; optional numpy for FFT |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Timeout or image decode failure → ASSESSMENT_ERROR per file |
| **Security requirements** | Subprocess isolation; image decode libraries pre-staged and version-pinned |
| **Evidence produced** | C2 image-level evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-W-C3A — Artifact-Unit Resolver

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C3A |
| **Name** | Artifact-Unit Resolver |
| **Responsibility** | Given a model artifact path and format, resolves the complete set of files constituting the artifact-unit (per SP-002 / GAP-004 definition). For ONNX with external tensor data: all `.onnx.data` and referenced external binary files are included. Emits ARTIFACT_UNIT_AMBIGUOUS when the unit cannot be frozen (e.g., external-data file manifest inconsistency). |
| **Inputs** | Model artifact path; format declaration; artifact-unit definition table (from SP-002 — PRE-03 BLOCKING) |
| **Outputs** | Resolved artifact-unit file list; ARTIFACT_UNIT_AMBIGUOUS flag if unit undefined or ambiguous |
| **Dependencies** | SP-002 artifact-unit definition (PRE-03 BLOCKING); `onnx` package for ONNX external-data manifest parsing |
| **Trust level** | Untrusted subprocess (receives model paths, does not load model code) |
| **Failure behavior** | ARTIFACT_UNIT_AMBIGUOUS emitted; hashing blocked until unit is frozen |
| **Security requirements** | Path traversal prevention: all resolved file paths must be within the submitted asset directory; ONNX external-data path containment enforced here |
| **Evidence produced** | Artifact-unit manifest (inputs to C3B) |
| **Consumers** | COMP-W-C3B; COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-W-C3B — Model Identity Hasher

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C3B |
| **Name** | Model Artifact Identity Hasher (REQ-05) |
| **Responsibility** | Streams the resolved artifact-unit bytes through SHA-256. Produces MATCH / DIFFERENT / UNAVAILABLE against a stored reference digest if one exists. Carries PF-002 non-claim: MATCH ≠ SAFE ≠ SEMANTICALLY_EQUIVALENT ≠ CAUSAL_EXECUTION_PROOF on every record. Reference digest absent → REFERENCE_UNAVAILABLE (not CLEAN). |
| **Inputs** | Artifact-unit file list (from COMP-W-C3A); reference digest (from COMP-REF, may be UNAVAILABLE) |
| **Outputs** | SHA-256 digest(s) per artifact-unit; MATCH / DIFFERENT / UNAVAILABLE; PF-002 non-claim; LIMITATIONS; NON_CLAIMS |
| **Dependencies** | Python stdlib `hashlib`; artifact-unit from COMP-W-C3A |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | File read error → UNAVAILABLE; reference absent → REFERENCE_UNAVAILABLE |
| **Security requirements** | Subprocess isolation; reads only resolved artifact-unit paths; no model code execution |
| **Evidence produced** | C3 artifact identity evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-W-C3C — ONNX Structural Validator

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C3C |
| **Name** | ONNX Structural Validator |
| **Responsibility** | Validates ONNX protobuf structure. Checks external-data path containment: all external data paths must be relative and contained within the declared artifact directory; absolute paths and path-traversal patterns (e.g., `../`) are rejected with ONNX_PATH_CONTAINMENT_VIOLATION. ONNX structural validity does NOT imply semantic equivalence with a PyTorch source model (EF-004 non-claim required). |
| **Inputs** | ONNX file path; external-data manifest (from COMP-W-C3A) |
| **Outputs** | STRUCTURAL_VALID / STRUCTURAL_INVALID / ONNX_PATH_CONTAINMENT_VIOLATION; EF-004 non-claim; LIMITATIONS |
| **Dependencies** | `onnx` Python package (pre-staged); not ONNX Runtime (ORT is deferred) |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Parse error → STRUCTURAL_INVALID; path violation → ONNX_PATH_CONTAINMENT_VIOLATION → pipeline BLOCKED for this model |
| **Security requirements** | Subprocess isolation with memory and timeout caps; `onnx.checker.check_model` only — no execution; external-data path sanitization before any file access |
| **Evidence produced** | C3 ONNX structural evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-W-C3D — Safe-Loading Gate Worker

| Field | Specification |
|---|---|
| **Component ID** | COMP-W-C3D |
| **Name** | Safe-Loading Gate Worker (REQ-07) |
| **Responsibility** | Loads PyTorch model artifacts inside an isolated subprocess using `weights_only=True`. No fallback to `weights_only=False` under any exception path (RC-013 REJECTED). Resource-capped: timeout, memory limit, file-descriptor limit. Emits LOAD_SUCCESS / LOAD_BLOCKED / LOAD_ERROR. LOAD_BLOCKED does NOT imply the model is malicious (ANOMALY ≠ PROVEN ATTACK). |
| **Inputs** | Model artifact path; format declaration (PyTorch); resource limits |
| **Outputs** | LOAD_SUCCESS / LOAD_BLOCKED / LOAD_ERROR; containment evidence; LIMITATIONS (safe loading not complete boundary); NON_CLAIMS |
| **Dependencies** | `torch` Python package ≥2.10.0 (pre-staged, CPU-only); no fallback path; no Ultralytics automatic fallback (RC-013 REJECTED) |
| **Trust level** | Untrusted subprocess |
| **Failure behavior** | Timeout → LOAD_ERROR; OOM → LOAD_ERROR; hostile pickle exception → LOAD_BLOCKED; all three propagate to C5 UNAVAILABLE/NO_DECISION via supervisor |
| **Security requirements** | Subprocess isolation with strict resource caps; signing key inaccessible from this process; no network access; no filesystem writes outside assigned temp directory; hostile fixture test required before any claim |
| **Evidence produced** | C3 safe-loading gate evidence record |
| **Consumers** | COMP-SUP |
| **Interface** | Subprocess invocation |

## COMP-C4 — Provenance Record Builder and Signing Module

| Field | Specification |
|---|---|
| **Component ID** | COMP-C4 |
| **Name** | Provenance Record Builder / Signing Module |
| **Responsibility** | Builds provenance records binding artifact digests + evidence record digests + timestamps + sequence state. Signs using the approved mechanism (XREG-002 PENDING). Maintains durable sequence state for replay protection. Appends signed record to hash-chained audit trail. Adds PF-002 non-claim on every record: signed digest commitment ≠ causal execution proof ≠ behavioral safety. |
| **Inputs** | Artifact-unit digest (from C3B); C2/C3 evidence record digests; signing key (from TE-06); sequence state; timestamp |
| **Outputs** | Signed provenance record; sequence-state update; audit event |
| **Dependencies** | XREG-002 decision (PRE-02 BLOCKING); SP-004 crypto profile (PRE-08 BLOCKING); SP-003 vocabulary contract (PRE-04 BLOCKING); SP-006 C3→C4 adapter schema (PRE-09 BLOCKING) |
| **Trust level** | Trusted (supervisor component — COMP-SUP) |
| **Failure behavior** | Key unavailable → SIGNING_UNAVAILABLE in record (not silently omitted); sequence state corruption → fail-closed; no unsigned record is silently treated as signed |
| **Security requirements** | Private key / HMAC key never passed to any worker; signing module executes in supervisor context only; sequence nonce non-reusable |
| **Evidence produced** | Signed provenance record; audit chain entry |
| **Consumers** | COMP-STORE; COMP-AUDIT; COMP-C5 |
| **Interface** | Direct function call within supervisor process |

## COMP-C5 — C5 Interpretation Engine

| Field | Specification |
|---|---|
| **Component ID** | COMP-C5 |
| **Name** | C5 Assurance Interpretation Engine |
| **Responsibility** | Consumes C2 evidence, C3 evidence, C4 binding outcomes. Produces structured five-layer findings. Enforces: UNAVAILABLE propagation (C6 ERROR → C5 UNAVAILABLE/NO_DECISION, no compression); ANOMALY_DETECTED ≠ PROVEN_MALICIOUS (must appear as machine-readable non-claim); T05d COVERAGE_GAP non-claim on every applicable finding; multi-detector DEPENDENCY_DECLARATION populated; no scalar risk score field emitted at any path; reference health state from COMP-REF passed through unchanged. |
| **Inputs** | C2 evidence records; C3 evidence records; C4 binding records; reference health state (from COMP-REF); access-mode declaration (from C3 bundle header) |
| **Outputs** | C5 structured finding per asset/method: {DETECTION_STATUS, INTERPRETATION_STATUS, APPLICABILITY_STATUS, RAW_SIGNAL, REFERENCE_HEALTH, LIMITATIONS, NON_CLAIMS, DEPENDENCY_DECLARATION, ANALYST_DISPOSITION_PROMPT} |
| **Dependencies** | Frozen evidence schema (PRE-04 BLOCKING); SP-003 vocabulary contract (PRE-04 BLOCKING) |
| **Trust level** | Trusted (supervisor component) |
| **Failure behavior** | Missing upstream evidence → UNAVAILABLE propagated; no field defaults to CLEAN or positive assurance state |
| **Security requirements** | Cannot produce a scalar risk score; cannot suppress UNAVAILABLE states |
| **Evidence produced** | C5 structured finding records |
| **Consumers** | COMP-STORE; COMP-IFACE |
| **Interface** | Direct function call within supervisor process |

## COMP-REF — Reference Manager

| Field | Specification |
|---|---|
| **Component ID** | COMP-REF |
| **Name** | Reference Manager |
| **Responsibility** | Maintains the health state of each reference artifact. Enforces R0–R7 gate rules before emitting HEALTH_VERIFIED. Emits REFERENCE_UNAVAILABLE for all reference-relative methods when no reference has completed R0–R7 (current state: all references UNAVAILABLE). Maintains FORMAT_ASSET vs. HEALTH_VERIFIED distinction: COCO val2017 is a FORMAT_ASSET only; using it as HEALTH_VERIFIED triggers REFERENCE_CATEGORY_VIOLATION. Triggers STALE_SUSPECTED on invalidating events. |
| **Inputs** | Reference artifact registry; health gate completion records; staleness events |
| **Outputs** | HEALTH_VERIFIED / HEALTH_UNVERIFIED / CONTAMINATION_SUSPECTED / STALE_SUSPECTED / UNAVAILABLE per reference |
| **Dependencies** | Reference artifact registry (local); R0–R7 gate procedure (SP-001 output) |
| **Trust level** | Trusted (supervisor component) |
| **Failure behavior** | Gate not completed → HEALTH_UNVERIFIED or UNAVAILABLE, never promoted to HEALTH_VERIFIED; staleness event → STALE_SUSPECTED |
| **Security requirements** | Health state not writable by workers or analyst interface; only supervisor may update reference health |
| **Evidence produced** | Reference health state passed to COMP-C5; audit event on state transition |
| **Consumers** | COMP-C5; COMP-W-C3B |
| **Interface** | Direct function call within supervisor process |

## COMP-AUDIT — Audit Chain Writer

| Field | Specification |
|---|---|
| **Component ID** | COMP-AUDIT |
| **Name** | Audit Chain Writer |
| **Responsibility** | Appends supervisor-produced audit events to the hash-chained audit trail. Each event includes: previous-event digest (hash chain); event type; timestamp; payload digest; sequence number. Fail-closed: on chain corruption → ERROR record emitted; no reset-to-empty; no silent data loss. |
| **Inputs** | Audit event payloads from COMP-SUP |
| **Outputs** | Hash-chained audit trail entries |
| **Dependencies** | Python stdlib `hashlib`; audit trail storage (SQLite or append-only log file) |
| **Trust level** | Trusted (supervisor component) |
| **Failure behavior** | Write failure → ERROR event recorded; chain corruption → CHAIN_CORRUPT event; no fail-open path |
| **Security requirements** | Only supervisor can write to audit trail; no external reset or truncation allowed |
| **Evidence produced** | Audit trail (temporal ordering, insertion/deletion detection) |
| **Consumers** | COMP-IFACE (read-only) |
| **Interface** | Direct function call within supervisor process |

## COMP-STORE — Evidence Store

| Field | Specification |
|---|---|
| **Component ID** | COMP-STORE |
| **Name** | Evidence Store (SQLite, local) |
| **Responsibility** | Persists all evidence records, structured findings, provenance records, audit events, and reference health states. Supervisor-only write path. Read-only access for analyst interface. WAL mode enabled (following R17 storage patterns). |
| **Inputs** | Schema-validated records from COMP-SUP |
| **Outputs** | Query responses to COMP-IFACE; no direct output to workers |
| **Dependencies** | Python stdlib `sqlite3`; R17 storage patterns (EXTRACT, MIT license) |
| **Trust level** | Trusted (supervised by COMP-SUP via OS ACL) |
| **Failure behavior** | Write failure → ERROR in COMP-AUDIT; no partial writes accepted; WAL ensures atomic commits |
| **Security requirements** | OS file ACL restricts write access to supervisor process account; no worker process can reach the evidence store path |
| **Evidence produced** | N/A (persistence layer) |
| **Consumers** | COMP-IFACE; COMP-C5 (reads evidence for interpretation); COMP-C4 (reads digests for binding) |
| **Interface** | SQLite Python API within supervisor process; read-only queries from COMP-IFACE |

## COMP-IFACE — Analyst Interface

| Field | Specification |
|---|---|
| **Component ID** | COMP-IFACE |
| **Name** | Analyst Interface (CLI + MVP value features) |
| **Responsibility** | Read-only access to evidence store. Displays findings with UNAVAILABLE, DEFERRED_IN_SCOPE, NOT_ASSESSED visible — never hidden or converted to positive assurance states. MVP value features: Dashboard (evidence-store-fed), Evidence Explorer (finding → evidence → asset → hash → audit event navigation), Audit Timeline, Evidence Bundle Export, Pipeline Visualization (execution state only, no assurance confidence). |
| **Inputs** | Evidence store queries (read-only); analyst disposition input (recorded as audit event, no evidence modification) |
| **Outputs** | Terminal display; JSON/CSV export; structured export ZIP |
| **Dependencies** | COMP-STORE (read-only); Python stdlib |
| **Trust level** | Untrusted relative to evidence store (cannot write evidence records) |
| **Failure behavior** | Missing evidence → displays UNAVAILABLE; store unavailable → interface error displayed |
| **Security requirements** | No evidence-record modification; export is a copy; analyst disposition recorded in COMP-AUDIT, not stored in evidence records themselves |
| **Evidence produced** | Analyst disposition audit events (via COMP-AUDIT) |
| **Consumers** | Human analyst |
| **Interface** | CLI commands; optional lightweight web or terminal UI for Dashboard |

## COMP-FIX — Hostile Fixture Suite and Synthetic Attack Generator

| Field | Specification |
|---|---|
| **Component ID** | COMP-FIX |
| **Name** | Hostile Fixture Suite and Synthetic Attack Generator |
| **Responsibility** | Provides reproducible ground-truth fixtures for testing and validation. Required fixture types: (a) hostile model checkpoints (malicious pickle, OOM trigger, timeout trigger); (b) ONNX path-traversal fixture (absolute path in external-data manifest); (c) archive bomb; (d) symlink escape; (e) all-box COCO/YOLO geometry violations; (f) exact duplicate pairs; (g) non-duplicate control pairs; (h) synthetic SYBIL fragmentation corpus; (i) UNAVAILABLE propagation injection points at each pipeline layer. All synthetic fixtures carry SYNTHETIC_FIXTURE provenance label. |
| **Inputs** | Seed parameters (pinned for reproducibility) |
| **Outputs** | Fixture files with manifests; SYNTHETIC provenance label on all fixture-derived records |
| **Dependencies** | Methodology from REUSE-007 (REIMPLEMENT — R01 license precludes code copy) |
| **Trust level** | Test infrastructure only; fixtures must never enter a production evidence chain without SYNTHETIC label |
| **Failure behavior** | Fixture generation failure → test suite ERROR; not a pipeline concern |
| **Security requirements** | Hostile fixtures stored in isolated directory; not accessible to production pipeline paths |
| **Evidence produced** | Test fixture manifest; regression test records |
| **Consumers** | Validation and red-team phases |
| **Interface** | CLI invocation (separate from production pipeline) |

---

# 7. ARTIFACT / DATA MODEL

## 7.1 Artifact classes

### AC-01 — Dataset Assets (Data submitted for assessment)

| Property | Specification |
|---|---|
| **Identity** | Per-file SHA-256 digest (M02); artifact-unit = individual file unless multi-file bundle (SP-002 BLOCKING) |
| **Lifecycle** | Submitted → ingested → assessed → evidence-bound → findings-produced |
| **Ownership** | Contributor; supervisor takes custody at ingestion gate |
| **Trust status** | UNTRUSTED at ingestion; trust status not upgraded by assessment results |
| **Persistence** | Original files remain in submitted asset directory; not copied into evidence store |
| **Hashing** | SHA-256 per file (COMP-W-C2B, COMP-W-C2D); binding recorded in provenance record (COMP-C4) |
| **Validation** | COMP-W-C2A structural validation |

### AC-02 — Annotation Files (COCO JSON or YOLO TXT)

| Property | Specification |
|---|---|
| **Identity** | Filename + SHA-256 |
| **Format coverage** | COCO (supported); YOLO detection/segmentation/pose/OBB (scope: GAP-013/GAP-008 PENDING — PRE-05 BLOCKING) |
| **Trust status** | UNTRUSTED; annotation content is assessed, not trusted |
| **Validation** | All-box structural/geometry (COMP-W-C2A) |

### AC-03 — Model Artifacts

| Property | Specification |
|---|---|
| **Identity** | Artifact-unit SHA-256 (all files in the unit per SP-002) |
| **Formats** | ONNX (supported); PyTorch `.pt/.pth` (supported, `weights_only=True`); TorchScript (DEFERRED_IN_SCOPE — isolated worker not demonstrated on target) |
| **Artifact-unit** | ONNX: main `.onnx` + all external tensor data files; PyTorch: as per SP-002 definition (PRE-03 BLOCKING); ARTIFACT_UNIT_AMBIGUOUS if unit undefined |
| **Trust status** | UNTRUSTED; processed only in isolated worker subprocess |
| **Hashing** | SHA-256 over complete artifact-unit (COMP-W-C3B) |
| **Validation** | Structural check (COMP-W-C3C); safe-loading gate (COMP-W-C3D) |

### AC-04 — Inference Records (if organizer-supplied — GAP-011 PENDING)

| Property | Specification |
|---|---|
| **Identity** | Record digest bound by C4 provenance record |
| **Lifecycle** | Supplied by organizer (or deferred if GAP-011 not resolved) → ingested → digest computed → C4-bound |
| **Trust status** | UNTRUSTED; binding does not establish causal execution (PF-002) |
| **Persistence** | Original record file; digest + binding in provenance record |

### AC-05 — Evidence Records

| Property | Specification |
|---|---|
| **Identity** | UUID per record; schema version field |
| **Lifecycle** | Produced by workers → schema-validated → supervisor-written to evidence store |
| **Ownership** | Supervisor; workers produce raw output only |
| **Trust status** | Trusted once schema-validated and supervisor-written |
| **Persistence** | Evidence store (COMP-STORE, SQLite); immutable after writing |
| **Schema requirements** | All required fields present; COVERAGE_GAP_CLEAN_LABEL on C2/C3 records; access_mode non-nullable on C3 records; no risk_score field; LIMITATIONS and NON_CLAIMS non-null |
| **Retention** | Policy decision pending (OQ-018) |

### AC-06 — Provenance Records

| Property | Specification |
|---|---|
| **Identity** | UUID; bound to artifact-unit digest + evidence record digests + sequence number |
| **Lifecycle** | Built by COMP-C4 after evidence records are written; signed; appended to audit chain |
| **Integrity** | Cryptographic signature (XREG-002 PENDING) + PF-002 non-claim field |
| **Non-claim** | signed_commitment ≠ causal_execution_proof ≠ behavioral_safety ≠ semantic_equivalence — machine-readable on every record |
| **Retention** | Policy decision pending (OQ-018) |

### AC-07 — Audit Events

| Property | Specification |
|---|---|
| **Identity** | Sequential event ID; hash of previous event (chain link) |
| **Lifecycle** | Emitted by supervisor for every significant pipeline action; appended to audit chain (fail-closed) |
| **Integrity** | Hash-chained; insertion/deletion detectable |
| **Tail completeness** | COMPLETENESS_UNAVAILABLE — external checkpoint/witness not in MVP |
| **Analyst identity** | Not currently recorded (OQ-018 / AF-003 open) |

### AC-08 — Structured Findings (C5)

| Property | Specification |
|---|---|
| **Identity** | UUID; linked to asset UUID and method ID |
| **Schema** | {DETECTION_STATUS, INTERPRETATION_STATUS, APPLICABILITY_STATUS, RAW_SIGNAL, REFERENCE_HEALTH, LIMITATIONS, NON_CLAIMS, DEPENDENCY_DECLARATION, ANALYST_DISPOSITION_PROMPT} |
| **Lifecycle** | Produced by COMP-C5 after evidence records and provenance records are written |
| **Non-claims** | T05d COVERAGE_GAP permanent; ANOMALY ≠ PROVEN_MALICIOUS on every finding where detection signal exists; global backdoor absence NOT established on any model finding |
| **Immutability** | Immutable after supervisor write; analyst dispositions are separate audit events |

### AC-09 — DEFERRED_IN_SCOPE Records

| Property | Specification |
|---|---|
| **Purpose** | Explicit capability declaration for every out-of-scope method; makes deferred capabilities visible to the analyst rather than silently absent |
| **Emitted by** | Supervisor (COMP-SUP), not workers |
| **Required for** | Behavioral battery; PDQ near-duplicate; statistical drift/OOD; M11 reference-relative; TorchScript loading; all heavyweight backdoor methods; tail completeness; Sybil-resistant T10 |
| **Persistence** | Evidence store (same schema as evidence records, with status = DEFERRED_IN_SCOPE) |

---

# 8. ASSESSMENT ORCHESTRATION

## 8.1 Orchestration decision logic

For each submitted asset × supported method pair, the supervisor applies the following decision tree before dispatching a worker:

```
IS the format supported?
  NO → emit UNSUPPORTED evidence record
  YES →
    IS the method in MVP scope?
      NO → emit DEFERRED_IN_SCOPE record (e.g., behavioral battery, PDQ, TorchScript)
      YES →
        IS the artifact-unit defined? (SP-002)
          NO → emit ARTIFACT_UNIT_AMBIGUOUS; block hash-dependent methods
          YES →
            IS the required reference available and HEALTH_VERIFIED? (if method is reference-relative)
              NO → emit REFERENCE_UNAVAILABLE (never CLEAN)
              YES (future state — currently UNAVAILABLE for all references) →
                IS the required access mode available? (GAP-003)
                  NO (access insufficient) → emit ASSESSMENT_UNAVAILABLE
                  YES →
                    dispatch worker subprocess
                    schema-validate raw worker output
                      SCHEMA_VALID → accept → write evidence record
                      SCHEMA_INVALID → reject → write SCHEMA_VIOLATION event
                    worker timeout/error → ASSESSMENT_ERROR → C5 UNAVAILABLE
```

## 8.2 Assessment states per method

| State | Meaning |
|---|---|
| APPLICABLE | Method dispatched; worker executing or complete |
| COMPLETED | Worker returned SCHEMA_VALID result; evidence record written |
| ASSESSMENT_ERROR | Worker timed out, crashed, or returned unparseable output; C5 receives UNAVAILABLE |
| UNAVAILABLE | Required prerequisite absent (reference, access, artifact-unit) |
| UNSUPPORTED | Format/task-variant combination not in declared implementation scope |
| DEFERRED_IN_SCOPE | Method is a known project capability (listed) but not included in MVP; explicit record emitted |
| ARTIFACT_UNIT_AMBIGUOUS | Artifact-unit cannot be defined; hash-dependent methods blocked |
| SCHEMA_VIOLATION | Worker output failed schema validation; evidence record not written; audit event written |

## 8.3 Format-method applicability table

| Method | COCO data | YOLO data | ONNX model | PyTorch model | TorchScript model |
|---|---|---|---|---|---|
| M01 Structural/geometry validation | APPLICABLE | APPLICABLE (scope: PRE-05) | N/A | N/A | N/A |
| M02 SHA-256 exact duplicate | APPLICABLE | APPLICABLE | N/A | N/A | N/A |
| M06 Source concentration | APPLICABLE | APPLICABLE | N/A | N/A | N/A |
| M15 Image-level hash | APPLICABLE | APPLICABLE | N/A | N/A | N/A |
| Model artifact identity (SHA-256) | N/A | N/A | APPLICABLE | APPLICABLE | DEFERRED_IN_SCOPE |
| ONNX structural validation | N/A | N/A | APPLICABLE | N/A | N/A |
| Safe-loading gate | N/A | N/A | N/A | APPLICABLE | DEFERRED_IN_SCOPE |
| Behavioral battery | N/A | N/A | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE |
| PDQ near-duplicate | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE | N/A | N/A | N/A |
| M11 Reference-relative comparison | REFERENCE_UNAVAILABLE | REFERENCE_UNAVAILABLE | N/A | N/A | N/A |
| Statistical drift/OOD | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE | DEFERRED_IN_SCOPE | N/A |

---

# 9. EVIDENCE / FINDING ARCHITECTURE

## 9.1 Evidence chain

```
[RAW WORKER OUTPUT]
      |
      | (schema validation by COMP-SCHEMA)
      ↓
[C2 / C3 EVIDENCE RECORD]
  Fields: asset_id, method_id, schema_version, assessment_status,
          raw_signal, access_mode (C3 required), artifact_unit_id (C3),
          coverage_gap_clean_label (NON_CLAIM — required on C2+C3),
          limitations, non_claims, dependency_declaration,
          assessment_timestamp, worker_id
      |
      | (C4 binding by COMP-C4)
      ↓
[PROVENANCE RECORD]
  Fields: provenance_id, artifact_unit_digest(s), evidence_record_digest(s),
          signing_key_id, signature, sequence_number, replay_nonce,
          pf_002_non_claim: "digest_match ≠ causal_execution_proof",
          timestamp
      |
      | (C5 interpretation by COMP-C5)
      ↓
[C5 STRUCTURED FINDING]
  Fields: finding_id, asset_id, method_id,
          detection_status, interpretation_status, applicability_status,
          raw_signal (pass-through from evidence record),
          reference_health (from COMP-REF),
          limitations (non-suppressible), non_claims (non-suppressible),
          dependency_declaration,
          analyst_disposition_prompt: {ACCEPT, ACCEPT_WITH_CONTEXT,
            ESCALATE, CONTAIN_HOLD, OVERRIDE, UNAVAILABLE_NO_DECISION}
      |
      | (analyst interaction — recorded as audit event, does not modify finding)
      ↓
[ANALYST DISPOSITION AUDIT EVENT]
  Fields: event_id, finding_id, disposition_selected, analyst_id (UNAVAILABLE until auth established),
          rationale_text, timestamp, chain_link_hash
```

## 9.2 Separation enforcement

The following separations must be enforced architecturally and cannot be violated by any implementation agent:

| Separation | Enforcement mechanism |
|---|---|
| RAW SIGNAL ≠ INTERPRETATION | Evidence records carry raw_signal; C5 produces interpretation_status separately |
| INTERPRETATION ≠ APPLICABILITY | interpretation_status and applicability_status are separate schema fields |
| DETECTION ≠ ATTRIBUTION | ANOMALY_DETECTED ≠ PROVEN_MALICIOUS must appear as NON_CLAIM field |
| REFERENCE_HEALTH ≠ ASSESSMENT_RESULT | reference_health is an input from COMP-REF, not derived from assessment findings |
| LIMITATIONS ≠ OPTIONAL | LIMITATIONS and NON_CLAIMS fields are non-nullable; schema validation rejects null values |
| UNAVAILABLE ≠ CLEAN | Schema default for all assessment fields is UNAVAILABLE; positive states require active assessment to be promoted |

## 9.3 Mandatory non-claims on every applicable record

| Non-claim | Required on | Machine-readable field |
|---|---|---|
| T05d: clean-label poisoning NOT covered | Every C2 evidence record AND every C3 evidence record AND every C5 finding | coverage_gap_clean_label = TRUE |
| Global backdoor absence NOT established | Every C3 behavioral/identity evidence record | global_backdoor_absence_not_established = TRUE |
| Digest match ≠ causal execution proof | Every C4 provenance record | pf_002_non_claim = "digest_match ≠ causal_execution_proof" |
| ANOMALY_DETECTED ≠ PROVEN_MALICIOUS | Every C5 finding where detection_status = ANOMALY_DETECTED | anomaly_not_malicious_non_claim = TRUE |
| Behavioral battery finite scope | Every DEFERRED_IN_SCOPE record for behavioral battery | finite_battery_non_claim = TRUE |
| UNAVAILABLE ≠ CLEAN | Enforced by schema default; no explicit field needed | (schema default enforcement) |

---

# 10. PROVENANCE / AUDIT ARCHITECTURE

## 10.1 Artifact binding

The provenance record binds together:
- The artifact-unit digest (SHA-256 of all files in the artifact-unit per SP-002)
- The evidence record digest(s) (SHA-256 of the schema-validated evidence record JSON)
- A replay nonce (unique per record; prevents replay attacks)
- A sequence number (monotonically increasing; gaps detectable)
- The signing key ID
- A timestamp (from local system clock — trusted-clock source not currently established; AF-003 open)
- PF-002 non-claim field (required on every record)

## 10.2 Canonicalization

Before signing, the evidence record is canonicalized using a deterministic serialization (SP-003 vocabulary contract defines the exact algorithm — PRE-04 BLOCKING). The canonicalization algorithm ID is included in the provenance record.

## 10.3 Hashing

SHA-256 is used for all artifact-unit digests and evidence-record digests. No algorithm substitution without architecture change control.

## 10.4 Signing (XREG-002 PENDING)

XREG-002 decision determines the signing mechanism:

| If XREG-002 → Ed25519 | If XREG-002 → HMAC-SHA256 |
|---|---|
| Asymmetric; private key held by supervisor only | Symmetric; shared key held by supervisor |
| Non-repudiation stronger | Non-repudiation weaker (shared key) |
| Key generation, storage, rotation policy required (GAP-006/SP-004) | Simpler key management; requires secure key provisioning |
| Uses `cryptography` Python package | Uses Python stdlib `hmac` |

This specification does not resolve XREG-002. The signing module interface is the same in both cases: `sign(record_bytes) → signature`. The choice of mechanism is a project decision (PRE-02 BLOCKING).

## 10.5 Sequence state and replay handling

- Every provenance record includes a monotonically increasing sequence number
- Every provenance record includes a per-record replay nonce
- Sequence gaps are detectable and trigger SEQUENCE_GAP event in audit chain
- Sequence state is durably stored by COMP-C4; in-memory state loss → state is recovered from last audit chain entry on restart
- Replay of a prior record produces a REPLAY_ATTEMPT event; the replayed record is rejected

## 10.6 Audit chain structure

Each audit event entry contains:
- event_id (sequential)
- event_type (enum — see Section 16)
- payload_digest (SHA-256 of event payload)
- previous_event_digest (SHA-256 of the preceding event's complete record — the chain link)
- timestamp
- supervisor_version_id

Chain integrity is verifiable by re-computing the chain from the first event. Any insertion, deletion, or modification produces a hash mismatch.

## 10.7 Tail completeness

The audit chain does NOT claim tail completeness. COMPLETENESS_UNAVAILABLE is emitted because no external checkpoint/witness exists. An attacker who truncates the chain at the tail produces an undetectable gap from the perspective of the chain alone.

## 10.8 Failure outcomes

| Failure | Response |
|---|---|
| Chain write failure | ERROR_CHAIN_WRITE event attempted in secondary log; supervisor raises alert; pipeline halts for the affected record |
| Chain corruption detected | CHAIN_CORRUPT event; chain verification halted; supervisor reports corrupt state; NO reset-to-empty |
| Signing key unavailable | SIGNING_UNAVAILABLE recorded in provenance record; record not silently treated as signed |
| Sequence state loss | Recovered from last valid chain entry on restart; gap logged |

## 10.9 Claim boundary

What cryptographic verification establishes:
- The signed record was produced and not modified after signing (under accepted-key assumptions)
- The artifact-unit bytes were committed to the record at signing time

What cryptographic verification does NOT establish (permanent non-claims):
- That the named model actually executed those inferences (PF-002)
- That the assessment was accurate
- That the key was not compromised
- That the system producing the record was not itself compromised

---

# 11. SAFE-LOADING / ISOLATION ARCHITECTURE

## 11.1 Entry point for untrusted artifacts

All untrusted model and data artifacts enter the system only through the ingestion gate (B1 boundary). They are never loaded or parsed in the supervisor process. The ingestion gate normalizes paths and applies artifact-unit resolution before any file is passed to a worker.

## 11.2 Where parsing and execution occur

All parsing, loading, and execution of untrusted artifacts occurs in COMP-W-C3D (safe-loading gate worker), COMP-W-C3C (ONNX structural validator), COMP-W-C3A (artifact-unit resolver), or data-assessment workers (COMP-W-C2A through COMP-W-C2D). These are separate OS subprocesses.

## 11.3 Isolation boundary

The isolation boundary (B2) is an OS subprocess boundary. The specific isolation mechanism is CONDITIONAL on target host (PRE-01 BLOCKING). The minimum required properties of the isolation boundary are:

- Workers cannot write to the evidence store path (OS ACL)
- Workers cannot access the signing key or HMAC key
- Workers cannot communicate with the supervisor except via the designated IPC channel (stdout JSON or named temp file)
- Workers have no network access
- Workers have limited filesystem write access (only a designated temp directory)

## 11.4 Resource limits per worker

| Resource | Limit | Rationale |
|---|---|---|
| Wall-clock timeout | Configurable (default 60s for model loading, 120s for large dataset scans) | Prevent timeout DoS |
| Memory (RSS) | Configurable (default 2GB) | Prevent OOM DoS |
| File descriptors | Configurable (default 64) | Prevent descriptor exhaustion |
| Subprocess children | 0 (workers must not spawn children) | Prevent process-tree escapes |
| Network sockets | 0 | Enforce offline requirement |

## 11.5 PyTorch safe-loading constraint

- `weights_only=True` is MANDATORY with no fallback path
- `weights_only=False` must not exist anywhere in the codebase, including exception handlers
- No Ultralytics automatic unsafe fallback (RC-013 REJECTED)
- Version floor: PyTorch ≥2.10.0 (implementation-inspected floor per XREG-005; SP-007 advisory confirmation pending)
- `weights_only=True` is NECESSARY but NOT SUFFICIENT — subprocess isolation, resource caps, and path restrictions are all required in addition

## 11.6 ONNX external-data path containment

- All external-data file references are resolved by COMP-W-C3A BEFORE any file access
- Absolute paths → ONNX_PATH_CONTAINMENT_VIOLATION → model pipeline BLOCKED
- Path traversal patterns (`../`, `./..`) → ONNX_PATH_CONTAINMENT_VIOLATION → BLOCKED
- Symlink escapes → path canonicalization check → BLOCKED if target is outside asset directory
- All resolved paths must be within the declared submitted asset directory

## 11.7 What happens on failure

| Failure | Propagation chain |
|---|---|
| Worker timeout | ASSESSMENT_ERROR in evidence record → C5 UNAVAILABLE/NO_DECISION |
| Worker OOM | ASSESSMENT_ERROR → C5 UNAVAILABLE/NO_DECISION |
| LOAD_BLOCKED (hostile pickle) | LOAD_BLOCKED evidence record (ANOMALY_DETECTED ≠ PROVEN_MALICIOUS) → C5 ESCALATE disposition prompt |
| ONNX_PATH_CONTAINMENT_VIOLATION | BLOCKED evidence record → model assessment stopped → C5 ESCALATE |
| SCHEMA_VIOLATION on worker output | Record rejected → SCHEMA_VIOLATION audit event → C5 UNAVAILABLE |

## 11.8 Prevention of assessment result contamination

A hostile model artifact in COMP-W-C3D cannot:
- Write directly to the evidence store (OS ACL enforcement)
- Access or modify the signing key
- Return an arbitrary JSON blob that passes schema validation (COMP-SCHEMA enforces all required fields and prohibits disallowed fields)
- Cause the supervisor to emit a CLEAN or SAFE result (no such result states exist in the schema)

---

# 12. OFFLINE ARCHITECTURE

## 12.1 Offline runtime requirements

The system must operate without any network access at runtime. This includes:
- No DNS queries
- No pip install at runtime
- No CDN or API calls
- No telemetry egress

## 12.2 Dependency packaging

All Python packages must be pre-staged in a wheelhouse before deployment. The wheelhouse must be composed and verified on the target host before any offline claim is made.

Required packages (provisional — exact versions subject to PRE-01 and PRE-02 resolution):

| Package | Purpose | Source | Offline status |
|---|---|---|---|
| Python stdlib (`hashlib`, `subprocess`, `sqlite3`, `json`, `hmac`) | Core functionality | Built-in | OFFLINE — no staging needed |
| `PyYAML==6.0.3` | Runtime configuration and YAML submission-manifest parsing through `yaml.safe_load` | Pre-staged binary wheel | CONDITIONAL — verified CPython 3.13 / Windows AMD64 wheel required; no source build |
| `onnx` | ONNX structural validation (COMP-W-C3C, COMP-W-C3A) | Pre-staged wheel | CONDITIONAL — must be verified on target host |
| `torch` (CPU-only) | PyTorch safe-loading gate (COMP-W-C3D) — if PyTorch in scope (PRE-05) | Pre-staged wheel | CONDITIONAL — depends on target OS/arch; PyTorch CPU wheel staging non-trivial |
| `cryptography` | Ed25519 signing (if XREG-002 → Ed25519) | Pre-staged wheel | CONDITIONAL — depends on XREG-002 |
| `pycocotools` (R27 COCO API) | COCO format parsing (COMP-W-C2A) | Pre-staged wheel with C extension build | CONDITIONAL — C extension must build on target host |

## 12.3 Local references and trust anchors

- Signing key (or HMAC secret): pre-provisioned before operation; stored in supervisor-accessible location on target host; not transmitted at runtime
- Reference artifact registry: local file (empty at MVP start; all references UNAVAILABLE)
- Schema definition files: bundled with the system; loaded at startup from local path only

## 12.4 No-network assumptions

- `onnx` package: no telemetry assumed (verify at staging)
- `torch` (CPU-only): no telemetry assumed (EF-003 gap applies — binary-specific telemetry behavior must be confirmed on the specific pre-staged binary on the target host before any offline claim)
- `pycocotools`: no telemetry assumed
- `cryptography`: no telemetry assumed

## 12.5 Offline failure behavior

| Scenario | Behavior |
|---|---|
| Network call attempted by worker | Worker receives connection refused; returns ASSESSMENT_ERROR |
| Package missing at runtime | System startup failure with explicit dependency error; not a silent assessment failure |
| Signing key unavailable offline | SIGNING_UNAVAILABLE in provenance record; pipeline continues without signing (signing is required for claim, not for assessment) |

## 12.6 What can be claimed about offline operation

```
CLAIMABLE (after confirmed on target host):
  System runs without network access after pre-staging

NOT YET CLAIMABLE (as of this specification):
  Offline operation has been validated on the target deployment host
  (GAP-001 PRE-01 remains BLOCKING — target host not yet specified)

NEVER CLAIMABLE from wheelhouse alone:
  The system is offline-validated
  (Package installation ≠ runtime execution ≠ zero-egress confirmation)
```

---

# 13. TARGET FORMAT COVERAGE

The following table states the exact format coverage of this architecture. Claims may only be made for formats marked SUPPORTED after executed fixture tests on the target host.

## 13.1 Dataset formats

| Format | Status | Conditions |
|---|---|---|
| COCO (object detection, JSON annotations) | SUPPORTED (conditional) | Parser fixture gate must pass; all-box validation confirmed |
| YOLO detection (.txt, per-image labels) | SUPPORTED (conditional) | Task-variant scope confirmed (PRE-05); parser fixture gate must pass |
| YOLO segmentation | CONDITIONAL | In scope only if PRE-05 includes segmentation; fixture required |
| YOLO pose | CONDITIONAL | In scope only if PRE-05 includes pose; fixture required |
| YOLO OBB (oriented bounding box) | CONDITIONAL | In scope only if PRE-05 includes OBB; fixture required |
| VisDrone format | NOT_VALIDATED | Toolkit (R20) usable as format reference; data rights (R26) unconfirmed |
| Any other annotation format | UNSUPPORTED | Emits UNSUPPORTED |

## 13.2 Model formats

| Format | Status | Conditions |
|---|---|---|
| ONNX (`.onnx` with or without external data) | SUPPORTED (conditional) | Path containment hostile fixture must pass; C extension build confirmed on target |
| PyTorch (`.pt`, `.pth`, `.ckpt`) | SUPPORTED (conditional) | PyTorch in scope (PRE-05); CPU wheel confirmed on target; `weights_only=True` hostile fixture must pass |
| TorchScript (`.torchscript`) | DEFERRED_IN_SCOPE | Isolated worker not demonstrated on target; emits DEFERRED_IN_SCOPE |
| SafeTensors + JSON config | DEFERRED_IN_SCOPE | YOLO state-dict mapping absent (RC-014 deferred) |
| Any other model format | UNSUPPORTED | Emits UNSUPPORTED |

## 13.3 Non-claims on format coverage

- SUPPORTED means the method was executed and the fixture test passed for that format. It does NOT mean:
  - Universal support for all variants, versions, or configurations of that format
  - Behavioral safety of a model in a supported format
  - Detection of attacks not in scope for the applied method
- Format support claims must name the specific target tuple (OS, Python version, package version) on which fixtures were confirmed

---

# 14. REUSE INTEGRATION

The following approved reuse decisions carry binding implementation constraints. Deviating from these constraints requires architecture change control.

| Reuse ID | Source | Decision | Destination component | Adaptation boundary | Required hardening | Tests | License / notice |
|---|---|---|---|---|---|---|---|
| REUSE-001 | R01 COCO/YOLO ingestion | REIMPLEMENT (reference only) | COMP-W-C2A | All-box geometry validation; worker isolation; structured evidence output | No R01 code copied; supervisor-isolated worker; YOLO task-variant awareness | All-box coverage; malformed input rejection; resource limits | N/A (reimplemented) |
| REUSE-002a | R01 SHA-256 duplicate | REIMPLEMENT (stdlib) | COMP-W-C2B | stdlib `hashlib` only | No R01 code copied | Known-duplicate / known-clean pairs; resource limit; structured output | N/A |
| REUSE-003 | R01 label integrity | REPLACE (all-box validator) | COMP-W-C2A | No ML feature approach; no first-box approach | Structural geometry only | All-box coverage test; multi-object scene | N/A |
| REUSE-005 | R01 trigger/backdoor scan | EXTRACT hash/FFT concepts; KEEP templates as test fixtures | COMP-W-C2D (hash tier); COMP-FIX (fixture templates) | Hash and FFT logic only; no attribution claim | COVERAGE_GAP_CLEAN_LABEL on every M15 record | Hash known-duplicate; hash known-clean; FFT floor | No code copied (license); fixture templates: SYNTHETIC label |
| REUSE-006 | R01 contributor risk | REIMPLEMENT | COMP-W-C2C | Raw statistics only; UNTRUSTED default; SYBIL_UNRELIABLE | No aggregate score; no code copied | SYBIL_UNRELIABLE propagation; HHI/entropy correctness | N/A |
| REUSE-007 | R01 attack generator methodology | KEEP methodology / REIMPLEMENT code | COMP-FIX | Fixture design reference; add hostile types | All fixtures labeled SYNTHETIC | Reproducibility (seed-pinned); manifest integrity; SYNTHETIC label propagation | N/A |
| REUSE-008 | R01 model hasher concept | HARDEN concept / REIMPLEMENT code | COMP-W-C3B | ONNX external-data inclusion; ARTIFACT_UNIT_AMBIGUOUS; LIMITATIONS/NON_CLAIMS | PF-002 non-claim on every record | Known-match; known-tamper; ONNX external-data; MATCH ≠ SAFE propagation | N/A |
| REUSE-009 | R01 model loader | REPLACE entirely | COMP-W-C3D | Subprocess; `weights_only=True`; no fallback; ONNX path containment; resource limits | Hostile pickle test; no fallback path in codebase | LOAD_BLOCKED on hostile pickle; LOAD_SUCCESS on benign; no unsafe fallback | N/A |
| REUSE-012 | R01 inference record HMAC concept | HARDEN concept / REIMPLEMENT | COMP-C4 | Input bytes + model hash + canonical config; replay nonce; durable sequence state | Supervisor-only signing; nonce non-reusable | Replay attack test; sequence-gap detection | N/A |
| REUSE-013 | R01 audit chain concept | HARDEN concept / REIMPLEMENT | COMP-AUDIT | Fail-closed corrupt handling; supervisor-only writes; no external HEAD reset | No fail-open path | Chain corruption detection; no-reset test; chain continuity | N/A |
| REUSE-015 | R01 Fabric client | REMOVE unconditionally | N/A | Must never enter codebase | Exclusion verified | Absence from codebase (grep check) | N/A |
| REUSE-016 | R01 benchmark metrics | REFERENCE ONLY | N/A | R01 F1 metrics are NOT project results | N/A | N/A | External intelligence only |
| REUSE-018 | R17 origin (SHA-256 / SQLite patterns) | EXTRACT patterns | COMP-STORE | SHA-256 hashing patterns; SQLite WAL access patterns; add supervisor-only writes; project schema; hash-chain | Supervisor-write enforcement; hash-chain integration | Write isolation test; WAL mode test | MIT — attribution required |
| REUSE-019 | R18 data-lineage (DAG / content hash) | ADAPT/EXTRACT | COMP-STORE (supplementary) | Dataset lineage metadata patterns; adapt to COCO/YOLO; supervisor-write | Cycle rejection; supervisor-write | Content-hash determinism; cycle rejection | MIT — attribution required |
| REUSE-020 | R27 COCO API (pycocotools) | ADOPT/ADAPT | COMP-W-C2A | COCO format parsing layer; geometry validation on top; worker-wrapped; C extension pre-staged | Path handling review in C extension; malformed JSON test | Malformed JSON; out-of-range boxes; empty annotations; all-box coverage | BSD-style permissive — attribution required |
| REUSE-021 | R24 PDQ (ThreatExchange) | DEFERRED — post-MVP spike required | (post-MVP: COMP-W-C2?) | Native build confirmation; threshold calibration; FPR measurement | CImg.h license exception must be inspected before use | (post-MVP) | BSD with CImg.h exception — inspect before use |
| REUSE-023 | R19 AuditTrail-Ledger | REFERENCE ONLY | N/A | Concept reference only | N/A | N/A | MIT |

**Excluded components (permanent; no change-control path exists for these specific items):**
- R01 Fabric client (fake CONNECTED state; excluded unconditionally)
- R01 first-box label detector (replaced by all-box structural validator)
- R01 aggregate risk score module (prohibited by project invariant)
- R13 Alibi-Detect (BSL 1.1 — not open source)
- R04 BackdoorBench (CC BY-NC — non-commercial)
- R05 BackdoorBox (GPL-2.0 — copyleft)

---

# 15. CONFIGURATION MODEL

## 15.1 Fixed values (not configurable)

| Parameter | Fixed value | Justification |
|---|---|---|
| PyTorch safe-loading mode | `weights_only=True` always | RC-013 REJECTED; security requirement |
| PyTorch version floor | ≥2.10.0 | XREG-005 implementation-inspected floor |
| Evidence field defaults | UNAVAILABLE / NOT_ASSESSED | AR-003; never CLEAN, SAFE, HEALTHY |
| Contributor identity default | UNTRUSTED | AR-011 |
| SYBIL_UNRELIABLE default | TRUE | DF-005 |
| Risk score field | PROHIBITED (schema rejects) | G-07; C5 absolute boundary |
| Behavioral battery status | DEFERRED_IN_SCOPE | D-AD-005 |
| T05d coverage gap non-claim | Required on C2+C3+C5 | AR-010 |
| Fail-open audit chain | PROHIBITED | AF-004 |
| First-box-only label analysis | PROHIBITED | REUSE-003 |
| Worker unsafe fallback | PROHIBITED | RC-013 |

## 15.2 Configurable parameters

| Parameter | Controls | How selected | Recorded in evidence? |
|---|---|---|---|
| Worker timeout (per worker type) | Maximum wall-clock time before ASSESSMENT_ERROR | Configuration file; project-owner policy | Yes — in evidence record |
| Worker memory limit | Maximum RSS before ASSESSMENT_ERROR | Configuration file | Yes |
| Worker file-descriptor limit | Maximum FDs per subprocess | Configuration file | Yes |
| Signing key path / HMAC key path | Trust anchor location | Provisioned before deployment (GAP-006) | Key ID recorded in provenance record |
| Evidence store path | SQLite file location | Configuration file | N/A |
| Audit trail path | Audit log location | Configuration file | N/A |
| Supported YOLO task variants | Which variants are in scope | Configuration file (PRE-05 decision) | Yes — in capability declaration |
| Artifact-unit definition table | Which files constitute the artifact-unit per format | Loaded from SP-002 output (PRE-03) | Yes — artifact-unit definition ID in evidence record |
| Schema version identifier | Which evidence schema version is active | Configuration file; bump required on schema change | Yes — every evidence record |
| Algorithm identifier | Which signing/hashing algorithm is active | XREG-002 decision; SP-004 output | Yes — provenance record |

## 15.3 Policy-controlled settings

| Setting | Policy decision pending | Owner |
|---|---|---|
| Analyst authentication method | OQ-017 open | Project owner / organizer |
| Analyst authority hierarchy (who can override) | OQ-017 open | Project owner |
| Evidence retention period | OQ-018 open | Project owner |
| Trusted-clock source | AF-003 open | Deployment environment |
| Reference staleness trigger conditions | COMP-REF implementation | Project owner |

## 15.4 No magic numbers

Every threshold or limit in the system must be:
- Named in the configuration model (above)
- Documented as to what it controls
- Recorded in the relevant evidence record or audit event
- Not embedded as a hardcoded literal without a named configuration reference

---

# 16. FAILURE / STATE MODEL

## 16.1 Assessment state machine

All possible states for an assessment result. No state transition may produce CLEAN, SAFE, HEALTHY, or any positive assurance state without active assessment completion.

| State | Meaning | Entry condition | Output | C5 disposition | Downstream processing |
|---|---|---|---|---|---|
| APPLICABLE | Method is applicable and dispatched | Format + method in scope; prerequisites met | Worker executing | — | Continue |
| COMPLETED | Worker returned valid result | Schema-validated worker output received | Evidence record written | Determined by C5 rule engine | Continue to C5 |
| ASSESSMENT_ERROR | Worker failed (timeout, crash, resource exhaustion) | Worker did not return valid result | Evidence record with ASSESSMENT_ERROR | UNAVAILABLE/NO_DECISION | Continue (other methods unaffected) |
| UNAVAILABLE | Required prerequisite absent | Reference absent; access mode insufficient; artifact-unit undefined | UNAVAILABLE evidence record | UNAVAILABLE/NO_DECISION | Continue (do not block other methods) |
| UNSUPPORTED | Format/task-variant not in implementation scope | Format/variant match fails against declared scope | UNSUPPORTED record | (No finding produced — scope boundary declared) | Continue |
| DEFERRED_IN_SCOPE | Method known but excluded from MVP | Method in deferred list | DEFERRED_IN_SCOPE record | Analyst sees explicit deferred notice | Continue |
| ARTIFACT_UNIT_AMBIGUOUS | Artifact-unit cannot be resolved | SP-002 definition absent or external-data manifest inconsistent | ARTIFACT_UNIT_AMBIGUOUS | UNAVAILABLE for hash-dependent methods | Hash-dependent methods blocked; structural checks continue |
| SCHEMA_VIOLATION | Worker output fails schema validation | Schema validator rejects output | SCHEMA_VIOLATION audit event; no evidence record | UNAVAILABLE (upstream validation failed) | Schema violation recorded; pipeline continues for other assets |
| LOAD_BLOCKED | Model loading actively blocked | Hostile checkpoint triggered containment | LOAD_BLOCKED evidence record | ESCALATE (not CLEAN — ANOMALY ≠ PROVEN_MALICIOUS) | Assessment stopped for this model |
| LOAD_SUCCESS | Model loaded safely | weights_only=True succeeded; no exception | LOAD_SUCCESS evidence record | Per C5 rule engine | Continue |
| ONNX_PATH_CONTAINMENT_VIOLATION | External data path traversal detected | Path check failed in COMP-W-C3A | BLOCKED evidence record | ESCALATE | Assessment stopped for this model |
| REFERENCE_UNAVAILABLE | Reference not available or not HEALTH_VERIFIED | COMP-REF returns UNAVAILABLE or HEALTH_UNVERIFIED | REFERENCE_UNAVAILABLE record | UNAVAILABLE — reference-relative finding blocked | Other findings unaffected |
| SIGNING_UNAVAILABLE | Signing key unavailable at signing time | Key access failed | SIGNING_UNAVAILABLE in provenance record | UNAVAILABLE for cryptographic binding claim | Evidence record exists; provenance binding claim not supported |

## 16.2 C5 analyst disposition mapping

| C5 Analyst disposition | Meaning | Conditions |
|---|---|---|
| ACCEPT | Evidence is within expected parameters; analyst accepts finding | COMPLETED; no anomaly detected; limitations acknowledged |
| ACCEPT_WITH_CONTEXT | Evidence is acceptable given stated context | COMPLETED; minor anomaly noted; analyst provides context |
| ESCALATE | Finding requires further investigation | LOAD_BLOCKED; ONNX_PATH_CONTAINMENT_VIOLATION; DIFFERENT on identity hash; behavioral inconsistency (future) |
| CONTAIN_HOLD | Asset held pending resolution | ESCALATE condition confirmed; analyst determines hold |
| OVERRIDE | Analyst overrides finding (requires justification) | Recorded as audit event with rationale |
| UNAVAILABLE/NO_DECISION | Assessment could not be completed | UNAVAILABLE; ASSESSMENT_ERROR; prerequisites absent |

## 16.3 Enforced invariants in the state model

- UNAVAILABLE ≠ CLEAN: no transition from UNAVAILABLE or ASSESSMENT_ERROR to any positive assurance state
- ANOMALY ≠ PROVEN_ATTACK: LOAD_BLOCKED and ONNX_PATH_CONTAINMENT_VIOLATION trigger ESCALATE, not CONFIRMED_MALICIOUS
- DEFERRED_IN_SCOPE ≠ CLEAN: deferred methods produce explicit records; their absence is not a no-issue finding
- REFERENCE_UNAVAILABLE ≠ CLEAN: reference-relative methods that cannot access a HEALTH_VERIFIED reference produce UNAVAILABLE, not a positive result
- C6 ERROR → C5 UNAVAILABLE: no ERROR state is compressed to PASS or silently dropped

---

# 17. API / INTERFACE CONTRACTS

The following contracts must not be invented by implementation agents. They are defined here.

## 17.1 Worker subprocess contract (B2 boundary)

### Input to worker (from supervisor)

```json
{
  "schema_version": "<string — schema version identifier>",
  "task": "<string — enum: C2A_STRUCTURAL | C2B_EXACT_HASH | C2C_CONCENTRATION |
             C2D_IMAGE_HASH | C3A_ARTIFACT_UNIT | C3B_MODEL_HASH |
             C3C_ONNX_STRUCTURAL | C3D_SAFE_LOAD>",
  "asset_paths": ["<string — absolute path within asset directory>"],
  "format": "<string — COCO | YOLO_DETECTION | YOLO_SEG | YOLO_POSE | YOLO_OBB |
              ONNX | PYTORCH>",
  "task_variant": "<string — task-specific>",
  "artifact_unit_definition_id": "<string — from SP-002; UNAVAILABLE if not frozen>",
  "resource_limits": {
    "timeout_seconds": "<integer>",
    "memory_limit_mb": "<integer>",
    "max_file_descriptors": "<integer>"
  },
  "identity_quality": "<string — TRUSTED | UNTRUSTED | UNAVAILABLE (default UNTRUSTED)>",
  "reference_digest": "<string — SHA-256 hex | null if UNAVAILABLE>"
}
```

### Output from worker (to supervisor via stdout or named temp file)

```json
{
  "schema_version": "<string>",
  "worker_id": "<string>",
  "assessment_status": "<string — COMPLETED | ASSESSMENT_ERROR | UNAVAILABLE |
                          UNSUPPORTED | DEFERRED_IN_SCOPE | ARTIFACT_UNIT_AMBIGUOUS |
                          SCHEMA_VIOLATION | LOAD_BLOCKED | LOAD_SUCCESS | LOAD_ERROR |
                          ONNX_PATH_CONTAINMENT_VIOLATION | STRUCTURAL_VALID |
                          STRUCTURAL_INVALID | REFERENCE_UNAVAILABLE>",
  "raw_signal": { /* method-specific; may be null */ },
  "access_mode": "<string — BLACK_BOX | GREY_BOX | WHITE_BOX | INTERNAL_ACTIVATION |
                   UNAVAILABLE (required field; non-nullable on C3 records)>",
  "artifact_unit_id": "<string — artifact-unit definition ID used | UNAVAILABLE>",
  "coverage_gap_clean_label": true,   /* required on C2 and C3 records */
  "limitations": ["<string>"],        /* non-nullable; at minimum one entry */
  "non_claims": ["<string>"],         /* non-nullable; at minimum one entry */
  "dependency_declaration": {         /* required when multiple detectors may co-fire */
    "co_firing_detectors": [],
    "independence_established": false
  },
  "assessment_timestamp": "<ISO 8601>",
  "error_detail": "<string | null>"
}
```

**Validation:** Supervisor rejects any worker output missing required fields. Supervisor rejects any output containing a `risk_score`, `aggregate_assurance`, `compromise_probability`, or semantically equivalent field. Supervisor rejects any output where `coverage_gap_clean_label` is absent or false on C2/C3 records.

## 17.2 Evidence store API (COMP-STORE)

Internal supervisor interface only. No external API exposed from evidence store.

```
write_evidence_record(record: dict) → record_id: str
  Precondition: COMP-SCHEMA validation passed
  Effect: Atomic write to SQLite; WAL mode
  Failure: raises StorageWriteError (never silently ignored)

write_audit_event(event: dict) → event_id: str
  Effect: Atomic write; appends chain link
  Failure: raises AuditWriteError (chain write failure triggers alert)

query_findings(filter: dict) → List[dict]
  Precondition: read-only query
  Effect: Returns matching structured findings

query_evidence(asset_id: str, method_id: str) → dict | None
  Precondition: read-only query
  Effect: Returns evidence record or None (never substitutes CLEAN for absent record)

export_bundle(asset_id: str) → ZipBytes
  Effect: Packages findings, evidence, provenance, audit events for the named asset
```

## 17.3 Analyst interface contract (COMP-IFACE)

The analyst interface reads from the evidence store only. It must not:
- Write evidence records
- Modify existing findings
- Aggregate findings into an overall risk score
- Convert UNAVAILABLE states to any positive display state

CLI contract (minimum):
```
assess --submission <path>
  → runs full pipeline; writes all records; prints summary

show-finding --asset-id <id>
  → prints C5 structured finding for the named asset; all fields visible

show-evidence --asset-id <id> --method <method-id>
  → prints evidence record for the named asset/method pair

show-audit-trail
  → prints audit chain (read-only); reports CHAIN_CORRUPT if detected

export-bundle --asset-id <id> --output <path>
  → produces structured ZIP with findings, evidence, provenance, audit events

list-deferred
  → lists all DEFERRED_IN_SCOPE records (makes deferred capabilities visible)
```

## 17.4 Signing module interface (COMP-C4)

```
sign_record(record_bytes: bytes, key_material: bytes) → signature: bytes
  Precondition: XREG-002 resolved; key material available
  Effect: Returns signature (Ed25519 or HMAC-SHA256 depending on XREG-002)
  Failure: raises SigningKeyUnavailableError → SIGNING_UNAVAILABLE recorded

verify_record(record_bytes: bytes, signature: bytes, key_material: bytes) → bool
  Effect: Returns True if signature valid; False if invalid
  Note: True does NOT establish causal execution; PF-002 applies
```

## 17.5 Interface failure contracts

| Interface | Failure | Required behavior |
|---|---|---|
| Worker → supervisor | Worker crashes / timeout | Supervisor receives empty or error output; emits ASSESSMENT_ERROR |
| Supervisor → evidence store | Write fails | StorageWriteError raised; audit event attempted; pipeline halts for this record |
| Supervisor → signing module | Key unavailable | SIGNING_UNAVAILABLE recorded; record not silently treated as signed |
| Analyst → evidence store | Record absent | None returned; interface displays UNAVAILABLE; never substitutes CLEAN |
| Supervisor → schema validator | Validation fails | Record rejected; SCHEMA_VIOLATION audit event |

---

# 18. STORAGE / STATE MODEL

## 18.1 Evidence store (primary persistent state)

| Item | Schema table | Integrity requirement | Ownership | Mutability | Retention |
|---|---|---|---|---|---|
| Evidence records (C2, C3) | `evidence_records` | Immutable after supervisor write; hash included in provenance record | Supervisor | Immutable | OQ-018 pending |
| Structured findings (C5) | `findings` | Immutable after supervisor write | Supervisor | Immutable | OQ-018 pending |
| Provenance records | `provenance_records` | Immutable; signature included | Supervisor | Immutable | OQ-018 pending |
| DEFERRED_IN_SCOPE records | `deferred_records` | Immutable after supervisor write | Supervisor | Immutable | OQ-018 pending |
| Reference health states | `reference_health` | Updatable only by supervisor (COMP-REF) | COMP-REF | Append + state-transition only | Permanent |
| Audit events | `audit_events` | Append-only; hash-chained | Supervisor (COMP-AUDIT) | Append-only | Permanent |

## 18.2 Cryptographic state

| Item | Location | Integrity requirement | Recovery behavior |
|---|---|---|---|
| Signing key / HMAC secret | Supervisor-accessible key store; outside evidence store | Must not be accessible to workers; stored per GAP-006/SP-004 | Key loss → signing unavailable; evidence records exist without valid binding |
| Sequence number | COMP-C4 durable state file + recoverable from audit chain | Durable; recovered from last valid audit chain entry on restart | Gap detected → logged as SEQUENCE_GAP |
| Last audit chain hash | COMP-AUDIT durable state file + audit chain itself | Recovered from last chain entry | Mismatch → CHAIN_CORRUPT |

## 18.3 Configuration state

| Item | Location | Integrity requirement | Mutability |
|---|---|---|---|
| Schema definition files | Bundled; loaded at startup from local path | Loaded from trusted location; not overrideable by submitted assets | Updated only with schema version bump |
| Artifact-unit definition table | Loaded from SP-002 output file at startup | Trusted; not writable at runtime | Updated only with definition version bump |
| Worker resource limits | Configuration file | Validated at startup | Operator-settable; not worker-settable |
| Supported format/variant list | Configuration file | Validated at startup | Updated only with architecture change |

## 18.4 What must not be persisted

- Raw model bytes inside the evidence store (only digest is stored)
- Image bytes inside the evidence store (only hash is stored)
- Signing key or HMAC secret inside evidence store
- Aggregate risk scores (prohibited; schema rejects)
- Anonymous contributor identity promoted to TRUSTED without external authentication

---

# 19. DEPLOYMENT ARCHITECTURE

## 19.1 Deployment topology

```
[Target Host — single machine, offline/air-gapped]
│
├── /opt/assurance-system/          (supervisor process; root of trusted zone)
│   ├── supervisor.py               (COMP-SUP orchestrator)
│   ├── schema/                     (evidence schema definitions — loaded at startup)
│   ├── artifact_unit_defs/         (SP-002 output — loaded at startup)
│   └── config/                     (configuration files)
│
├── /var/assurance/evidence-store/  (COMP-STORE — SQLite; OS ACL: supervisor-rw, all-others-none)
├── /var/assurance/audit-trail/     (COMP-AUDIT output; OS ACL: supervisor-rw, all-others-r)
├── /var/assurance/references/      (reference registry; OS ACL: supervisor-rw, all-others-none)
├── /var/assurance/keys/            (signing keys; OS ACL: supervisor-r, all-others-none)
│
├── /tmp/assurance-workers/         (ephemeral worker temp directories; OS ACL: per-subprocess)
│
├── /opt/assurance-wheelhouse/      (pre-staged Python wheels — offline dependency closure)
│   ├── onnx-*.whl
│   ├── torch-*+cpu-*.whl           (CPU-only, if PyTorch in scope)
│   ├── pycocotools-*.whl           (with C extension build artifact)
│   └── cryptography-*.whl          (if XREG-002 → Ed25519)
│
└── /opt/assurance-fixtures/        (COMP-FIX hostile fixture suite — test use only)
    └── ...
```

## 19.2 Trust boundary implementation

- B2 (supervisor / worker): OS subprocess; supervisor spawns workers via Python `subprocess.Popen`; workers have no access to `/var/assurance/` paths (OS-level, enforced by file ACL or container if available on target)
- B3 (evidence store write): SQLite file owned by supervisor process account; OS ACL prevents writes by other accounts
- B5 (signing key): `/var/assurance/keys/` readable only by supervisor process account

## 19.3 Packaging boundary

The system is delivered as:
- A Python source distribution (supervisor + worker modules)
- A pre-composed wheelhouse (`/opt/assurance-wheelhouse/`)
- Schema definition files
- Artifact-unit definition files (once SP-002 is produced)
- A configuration file template
- The hostile fixture suite (in a separately packaged test tarball)

No runtime internet connectivity is required after deployment.

## 19.4 Offline dependency claim

**CONDITIONAL:** The offline dependency claim requires:
1. Wheelhouse composition on the target host (PRE-01 BLOCKING — target host not yet specified)
2. All wheels install successfully with no native dependency missing on the target
3. Zero-egress confirmation on the target host (network isolation confirmed by monitoring)
4. ORT binary telemetry confirmed absent (EF-003 — applies if ORT is used; not required for MVP scope which does not include ORT)

No offline claim may be made until all four of these are confirmed on the actual target host.

---

# 20. OBSERVABILITY / TESTABILITY

## 20.1 Observable outputs per component

| Component | Observable outputs |
|---|---|
| COMP-SUP | Audit events (every significant action); pipeline run summary |
| COMP-SCHEMA | SCHEMA_VIOLATION audit events; acceptance events |
| COMP-W-C2A | C2 structural evidence records; per-violation entries |
| COMP-W-C2B | C2 exact-duplicate evidence records; per-file SHA-256 |
| COMP-W-C2C | C2 concentration evidence records; HHI, entropy, per-source share values |
| COMP-W-C2D | C2 image-level hash records; per-image SHA-256 |
| COMP-W-C3A | Artifact-unit manifest; ARTIFACT_UNIT_AMBIGUOUS events |
| COMP-W-C3B | C3 identity evidence records; SHA-256 per artifact-unit; MATCH / DIFFERENT / UNAVAILABLE |
| COMP-W-C3C | C3 ONNX structural records; ONNX_PATH_CONTAINMENT_VIOLATION events |
| COMP-W-C3D | C3 safe-loading records; LOAD_BLOCKED / LOAD_SUCCESS / LOAD_ERROR |
| COMP-C4 | Signed provenance records; sequence state events |
| COMP-C5 | C5 structured findings per asset/method |
| COMP-REF | Reference health state transitions; REFERENCE_UNAVAILABLE events |
| COMP-AUDIT | Hash-chained audit events; CHAIN_CORRUPT if detected |
| COMP-STORE | WAL commit events (SQLite) |
| COMP-IFACE | Displayed findings; DEFERRED_IN_SCOPE visible |

## 20.2 Deterministic / reproducible behavior

| Behavior | Deterministic? |
|---|---|
| M01 structural validation | Yes — parse-rule based |
| M02 SHA-256 exact hashing | Yes |
| M06 source concentration statistics | Yes given same inputs |
| M15 image-level hash | Yes |
| Model SHA-256 artifact identity | Yes given frozen artifact-unit definition |
| ONNX structural validation | Yes |
| Safe-loading gate result (LOAD_BLOCKED / LOAD_SUCCESS) | Yes for the same binary, same model, same PyTorch version |
| Provenance record signature | Yes (deterministic signing algorithm) |
| Hash-chain | Yes (given same events in same order) |
| C5 finding | Yes (rule-engine based, not probabilistic) |

## 20.3 Required test hooks

| Test hook | Purpose |
|---|---|
| UNAVAILABLE injection point per pipeline layer | Confirm UNAVAILABLE propagates to C5 without conversion |
| C6 ERROR injection | Confirm C6 ERROR → C5 UNAVAILABLE/NO_DECISION (no compression) |
| Schema violation injection | Confirm rejected records produce audit event; do not enter evidence store |
| Hostile pickle fixture (COMP-FIX) | Confirm LOAD_BLOCKED; confirm no fallback to `weights_only=False` |
| ONNX path-traversal fixture (COMP-FIX) | Confirm ONNX_PATH_CONTAINMENT_VIOLATION |
| COVERAGE_GAP_CLEAN_LABEL absent | Confirm schema validator rejects record |
| Access_mode null on C3 record | Confirm schema validator rejects record |
| risk_score field present | Confirm schema validator rejects record |
| Reference HEALTH_VERIFIED without R0–R7 | Confirm REFERENCE_CATEGORY_VIOLATION or HEALTH_UNVERIFIED emitted |
| Audit chain corruption | Confirm CHAIN_CORRUPT event; confirm no reset-to-empty |
| Worker timeout | Confirm ASSESSMENT_ERROR; confirm pipeline continues for other assets |
| Worker OOM | Confirm ASSESSMENT_ERROR; confirm resource limit enforced |
| Synthetic fixture SYNTHETIC label | Confirm SYNTHETIC propagates through evidence chain |
| DEFERRED_IN_SCOPE record emission | Confirm all deferred methods produce explicit records; confirm none silently absent |

## 20.4 Failure injection points

All hostile fixture tests (Section 20.3) double as failure injection points for red-team validation. The system must produce correct evidence-chain outputs (LOAD_BLOCKED, BLOCKED, ASSESSMENT_ERROR) for every injection. A failure injection that causes a CLEAN or positive assurance output is a critical defect.

---

# 21. IMPLEMENTATION READINESS MATRIX

| Component | Owner | Inputs | Outputs | Dependencies | Security boundary | Tests | Reused component | Status |
|---|---|---|---|---|---|---|---|---|
| COMP-SUP | Backend team | Submission manifest; worker IPC outputs | Evidence records; audit events; findings; DEFERRED_IN_SCOPE records | COMP-SCHEMA, COMP-C4, COMP-C5, COMP-REF, COMP-STORE, COMP-AUDIT | Trusted zone; signing key inaccessible to workers | Pipeline integration test; UNAVAILABLE propagation test | None | BLOCKED (PRE-01, PRE-02, PRE-03, PRE-04) |
| COMP-SCHEMA | Backend team | Worker output JSON; evidence record JSON | VALID / INVALID + reason | Schema definition files (PRE-04) | Trusted (supervisor component) | Schema violation injection tests; field-presence tests; risk_score rejection test | None | BLOCKED (PRE-04) |
| COMP-W-C2A | Data team | Asset paths; format; task-variant | C2 structural evidence record | R27 COCO API; REIMPLEMENT YOLO parser | Untrusted subprocess | All-box coverage; malformed input; hostile inputs; task-variant | R27 ADOPT/ADAPT (BSD) | CONDITIONAL (PRE-05 for YOLO variants) |
| COMP-W-C2B | Data team | Asset file paths | C2 exact-duplicate evidence record | Python stdlib hashlib | Untrusted subprocess | Known-duplicate pairs; known-clean pairs; resource limit | REIMPLEMENT (stdlib) | READY (design) — BLOCKED integration (PRE-04) |
| COMP-W-C2C | Data team | Contributor metadata; identity quality | C2 concentration evidence record | Python stdlib math | Untrusted subprocess | SYBIL_UNRELIABLE propagation; HHI/entropy correctness | REIMPLEMENT | READY (design) — BLOCKED integration (PRE-04) |
| COMP-W-C2D | Data team | Image file paths | C2 image-level hash record | Python stdlib hashlib; optional numpy | Untrusted subprocess | Hash known-duplicate; hash known-clean; COVERAGE_GAP_CLEAN_LABEL | REIMPLEMENT | READY (design) — BLOCKED integration (PRE-04) |
| COMP-W-C3A | Model team | Model path; format | Artifact-unit file list; ARTIFACT_UNIT_AMBIGUOUS | SP-002 (PRE-03); `onnx` package | Untrusted subprocess | ARTIFACT_UNIT_AMBIGUOUS on undefined; path-traversal containment | REIMPLEMENT | BLOCKED (PRE-03) |
| COMP-W-C3B | Model team | Artifact-unit file list; reference digest | C3 identity evidence record | Python stdlib hashlib; COMP-W-C3A | Untrusted subprocess | Known-match; known-tamper; ONNX external-data; MATCH ≠ SAFE | REIMPLEMENT | BLOCKED (PRE-03) |
| COMP-W-C3C | Model team | ONNX path; external-data manifest | C3 ONNX structural evidence record | `onnx` package | Untrusted subprocess | Valid ONNX; invalid ONNX; path-traversal fixture | REIMPLEMENT | CONDITIONAL (pre-stage `onnx` on target) |
| COMP-W-C3D | Model team | PyTorch model path | C3 safe-loading evidence record | `torch` ≥2.10.0 CPU; no fallback | Untrusted subprocess | Hostile pickle → LOAD_BLOCKED; benign → LOAD_SUCCESS; no fallback path | REPLACE (R01 loader) | CONDITIONAL (PRE-01; PRE-05 for PyTorch) |
| COMP-C4 | Provenance team | Evidence record bytes; signing key; sequence state | Signed provenance record; audit event | XREG-002 (PRE-02); SP-004 (PRE-08); SP-006 (PRE-09); SP-003 (PRE-04) | Trusted supervisor component | Replay attack; sequence gap; signing unavailable; PF-002 present | REIMPLEMENT (concept from REUSE-012) | BLOCKED (PRE-02, PRE-04, PRE-08, PRE-09) |
| COMP-C5 | Assurance team | C2/C3 evidence; C4 binding; reference health | C5 structured findings | SP-003 (PRE-04) | Trusted supervisor component | UNAVAILABLE propagation; T05d non-claim; risk_score absence; dependency declaration | REIMPLEMENT | BLOCKED (PRE-04) |
| COMP-REF | Assurance team | Reference artifact registry; health gate records | Reference health states | SP-001 R0–R7 procedure | Trusted supervisor component | HEALTH_VERIFIED gate enforcement; STALE_SUSPECTED trigger; FORMAT_ASSET vs HEALTH_VERIFIED distinction | REIMPLEMENT | READY (design) — all references UNAVAILABLE at MVP |
| COMP-AUDIT | Backend team | Audit event payloads | Hash-chained audit trail | Python stdlib hashlib; SQLite | Trusted supervisor component | Chain corruption detection; no-reset test; continuity test | REIMPLEMENT (concept from REUSE-013) | READY (design) — BLOCKED integration (PRE-04) |
| COMP-STORE | Backend team | Schema-validated records | Persisted evidence records | Python stdlib sqlite3; R17 patterns (MIT) | Supervisor-only write; OS ACL | Write isolation; WAL mode; ACL enforcement | EXTRACT R17 patterns (MIT) | READY (design) — BLOCKED integration (PRE-04) |
| COMP-IFACE | Frontend / analyst team | Evidence store queries | CLI display; JSON/CSV export; ZIP bundle; Dashboard | COMP-STORE (read-only) | Untrusted relative to evidence store | UNAVAILABLE display; DEFERRED_IN_SCOPE visible; no risk score in output | REIMPLEMENT | READY (design) — BLOCKED integration (PRE-04) |
| COMP-FIX | Test team | Seed parameters | Hostile fixtures; synthetic attack corpus; regression manifests | Python stdlib + format-specific libraries | Test infrastructure only | Fixture reproducibility; SYNTHETIC label propagation; hostile type coverage | REIMPLEMENT (methodology from REUSE-007) | READY (design) — highest priority; build before any security claim |

---

# 22. LOCKED / CONDITIONAL / OPEN / DEFERRED ITEMS

## LOCKED — Approved and ready for specification (no further decision required)

| Item | Source |
|---|---|
| Option A architecture selected | D-AD-001 (project-owner approved 2026-09-25) |
| All-box structural/geometry validation replaces first-box | REUSE-003 |
| SHA-256 exact duplicate detection (M02) in scope | EF-009; AR-006 |
| ONNX structural validation + path containment in scope | G-08; EF-005 |
| PyTorch safe-loading gate with `weights_only=True`, no fallback | RC-013 REJECTED; EF-012 |
| Supervisor-only evidence store writes | AR-002; AF-004 |
| Hash-chained audit trail (fail-closed) | AR-008; AF-001 |
| No aggregate risk score at any layer | G-07; C5 absolute boundary |
| T05d non-claim on C2 AND C3 records (machine-readable) | AR-010; G-11 |
| COVERAGE_GAP_CLEAN_LABEL required field on C2/C3 | AR-010 |
| access_mode non-nullable on C3 bundles | AR-013; G-13 |
| DEFERRED_IN_SCOPE records for all out-of-scope methods | EF-010; G-10 |
| Contributor identity default UNTRUSTED | AR-011; G-12 |
| SYBIL_UNRELIABLE default TRUE | DF-005 |
| PF-002 non-claim on every provenance record | PF-002 |
| ANOMALY_DETECTED ≠ PROVEN_MALICIOUS on every applicable finding | Master Context §3 |
| Blockchain/DLT deferred for MVP | D-AD-004 |
| Behavioral battery deferred for MVP (DEFERRED_IN_SCOPE) | D-AD-005 |
| PDQ near-duplicate deferred for MVP (post-MVP spike) | D-AD-006 |
| R01 code not copied (license unresolved; all REIMPLEMENTED) | P-R-03; REUSE-001 through REUSE-016 |
| R01 Fabric client excluded unconditionally | REUSE-015 |
| R27 COCO API ADOPT/ADAPT (BSD) | REUSE-020 |
| R17 storage patterns EXTRACT (MIT) | REUSE-018 |
| PyTorch version floor ≥2.10.0 | XREG-005 |
| Evidence field defaults = UNAVAILABLE | AR-003 |
| UNAVAILABLE ≠ CLEAN propagation enforced by schema | AR-003; G-06 |

## CONDITIONAL — Can proceed when stated condition is satisfied

| Item | Condition | Status |
|---|---|---|
| Offline deployment claim | Target host specified (PRE-01); wheelhouse verified on target; zero-egress confirmed; ORT telemetry confirmed (EF-003) if applicable | PRE-01 BLOCKING |
| PyTorch in MVP scope | PRE-05 mandatory format list confirmed; CPU wheel confirmed on target | PRE-01 + PRE-05 BLOCKING |
| COCO API C extension build | C extension builds on target host; path handling reviewed | PRE-01 BLOCKING |
| M01 structural validation BUILD claim | Parser fixture gate passes (EVF-001 Layer 1) | Post-implementation |
| Model identity hash BUILD claim | SP-002 artifact-unit definitions frozen (PRE-03) | PRE-03 BLOCKING |
| Provenance binding implementation | PRE-02 (XREG-002), PRE-04 (SP-003), PRE-08 (SP-004), PRE-09 (SP-006) all resolved | PRE-02, PRE-04, PRE-08, PRE-09 BLOCKING |
| Any offline capability claim | C6 Level C target-host execution evidence (EVF-001 Layer 1) | Post-implementation on confirmed target |
| ONNX behavioral battery as MVP extension | All four pre-conditions met before implementation day 1: qualified reference, canonicalization spec frozen, ORT telemetry confirmed, PDQ spike confirmed | Currently UNAVAILABLE |
| PDQ near-duplicate post-MVP | R24 native build confirmed; FPR calibration corpus prepared | Post-MVP spike |
| TorchScript loading | Isolated worker demonstrated on target host | Deferred |
| Reference-relative assessments (M11) | At least one reference completes R0–R7 | Currently UNAVAILABLE for all references |
| Reference health claim HEALTH_VERIFIED | R0–R7 gates completed for the specific reference, scope, and time | Currently UNAVAILABLE |

## OPEN — Not yet decided; blocks specific implementation work

| Item | Blocking what | Resolution path |
|---|---|---|
| PRE-01 / GAP-001: Target host | All offline claims; COMP-W-C3D isolation mechanism; wheel staging; zero-egress confirmation | Project owner / organizer decision |
| PRE-02 / XREG-002: Signing mechanism (HMAC vs. Ed25519) | COMP-C4 design; key management design | Project owner decision |
| PRE-03 / GAP-004 / SP-002: Artifact-unit definitions | COMP-W-C3A; COMP-W-C3B | SP-002 session |
| PRE-04 / GAP-005 / SP-003: Vocabulary contract | COMP-SCHEMA; COMP-C5; all cross-layer integration | SP-003 session |
| PRE-05 / GAP-013: Mandatory format list | YOLO task-variant scope; PyTorch in/out scope; COMP-W-C2A test coverage | Project owner / organizer decision |
| PRE-06 / GAP-009: Blockchain posture | (Expected: DEFER for MVP — but formally open) | Project owner decision |
| PRE-07: COCO API C extension staging | COMP-W-C2A integration | Depends on PRE-01 |
| PRE-08 / GAP-006 / SP-004: Crypto profile | COMP-C4 algorithm identifiers; key-management design | SP-004 session |
| PRE-09 / GAP-014 / SP-006: C3→C4 adapter schema | COMP-C4 ← COMP-W-C3 interface | Depends on PRE-03 + PRE-04 |
| GAP-003: Model access mode at judging | C3 access-mode declaration values; method applicability | Organizer decision |
| GAP-011: Inference record source | Whether and how inference records are ingested | Organizer decision |
| OQ-017: Analyst authentication / authority hierarchy | Analyst disposition recording; COMP-IFACE authentication | Project owner / policy decision |
| OQ-018: Evidence retention policy | COMP-STORE retention; audit trail duration | Project owner decision |
| AF-003: Trusted clock source | Timestamp reliability in provenance records | Deployment environment decision |
| SP-007: PyTorch CVE advisory text | Strength of `weights_only=True` claim; version floor evidence | SP-007 session |
| GAP-010 / XREG-010: M15 evidence ownership | Whether M15 is C2 or C3 evidence; independence declaration | Project owner decision |

## DEFERRED — Intentionally outside MVP scope

| Item | Required for inclusion |
|---|---|
| Behavioral model consistency battery (Option B scope) | All four pre-conditions met (PRE-01, qualified reference, canonicalization spec, ORT telemetry); project-owner authorization |
| PDQ near-duplicate (M03-PDQ) | R24 native build spike confirmed on target; FPR calibration corpus |
| Statistical drift / OOD detection (M04, M05) | GAP-007 FPR calibration gap resolved; SIH operational data available |
| M11 reference-relative data comparison | R0–R7 completed for at least one reference |
| Blockchain / DLT integration | GAP-009 project decision made; separate architecture amendment |
| Activation-space analysis, Neural Cleanse, B3D, ABS, AC | Out of MVP scope; separate authorization required |
| TorchScript safe-loading | Isolated worker demonstrated on target |
| SafeTensors + JSON config loading | YOLO state-dict mapping resolved |
| Grad-CAM analyst explanations | Post-MVP P2; model-architecture coupling resolved |
| FiftyOne analyst tooling | Post-MVP P3; high infrastructure burden |
| External checkpoint / tail completeness | External witness deployment |
| Sybil-resistant contributor identity | External authenticated identity mechanism |
| Analyst authentication and authority hierarchy | OQ-017 policy decision |
| SIH-calibrated drift detection | Real SIH operational data collection |

---

# 23. ARCHITECTURE CHANGE CONTROL

After this document is approved, any change to the following requires an explicit architecture-change decision (proposed change → review → project-owner decision → specification update → implementation):

- Trust boundaries (B1 through B5)
- Core dataflow (Section 5)
- Cryptographic semantics (signing mechanism, algorithm identifiers, key roles)
- Assessment interface contracts (Section 17)
- Security assumptions (supervisor-worker isolation model)
- Persistence semantics (evidence store schema, immutability rules)
- MVP scope boundaries (adding or removing supported formats, methods, or components)
- Evidence schema (any schema change requires version bump and revalidation per ACC-05)

**Specific prohibited changes without change control:**
- Adding any aggregate risk score or compromise probability field
- Adding fail-open audit chain handling
- Adding first-box-only label analysis
- Adding R01 Fabric client or equivalent false-CONNECTED component
- Adding automatic unsafe fallback in PyTorch loading
- Adding a second write path to the evidence store that bypasses COMP-SCHEMA
- Removing COVERAGE_GAP_CLEAN_LABEL or access_mode as required fields
- Removing PF-002 non-claim from provenance records
- Removing DEFERRED_IN_SCOPE records for any currently deferred method

**Implementation agents:** Implementation agents (Codex, Antigravity, or similar) must not propose changes to this architecture without triggering the change-control process. If an implementation agent's proposal conflicts with any constraint in this specification, the conflict must be raised as a proposed change — not silently resolved in the implementation.

**Repository code does not override this specification.** If the codebase diverges from this specification, the specification is the authority unless a formal change-control decision has been made.

---

# 24. NEXT_STAGE_HANDOFF

## CURRENT STAGE

Stage 10 — Architecture Specification

## ARTIFACT

`09_ARCHITECTURE_SPECIFICATION_SIH26228.md`

## ESTABLISHED FACTS (from this stage)

- **F-AS-001:** The architecture is a layered, deterministic, supervisor-bounded evidence system (Option A). Approved 2026-09-25.
- **F-AS-002:** The five trust boundaries (B1–B5) are defined with explicit crossing rules, validation requirements, and failure behaviors.
- **F-AS-003:** All 16 components (COMP-SUP through COMP-FIX) have complete specifications: responsibility, inputs, outputs, dependencies, trust level, failure behavior, security requirements, evidence produced, consumers, interface.
- **F-AS-004:** The end-to-end lifecycle (9 stages from submission to audit) is defined.
- **F-AS-005:** The evidence chain (raw worker output → evidence record → provenance record → C5 finding → analyst disposition event) is specified with all required fields.
- **F-AS-006:** All mandatory non-claims are identified with machine-readable field names: coverage_gap_clean_label, global_backdoor_absence_not_established, pf_002_non_claim, anomaly_not_malicious_non_claim.
- **F-AS-007:** All assessment states (APPLICABLE, COMPLETED, ASSESSMENT_ERROR, UNAVAILABLE, UNSUPPORTED, DEFERRED_IN_SCOPE, ARTIFACT_UNIT_AMBIGUOUS, SCHEMA_VIOLATION, LOAD_BLOCKED, LOAD_SUCCESS, LOAD_ERROR, ONNX_PATH_CONTAINMENT_VIOLATION, REFERENCE_UNAVAILABLE, SIGNING_UNAVAILABLE) are defined.
- **F-AS-008:** All DEFERRED_IN_SCOPE methods are listed (behavioral battery, PDQ, drift/OOD, M11, TorchScript, activation-space analysis, tail completeness, Sybil-resistant T10).
- **F-AS-009:** The implementation readiness matrix covers all 16 components with status (BLOCKED, CONDITIONAL, or READY-design).
- **F-AS-010:** The configuration model distinguishes fixed values, configurable parameters, and policy-controlled settings.

## DECISIONS (from this stage)

- **D-AS-001:** Worker subprocess contract (Section 17.1) is the authoritative interface between workers and supervisor. Implementation must not deviate.
- **D-AS-002:** Evidence store API (Section 17.2) is the authoritative persistence interface.
- **D-AS-003:** CLI interface contract (Section 17.3) is the minimum analyst interface specification.
- **D-AS-004:** Signing module interface (Section 17.4) is the cryptographic binding interface.
- **D-AS-005:** Artifact classes AC-01 through AC-09 are the authoritative data model.
- **D-AS-006:** Assessment states and C5 analyst disposition mapping (Section 16) are authoritative; no additional states may be introduced without change control.
- **D-AS-007:** The UNAVAILABLE ≠ CLEAN invariant is enforced by schema default (all fields default to UNAVAILABLE); positive states require active assessment promotion.

## OPEN QUESTIONS (from this stage)

All P1 blocking conditions (PRE-01 through PRE-09) remain open and block specific components as identified in the implementation readiness matrix. The following are most urgently required:

1. **PRE-01 / GAP-001:** Target host — blocks all offline claims, COMP-W-C3D isolation mechanism, and wheel staging
2. **PRE-02 / XREG-002:** Signing mechanism — blocks COMP-C4 design
3. **PRE-03 / GAP-004 / SP-002:** Artifact-unit definitions — blocks COMP-W-C3A and COMP-W-C3B
4. **PRE-04 / GAP-005 / SP-003:** Vocabulary contract — blocks COMP-SCHEMA, COMP-C5, all cross-layer integration
5. **PRE-05 / GAP-013:** Mandatory format list — blocks YOLO task-variant scope, PyTorch in/out decision
6. **PRE-08 / GAP-006 / SP-004:** Crypto profile — blocks COMP-C4 algorithm identifiers
7. **PRE-09 / GAP-014 / SP-006:** C3→C4 adapter schema — blocks COMP-C4 ← COMP-W-C3 interface

## CONTRADICTIONS (carried forward)

- CONT-R-001: R01 README "air-gapped" vs. "offline after provisioning only." Resolution: R01 not reused; our system requires confirmed zero-egress on target host (EF-003; PRE-01).
- CONT-R-002: R01 F1 .807 vs. .537 — neither is a project metric.
- CONT-R-003: R01 documentation "Fabric 100% operational" vs. local JSON emulator. Resolution: Fabric excluded unconditionally (REUSE-015).
- XREG-008: Multi-cell vocabulary conflict — UNRESOLVED at contract level; SP-003 required (PRE-04).
- XREG-009: T05d gap ownership — PARTIALLY RESOLVED; SP-005 still pending (disclosure path design).
- XREG-010: M15 residual ownership — UNRESOLVED; project-owner decision required (GAP-010).

## IMPORTANT LIMITATIONS (from this stage)

1. This specification defines the architecture but does not constitute implementation authorization. Stage 11 (MVP Implementation Plan) must be produced before implementation begins.
2. No offline claim is currently permissible — GAP-001 (PRE-01) is unresolved and no target-host execution evidence exists.
3. All capabilities described remain research proposals or pre-registered implementation plans. No end-to-end validation evidence exists.
4. The T05d clean-label poisoning coverage gap is permanent under the current baseline. This specification does not close it.
5. The signing mechanism (XREG-002) is not resolved. COMP-C4 cannot be fully specified until PRE-02 and PRE-08 are resolved.
6. The cross-layer vocabulary contract (SP-003) is not produced. COMP-SCHEMA and COMP-C5 cannot be fully specified until PRE-04 is resolved.
7. The hostile fixture suite (COMP-FIX) must be built before any security claim is made. This is the highest implementation priority after the supervisor skeleton and evidence schema.

## DO-NOT-INFER (from this stage)

- Do not infer that this specification authorizes implementation to begin — Stage 11 is still required.
- Do not infer that approval of the architecture resolves the P1 blocking conditions — they remain open.
- Do not infer that any assessed state (COMPLETED, LOAD_SUCCESS, STRUCTURAL_VALID) implies safety, cleanliness, or absence of attacks outside the method scope.
- Do not infer that DEFERRED_IN_SCOPE records mean the deferred method was assessed and found acceptable.
- Do not infer that UNAVAILABLE assessments mean no threat is present.
- Do not infer that a schema-valid evidence record with ANOMALY_DETECTED means malicious intent is proven.
- Do not infer that a valid provenance signature means the named model executed the assessed inferences (PF-002).
- Do not infer that this specification resolves XREG-002 — it describes both signing paths; the project owner must decide.
- Do not infer that format SUPPORTED status in Section 13 means those formats are currently validated — fixture tests must be executed on the target host.
- Do not infer that the implementation readiness status "READY (design)" means implementation can begin without resolving the stated blocking conditions.

## NEXT STAGE INPUTS

For Stage 11 (MVP Implementation Plan), the following must be available or explicitly noted as still-blocking:

1. **This document:** `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` (complete)
2. **Architecture Decision Packet:** `08_ARCHITECTURE_DECISION_PACKET_SIH26228.md` (approval block updated)
3. **P1 condition resolutions (required before final plan):**
   - PRE-01: target host specification
   - PRE-02: XREG-002 signing mechanism decision
   - PRE-03: SP-002 artifact-unit definitions
   - PRE-04: SP-003 vocabulary contract
   - PRE-05: mandatory format list
   - PRE-08: SP-004 crypto profile
   - PRE-09: SP-006 C3→C4 adapter schema
4. **Reuse Matrix:** `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` (binding reuse decisions)
5. **Master Research Bible:** `04_MASTER_RESEARCH_BIBLE_SIH26228__1__new.md` (highest authority)

## NEXT STAGE

**Stage 11 — MVP Implementation Plan**

The MVP Implementation Plan should:
1. Derive a day-by-day implementation sequence from this specification, respecting the component dependency order: supervisor skeleton + evidence schema (COMP-SUP + COMP-SCHEMA + COMP-STORE) first → hostile fixture suite (COMP-FIX) second → workers (COMP-W-C2A through COMP-W-C3D) → COMP-C4 (after P1 conditions resolved) → COMP-C5 → COMP-IFACE → integration + end-to-end test.
2. Name the exact file/module structure for the new project repository.
3. Map each component to an implementation task with a testability gate.
4. Identify which tasks are BLOCKED until which P1 conditions are resolved.
5. Define the hostile fixture suite build as a P0 task (before any security claim is made).
6. Define the UNAVAILABLE propagation test suite as a P0 task (before integration).
7. Budget the hostile-fixture testing priority — it must not be displaced by analyst interface or feature work.
8. NOT authorize specific library versions as final without confirmed target-host execution (except the hard constraints established by research: PyTorch ≥2.10.0 floor).
9. Identify which tasks can proceed in parallel and which are strictly sequential.
10. Define the GitHub branching model consistent with the implementation control rules (one repository; branches = tasks; not two independent versions).

---

# QUALITY CONTROL — STAGE 10 SELF-CHECK

- [x] Project-owner approval verified (verbal confirmation 2026-09-25; note on document update included)
- [x] Specification matches the approved Option A architecture decision
- [x] No rejected architecture (Option B behavioral battery, Option C governance, Blockchain) silently reintroduced
- [x] Trust boundaries (B1–B5) are explicit with crossing rules and failure behaviors
- [x] Component responsibilities are explicit (16 components with complete specifications)
- [x] Inputs and outputs are explicit for every component
- [x] Failure behavior is explicit for every component
- [x] Evidence flow is explicit (Section 9 evidence chain, mandatory non-claims, separation enforcement)
- [x] Provenance semantics match the approved decision (Section 10; XREG-002 acknowledged as open)
- [x] Safe-loading/isolation boundary is explicit (Section 11)
- [x] Offline requirements are explicit (Section 12; conditional on PRE-01)
- [x] Target-format coverage is bounded (Section 13; CONDITIONAL / DEFERRED clearly distinguished from SUPPORTED)
- [x] Reused components have explicit integration boundaries (Section 14)
- [x] No magic architecture decisions invented (all decisions trace to MRB ARs, decision packet decisions, or reuse matrix decisions)
- [x] Configuration and thresholds are traceable (Section 15)
- [x] UNAVAILABLE ≠ CLEAN enforced in state model, schema defaults, and failure contracts
- [x] ANOMALY ≠ PROVEN ATTACK enforced in state model and non-claims
- [x] Open/conditional/deferred items remain explicit (Section 22)
- [x] All 16 major components represented in implementation-readiness table (Section 21)
- [x] NEXT_STAGE_HANDOFF gives Stage 11 everything needed for the MVP Implementation Plan
- [x] All 14 architecture requirements (AR-001 through AR-014) traceable to specification sections
- [x] All 14 hard requirement gates (G-01 through G-14) addressed
- [x] All P1 blocking conditions (PRE-01 through PRE-09) acknowledged and tracked
- [x] PF-002 non-claim appears on every provenance record specification
- [x] T05d COVERAGE_GAP non-claim appears as machine-readable required field on C2 AND C3
- [x] access_mode non-nullable on C3 records specified
- [x] DEFERRED_IN_SCOPE records specified for all out-of-scope methods
- [x] No overall risk score, aggregate assurance score, or compromise probability appears anywhere
- [x] VIKASHL25 architectural failures explicitly excluded (first-box, fake CONNECTED, fail-open audit, aggregate score, synthetic fixture provenance, unqualified battery reference)
- [x] Reuse exclusions explicitly listed (REUSE-015 Fabric client; R13, R04, R05 license issues)
- [x] Architecture change control rules stated (Section 23)

---

**End of document — 09_ARCHITECTURE_SPECIFICATION_SIH26228.md**
**Stage:** 10 — Architecture Specification
**Status:** COMPLETE
**Next stage:** Stage 11 — MVP Implementation Plan (requires P1 conditions to be resolved first)
