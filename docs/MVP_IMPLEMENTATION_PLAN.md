# 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md

## SIH 2026 · PS 26228
### Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines

**Stage:** Stage 12 — MVP Implementation Plan
**Document class:** Task-by-task implementation plan for the five-day MVP build. NOT a new architecture decision. NOT a technical specification. NOT a validation record.
**Status:** COMPLETE — subject to P1 condition resolution before implementation begins
**Input artifacts:**
- `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` (system boundary authority)
- `10_TECHNICAL_SPECIFICATION_SIH26228.md` (implementation contract authority)
- `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` (binding reuse decisions)

**Governing invariants (inherited; absolute; no exception throughout this plan):**
```
UNAVAILABLE ≠ CLEAN
NOT_ASSESSED ≠ CLEAN
DEFERRED_IN_SCOPE ≠ CLEAN
anomaly ≠ malicious intent
ANOMALY ≠ PROVEN ATTACK
raw detector score ≠ compromise probability
```

**Architecture change control: ACTIVE** — Implementation agents (Codex, Antigravity) must not deviate from `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` without a formal change-control decision. This plan does not grant authority to redesign the architecture.

---

# 1. MVP OBJECTIVE

Produce a **validated, integrated, offline-demonstrable assurance system** that:

1. Ingests COCO and YOLO dataset assets and ONNX/PyTorch model artifacts through a supervised pipeline.
2. Applies deterministic integrity assessments (structural/geometry validation, exact duplicate detection, source concentration statistics, image-level hash floor, model identity hashing, ONNX path-containment checking, PyTorch safe-loading gate).
3. Generates cryptographically-bound provenance records and a hash-chained fail-closed audit trail.
4. Produces structured C5 five-layer findings with mandatory UNAVAILABLE propagation, ANOMALY ≠ PROVEN_ATTACK non-claims, and T05d coverage-gap non-claims.
5. Emits explicit DEFERRED_IN_SCOPE records for all out-of-scope methods so analysts see what was not assessed.
6. Provides a read-only analyst interface (CLI + Dashboard + Evidence Explorer + Audit Timeline + Evidence Bundle Export).
7. Runs end-to-end on hostile fixtures in an offline (air-gapped) environment.

**What the MVP is NOT:**
- It is not a behavioral model consistency battery (deferred).
- It is not a PDQ near-duplicate detector (deferred).
- It is not a blockchain/DLT provenance system (deferred).
- It does not produce an overall risk score or compromise probability (prohibited absolutely).
- It does not claim T05d clean-label detection (permanent non-claim).
- It does not claim global backdoor absence from any finite fixture test.

---

# 2. SCOPE BOUNDARY

## 2.1 In MVP scope

| Layer | Capability | Specification authority |
|---|---|---|
| Ingestion | COCO + YOLO + ONNX + PyTorch (.pt/.pth) manifest intake; format detection; path normalization | §09 §2.1, §4 |
| C2 data integrity | All-box COCO/YOLO structural/geometry validation (M01); SHA-256 exact duplicate detection (M02); source concentration statistics + HHI/entropy (M06); image-level hash floor — hash tier only (M15 partial) | §09 §6 |
| C3 model security | Artifact-unit resolver (ONNX path); model SHA-256 identity hasher; ONNX structural validator + path-containment check; PyTorch safe-loading gate (weights_only=True; no fallback) | §09 §6 |
| C4 provenance | Provenance record builder; signing (HMAC-SHA256 or Ed25519 per XREG-002); hash-chained audit chain (fail-closed) | §09 §6, §10 |
| C5 interpretation | Five-layer structured findings; UNAVAILABLE propagation; ANOMALY ≠ PROVEN_ATTACK; T05d non-claim; DEFERRED_IN_SCOPE emitter; ANALYST_DISPOSITION_PROMPT | §09 §6 |
| Persistence | SQLite evidence store (WAL; supervisor-only writes); audit trail; reference registry stub | §10 §3.15 |
| Analyst interface | CLI (all entry points); Dashboard (stdlib http.server); Evidence Explorer; Audit Timeline; Evidence Bundle Export (ZIP) | §09 §2.1, §10 §3.16 |
| Test infrastructure | Hostile fixture suite (COMP-FIX); UNAVAILABLE propagation injectors; reproducibility tests | §10 §19 |

## 2.2 Conditionally in scope (blocked until P1 conditions resolved)

| Capability | Blocking condition | Status |
|---|---|---|
| COCO parsing via pycocotools | PRE-01 (C extension builds on target host) | BLOCKED |
| PyTorch model scope | PRE-01 + PRE-05 (torch CPU wheel; format list confirms PyTorch) | BLOCKED |
| YOLO task-variant scope (seg/pose/OBB) | PRE-05 (mandatory format list) | BLOCKED |
| C4 signing module | PRE-02 + PRE-04 + PRE-08 + PRE-09 all resolved | BLOCKED |
| PyTorch / ONNX artifact-unit definitions | PRE-03 + SP-002-ONNX | RESOLVED: two frozen format-specific records in artifact_unit_defs/ |
| Offline claim | PRE-01 confirmed + wheelhouse verified + zero-egress test passed | BLOCKED |
| COCO/YOLO structural parsing beyond detection format | PRE-05 | BLOCKED |

## 2.3 Pipeline Visualization feature

**Status: SHOULD BUILD — time-permitting only.** Executes after all MUST BUILD items are complete and validated. Shows execution state (running/pending) only — does NOT imply assurance confidence.

---

# 3. MUST BUILD

Every item below is required for a defensible MVP. None may be cut without architecture change control.

| ID | Component | Reason mandatory |
|---|---|---|
| MB-01 | `exceptions.py` + `constants.py` + `config/loader.py` | Type safety and vocabulary foundation for all other components |
| MB-02 | `supervisor/evidence_store.py` (SQLite DDL, write methods, ACL enforcement) | Required store before any evidence can be persisted |
| MB-03 | `supervisor/audit_chain.py` (hash-chained, fail-closed) | Security and provenance integrity non-negotiable |
| MB-04 | `supervisor/schema_validator.py` (custom, no jsonschema package) | Evidence records must be validated before persistence; UNAVAILABLE ≠ CLEAN |
| MB-05 | `workers/base.py` (IPC boilerplate; named temp file; resource-limit enforcement) | All workers require this; supervisor isolation depends on it |
| MB-06 | `fixtures/` — full hostile fixture suite (COMP-FIX) | Required before ANY security test or security claim |
| MB-07 | `workers/c2a_structural.py` — all-box COCO/YOLO structural/geometry validator | M01 is the primary data-integrity floor; first-box approach is prohibited |
| MB-08 | `workers/c2b_exact_hash.py` — SHA-256 exact duplicate detector (stdlib) | M02 is the deterministic duplicate floor |
| MB-09 | `workers/c2c_concentration.py` — source concentration statistics (HHI/entropy; SYBIL_UNRELIABLE) | M06 contributor concentration signal |
| MB-10 | `workers/c2d_image_hash.py` — image-level hash floor (M15 hash tier) | Image identity floor; COVERAGE_GAP_CLEAN_LABEL mandatory on all records |
| MB-11 | `workers/c3a_artifact_unit.py` — ONNX artifact-unit resolver (ONNX path; PyTorch BLOCKED on PRE-03) | Prerequisite for model hashing |
| MB-12 | `workers/c3b_model_hash.py` — model SHA-256 identity hasher | Model identity floor; PF-002 non-claim mandatory |
| MB-13 | `workers/c3c_onnx_structural.py` — ONNX structural validator + path-containment check | Security: path-traversal hostile fixture must pass |
| MB-14 | `workers/c3d_safe_load.py` — PyTorch safe-loading gate (weights_only=True; no fallback; hostile pickle test) | RC-013 REJECTED; no fallback permitted |
| MB-15 | `supervisor/provenance.py` — provenance record builder + signing (BLOCKED on XREG-002 etc.; shell builds; signing completes when PRE-02/08/09 resolved) | PF-002 non-claim mandatory; audit chain entry |
| MB-16 | `supervisor/reference_manager.py` — reference manager stub (all references UNAVAILABLE at MVP start) | REFERENCE_UNAVAILABLE must propagate; not emitting REFERENCE_UNAVAILABLE silently is a project violation |
| MB-17 | `supervisor/capability_declaration.py` — DEFERRED_IN_SCOPE emitter | Every deferred method must produce an explicit record |
| MB-18 | `supervisor/interpretation.py` — C5 assurance interpretation rule engine | Five-layer findings; UNAVAILABLE propagation; non-claim fields mandatory |
| MB-19 | `supervisor/orchestrator.py` — supervisor pipeline controller | Integrates all components; B2 boundary enforcement |
| MB-20 | `interfaces/cli.py` + `cli.py` top-level entry point | Analyst interface — all entry points as specified in §10 §2.4 |
| MB-21 | `interfaces/exporter.py` — evidence bundle export (ZIP) | Required for demo and audit delivery |
| MB-22 | `interfaces/dashboard.py` — read-only stdlib http.server dashboard | MVP value feature; offline; no npm/CDN |
| MB-23 | End-to-end integration test on hostile fixtures (test battery) | Core validation: vertical slice must pass before any capability claim |
| MB-24 | UNAVAILABLE propagation test suite (FIX-013 family) | Non-negotiable; UNAVAILABLE ≠ CLEAN cannot be verified without this |
| MB-25 | weights_only=False grep test — automated in CI from Day 1 | No unsafe fallback must be verifiable at any point in the build |
| MB-26 | Schema files (6 JSON schemas: evidence_record_v1, worker_input_v1, worker_output_v1, provenance_record_v1, finding_v1, deferred_record_v1) | Validation cannot operate without these |
| MB-27 | `config/system_config.yaml` + `config/resource_limits.yaml` + `config/supported_formats.yaml` | No magic numbers; all configurable parameters named |
| MB-28 | Repository setup (`setup.py`/`pyproject.toml`; `requirements.txt` stub; `wheelhouse/` directory; `artifact_unit_defs/` stub) | Offline deployment baseline |
| MB-29 | All `tests/` structure (unit/, integration/, negative/, security/, offline/ stubs with test skeletons) | Acceptance criteria require executable tests |

---

# 4. SHOULD BUILD

Items that substantially strengthen the demo and evidence base, addable without threatening the core path.

| ID | Component | Condition for inclusion | Risk if cut |
|---|---|---|---|
| SB-01 | Pipeline Visualization (execution-state only; no assurance confidence) | All MB items complete and validated | Demo is less visual; no correctness impact |
| SB-02 | Wheel staging verification script (`scripts/verify_wheelhouse.py`) | After PRE-01 resolved | Offline claim cannot be made without it |
| SB-03 | Evidence Explorer (finding → evidence → asset → hash → audit event navigation) | Included as part of Dashboard (see MB-22); can be enhanced if time permits | Core analyst navigation still works via CLI |
| SB-04 | Audit Timeline display (temporal event chain, CHAIN_CORRUPT visibility) | Included in Dashboard; enhanced display if time permits | CLI `show-audit-trail` covers this |
| SB-05 | `scripts/demo.sh` — reproducible end-to-end demo script | After vertical slice validated | Demo can be run manually; script makes it reproducible |

---

# 5. DEFER

Items deferred to post-MVP. Each must receive an explicit DEFERRED_IN_SCOPE record in the system (emitted by COMP-CAP / COMP-SUP).

| ID | Item | Reason for deferral | Record type emitted |
|---|---|---|---|
| DF-01 | PDQ near-duplicate detection (M03-PDQ) | Native build spike not executed; calibration corpus not prepared; R24 CImg.h license exception unresolved | DEFERRED_IN_SCOPE |
| DF-02 | Behavioral model consistency battery (M07 class) | Reference artifact UNAVAILABLE; canonicalization spec (SP-003) unresolved; ORT telemetry unverified | DEFERRED_IN_SCOPE |
| DF-03 | Statistical drift / OOD detection (M04, M05) | Calibration corpus and reference UNAVAILABLE; FPR calibration gap (GAP-007) open | DEFERRED_IN_SCOPE |
| DF-04 | Reference-relative data comparison (M11) | No HEALTH_VERIFIED reference available at MVP | REFERENCE_UNAVAILABLE |
| DF-05 | TorchScript loading | Isolated worker not demonstrated on target; RC-014 state-dict mapping unresolved | DEFERRED_IN_SCOPE |
| DF-06 | SafeTensors + JSON config loading | YOLO state-dict mapping absent (RC-014) | DEFERRED_IN_SCOPE |
| DF-07 | Blockchain/DLT integration | GAP-009 project decision pending | Not represented at MVP |
| DF-08 | Activation-space analysis, Neural Cleanse, B3D, ABS, Activation Clustering | Post-MVP research; require behavioral battery infrastructure | DEFERRED_IN_SCOPE |
| DF-09 | Tail completeness / external checkpoint witness | External witness deployment not in MVP | COMPLETENESS_UNAVAILABLE |
| DF-10 | Sybil-resistant contributor identity authentication | External authenticated identity mechanism not established | SYBIL_UNRELIABLE flag on every C2C record |
| DF-11 | Analyst authentication / authority hierarchy | OQ-017 policy decision pending | analyst_id = 'UNAVAILABLE' on all analyst disposition events |
| DF-12 | Grad-CAM analyst explanations | Model-architecture coupling; post-MVP P2 | Not represented |
| DF-13 | FiftyOne analyst tooling | High infrastructure burden; post-MVP P3 | Not represented |
| DF-14 | SIH-calibrated drift detection | Real SIH operational data required | Not represented |

---

# 6. NOT BUILD

Items permanently excluded. No change-control path exists for these specific exclusions within this project.

| ID | Item | Authority for exclusion |
|---|---|---|
| NB-01 | R01 Fabric client (or any equivalent fake-CONNECTED blockchain facade) | §09 §1.4; REUSE-015 unconditional |
| NB-02 | Aggregate risk score / compromise probability / overall assurance score (any form) | Absolutely prohibited; §09 §1.4; G-07 |
| NB-03 | First-box-only label analysis | Replaced by all-box structural validator; §09 §1.4; REUSE-003 |
| NB-04 | Automatic unsafe fallback in PyTorch loading (weights_only=False at any path) | RC-013 REJECTED; §09 §1.4 |
| NB-05 | Fail-open audit chain handling (any silent swallow of AuditWriteError) | AF-004; §09 §1.4 |
| NB-06 | R13 Alibi-Detect (BSL 1.1 — not open source) | License gate; §07 §1.3 |
| NB-07 | R04 BackdoorBench code reuse (CC BY-NC 4.0 — non-commercial) | License gate; §07 §1.3 |
| NB-08 | R05 BackdoorBox code reuse (GPL-2.0 — copyleft) | License gate; §07 §1.3 |
| NB-09 | Evidence store write path from any worker or analyst interface | AR-002; supervisor-only writes enforced |
| NB-10 | UNAVAILABLE → CLEAN conversion at any layer | AR-003; UNAVAILABLE ≠ CLEAN is an absolute invariant |
| NB-11 | R01 benchmark metrics presented as project results | P-R-06 reuse principle; §07 §2 |
| NB-12 | Second write path to evidence store that bypasses COMP-SCHEMA | §09 §23 change-control |
| NB-13 | DEFERRED_IN_SCOPE presented as CLEAN or ASSESSED | AR-003 extension; explicit in state model |

---

# 7. IMPLEMENTATION TASK REGISTER

## Naming and conventions

- Task IDs: `TASK-###`
- All tasks are MUST BUILD unless explicitly marked `[SHOULD BUILD]` or `[DEFER]`
- Reuse decisions cite the Reuse Matrix ID from `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md`
- Technical Specification section references cite `10_TECHNICAL_SPECIFICATION_SIH26228.md`
- Architecture Specification references cite `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`
- Completion state: `[ ] NOT STARTED` | `[~] IN PROGRESS` | `[x] COMPLETE` | `[!] BLOCKED`

---

### TASK-001 — P1 Condition Resolution (Day 0 prerequisite)

**Name:** Resolve all blocking P1 conditions before implementation begins
**Purpose:** Implementation cannot produce defensible code without these decisions. Coding before P1 resolution produces stubs that will need to be partially rewound.
**Source specification:** §10 §1.4; §09 §22 open conditions
**Dependencies:** None (precedes all implementation)
**Expected output:** Written decision records for each P1 condition:
- PRE-01: target host (OS, Python version, CPU architecture, RAM) — determines wheel staging, C extension compatibility, subprocess isolation mechanism, pycocotools build path
- PRE-02: XREG-002 signing mechanism (HMAC-SHA256 vs Ed25519) — determines cryptography package requirement
- PRE-03: SP-002 artifact-unit definitions (PyTorch path) — determines COMP-W-C3A + C3B PyTorch scope
- PRE-04: SP-003 vocabulary contract + schema version freeze — gates COMP-SCHEMA, COMP-C5, evidence schema DDL
- PRE-05: mandatory format list (YOLO task variants; PyTorch in/out of scope) — gates C2A scope and C3D scope
- PRE-06: SP-001 reference-health gate procedure — gates COMP-REF implementation
- PRE-07: GAP-011 inference record source — gates inference-record ingestion path
- PRE-08: SP-004 crypto profile — gates signing algorithm parameters in COMP-C4
- PRE-09: SP-006 C3→C4 adapter schema — gates evidence-to-provenance binding field list
**Files/modules affected:** All
**Reuse decision:** N/A
**Tests:** N/A (decisions, not code)
**Acceptance criteria:** Written record for each PRE-0x decision. PRE-01 through PRE-05 are the hard gates; without them, no implementation may begin. PRE-06 through PRE-09 can be resolved by Day 1 end; their components can begin with a placeholder shell.
**Risk/blockers:** If PRE-01 is unresolved, no offline claim is permissible and wheel staging cannot be confirmed. If PRE-04 is unresolved, the evidence schema DDL, schema validator, and C5 rule engine cannot be finalized.
**Completion state:** `[!] BLOCKED — must complete before Day 1 of implementation`

---

### TASK-002 — Repository Skeleton

**Name:** Initialize project repository structure
**Purpose:** Establish the authoritative module layout, prevent agents from inventing alternative layouts
**Source specification:** §10 §2.2 (module structure is authoritative)
**Dependencies:** TASK-001 (PRE-04 minimum — schema version needed for schema/ directory naming)
**Expected output:**
- Full directory tree matching §10 §2.2 exactly
- All `__init__.py` files
- `cli.py` top-level entry point (stub)
- `setup.py`/`pyproject.toml` with package name and dependency list (requirements pinned after PRE-01 confirmed)
- `requirements.txt` — pin list stub (frozen after PRE-01)
- `wheelhouse/` — empty directory with README noting pre-staging requirement
- `artifact_unit_defs/` — empty directory with README noting PRE-03 dependency
- `tests/unit/`, `tests/integration/`, `tests/negative/`, `tests/security/`, `tests/offline/` — directories with `__init__.py` and stub test files
- `.gitignore` — excludes `wheelhouse/`, keys, `__pycache__`
**Files/modules affected:** Repository root; all top-level directories
**Reuse decision:** N/A (fresh structure)
**Tests:** `test_repository_structure.py` — verifies all expected paths exist (can run from Day 1)
**Acceptance criteria:** `python -m pytest tests/` exits without import errors; all directories present; top-level `cli.py` importable; no extraneous directories outside the approved layout
**Risk/blockers:** None (can proceed immediately once PRE-04 minimum is resolved)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-003 — Core Type Foundation (exceptions.py + constants.py)

**Name:** Implement project exception hierarchy and state vocabulary constants
**Purpose:** Shared vocabulary prevents agents from inventing inconsistent state strings; exception types enforce fail-closed error handling
**Source specification:** §10 §3.18 (exception hierarchy); §10 §3.2 (state constants); §09 §16.1 (state machine)
**Dependencies:** TASK-002
**Expected output:**
- `assurance_system/exceptions.py` — full exception hierarchy (AssuranceSystemError, WorkerError, SchemaViolationError, AuditWriteError, PipelineError, IngestError, SigningError, etc.)
- `assurance_system/constants.py` — all state string enums:
  - AssessmentStatus: APPLICABLE, COMPLETED, ASSESSMENT_ERROR, UNAVAILABLE, UNSUPPORTED, DEFERRED_IN_SCOPE, ARTIFACT_UNIT_AMBIGUOUS, SCHEMA_VIOLATION, LOAD_BLOCKED, LOAD_SUCCESS, LOAD_ERROR, ONNX_PATH_CONTAINMENT_VIOLATION, REFERENCE_UNAVAILABLE, SIGNING_UNAVAILABLE
  - AnalystDisposition: ACCEPT, ACCEPT_WITH_CONTEXT, ESCALATE, CONTAIN_HOLD, OVERRIDE, UNAVAILABLE_NO_DECISION
  - IdentityQuality: TRUSTED, UNTRUSTED
  - ReferenceHealth: HEALTH_VERIFIED, HEALTH_UNVERIFIED, CONTAMINATION_SUSPECTED, STALE_SUSPECTED, UNAVAILABLE
  - Non-claim field name constants
**Files/modules affected:** `assurance_system/exceptions.py`, `assurance_system/constants.py`
**Reuse decision:** Fresh build (no reuse candidate; defines project-specific vocabulary)
**Tests:**
- `tests/unit/test_constants.py` — verify no state string duplicates; verify UNAVAILABLE default is represented; verify prohibited strings (CLEAN, SAFE, HEALTHY) are NOT present as constants
- `tests/unit/test_exceptions.py` — verify exception hierarchy imports correctly
**Acceptance criteria:** All constants importable; no duplicate values; CLEAN/SAFE/HEALTHY not present as positive state constants; exception hierarchy forms correct inheritance tree
**Risk/blockers:** PRE-04 must be resolved before finalizing vocabulary to ensure SP-003 alignment
**Completion state:** `[ ] NOT STARTED`

---

### TASK-004 — Configuration System

**Name:** Implement configuration loader + YAML config files
**Purpose:** No magic numbers; all thresholds and paths configurable and recorded in evidence
**Source specification:** §10 §3.2 config loader; §09 §15.1 fixed values; §09 §15.2 configurable parameters
**Dependencies:** TASK-003
**Expected output:**
- `assurance_system/config/loader.py` — `ConfigLoader.load()` reads system_config.yaml, resource_limits.yaml, supported_formats.yaml; validates required fields; raises ConfigError on missing required keys; provides typed accessors
- `assurance_system/config/system_config.yaml` — all configurable parameters named (evidence store path, audit trail path, signing key path, schema version, algorithm identifier)
- `assurance_system/config/resource_limits.yaml` — per-worker timeout, memory limit, file-descriptor limit (defaults from §09 §15.2)
- `assurance_system/config/supported_formats.yaml` — format/variant scope declaration (filled after PRE-05 resolved)
**Files/modules affected:** `assurance_system/config/`
**Reuse decision:** Fresh build
**Tests:**
- `tests/unit/test_config_loader.py` — load valid config; detect missing required key; detect invalid type; verify resource_limits accessible per worker type
**Acceptance criteria:** Config loads cleanly on valid YAML; ConfigError raised on missing required field; resource limits accessible by worker module name; supported_formats readable
**Risk/blockers:** PRE-05 blocks `supported_formats.yaml` from being final; use placeholder until resolved
**Completion state:** `[ ] NOT STARTED`

---

### TASK-005 — Evidence Store (SQLite, WAL, supervisor-only writes)

**Name:** Implement SQLite evidence persistence layer
**Purpose:** Supervisor-only, immutable evidence record persistence; foundation for all downstream components
**Source specification:** §10 §3.15 (SQLite DDL, authoritative); §09 §6 COMP-STORE; REUSE-018 (R17 storage patterns, MIT)
**Dependencies:** TASK-003; TASK-004; PRE-04 (schema version freeze)
**Expected output:**
- `assurance_system/supervisor/evidence_store.py`
- Full SQLite DDL as per §10 §3.15 exactly:
  - `evidence_records` table with all fields, CHECK constraints (coverage_gap_clean_label INTEGER CHECK IN (0,1) NOT NULL; schema_version NOT NULL; status NOT NULL)
  - `provenance_records` table
  - `audit_events` table
  - `findings` table
  - `deferred_records` table
  - `reference_health` table
  - `chain_state` table (single-row; last_hash + sequence_number)
  - UNIQUE constraint on replay_nonce
- `EvidenceStore.write_evidence_record()` — supervisor-called; validates schema first
- `EvidenceStore.read_evidence_record()` — read-only; used by analyst interface and C5
- WAL mode enabled on connection
- OS ACL enforcement: store opened only by supervisor process (documented; enforced at deployment)
**Files/modules affected:** `assurance_system/supervisor/evidence_store.py`
**Reuse decision:** REUSE-018 — R17 storage patterns EXTRACT (MIT; attribution required in code header)
**Tests:**
- `tests/unit/test_evidence_store.py`:
  - UT-STORE-001: write valid evidence record; read back; verify field equality
  - UT-STORE-002: write record missing required field → raises SchemaViolationError before DB write
  - UT-STORE-003: write record with risk_score field → rejected (CHECK or application-layer rejection)
  - UT-STORE-004: write record with coverage_gap_clean_label=False → rejected
  - UT-STORE-005: duplicate replay_nonce → UNIQUE constraint violation detected
  - UT-STORE-006: WAL mode confirmed (PRAGMA journal_mode returns 'wal')
**Acceptance criteria:** All 6 unit tests pass; UNIQUE constraint on replay_nonce confirmed; WAL mode confirmed; risk_score field rejection confirmed; no partial writes accepted; attribution comment present in source
**Risk/blockers:** PRE-04 required before final DDL; use schema version placeholder ('v1-pending') until SP-003 resolved
**Completion state:** `[ ] NOT STARTED`

---

### TASK-006 — Audit Chain Writer (fail-closed, hash-chained)

**Name:** Implement hash-chained audit trail writer
**Purpose:** Tamper-detectable audit trail; fail-closed (no swallow of write errors); insertion/deletion detectable
**Source specification:** §10 §3.14 (audit chain); §09 §6 COMP-AUDIT; REUSE-013 (concept HARDEN; REIMPLEMENT code)
**Dependencies:** TASK-005
**Expected output:**
- `assurance_system/supervisor/audit_chain.py`
- `AuditChainWriter.append(event_type, payload_dict)`:
  - Reads last_hash from chain_state table
  - Computes: `event_hash = SHA256(last_hash_hex + event_type + json_canonical(payload_dict) + timestamp + sequence_number)`
  - Inserts audit event and updates chain_state atomically
  - On ANY write failure: raises AuditWriteError — no swallow; no fail-open
- `AuditChainWriter.verify_chain()` — detects modification; emits CHAIN_CORRUPT event (does NOT reset chain)
- Sequence gap detection (sequence_number must be monotonically increasing)
- No external reset or truncation allowed (no reset() method exposed)
**Files/modules affected:** `assurance_system/supervisor/audit_chain.py`
**Reuse decision:** REUSE-013 — HARDEN concept; REIMPLEMENT code (R01 license precludes copy; audit also found fail-open path in R01)
**Tests:**
- `tests/unit/test_audit_chain.py`:
  - UT-AUD-001: append 3 events; verify chain links (each event references previous hash)
  - UT-AUD-002: manually modify stored event; verify_chain() returns CHAIN_CORRUPT
  - UT-AUD-003: simulate AuditWriteError; verify no silent swallow; exception propagates
  - UT-AUD-004: verify no reset() method exists on AuditChainWriter
  - UT-AUD-005: sequence gap injected; detected and flagged
- `tests/security/test_audit_security.py`:
  - SEC-010: modified event detected (CHAIN_CORRUPT emitted; no reset)
**Acceptance criteria:** All 5 unit tests pass; SEC-010 passes; AuditWriteError never swallowed; no reset method; sequence gap detection confirmed; CHAIN_CORRUPT does not reset chain
**Risk/blockers:** None (stdlib hashlib; no P1 dependency for core logic)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-007 — Worker Base (IPC boilerplate; named temp file; resource limits)

**Name:** Implement worker entry-point boilerplate and IPC mechanism
**Purpose:** All workers share the same subprocess invocation pattern; named temp file IPC; resource-limit enforcement; clean failure path
**Source specification:** §10 §3.1 (supervisor dispatch template — authoritative; named temp file IPC); §09 §5 (B2 trust boundary)
**Dependencies:** TASK-003; TASK-004
**Expected output:**
- `assurance_system/workers/base.py`:
  - `build_worker_output(worker_id, assessment_status, raw_signal, limitations, non_claims, ...)` — constructs standard worker output dict; enforces non-null limitations and non_claims; enforces coverage_gap_clean_label=True as default
  - `main(run_assessment_fn)` — reads `--task-file`; calls `run_assessment_fn(task_dict)`; writes result to `--result-file`; on any exception: writes ASSESSMENT_ERROR result to result file (never exits without writing result file)
  - `is_within_directory(path_str, base_dir_str)` — path containment check used by all workers
- Supervisor `_dispatch_worker()` template (in orchestrator, but base.py provides the pattern):
  - Named temp dir with mode 0o700
  - Writes task JSON → task_path
  - Spawns subprocess with stripped env (removes ASSURANCE_KEY_PATH, ASSURANCE_DB_PATH)
  - CWD isolated to worker_tmp
  - Enforces timeout from resource_limits
  - Reads result from result_path
  - Cleans up temp dir on all code paths
  - On timeout/crash/missing result: returns ASSESSMENT_ERROR (never CLEAN)
**Files/modules affected:** `assurance_system/workers/base.py`
**Reuse decision:** Fresh build (implements the B2 boundary that R01 does not have)
**Tests:**
- `tests/unit/test_worker_base.py`:
  - UT-BASE-001: `build_worker_output` with COMPLETED status → valid dict with all required fields
  - UT-BASE-002: `build_worker_output` with empty limitations → raises error (limitations must be non-empty)
  - UT-BASE-003: `build_worker_output` with empty non_claims → raises error
  - UT-BASE-004: `is_within_directory` — file inside base dir → True
  - UT-BASE-005: `is_within_directory` — path traversal attempt (`../`) → False
  - UT-BASE-006: `is_within_directory` — symlink pointing outside → False (uses os.path.realpath)
  - UT-BASE-007: worker subprocess: crashes with exception → result file contains ASSESSMENT_ERROR
  - UT-BASE-008: worker subprocess: times out → supervisor returns ASSESSMENT_ERROR (not hang)
**Acceptance criteria:** All 8 tests pass; no worker can exit without writing result file; no timeout can hang supervisor; path containment rejects traversal and symlink escape; coverage_gap_clean_label defaults to True; stripped env confirmed (key paths absent in worker env)
**Risk/blockers:** PRE-01 for exact subprocess isolation mechanism (use subprocess.Popen as default; adjust after PRE-01 if host requires alternate isolation)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-008 — Schema Validator + JSON Schemas

**Name:** Implement evidence schema validation and produce all 6 JSON schema files
**Purpose:** COMP-SCHEMA is the gatekeeper before any evidence record enters the store; schema violation must produce audit event, not a silent bad record
**Source specification:** §10 §3.2 (schema validator); §10 §4 (JSON schemas); PRE-04 BLOCKING for final freeze
**Dependencies:** TASK-003; TASK-005; TASK-004; PRE-04 (vocabulary contract)
**Expected output:**
- `assurance_system/supervisor/schema_validator.py`:
  - `SchemaValidator.validate(record_dict, schema_name)` — custom validation (no jsonschema package per §10 §2.1); checks required fields, types, allowed values, prohibited fields (risk_score), mandatory non-null coverage_gap_clean_label=1 on C2/C3 records, access_mode non-nullable on C3 records
  - Returns (is_valid: bool, violations: list[str])
  - Does NOT raise on validation failure; raises only on internal validator error
- Schema files (all in `assurance_system/schema/`):
  - `evidence_record_v1.schema.json`
  - `worker_input_v1.schema.json`
  - `worker_output_v1.schema.json`
  - `provenance_record_v1.schema.json`
  - `finding_v1.schema.json`
  - `deferred_record_v1.schema.json`
**Files/modules affected:** `assurance_system/supervisor/schema_validator.py`; `assurance_system/schema/*.json`
**Reuse decision:** Fresh build (custom validator by design — no jsonschema package; per §10 §2.1)
**Tests:**
- `tests/unit/test_schema_validator.py`:
  - UT-SCHEMA-001: valid evidence record → (True, [])
  - UT-SCHEMA-002: missing required field → (False, [violation_description])
  - UT-SCHEMA-003: risk_score field present → (False, [violation_description]) — SEC-011
  - UT-SCHEMA-004: coverage_gap_clean_label=0 (False) on C2 record → (False, ...)  — SEC-012
  - UT-SCHEMA-005: access_mode null on C3 record → (False, ...)
  - UT-SCHEMA-006: invalid assessment_status value → (False, ...)
  - UT-SCHEMA-007: UNAVAILABLE field (valid — should pass)
  - UT-SCHEMA-008: all required fields present, all correct types → (True, [])
- `tests/security/test_schema_security.py`:
  - SEC-011: risk_score field rejected — no evidence record written
  - SEC-012: coverage_gap_clean_label=False rejected — no evidence record written
**Acceptance criteria:** All 8 unit tests pass; SEC-011, SEC-012 pass; risk_score field never enters evidence store; coverage_gap_clean_label=False never enters evidence store; no jsonschema import in codebase (grep check)
**Risk/blockers:** PRE-04 blocks final vocabulary freeze; build with pending-vocabulary placeholder; update when SP-003 produced
**Completion state:** `[ ] NOT STARTED`

---

### TASK-009 — Hostile Fixture Suite (P0 — must precede security tests)

**Name:** Build complete COMP-FIX hostile fixture suite and synthetic attack generator
**Purpose:** No security test or security claim may be made before hostile fixtures exist; this is a P0 task per §10 §19 Tier 2-B
**Source specification:** §09 §6 COMP-FIX; §10 §17 (test requirements); §10 §18 (experiment contracts); REUSE-007 (methodology KEEP; code REIMPLEMENT)
**Dependencies:** TASK-007 (path containment utility); TASK-003 (constants)
**Expected output:**
- `assurance_system/fixtures/generator.py` — CLI: `python -m assurance_system.fixtures.generator <fixture-type> --output <dir> --seed <n>`
- `assurance_system/fixtures/hostile/pickle_payload.py` — FIX-001: hostile pickle that triggers UnpicklingError under weights_only=True; seed-pinned; SYNTHETIC label
- `assurance_system/fixtures/hostile/onnx_path_traversal.py` — FIX-004: absolute path in external data manifest; FIX-005: `..` traversal; FIX-006: symlink escape; all SYNTHETIC labeled
- `assurance_system/fixtures/hostile/archive_bomb.py` — FIX-007: archive bomb (limited; zip bomb pattern); SYNTHETIC label
- `assurance_system/fixtures/hostile/coco_geometry.py` — FIX-008: known geometry violations (negative coordinates, area=0, out-of-range category IDs, NaN coords, truncated bounding boxes) injected into COCO JSON; seed-pinned; all-box coverage; manifest records expected violation count per type
- `assurance_system/fixtures/hostile/yolo_geometry.py` — FIX-009: equivalent for YOLO detection format; expandable to seg/pose/OBB after PRE-05
- `assurance_system/fixtures/hostile/exact_duplicate.py` — FIX-010: known exact-duplicate file pairs; FIX-011: known non-duplicate control pairs
- `assurance_system/fixtures/hostile/sybil_corpus.py` — FIX-012: synthetic SYBIL fragmentation corpus (single source masquerading as many; known HHI=1)
- `assurance_system/fixtures/hostile/unavailable_injector.py` — FIX-013: UNAVAILABLE injection at each of 4 pipeline layers (ingestion, C2 output, C3 output, C4 output)
- `assurance_system/fixtures/hostile/schema_violation.py` — FIX-018: record with risk_score field present; FIX-019: record with coverage_gap_clean_label=False
- `assurance_system/fixtures/hostile/benign.py` — FIX-015: benign PyTorch model (loads cleanly under weights_only=True); FIX-016: valid COCO annotation; FIX-017: valid YOLO annotation
- `assurance_system/fixtures/hostile/oom_trigger.py` — FIX-002: OOM trigger (allocates large memory); timeout trigger FIX-003 (infinite loop)
- Fixture manifest: every fixture directory contains `manifest.json` with {fixture_id, seed, expected_result, is_synthetic: true}
**Files/modules affected:** `assurance_system/fixtures/`
**Reuse decision:** REUSE-007 — methodology KEEP from R01 attack generator; code REIMPLEMENT (R01 license; additional hostile fixture types added)
**Tests:**
- `tests/unit/test_fixture_generator.py`:
  - REPRO-006: fixture generator with same seed → same output on two runs
  - verify all fixture output files carry is_synthetic=True in manifest
  - FIX-001 hostile pickle: loads without error when opened as bytes; raises UnpicklingError under torch.load with weights_only=True
**Acceptance criteria:** All 14+ fixture types generated successfully; all carry SYNTHETIC label; all have seed-pinned reproducibility confirmed; hostile pickle confirmed to trigger UnpicklingError under weights_only=True; COCO geometry fixture violation count matches manifest
**Risk/blockers:** FIX-001 requires torch installed to verify (blocked until PRE-01 + PRE-05 if PyTorch in scope); FIX-009 YOLO variants blocked on PRE-05 for scope; build FIX-001 verification test as conditional skip until torch available
**Completion state:** `[ ] NOT STARTED`

---

### TASK-010 — COMP-W-C2A: All-Box Structural/Geometry Validator

**Name:** Implement COCO/YOLO all-box structural and geometry validator worker
**Purpose:** M01 data integrity floor; first-box approach is unconditionally prohibited; all violations must be detected
**Source specification:** §10 §3.3; REUSE-001 (REIMPLEMENT — R01 code not copied; R27 pycocotools ADOPT/ADAPT); REUSE-020 (R27)
**Dependencies:** TASK-007 (base.py); TASK-009 (fixture suite — tests require FIX-008/009); PRE-05 (YOLO variant scope)
**Expected output:**
- `assurance_system/workers/c2a_structural.py`
- Pseudocode per §10 §3.3, fully implemented:
  - COCO path: pycocotools for format parsing; then all-box geometry validation (every annotation in the file; no first-box shortcut); checks: bounding box coordinates in image dimensions, area > 0, category ID in declared categories, image ID exists, NaN/Inf in any numeric field
  - YOLO path: per-format parser for detection/seg/pose/OBB (scope per PRE-05); all-box validation
  - Returns: `violations_by_type` (dict), `violation_count`, `total_boxes_checked`, `task_variant`
  - `C2A_LIMITATIONS` and `C2A_NON_CLAIMS` as hardcoded non-suppressible strings per §10 §3.3
  - `coverage_gap_clean_label=True` on all records
- Path containment re-check on every file path before opening
**Files/modules affected:** `assurance_system/workers/c2a_structural.py`
**Reuse decision:** REUSE-001 (logic reference; REIMPLEMENT code) + REUSE-020 (R27 pycocotools ADOPT/ADAPT, BSD license, attribution required)
**Tests:**
- `tests/unit/test_c2a_structural.py`:
  - UT-C2A-001: valid COCO annotation → COMPLETED; violation_count=0
  - UT-C2A-002: FIX-008 geometry violations → COMPLETED; violations match expected manifest count per type
  - UT-C2A-003: empty annotation file → COMPLETED; 0 boxes checked; limitations note empty input
  - UT-C2A-004: multi-object scene → all boxes checked (total_boxes_checked = known total) — **all-box coverage test; must pass before any data-integrity claim**
  - UT-C2A-005: malformed JSON → ASSESSMENT_ERROR; worker exits cleanly
  - UT-C2A-006: NaN coordinate in COCO box → COMPLETED; NaN violation recorded
  - UT-C2A-007: coverage_gap_clean_label=True on every output record
  - UT-C2A-008 [conditional on PRE-05]: YOLO detection format valid → COMPLETED; violations=0
  - UT-C2A-009 [conditional on PRE-05]: YOLO detection geometry violation → violation detected
**Acceptance criteria:** UT-C2A-001 through UT-C2A-007 pass; UT-C2A-004 (all-box coverage) is mandatory before any M01 claim; coverage_gap_clean_label confirmed on all output; C2A_LIMITATIONS and C2A_NON_CLAIMS present on all records; STRUCTURAL_VALID claim limited to tested violations types only
**Risk/blockers:** pycocotools C extension build blocked on PRE-01; YOLO variant scope blocked on PRE-05; build with pure-Python COCO parser fallback stub for early testing if pycocotools not yet available
**Completion state:** `[ ] NOT STARTED`

---

### TASK-011 — COMP-W-C2B: SHA-256 Exact Duplicate Detector

**Name:** Implement SHA-256 exact duplicate detection worker (stdlib only)
**Purpose:** M02 exact duplicate floor; deterministic; no external dependency
**Source specification:** §10 §3.4; REUSE-002a (REIMPLEMENT with stdlib)
**Dependencies:** TASK-007 (base.py); TASK-009 (fixture suite — FIX-010/011)
**Expected output:**
- `assurance_system/workers/c2b_exact_hash.py`
- Algorithm per §10 §3.4 exactly:
  - Path containment re-check per file
  - SHA-256 chunked streaming (64 KB chunks; handles large files)
  - `digest_map`, `duplicate_groups`, `file_digest_map` — all populated
  - `pdq_status: 'DEFERRED_IN_SCOPE'` in raw_signal
  - `coverage_gap_clean_label=True` on all records
  - All limitations and non_claims per §10 §3.4
**Files/modules affected:** `assurance_system/workers/c2b_exact_hash.py`
**Reuse decision:** REUSE-002a — REIMPLEMENT with Python stdlib `hashlib` (R01 code not copied; SHA-256 implementation is trivial and avoids license issues)
**Tests:**
- `tests/unit/test_c2b_exact_hash.py`:
  - UT-C2B-001: known duplicate pair (FIX-010) → duplicate_group_count=1; paths both in group
  - UT-C2B-002: known non-duplicate pair (FIX-011) → duplicate_group_count=0
  - UT-C2B-003: path containment violation → excluded from results; error_files populated
  - UT-C2B-004: unreadable file → error_files populated; other files assessed
  - UT-C2B-005: pdq_status='DEFERRED_IN_SCOPE' in raw_signal
  - UT-C2B-006: coverage_gap_clean_label=True confirmed
  - REPRO-002: same image → same SHA-256 on two runs
**Acceptance criteria:** All 6 tests + REPRO-002 pass; no external library (import audit — stdlib hashlib only); duplicate presence non-claim present; PDQ noted as DEFERRED_IN_SCOPE
**Risk/blockers:** None (stdlib only; no P1 dependency)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-012 — COMP-W-C2C: Source Concentration Statistics

**Name:** Implement source concentration statistics worker (HHI/entropy; SYBIL_UNRELIABLE)
**Purpose:** M06 contributor concentration signal; SYBIL_UNRELIABLE mandatory; no aggregate risk score
**Source specification:** §10 §3.5; REUSE-006 (REIMPLEMENT)
**Dependencies:** TASK-007 (base.py)
**Expected output:**
- `assurance_system/workers/c2c_concentration.py`
- Algorithm per §10 §3.5 exactly:
  - HHI (Herfindahl-Hirschman Index): `sum(s**2 for s in shares.values())`
  - Shannon entropy: `-sum(s * math.log2(s) for s in shares.values() if s > 0)`
  - `sybil_unreliable = (identity_quality != 'TRUSTED')` — True by default
  - No aggregate risk score field anywhere
  - All limitations and non_claims per §10 §3.5
  - Missing metadata → ASSESSMENT_ERROR (not CLEAN)
**Files/modules affected:** `assurance_system/workers/c2c_concentration.py`
**Reuse decision:** REUSE-006 — REIMPLEMENT (R01 code not copied; aggregate risk score removed; SYBIL_UNRELIABLE added)
**Tests:**
- `tests/unit/test_c2c_concentration.py`:
  - UT-C2C-001: single-source corpus (FIX-012) → HHI=1.0; entropy=0; sybil_unreliable=True
  - UT-C2C-002: uniform 10-source corpus → HHI=0.1; entropy≈3.32
  - UT-C2C-003: missing contributor_metadata → ASSESSMENT_ERROR
  - UT-C2C-004: identity_quality='TRUSTED' → sybil_unreliable=False
  - UT-C2C-005: identity_quality='UNTRUSTED' → sybil_unreliable=True
  - UT-C2C-006: no risk_score field in output
**Acceptance criteria:** All 6 tests pass; no risk_score field; HHI and entropy values mathematically correct; sybil_unreliable defaults True; non_claims include "No aggregate risk score is produced"
**Risk/blockers:** None (stdlib math only; no P1 dependency for core logic)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-013 — COMP-W-C2D: Image-Level Hash Floor (M15 hash tier)

**Name:** Implement image-level hash floor worker (SHA-256 per image; COVERAGE_GAP_CLEAN_LABEL mandatory)
**Purpose:** M15 image identity floor; coverage gap for T05d clean-label attacks is permanent and must appear on every record
**Source specification:** §10 §3.6 (C2D algorithm); REUSE-005 (EXTRACT hash logic; REIMPLEMENT code)
**Dependencies:** TASK-007 (base.py)
**Expected output:**
- `assurance_system/workers/c2d_image_hash.py`
- Per-image SHA-256 streaming hash (same chunked pattern as C2B)
- Hash tier only (PDQ: DEFERRED_IN_SCOPE noted in output)
- `coverage_gap_clean_label=True` hardcoded and non-suppressible
- Non-claim: "Clean-label poisoning (T05d) is not detectable by image hashing" — on every record
- Limitations: scope bounded to exact-match detection only
**Files/modules affected:** `assurance_system/workers/c2d_image_hash.py`
**Reuse decision:** REUSE-005 — EXTRACT hash logic concept; REIMPLEMENT code (R01 license precludes copy; attribution claim for image-level hashes must not travel with any detection framing from R01)
**Tests:**
- `tests/unit/test_c2d_image_hash.py`:
  - UT-C2D-001: known image → deterministic SHA-256 hash (REPRO-002 pattern)
  - UT-C2D-002: coverage_gap_clean_label=True on all records
  - UT-C2D-003: T05d non-claim present in non_claims list
  - UT-C2D-004: PDQ noted as DEFERRED_IN_SCOPE in raw_signal
**Acceptance criteria:** All 4 tests pass; coverage_gap_clean_label=True non-suppressible; T05d non-claim present; PDQ DEFERRED_IN_SCOPE noted
**Risk/blockers:** None (stdlib hashlib; no P1 dependency)
**Completion state:** `[ ] NOT STARTED`

---

### TASK-014 — COMP-W-C3A: Artifact-Unit Resolver

**Name:** Implement ONNX artifact-unit resolver (frozen SP-002 format definitions)
**Purpose:** Resolve which files constitute the artifact-unit for each model format; prerequisite for model hashing
**Source specification:** §10 §3.7 (C3A algorithm); §09 §6 COMP-W-C3A; REUSE-008 (concept HARDEN; REIMPLEMENT)
**Dependencies:** TASK-007 (base.py); PRE-03 (for PyTorch path)
**Expected output:**
- `assurance_system/workers/c3a_artifact_unit.py`
- ONNX path (unblocked): resolves main `.onnx` + all external data files referenced in ExternalDataInfo; path containment check on each external data path; emits ONNX_PATH_CONTAINMENT_VIOLATION if any external data path escapes the asset directory
- PyTorch path: `pytorch-single-file-v1` (PRE-03 resolved); incomplete units remain ARTIFACT_UNIT_AMBIGUOUS
- ONNX path: `onnx-main-referenced-external-data-v1` (SP-002-ONNX resolved); complete recursive reference discovery, unique canonical regular members, whole external-file bytes, no unreferenced neighbours
- `access_mode` field: non-nullable; populated from task spec
- PF-002 non-claim: `hash_match_not_safe = True` on every record
**Files/modules affected:** `assurance_system/workers/c3a_artifact_unit.py`
**Reuse decision:** REUSE-008 — HARDEN concept; REIMPLEMENT code
**Tests:**
- `tests/unit/test_c3a_artifact_unit.py`:
  - UT-C3A-001: valid ONNX (no external data) → unit = [main .onnx]; path containment check passes
  - UT-C3A-002: ONNX with valid external data → unit includes external file; path check passes
  - UT-C3A-003: FIX-004 absolute path in external data → ONNX_PATH_CONTAINMENT_VIOLATION
  - UT-C3A-004: FIX-005 traversal path in external data → ONNX_PATH_CONTAINMENT_VIOLATION (SEC-004)
  - UT-C3A-005: FIX-006 symlink in external data → ONNX_PATH_CONTAINMENT_VIOLATION (SEC-006)
  - UT-C3A-006: access_mode non-null confirmed on all records
  - UT-C3A-007: pf_002_non_claim present and True on all records
**Acceptance criteria:** All 7 tests pass; SEC-004, SEC-005, SEC-006 pass via this worker; access_mode non-null confirmed; PF-002 non-claim present; unresolved/incomplete units emit ARTIFACT_UNIT_AMBIGUOUS
**Risk/blockers:** Frozen definitions are resolved; missing ONNX runtime still fails closed. HOST-CAP-003 procedural re-entry remains separate from passing real component acceptance.
**Completion state:** `[x] TESTED` — 30 targeted tests and real ONNX identity/supervisor acceptance pass; see `docs/validation/e2_onnx_identity_acceptance.md`.

---

### TASK-015 — COMP-W-C3B: Model SHA-256 Identity Hasher

**Name:** Implement model artifact-unit identity hasher
**Purpose:** Model identity floor; PF-002 non-claim mandatory on every record; MATCH ≠ SAFE
**Source specification:** §10 §3.8 (C3B algorithm); REUSE-008
**Dependencies:** TASK-014 (C3A — artifact unit must be resolved before hashing); TASK-007 (base.py)
**Expected output:**
- `assurance_system/workers/c3b_model_hash.py`
- Hashes all files in artifact unit (from C3A output); combines into `combined_digest` (SHA-256 of sorted per-file digests concatenated)
- `access_mode` non-nullable (passed through from C3A)
- PF-002 non-claim fields: `hash_match_not_safe=True`; `hash_match_not_semantically_equivalent=True`; `hash_match_not_causal_execution_proof=True`
- ARTIFACT_UNIT_AMBIGUOUS from C3A → C3B emits BLOCKED (not CLEAN)
**Files/modules affected:** `assurance_system/workers/c3b_model_hash.py`
**Reuse decision:** REUSE-008 — HARDEN + REIMPLEMENT (PF-002 non-claim; ONNX external data inclusion; ARTIFACT_UNIT_AMBIGUOUS propagation)
**Tests:**
- `tests/unit/test_c3b_model_hash.py`:
  - UT-C3B-001: known artifact unit → deterministic combined_digest (REPRO-003)
  - UT-C3B-002: tampered file in unit → different combined_digest
  - UT-C3B-003: ARTIFACT_UNIT_AMBIGUOUS from C3A → C3B returns BLOCKED, not a hash
  - UT-C3B-004: PF-002 non-claim fields present and True on all records
  - REPRO-003: same artifact unit → same combined_digest on two runs
**Acceptance criteria:** All 4 tests + REPRO-003 pass; PF-002 non-claim fields present; ARTIFACT_UNIT_AMBIGUOUS propagates correctly; combined_digest is deterministic
**Risk/blockers:** Depends on a COMPLETED C3A unit; ambiguous diagnostic partial membership is not forwarded for hashing. E-2 resolved; C3B remains stdlib-only and does not import ONNX.
**Completion state:** `[x] TESTED` — 18 targeted tests plus real frozen-definition ONNX identity/supervisor acceptance pass; existing ordered inner/outer SHA-256 unchanged.

---

### TASK-016 — COMP-W-C3C: ONNX Structural Validator + Path Containment

**Name:** Implement ONNX structural validator worker
**Purpose:** Validates ONNX graph structure; enforces path containment on external data; security-critical
**Source specification:** §10 §3.9 (C3C algorithm); REUSE-009 (path containment adds to R01 loader REPLACE)
**Dependencies:** TASK-007 (base.py); TASK-014 (C3A for artifact unit paths); onnx package staged
**Expected output:**
- `assurance_system/workers/c3c_onnx_structural.py`
- `onnx.load(path, load_external_data=False)` for initial structural check (no data loading)
- `onnx.checker.check_model(model)` — structural validation
- Path containment check on all external data paths in model
- Does NOT run OnnxRuntime; structural only
- access_mode non-nullable
- PF-002 non-claim: STRUCTURAL_VALID ≠ behavioral safety ≠ semantic equivalence
**Files/modules affected:** `assurance_system/workers/c3c_onnx_structural.py`
**Reuse decision:** REUSE-009 — REPLACE R01 model loader approach; path containment is new security requirement
**Tests:**
- `tests/unit/test_c3c_onnx_structural.py`:
  - UT-C3C-001: valid minimal ONNX model → STRUCTURAL_VALID; COMPLETED
  - UT-C3C-002: FIX-004 ONNX absolute path → ONNX_PATH_CONTAINMENT_VIOLATION (SEC-004)
  - UT-C3C-003: FIX-005 ONNX traversal → ONNX_PATH_CONTAINMENT_VIOLATION (SEC-005)
  - UT-C3C-004: malformed ONNX (invalid protobuf) → ASSESSMENT_ERROR; worker exits cleanly
  - UT-C3C-005: PF-002 non-claim: STRUCTURAL_VALID ≠ safe
**Acceptance criteria:** All 5 tests pass; SEC-004, SEC-005 pass; no ORT dependency; PF-002 non-claim present; structural-validity claim bounded to format validation only
**Risk/blockers:** onnx package staged blocked on PRE-01
**Completion state:** `[ ] NOT STARTED`

---

### TASK-017 — COMP-W-C3D: PyTorch Safe-Loading Gate

**Name:** Implement PyTorch safe-loading gate worker (weights_only=True; no fallback absolutely prohibited)
**Purpose:** Blocks hostile pickle artifacts; RC-013 REJECTED means no fallback path in any code path
**Source specification:** §10 §3.10 (C3D algorithm); REUSE-009; RC-013 REJECTED; XREG-005 (≥2.10.0 floor)
**Dependencies:** TASK-007 (base.py); TASK-009 (FIX-001 hostile pickle; FIX-015 benign); torch CPU wheel staged (PRE-01 + PRE-05)
**Expected output:**
- `assurance_system/workers/c3d_safe_load.py`
- `torch.load(path, map_location='cpu', weights_only=True)` — only this call; no other load path
- On `UnpicklingError` or `Exception`: LOAD_BLOCKED (not ASSESSMENT_ERROR — this is a detection signal)
- `fallback_attempted=False` on ALL records — mandatory field
- `access_mode` non-nullable
- PF-002 non-claim: LOAD_SUCCESS ≠ behavioral safety
- LOAD_BLOCKED non-claim: LOAD_BLOCKED ≠ PROVEN_MALICIOUS; ANOMALY ≠ PROVEN_ATTACK
**Files/modules affected:** `assurance_system/workers/c3d_safe_load.py`
**Reuse decision:** REUSE-009 — REPLACE R01 loader entirely (adds fallback_attempted field; removes any fallback path; adds PF-002/anomaly non-claims)
**Tests:**
- `tests/unit/test_c3d_safe_load.py`:
  - UT-C3D-001: FIX-001 hostile pickle → LOAD_BLOCKED; fallback_attempted=False (SEC-001)
  - UT-C3D-002: FIX-015 benign model → LOAD_SUCCESS; fallback_attempted=False
  - UT-C3D-003: FIX-002 OOM trigger → worker killed; supervisor gets ASSESSMENT_ERROR (SEC-002)
  - UT-C3D-004: FIX-003 hang trigger → ASSESSMENT_ERROR after timeout_seconds; supervisor not hung (SEC-003)
  - UT-C3D-005: LOAD_BLOCKED non-claim present (ANOMALY ≠ PROVEN_ATTACK)
  - UT-C3D-006: LOAD_SUCCESS non-claim present (LOAD_SUCCESS ≠ behavioral safety)
- `tests/security/test_c3d_security.py`:
  - SEC-001: hostile pickle → LOAD_BLOCKED; no code execution in supervisor; fallback_attempted=False
  - SEC-002: OOM → worker killed; ASSESSMENT_ERROR; supervisor continues
  - SEC-003: hang → ASSESSMENT_ERROR after timeout; supervisor not hung
  - Windows SEC-002 uses approved ACC-2026-10-02-01 Job Object committed-memory
    containment: configure from `ResourceLimits.memory_limit_mb`, create
    suspended, assign before execution, then resume; Unix/Linux RLIMIT behavior
    remains unchanged.
- `tests/security/test_no_unsafe_fallback.py`:
  - SEC-007: grep weights_only=False in entire codebase → 0 matches
**Acceptance criteria:** All tests pass; SEC-001 through SEC-003 pass; SEC-007 passes (0 matches for weights_only=False across entire codebase); fallback_attempted=False on all records
**Risk/blockers:** torch CPU wheel blocked on PRE-01; PyTorch scope blocked on PRE-05; build as conditional module with skip-if-torch-unavailable test marks until PRE-01 resolved
**Completion state:** `[ ] NOT STARTED`

---

### TASK-018 — COMP-REF: Reference Manager

**Name:** Implement reference manager (all references UNAVAILABLE at MVP start)
**Purpose:** REFERENCE_UNAVAILABLE must propagate correctly; COMP-REF must never emit HEALTH_VERIFIED without completed R0–R7 gates
**Source specification:** §09 §6 COMP-REF; PRE-06 (SP-001) BLOCKING for gate procedure
**Dependencies:** TASK-005 (evidence_store for reference_health table); TASK-003 (constants)
**Expected output:**
- `assurance_system/supervisor/reference_manager.py`
- `ReferenceManager.get_health_state(reference_id)` — returns UNAVAILABLE at MVP (no references have completed R0–R7)
- `ReferenceManager.update_health_state(reference_id, new_state, evidence)` — supervisor-only; records state transition as audit event
- Cannot promote to HEALTH_VERIFIED without gate completion record
- FORMAT_ASSET ≠ HEALTH_VERIFIED distinction enforced: COCO val2017 is FORMAT_ASSET, not HEALTH_VERIFIED
- REFERENCE_CATEGORY_VIOLATION emitted if FORMAT_ASSET used as if HEALTH_VERIFIED
**Files/modules affected:** `assurance_system/supervisor/reference_manager.py`
**Reuse decision:** Fresh build (no reuse candidate)
**Tests:**
- `tests/unit/test_reference_manager.py`:
  - UT-REF-001: no references registered → get_health_state() returns UNAVAILABLE
  - UT-REF-002: FORMAT_ASSET registered (COCO val2017) → HEALTH_VERIFIED NOT returned; REFERENCE_CATEGORY_VIOLATION on inappropriate use
  - UT-REF-003: health state transition logged as audit event
**Acceptance criteria:** All 3 tests pass; HEALTH_VERIFIED never returned without gate completion; FORMAT_ASSET ≠ HEALTH_VERIFIED enforced
**Risk/blockers:** PRE-06 blocks full gate procedure; build MVP shell (returns UNAVAILABLE always) and expand when SP-001 produced
**Completion state:** `[ ] NOT STARTED`

---

### TASK-019 — COMP-C4: Provenance Record Builder + Signing

**Name:** Implement provenance record builder and signing module
**Purpose:** Cryptographic binding of evidence to artifacts; PF-002 non-claim mandatory; signing BLOCKED on XREG-002 etc. but shell builds
**Source specification:** §10 §8 (provenance + signing); §09 §6 COMP-C4; REUSE-012 (HARDEN concept; REIMPLEMENT code); PRE-02, PRE-04, PRE-08, PRE-09 BLOCKING for signing
**Dependencies:** TASK-006 (audit chain); TASK-005 (evidence store for digest reads); TASK-003 (constants); PRE-02, PRE-04, PRE-08, PRE-09
**Expected output:**
- `assurance_system/supervisor/provenance.py`
- Provenance record schema: binds artifact-unit digest + evidence record digests + timestamp + replay nonce (UUID4) + sequence number + PF-002 non-claim fields
- `ProvenanceBuilder.build_and_sign(artifact_digest, evidence_record_ids)` → provenance record
- Canonicalization: `json-canonical-utf8-sort-keys-v1` algorithm (per §10 §3.12; pending SP-003 confirmation)
- Signing:
  - HMAC path: `hmac.new(key, canonical_bytes, hashlib.sha256).digest()` — stdlib only
  - Ed25519 path: `cryptography` package (staged wheel) — if XREG-002 selects Ed25519
  - Both paths output same field names; algorithm ID recorded
- `SIGNING_UNAVAILABLE` if key not accessible (pipeline continues; signing claim blocked)
- Replay nonce: UUID4; UNIQUE DB constraint enforces non-reuse
- Sequence nonce: monotonically increasing; gap detected in audit chain
- PF-002 non-claim: `signed_commitment_not_causal_execution_proof = True` on every record
**Files/modules affected:** `assurance_system/supervisor/provenance.py`
**Reuse decision:** REUSE-012 — HARDEN + REIMPLEMENT (replay nonce added; durable sequence state; supervisor-only key access)
**Tests:**
- `tests/unit/test_provenance.py`:
  - UT-C4-001: build provenance record; PF-002 non-claim field present and True
  - UT-C4-002: replay attack — duplicate nonce → REPLAY_ATTEMPT_DETECTED (SEC-009)
  - UT-C4-003: sequence gap → audit event flagged
  - UT-C4-004 [conditional on XREG-002]: HMAC signing path produces consistent signature for same input
  - UT-C4-005 [conditional on XREG-002 + Ed25519]: Ed25519 signature verifiable with public key
  - UT-C4-006: key unavailable → SIGNING_UNAVAILABLE in record; pipeline continues
- `tests/security/test_provenance_security.py`:
  - SEC-009: duplicate replay_nonce rejected; REPLAY_ATTEMPT_DETECTED emitted
**Acceptance criteria:** PF-002 non-claim present; replay nonce rejection confirmed; sequence gap detection confirmed; SIGNING_UNAVAILABLE handled gracefully (not a pipeline error); key never passed to any worker
**Risk/blockers:** Signing implementation fully BLOCKED on PRE-02 + PRE-04 + PRE-08 + PRE-09; build provenance record structure and replay/sequence logic first; complete signing when P1 resolved
**Completion state:** `[ ] NOT STARTED`

---

### TASK-020 — COMP-CAP: Capability Declaration + DEFERRED_IN_SCOPE Emitter

**Name:** Implement capability declaration and DEFERRED_IN_SCOPE record emitter
**Purpose:** Every out-of-scope method must produce an explicit record; absence is not a no-issue finding
**Source specification:** §09 §6 COMP-CAP; §09 §2.3 (explicit out-of-scope items); §10 §3.17
**Dependencies:** TASK-005 (evidence store); TASK-008 (schema for deferred records); TASK-003 (constants)
**Expected output:**
- `assurance_system/supervisor/capability_declaration.py`
- `CapabilityDeclaration.emit_deferred_records(asset_id)` — emits DEFERRED_IN_SCOPE records for all deferred methods:
  - Behavioral battery (M07 class)
  - PDQ near-duplicate (M03-PDQ)
  - Statistical drift / OOD (M04, M05)
  - Reference-relative comparison (M11)
  - TorchScript loading
  - External tail completeness
  - Sybil-resistant T10
  - T05d clean-label (permanent NON_CLAIM — not a deferred method but a permanent gap)
  - Activation-space analysis, Neural Cleanse, B3D, ABS, AC
- Each record carries: method_id, reason, status=DEFERRED_IN_SCOPE or permanent NON_CLAIM
- `list-deferred` CLI shows all such records per asset
**Files/modules affected:** `assurance_system/supervisor/capability_declaration.py`
**Reuse decision:** Fresh build
**Tests:**
- `tests/unit/test_capability_declaration.py`:
  - UT-CAP-001: emit_deferred_records for an asset → at minimum 9 DEFERRED_IN_SCOPE records created
  - UT-CAP-002: T05d permanent NON_CLAIM record present
  - UT-CAP-003: CLI `list-deferred` shows all records (integration test; requires TASK-023)
**Acceptance criteria:** All deferred methods produce explicit records; T05d NON_CLAIM present; `list-deferred` CLI works
**Risk/blockers:** PRE-04 for final method vocabulary; build with pending vocabulary and update
**Completion state:** `[ ] NOT STARTED`

---

### TASK-021 — COMP-C5: Assurance Interpretation Rule Engine

**Name:** Implement C5 five-layer structured finding producer
**Purpose:** UNAVAILABLE propagation; ANOMALY ≠ PROVEN_ATTACK; T05d non-claim; no risk score; multi-detector dependency declaration
**Source specification:** §10 §9.1 (C5 rule engine — fully specified; priority ordering is authoritative)
**Dependencies:** TASK-005 (evidence store reads); TASK-008 (schema for findings); TASK-010 through TASK-017 (workers must produce evidence for C5 to consume); TASK-018 (reference manager); TASK-020 (deferred records); PRE-04 (vocabulary)
**Expected output:**
- `assurance_system/supervisor/interpretation.py`
- `C5InterpretationEngine.produce_finding(asset_id, method_id, evidence_records, reference_health, access_mode)` → structured finding
- Priority rule 1 (highest): ANY upstream UNAVAILABLE or ASSESSMENT_ERROR → finding detection_status = UNAVAILABLE; analyst_disposition_prompt = UNAVAILABLE_NO_DECISION. No other rules fire.
- Priority rule 2: LOAD_BLOCKED or ONNX_PATH_CONTAINMENT_VIOLATION → ESCALATE; anomaly_not_malicious_non_claim = True; ANOMALY ≠ PROVEN_ATTACK in non_claims
- Priority rule 3: COMPLETED with anomaly signal → DETECT; anomaly_not_malicious_non_claim = True; ANOMALY ≠ PROVEN_ATTACK
- Priority rule 4: COMPLETED with no anomaly → WITHIN_EXPECTED_PARAMETERS (NOT a "CLEAN" claim)
- All findings carry: T05d coverage_gap_non_claim; global_backdoor_absence_not_established (on model findings); LIMITATIONS; NON_CLAIMS; DEPENDENCY_DECLARATION; ANALYST_DISPOSITION_PROMPT
- risk_score field: schema validator must reject any finding with this field; C5 engine must not produce it
**Files/modules affected:** `assurance_system/supervisor/interpretation.py`
**Reuse decision:** Fresh build (C5 rule engine is project-specific; no reuse candidate)
**Tests:**
- `tests/unit/test_interpretation.py`:
  - UT-C5-001: UNAVAILABLE evidence record → finding detection_status=UNAVAILABLE (priority rule 1)
  - UT-C5-002: ASSESSMENT_ERROR evidence record → finding detection_status=UNAVAILABLE
  - UT-C5-003: LOAD_BLOCKED → ESCALATE; anomaly_not_malicious_non_claim=True
  - UT-C5-004: COMPLETED with no anomaly → WITHIN_EXPECTED_PARAMETERS; risk_score field absent
  - UT-C5-005: T05d NON_CLAIM present on all C2 findings
  - UT-C5-006: global_backdoor_absence_not_established present on all C3 findings
  - UT-C5-007: risk_score field not present (all code paths)
  - REPRO-004: same evidence records → same finding on two runs
- `tests/negative/test_unavailable_propagation.py`:
  - FIX-013 at each of 4 pipeline layers: UNAVAILABLE propagates without conversion to positive state
**Acceptance criteria:** Priority rule 1 enforced (UNAVAILABLE never compressed); risk_score field absent on all outputs; anomaly non-claim present on ESCALATE and DETECT; T05d non-claim present on C2; global backdoor non-claim present on C3; REPRO-004 passes; FIX-013 propagation at all 4 layers confirmed
**Risk/blockers:** PRE-04 blocks final vocabulary; build with placeholder and update; all downstream workers must complete before full C5 integration test
**Completion state:** `[ ] NOT STARTED`

---

### TASK-022 — COMP-SUP: Supervisor Orchestrator

**Name:** Implement supervisor pipeline controller (integrates all components)
**Purpose:** Enforces B2 boundary; sequences all workers; writes all evidence; never returns CLEAN on error; end-to-end pipeline control
**Source specification:** §10 §3.1 (orchestrator signatures); §09 §6 COMP-SUP; §09 §5 dataflow
**Dependencies:** TASK-005; TASK-006; TASK-007; TASK-008; TASK-009; TASK-010 through TASK-021 (all supervisor components); PRE-02 (C4 signing completes when resolved)
**Expected output:**
- `assurance_system/supervisor/orchestrator.py`
- `SupervisorOrchestrator.run_pipeline(manifest_path)`:
  - Validate manifest → emit capability declarations + DEFERRED_IN_SCOPE records (TASK-020)
  - Dispatch C2 workers (T-010 through T-013): C2A, C2B, C2C, C2D — all in parallel (separate subprocess per)
  - Dispatch C3 workers (T-014 through T-017): C3A → C3B (sequential); C3C + C3D (parallel with each other)
  - Run C4 binding (T-019)
  - Run C5 interpretation (T-021)
  - Write PIPELINE_RUN_COMPLETE audit event
  - Return PipelineRunSummary
  - On any unrecoverable error: write PIPELINE_RUN_ERROR audit event; raise PipelineError (never silently continue past evidence-integrity-affecting failure)
- `_dispatch_worker()` per §10 §3.1 template (named temp file; clean env; resource limits; cleanup on all paths)
- `_accept_worker_result()`: schema validate → write to store → audit event; on schema violation: audit event only, no store write
- All workers untrusted; signing key never accessible to workers (cleaned from env)
**Files/modules affected:** `assurance_system/supervisor/orchestrator.py`
**Reuse decision:** Fresh build (no reuse candidate for supervisor boundary pattern)
**Tests:**
- `tests/integration/test_orchestrator.py`:
  - INT-001: valid COCO dataset + ONNX model → complete pipeline run; all evidence records written; C5 finding produced; audit events present
  - INT-002: hostile pickle model → LOAD_BLOCKED evidence record; pipeline continues for data integrity checks
  - INT-003: UNAVAILABLE propagation: inject UNAVAILABLE at C3 layer → C5 finding shows UNAVAILABLE (FIX-013)
  - INT-004: schema violation from worker → WORKER_RESULT_REJECTED_SCHEMA_VIOLATION audit event; no evidence record written
  - INT-005: all deferred methods → DEFERRED_IN_SCOPE records present in store
- `tests/security/test_supervisor_security.py`:
  - SEC-008: non-supervisor process cannot write to evidence store path (ACL test)
**Acceptance criteria:** INT-001 through INT-005 pass; SEC-008 passes; signing key not in worker subprocess env; all temp directories cleaned after run; PIPELINE_RUN_COMPLETE or PIPELINE_RUN_ERROR audit event on every run
**Risk/blockers:** Requires all workers (TASK-010 through TASK-021); this is the integration task — some workers may be stubs initially. Build with stub workers for early integration testing.
**Completion state:** `[ ] NOT STARTED`

---

### TASK-023 — COMP-IFACE: CLI + Entry Points

**Name:** Implement CLI analyst interface and top-level entry point
**Purpose:** Analyst access to all evidence; read-only; UNAVAILABLE never hidden
**Source specification:** §10 §2.4 (entry points — authoritative); §09 §6 COMP-IFACE; §10 §3.16
**Dependencies:** TASK-022 (orchestrator — all pipeline components)
**Expected output:**
- `assurance_system/interfaces/cli.py` and top-level `cli.py`:
  - `python cli.py assess --submission <manifest_path>` — full pipeline run
  - `python cli.py show-finding --asset-id <id>` — all C5 fields including UNAVAILABLE; never hides any field
  - `python cli.py show-evidence --asset-id <id> --method <method-id>` — evidence record
  - `python cli.py show-audit-trail` — read-only chain; CHAIN_CORRUPT reported if detected
  - `python cli.py export-bundle --asset-id <id> --output <path>` — ZIP bundle
  - `python cli.py list-deferred` — all DEFERRED_IN_SCOPE and NON_CLAIM records
  - `python cli.py dashboard --port <port>` — starts http.server dashboard
- All display: UNAVAILABLE shown explicitly; NOT_ASSESSED shown explicitly; DEFERRED_IN_SCOPE shown explicitly; never suppressed or converted to positive assurance language
**Files/modules affected:** `assurance_system/interfaces/cli.py`, `cli.py`
**Reuse decision:** Fresh build (stdlib argparse only)
**Tests:**
- `tests/integration/test_cli.py`:
  - INT-CLI-001: `assess` command on valid submission → exits 0; evidence written
  - INT-CLI-002: `show-finding` on completed asset → all C5 fields printed; UNAVAILABLE visible if present
  - INT-CLI-003: `list-deferred` → at minimum 9 DEFERRED_IN_SCOPE records shown
  - INT-CLI-004: `show-audit-trail` with CHAIN_CORRUPT → CHAIN_CORRUPT visible in output
**Acceptance criteria:** All 4 CLI integration tests pass; UNAVAILABLE never hidden in any output path; all 7 entry points functional; no evidence store write path from CLI
**Risk/blockers:** Depends on TASK-022 (full pipeline); build CLI stubs early to validate command parsing
**Completion state:** `[ ] NOT STARTED`

---

### TASK-024 — COMP-IFACE Dashboard: Read-only Evidence Dashboard

**Approved contract clarification ACC-2026-10-02-03:** Dashboard and read-only
`show-audit-trail` use `inspect_chain_integrity()` with zero persistence. Trusted
`verify_chain_integrity()` shares the complete algorithm and retains corruption
and sequence-gap diagnostics; SEC-010 is unchanged. Narrow SELECT-only evidence,
provenance and chain-state queries are permitted for this task.

**Name:** Implement read-only stdlib http.server dashboard (MVP value feature)
**Purpose:** Visual analyst interface; offline; no npm/CDN; execution state visualization only (no assurance confidence implied)
**Source specification:** §09 §2.1 (MVP value features); §10 §2.1 (stdlib http.server); §09 §16.2 (C5 analyst disposition mapping)
**Dependencies:** TASK-023 (CLI and entry points); TASK-005 (evidence store read)
**Expected output:**
- `assurance_system/interfaces/dashboard.py`
- Single self-contained HTML file served by `http.server.HTTPServer`
- Reads evidence store (read-only) on each request
- Displays: Pipeline run summary; Evidence Explorer (finding → evidence → asset → hash → audit event navigation); Audit Timeline (temporal chain; CHAIN_CORRUPT flagged); all UNAVAILABLE/DEFERRED_IN_SCOPE findings visible
- Pipeline Visualization [SHOULD BUILD — time-permitting]: execution state (running/pending/completed) per worker; does NOT display assurance confidence levels; no color coding implying safe/unsafe
- No localStorage; no CDN; no npm; no React; all assets inline in the HTML file
- Port configurable; default localhost only
**Files/modules affected:** `assurance_system/interfaces/dashboard.py`
**Reuse decision:** Fresh build (stdlib only by design)
**Tests:**
- `tests/integration/test_dashboard.py`:
  - INT-DASH-001: dashboard starts on configured port; returns HTTP 200
  - INT-DASH-002: UNAVAILABLE finding visible in dashboard output (not hidden)
  - INT-DASH-003: no CDN URLs in served HTML (offline requirement)
**Acceptance criteria:** Starts offline; UNAVAILABLE findings visible; no CDN; no npm; CHAIN_CORRUPT visible in Audit Timeline; Pipeline Visualization (if built) shows execution state only with no assurance confidence labels
**Risk/blockers:** Lower priority than MB items; cut if time is constrained — CLI covers analyst access
**Completion state:** `[x] TESTED` (2026-10-02): INT-DASH-001..015 and additional
cases, 27 passed. Approved read-only inspection and trusted SEC-010 pass;
non-offline regression 588 passed/11 unchanged skips. Visual acceptance is
static/CSS composition review only; Windows browser input access denied.
Observed pipeline derives stored observations, not live telemetry. Gate-5 remains
NOT PASSED; its demonstration criteria were not executed by TASK-024.

---

### TASK-025 — Evidence Bundle Export

**Name:** Implement evidence bundle ZIP exporter
**Purpose:** Analyst can export structured evidence for audit and delivery
**Source specification:** §09 §2.1; §10 §2.4 (`export-bundle` entry point)
**Dependencies:** TASK-023 (CLI); TASK-005 (evidence store read)
**Expected output:**
- `assurance_system/interfaces/exporter.py`
- `EvidenceExporter.export_bundle(asset_id, output_path)` — produces ZIP:
  - `findings.json` — all C5 findings for asset
  - `evidence_records.json` — all evidence records for asset
  - `provenance_records.json` — all provenance records for asset
  - `audit_events.json` — relevant audit events for asset
  - `deferred_records.json` — all DEFERRED_IN_SCOPE records for asset
  - `manifest.json` — export metadata, schema version, export timestamp
- All UNAVAILABLE, DEFERRED_IN_SCOPE, NON_CLAIM fields included — never omitted from export
- Export is a copy; does not modify evidence store
**Files/modules affected:** `assurance_system/interfaces/exporter.py`
**Reuse decision:** Fresh build
**Tests:**
- `tests/integration/test_exporter.py`:
  - INT-EXP-001: export bundle for a completed asset → valid ZIP; all 6 files present
  - INT-EXP-002: UNAVAILABLE finding in findings.json — present, not omitted
  - INT-EXP-003: DEFERRED_IN_SCOPE records in deferred_records.json — present
  - INT-EXP-004: export does not modify evidence store (read-only confirmed)
**Acceptance criteria:** All 4 tests pass; UNAVAILABLE and DEFERRED_IN_SCOPE fields present in export; evidence store not modified by export
**Risk/blockers:** Depends on TASK-022 for evidence to exist; otherwise no blockers
**Completion state:** `[ ] NOT STARTED`

---

### TASK-026 — End-to-End Integration Test + Vertical Slice Validation

**Name:** Run and pass the vertical-slice end-to-end integration test
**Purpose:** Validates the complete path: asset → ingestion → assessment → evidence → finding → analyst output; this is the gate before capability expansion
**Source specification:** §10 §18 (experiment/validation contracts); §10 §19 Tier 8
**Dependencies:** TASK-022 (orchestrator); TASK-023 (CLI); all workers (TASK-010 through TASK-021); TASK-009 (fixtures)
**Expected output:**
- `tests/integration/test_vertical_slice.py`:
  - VS-001: valid COCO dataset submission → COMPLETED evidence; C5 finding with WITHIN_EXPECTED_PARAMETERS; no UNAVAILABLE unless upstream blocked; audit trail complete
  - VS-002: FIX-008 COCO geometry violations → C2A COMPLETED; violations listed; C5 finding DETECT; ANOMALY ≠ PROVEN_ATTACK non-claim present
  - VS-003: FIX-001 hostile PyTorch pickle → C3D LOAD_BLOCKED; C5 finding ESCALATE; non-claim present; pipeline continues for C2
  - VS-004: FIX-013 UNAVAILABLE injection at each of 4 layers → C5 finding UNAVAILABLE each time; no conversion to positive state
  - VS-005: DEFERRED_IN_SCOPE records present for all out-of-scope methods
  - VS-006: `list-deferred` CLI shows all deferred records
  - VS-007: `export-bundle` produces valid ZIP with all required files including UNAVAILABLE findings
- All experiment validation contracts per §10 §18.1 through §10 §18.5 executed and observed results recorded
**Files/modules affected:** `tests/integration/test_vertical_slice.py`; observed results recorded in experiment log
**Reuse decision:** N/A (test execution)
**Tests:** VS-001 through VS-007 (self-describing)
**Acceptance criteria:** All 7 vertical-slice tests pass; ALL §10 §18 experiment validation contracts have observed results recorded; UNAVAILABLE propagation confirmed at all 4 injection points; security fixture tests (SEC-001 through SEC-012) pass
**Risk/blockers:** Blocked until all upstream MUST BUILD tasks complete; is the integration gate
**Completion state:** `[x] TESTED — 2026-10-02; GATE-4 PASS`

Maintained validation state: [criterion-by-criterion Gate-4 evaluation](validation/task026_gate4_evaluation.md).
VS 7 passed; §18.1–§18.5 observations recorded; synthetic propagation,
REPRO-001..006 and INT-001..005 pass; accepted OFF-001..004 evidence reused
without network execution. Non-offline regression: 552 passed / 11 unchanged
skips / 0 failures. Original expected outputs above remain historical task text;
the approved frozen vocabulary and bounded observation record govern findings.

---

### TASK-027 — Offline Validation + Wheelhouse Verification

**Name:** Execute wheelhouse staging, dependency verification, and zero-egress test on target host
**Purpose:** Offline capability claim requires confirmed execution on the actual target host — not just local test
**Source specification:** §09 §12; §10 §17.4; PRE-01 BLOCKING
**Dependencies:** TASK-001 (PRE-01 resolved); all MUST BUILD complete; wheelhouse staged
**Expected output:**
- `scripts/verify_wheelhouse.py` [SHOULD BUILD]: verifies all packages install from wheelhouse/ without network
- Offline test execution:
  - OFF-001: all packages install from wheelhouse on target host with no network
  - OFF-002: full pipeline run with network monitor shows 0 bytes egress
  - OFF-003: `python -c "import onnx, torch, pycocotools"` succeeds offline on target host
  - OFF-004: SQLite evidence store read/write succeeds with no network
- Telemetry verification: confirm onnx, torch (CPU-only), pycocotools emit no network traffic on this specific binary/version
- Document: target host tuple (OS, Python version, CPU arch, package versions) as the scope of the offline claim
**Files/modules affected:** `scripts/verify_wheelhouse.py`; `wheelhouse/` populated; `tests/offline/`
**Tests:** OFF-001 through OFF-004
**Acceptance criteria:** All 4 offline tests pass on actual target host (not on development machine); target host tuple documented; offline claim scoped to confirmed tuple only
**Risk/blockers:** Hard-blocked on PRE-01; cannot be completed until target host is known and available; schedule as Day 4-5 task after PRE-01 resolved
**Completion state:** `[!] BLOCKED — PRE-01 required`

---

# 8. DEPENDENCY GRAPH

```
TIER 0 — PREREQUISITE DECISIONS
  TASK-001 (P1 condition resolution)
  → All implementation tiers unblock as P1 conditions are resolved

TIER 1 — FOUNDATION (parallel once TASK-001/PRE-04 minimum resolved)
  TASK-002 (repository skeleton)       → no code dependency
  TASK-003 (exceptions + constants)    → TASK-002
  TASK-004 (config system)             → TASK-003

TIER 2 — CORE PERSISTENCE + SCHEMA (parallel within tier)
  TASK-005 (evidence store, SQLite)    → TASK-003, TASK-004, PRE-04
  TASK-006 (audit chain writer)        → TASK-005
  TASK-007 (worker base, IPC)          → TASK-003, TASK-004
  TASK-008 (schema validator + schemas)→ TASK-003, TASK-005, PRE-04
  TASK-009 (hostile fixture suite — P0)→ TASK-007, TASK-003

TIER 3 — DATA-INTEGRITY WORKERS (parallel within tier)
  TASK-010 (C2A structural validator)  → TASK-007, TASK-009, [PRE-05]
  TASK-011 (C2B exact hash)            → TASK-007, TASK-009
  TASK-012 (C2C concentration)         → TASK-007
  TASK-013 (C2D image hash)            → TASK-007

TIER 4 — MODEL-INTEGRITY WORKERS (sequential C3A→C3B; parallel C3C+C3D)
  TASK-014 (C3A artifact-unit resolver)→ TASK-007, [PRE-03 for PyTorch]
  TASK-015 (C3B model hasher)          → TASK-014
  TASK-016 (C3C ONNX structural)       → TASK-007, TASK-014
  TASK-017 (C3D PyTorch safe-load)     → TASK-007, TASK-009, [PRE-01, PRE-05]

TIER 5 — PROVENANCE + INTERPRETATION
  TASK-018 (COMP-REF reference manager)→ TASK-005, TASK-006, TASK-003
  TASK-019 (COMP-C4 provenance + sign) → TASK-005, TASK-006, TASK-003, [PRE-02, PRE-04, PRE-08, PRE-09]
  TASK-020 (COMP-CAP deferred emitter) → TASK-005, TASK-008, TASK-003, [PRE-04]
  TASK-021 (COMP-C5 interpretation)    → TASK-005, TASK-008, TASK-010–TASK-017, TASK-018, TASK-020, [PRE-04]

TIER 6 — ORCHESTRATOR
  TASK-022 (COMP-SUP orchestrator)     → TASK-005, TASK-006, TASK-007, TASK-008, TASK-009,
                                          TASK-010–TASK-021

TIER 7 — ANALYST INTERFACE
  TASK-023 (CLI + entry points)        → TASK-022
  TASK-024 (dashboard)                 → TASK-023, TASK-005
  TASK-025 (evidence bundle export)    → TASK-023, TASK-005

TIER 8 — INTEGRATION + VALIDATION
  TASK-026 (end-to-end integration + vertical slice) → TASK-022, TASK-023, TASK-025, TASK-009
  TASK-027 (offline validation — target host)        → TASK-026, PRE-01 confirmed

CRITICAL PATH:
  PRE-04 → TASK-005 → TASK-008 → TASK-021 → TASK-022 → TASK-023 → TASK-026
  PRE-02+PRE-04+PRE-08+PRE-09 → TASK-019 → TASK-022
  TASK-009 (fixtures P0) → TASK-026 (security tests)
  PRE-01 → TASK-027 (offline claim)
```

---

# 9. CRITICAL PATH

The following tasks can block the end-to-end demonstration if not completed. Delay in any item on the critical path cascades to all downstream tasks.

| Position | Task | Why critical |
|---|---|---|
| 1 | TASK-001 (PRE-04) | Schema version freeze gates evidence store DDL, schema validator, C5 rule engine |
| 2 | TASK-005 (evidence store) | All evidence persistence depends on this |
| 3 | TASK-008 (schema validator) | No evidence record can enter store without this |
| 4 | TASK-009 (hostile fixtures) | No security test can run without this; build in parallel with Tier 2 |
| 5 | TASK-010 (C2A) | All-box validation is the primary data integrity floor |
| 6 | TASK-014 → TASK-015 (C3A → C3B) | Sequential dependency; C3B cannot hash before unit is resolved |
| 7 | TASK-021 (C5 rule engine) | Produces the analyst-facing findings; depends on all workers |
| 8 | TASK-022 (orchestrator) | End-to-end integration layer |
| 9 | TASK-023 (CLI) | Analyst cannot access findings without this |
| 10 | TASK-026 (vertical slice test) | Core validation; demo depends on this passing |

**Secondary critical path: C4 signing**

PRE-02 + PRE-04 + PRE-08 + PRE-09 → TASK-019 → TASK-022

If these P1 conditions remain unresolved beyond Day 2, COMP-C4 must ship as a provenance-record-without-signature shell. The pipeline can run and demonstrate; the signing claim is blocked but must show SIGNING_UNAVAILABLE rather than silently omitting provenance.

---

# 10. PARALLELIZABLE WORK

These task groups can proceed simultaneously across team members without shared-state conflicts.

| Parallel group | Tasks | Parallel-safe because |
|---|---|---|
| Tier 2 parallel set | TASK-005 + TASK-007 + TASK-009 | Different modules; no shared mutable state during build |
| Tier 3 data workers | TASK-010 + TASK-011 + TASK-012 + TASK-013 | Independent worker modules; same base.py; no inter-worker dependency |
| Tier 4 model workers | TASK-016 + TASK-017 (after TASK-014) | C3C and C3D share no state; C3A must complete before C3B |
| Tier 5 supervisor | TASK-018 + TASK-019 (shell) + TASK-020 + TASK-021 (partial) | Different supervisor modules; COMP-C5 needs workers complete for integration testing but can be built while workers are in progress |
| Tier 7 interface | TASK-023 + TASK-024 + TASK-025 | After TASK-022 complete; three interface components share no state |

**Codex / Antigravity split is the primary parallelization lever** — see Section 12.

---

# 11. VERTICAL-SLICE PLAN

The vertical slice is the earliest demonstrable end-to-end path. It must be complete before any optional feature work begins.

## Vertical slice definition

```
Synthetic COCO dataset submission
  → Ingestion gate (B1)
  → C2A structural validator subprocess (B2)
  → C2B exact hash subprocess (B2)
  → Schema validation (COMP-SCHEMA)
  → Evidence store write (COMP-STORE)
  → Provenance record (COMP-C4 — shell; SIGNING_UNAVAILABLE if PRE-02 not yet resolved)
  → C5 interpretation (COMP-C5) → structured finding
  → Audit chain entry (COMP-AUDIT)
  → CLI show-finding → analyst sees all fields including UNAVAILABLE and non-claims
  → Export bundle → ZIP with findings.json, evidence_records.json, deferred_records.json
```

## Vertical slice does NOT require

- YOLO format (conditional on PRE-05)
- PyTorch model workers (conditional on PRE-01/PRE-05)
- Completed signing (PRE-02 etc. — SIGNING_UNAVAILABLE acceptable for VS gate)
- Dashboard (SHOULD BUILD — not VS gate)
- Hostile fixture security tests (required before security claims, not before VS gate)

## Vertical slice gate criteria (must ALL pass)

- [ ] `python cli.py assess --submission tests/fixtures/valid_coco_submission.json` exits 0
- [ ] Evidence store contains C2A evidence record for the submission (all boxes checked, not first-box only)
- [ ] C5 finding for the submission is present in the store with all mandatory fields
- [ ] `python cli.py show-finding --asset-id <id>` prints all C5 fields including UNAVAILABLE, non-claims
- [ ] DEFERRED_IN_SCOPE records present for all deferred methods (`list-deferred` output non-empty)
- [ ] `python cli.py export-bundle` produces valid ZIP with `findings.json`, `deferred_records.json`
- [ ] Audit chain has at minimum 3 events (PIPELINE_RUN_START, EVIDENCE_RECORD_WRITTEN, PIPELINE_RUN_COMPLETE)
- [ ] No risk_score field anywhere in any output (grep check)

**Earliest achievable vertical slice: end of Day 2** (assuming PRE-04 and PRE-01 resolved on Day 0; COCO-only path; no PyTorch; pycocotools staged).

---

# 12. CODEX / ANTIGRAVITY ALLOCATION

## Allocation principle

Codex operates on the repository implementation. Antigravity operates on the browser/visual layer. Both push to the same repository. Branches = tasks, not devices. No architecture redesign is permitted.

## Codex responsibilities

| Task | Codex role |
|---|---|
| TASK-002 through TASK-009 | All Tier 1–2 foundation and schema work |
| TASK-010 through TASK-013 | C2 worker implementations |
| TASK-014 through TASK-017 | C3 worker implementations |
| TASK-018 through TASK-022 | Supervisor components (C4, C5, REF, CAP, SUP) |
| TASK-023 | CLI entry points |
| TASK-025 | Evidence bundle exporter |
| TASK-026 | End-to-end integration tests |
| TASK-027 | Wheelhouse verification script and offline test runner |
| All `tests/unit/`, `tests/integration/`, `tests/security/`, `tests/negative/` | Full test suite |

## Antigravity responsibilities

| Task | Antigravity role |
|---|---|
| TASK-024 | Dashboard (stdlib http.server; self-contained HTML; read-only evidence store integration) |
| Dashboard visual QA | Verify UNAVAILABLE and DEFERRED_IN_SCOPE findings visible; no CDN URLs; Pipeline Visualization if time-permitting |
| Evidence Explorer navigation | Verify finding → evidence → asset → hash → audit event drill-down works in dashboard |
| Audit Timeline display | Verify CHAIN_CORRUPT visibility in dashboard |

## Non-negotiable boundaries for Antigravity

- Antigravity must NOT define new security semantics, state transitions, or evidence field values
- Antigravity must NOT add any write path to the evidence store from the dashboard
- Antigravity reads evidence store via the read-only query interface only
- Antigravity must NOT change the dashboard to show assurance confidence levels, risk scores, or positive-assurance colors
- Any Antigravity change that touches `supervisor/`, `workers/`, `schema/`, or any `tests/security/` file requires explicit Codex review before merge

## Common contract between Codex and Antigravity

The dashboard receives evidence from the evidence store via the same read-only query API used by the CLI. Antigravity must not implement its own parallel evidence query path. Codex defines the query API; Antigravity consumes it.

---

# 13. GIT BRANCH / WORKSTREAM PLAN

## Repository principles

- One repository
- Branches represent tasks or workstreams, not devices
- `main` branch: only receives merges after integration gate passes
- All work in feature branches; merge via pull request with test evidence

## Branch structure

```
main
│
├── feature/foundation
│   (TASK-002, TASK-003, TASK-004 — repository skeleton + types + config)
│
├── feature/persistence
│   (TASK-005, TASK-006 — evidence store + audit chain)
│
├── feature/worker-base
│   (TASK-007 — IPC boilerplate)
│
├── feature/schema
│   (TASK-008 — schema validator + JSON schema files)
│
├── feature/fixtures
│   (TASK-009 — full hostile fixture suite — P0)
│
├── feature/c2-data-workers
│   (TASK-010, TASK-011, TASK-012, TASK-013 — all C2 workers)
│
├── feature/c3-model-workers
│   (TASK-014, TASK-015, TASK-016, TASK-017 — all C3 workers)
│
├── feature/provenance
│   (TASK-019 — C4 provenance + signing)
│
├── feature/reference-manager
│   (TASK-018 — COMP-REF)
│
├── feature/capability-declaration
│   (TASK-020 — COMP-CAP)
│
├── feature/interpretation
│   (TASK-021 — C5 rule engine)
│
├── feature/orchestrator
│   (TASK-022 — supervisor pipeline controller)
│
├── feature/cli
│   (TASK-023 — CLI entry points)
│
├── feature/exporter
│   (TASK-025 — evidence bundle ZIP export)
│
├── feature/dashboard
│   (TASK-024 — read-only dashboard [Antigravity primary])
│
├── feature/integration-tests
│   (TASK-026 — end-to-end vertical slice + security test battery)
│
└── feature/offline-validation
    (TASK-027 — wheelhouse + zero-egress tests [after PRE-01])
```

## Merge order (critical path mirrors)

```
foundation → persistence → worker-base → schema
                                        ↓
fixtures → c2-data-workers → c3-model-workers
                                        ↓
reference-manager + capability-declaration + provenance → interpretation
                                        ↓
orchestrator → cli + exporter + dashboard
                                        ↓
integration-tests → offline-validation
```

---

# 14. INTEGRATION GATES

Five gates govern progression. A gate must pass before work beyond it begins.

## GATE-1: Foundation Gate

**Trigger:** After TASK-002 through TASK-008 complete
**Criteria:**
- [ ] Repository structure matches §10 §2.2 exactly
- [ ] `exceptions.py` and `constants.py` importable; no CLEAN/SAFE/HEALTHY constants
- [ ] Evidence store: 6 unit tests pass; WAL mode confirmed
- [ ] Audit chain: 5 unit tests pass; no reset() method
- [ ] Schema validator: 8 unit tests pass; risk_score rejected; coverage_gap=False rejected
- [ ] Config loader: loads valid config; rejects invalid config
- [ ] Worker base: 8 unit tests pass; path containment confirmed; timeout confirmed
- [ ] `test_repository_structure.py` passes
- [ ] grep weights_only=False → 0 matches (from Day 1)

## GATE-2: Vertical Slice Gate (P0)

**Trigger:** After vertical slice criteria all pass (Section 11)
**Criteria:**
- [ ] All 7 vertical slice criteria pass (Section 11)
- [ ] Hostile fixture suite complete (all fixture types generated; reproducibility confirmed)
- [ ] DEFERRED_IN_SCOPE records present for all deferred methods
- [ ] No risk_score field in any output (grep)
- [ ] UNAVAILABLE propagation confirmed at ≥ 1 injection point

**No expansion of capability scope until GATE-2 passes.**

## GATE-3: Capability Gate

**Current adjudication: PASS**, validation executed 2026-10-02 after owner-approved
SP-002-ONNX closure. See `docs/validation/e2_onnx_identity_acceptance.md` for
criterion-level observations and historical checkpoint boundaries. This is not
Gate-4 acceptance or authorization for another task.

**Trigger:** After all C2 workers, all C3 workers, COMP-C4 (shell), COMP-C5, COMP-REF, COMP-CAP complete
**Criteria:**
- [x] All C2 worker unit tests pass (including UT-C2A-004 all-box coverage)
- [x] All C3 worker unit tests pass
- [x] Security fixture tests SEC-001 through SEC-012 pass
- [x] UNAVAILABLE propagation at all 4 injection points confirmed (FIX-013)
- [x] C5 finding: priority rule 1 enforced; risk_score field absent; T05d non-claim present; PF-002 non-claim present on C3 findings
- [x] Audit chain: SEC-010 (CHAIN_CORRUPT on modification) passes
- [x] Replay nonce: SEC-009 passes
- [x] weights_only=False grep check: 0 matches

## GATE-4: Validation Gate

**Trigger:** After TASK-026 (full vertical slice test battery) passes
**Criteria:**
- [x] All VS-001 through VS-007 pass
- [x] All §10 §18 experiment validation contracts have observed results recorded
- [x] Evidence records are_synthetic=1 for all fixture-derived results (frozen field: `is_synthetic`)
- [x] REPRO-001 through REPRO-006 pass (reproducibility)
- [x] INT-001 through INT-005 (orchestrator integration) pass
- [x] Offline tests OFF-001 through OFF-004 pass [conditional on PRE-01 resolved]

**GATE-4: PASS — 2026-10-02**, all-of evaluation and exact evidence in
[TASK-026 Gate-4 review](validation/task026_gate4_evaluation.md). Accepted
target-host OFF evidence was reused; OFF-002 acceptance PASS, original recovery
marker FAIL and independent restored-state PASS remain separate. PRE-08 PARTIAL
and HOST-CAP-003's historical procedural re-entry remain carried. GATE-5 is
NOT PASSED and TASK-024 is NOT STARTED; neither is executed by this review.

## GATE-5: Demo Gate

**Trigger:** After GATE-4 passes + demo script complete
**Criteria:**
- [ ] `scripts/demo.sh` (or equivalent) runs end-to-end offline without manual intervention
- [ ] Dashboard starts and displays evidence correctly (UNAVAILABLE visible)
- [ ] Export bundle ZIP produced and valid
- [ ] CHAIN_CORRUPT displayed correctly in `show-audit-trail`
- [ ] All DEFERRED_IN_SCOPE records visible in `list-deferred`
- [ ] Target host tuple documented in project records
- [ ] No claim broader than demonstrated fixture evidence

---

# 15. DEFINITION OF DONE

Every MUST BUILD task must satisfy these universal criteria PLUS its task-specific acceptance criteria.

## Universal DoD criteria (apply to every MUST BUILD task)

- [ ] All task-specific unit tests pass in CI
- [ ] No import of a prohibited package (jsonschema, OnnxRuntime in non-designated components, any unlicensed package)
- [ ] No CLEAN/SAFE/HEALTHY as a positive assurance state (grep check)
- [ ] No risk_score field produced or consumed
- [ ] No weights_only=False in any code path (grep check from TASK-017 onward)
- [ ] LIMITATIONS and NON_CLAIMS fields non-empty on every worker output
- [ ] coverage_gap_clean_label=True on all C2 and C3 evidence records
- [ ] attribution comments present for all MIT/BSD reused patterns (REUSE-018 R17; REUSE-020 R27)
- [ ] All temp files and worker directories cleaned after every code path
- [ ] Offline: no network call in any code path (verified by static analysis and/or test)
- [ ] Task completion state updated in this document

## Task-specific criteria

Each task's acceptance criteria in Section 7 are in addition to the above, not a replacement. Tasks TASK-009 (fixtures) and TASK-026 (vertical slice) have elevated criteria — see their sections.

---

# 16. CUT / STOPPING POLICY

If any of the following conditions occur, stop optional/SHOULD BUILD work immediately and return to the core integration path.

| Trigger condition | Action |
|---|---|
| GATE-2 (vertical slice) is not passing by end of Day 3 | Suspend TASK-024 (dashboard), TASK-027 (offline validation); concentrate all effort on TASK-022 (orchestrator) and TASK-026 (integration tests) |
| C4 signing (TASK-019) requires more than 0.5 days after P1 conditions resolved | Ship provenance shell (SIGNING_UNAVAILABLE); signing completes post-GATE-2 |
| TASK-024 (dashboard) is threatening GATE-2 | Cut dashboard immediately; CLI covers analyst access; dashboard is SHOULD BUILD, not MUST BUILD |
| PyTorch worker (TASK-017) C extension staging fails (onnx/torch wheel issue) | Emit ASSESSMENT_ERROR for all PyTorch assets; proceed with ONNX + COCO vertical slice; document format scope limitation |
| pycocotools C extension build fails (PRE-01) | Use pure-Python COCO parser stub for VS gate; document as conditional; revisit after PRE-01 |
| Any test reveals that a security invariant (UNAVAILABLE ≠ CLEAN; no fallback; no risk score) is violated | Stop ALL other work; fix the invariant violation before continuing |
| Integration test reveals a worker is writing to evidence store directly | Stop; this is an architecture violation; fix before continuing |

## Non-cuttable items (regardless of time pressure)

The following may NOT be cut even under maximum schedule pressure:

- TASK-009 (hostile fixtures) — no security test without fixtures
- TASK-008 (schema validator) — UNAVAILABLE ≠ CLEAN enforcement requires this
- TASK-021 (C5 rule engine) — required for UNAVAILABLE propagation; non-negotiable
- TASK-006 (audit chain, fail-closed) — security requirement; no fail-open permitted
- All-box coverage requirement on C2A (UT-C2A-004) — first-box approach is prohibited; cutting this test would invalidate the M01 claim entirely
- weights_only=False grep check (SEC-007) — non-negotiable from Day 1
- coverage_gap_clean_label=True on all C2/C3 records — AR-010; cannot be omitted

---

# 17. RELEASE-CRITICAL WORK

The following must be complete before any final demo, PPT, or public-facing claim.

| Category | Required item | Status |
|---|---|---|
| Core functionality | GATE-4 (validation gate) passed | PASS — TASK-026 Gate-4 evaluation, 2026-10-02 |
| Core functionality | All MUST BUILD tasks complete | Pending |
| Security | SEC-001 through SEC-012 all pass | PASS — functional acceptance retained; current security regression passes |
| Security | weights_only=False grep: 0 matches | PASS — current universal guards |
| Security | Evidence store ACL test (SEC-008) | PASS — accepted frozen Windows deployment/worker boundary |
| Security | Replay nonce rejection (SEC-009) | PASS — current provenance security regression |
| Evidence | All §10 §18 experiment contracts have OBSERVED RESULTS | PASS — maintained §18 observation rows and validation record |
| Evidence | All fixture records carry is_synthetic=True | PASS — explicit real pipeline acceptance |
| Evidence | is_synthetic flag verified in export bundle | PASS — existing six-document export path |
| Offline | Target host tuple documented | PASS — resolved PRE-01; accepted frozen Windows AMD64 / CPython 3.13.12 scope |
| Offline | OFF-001 through OFF-004 pass on target host | PASS — accepted TASK-027 evidence reused; no rerun |
| Claims | No claim broader than observed fixture evidence | Ongoing |
| Claims | No R01 benchmark metrics presented as project results | Ongoing |
| Claims | All project capability claims bounded to fixture scope | Ongoing |
| Repository | License attribution comments for R17 + R27 reuse | Pending |
| Repository | `NOTICES.md` or equivalent for MIT/BSD attribution | Pending |
| Repository | REUSE-015 exclusion verified: grep for Fabric/HyperLedger in codebase → 0 matches | PASS — zero production Python matches in Gate-4 review |
| Repository | Architecture change control log: any change-control decisions recorded | Ongoing |
| Reproducibility | REPRO-001 through REPRO-006 pass | Pending |
| Demo | GATE-5 (demo gate) passed | Pending |
| Demo | `scripts/demo.sh` runs end-to-end offline | Pending |
| Demo | Dashboard offline (no CDN; UNAVAILABLE visible) | Pending |

---

# 18. MAJOR BLOCKERS AND ASSUMPTIONS

## P1 blockers (must resolve before Day 1 of implementation)

| Blocker | Impact if unresolved | Owner |
|---|---|---|
| PRE-01: target host not confirmed | Cannot confirm offline; cannot stage wheels; cannot confirm pycocotools C extension; cannot confirm subprocess isolation mechanism | Project owner / organizer |
| PRE-04: SP-003 vocabulary contract not produced | Cannot finalize evidence schema DDL, schema validator, C5 rule engine | Project team (pre-implementation design session) |
| PRE-05: mandatory format list not confirmed | Cannot scope YOLO task variants; cannot confirm PyTorch workers in scope | Project owner / organizer |

## Secondary blockers (Day 1–2)

| Blocker | Impact if delayed | Owner |
|---|---|---|
| PRE-02: XREG-002 (HMAC vs Ed25519) | C4 signing module ships as SIGNING_UNAVAILABLE shell; signing claim blocked | Project owner decision |
| PRE-03: SP-002 artifact-unit definitions | PyTorch C3A path emits ARTIFACT_UNIT_AMBIGUOUS; ONNX path proceeds | Project team |
| PRE-06: SP-001 reference-health gate | Reference manager ships as all-UNAVAILABLE shell; no HEALTH_VERIFIED at MVP | Project team |
| PRE-08 + PRE-09: SP-004 + SP-006 | C4 signing module blocked alongside PRE-02 | Project team |

## Working assumptions (must be validated or revised)

| Assumption | Risk if wrong | Validation method |
|---|---|---|
| pycocotools C extension builds on target host | COCO parsing falls back to pure-Python stub; structural validation still possible but slower | Confirmed after PRE-01 resolved; build test on target |
| torch CPU wheel available for target OS/arch | C3D emits ASSESSMENT_ERROR for all PyTorch models; demo limited to ONNX model scope | Confirmed after PRE-01 resolved |
| Python subprocess isolation sufficient for B2 boundary on target OS | Subprocess isolation may require OS-specific hardening (namespaces, seccomp) | Confirmed after PRE-01 resolved |
| 5-day window begins after P1 conditions resolved | If P1 resolution is not complete by Day 0, the 5-day clock must be adjusted | Project owner |
| No estimate-as-fact: time allocations are ordering guidance, not guaranteed hours | Any task may take longer than expected | Build to GATE-2 first; expand only after vertical slice passes |

---

# 19. NEXT_STAGE_HANDOFF

## CURRENT STAGE
Stage 12 — MVP Implementation Plan

## ARTIFACT
`11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`

## ESTABLISHED FACTS

- **F-MVP-001:** 29 implementation tasks defined (TASK-001 through TASK-027) in dependency order matching §10 §19 tiers.
- **F-MVP-002:** MUST BUILD, SHOULD BUILD, DEFER, and NOT BUILD classifications are complete for all architecture components.
- **F-MVP-003:** Critical path is: PRE-04 → TASK-005 → TASK-008 → TASK-021 → TASK-022 → TASK-023 → TASK-026.
- **F-MVP-004:** Vertical slice is defined and achievable as the earliest end-to-end demonstration path.
- **F-MVP-005:** TASK-009 (hostile fixtures) is a Tier 2 P0 task — must precede all security tests and security claims.
- **F-MVP-006:** TASK-026 (end-to-end integration + validation) is the gate that enables demo-ready status.
- **F-MVP-007:** Five integration gates (GATE-1 through GATE-5) govern progression; GATE-2 (vertical slice) may not be bypassed.
- **F-MVP-008:** Codex handles backend, workers, schema, tests, and orchestrator. Antigravity handles dashboard. Both use one repository; branches = tasks.
- **F-MVP-009:** TASK-027 (offline validation) is blocked on PRE-01; no offline claim may be made before this task passes on actual target host.
- **F-MVP-010:** No time estimate is treated as a guarantee; the plan orders work by dependency, not by clock hours.

## DECISIONS

- **D-MVP-001:** Vertical slice is COCO-first + ONNX-first. PyTorch and YOLO variant expansion occur only after GATE-2 passes and PRE-01/PRE-05 are resolved.
- **D-MVP-002:** C4 signing ships as SIGNING_UNAVAILABLE shell until PRE-02 + PRE-04 + PRE-08 + PRE-09 are all resolved. Pipeline is not blocked by this.
- **D-MVP-003:** COMP-REF ships as all-UNAVAILABLE shell at MVP (no HEALTH_VERIFIED reference can be established in MVP timeframe).
- **D-MVP-004:** Dashboard (TASK-024) is SHOULD BUILD; cut if it threatens GATE-2.
- **D-MVP-005:** The weights_only=False grep check (SEC-007) is enforced from Day 1 (TASK-009) and must pass continuously.
- **D-MVP-006:** Architecture change control is ACTIVE; implementation agents (Codex, Antigravity) must not redesign the architecture; all conflicts must be raised as proposed changes.

## OPEN QUESTIONS

- All P1 conditions (PRE-01 through PRE-09) remain open. PRE-01, PRE-04, PRE-05 are the hardest gates; implementation must not begin until these are resolved.
- OQ-017 (analyst authentication): analyst_id='UNAVAILABLE' at MVP; no authentication infrastructure built.
- OQ-018 (evidence retention policy): no retention enforcement at MVP; all records retained.
- AF-003 (trusted clock): system timestamp used; TRUSTED_CLOCK_UNAVAILABLE noted in relevant records.
- GAP-010/XREG-010 (M15 evidence ownership): M15 records attributed to C2D at MVP pending project-owner decision.

## CONTRADICTIONS

None identified between this plan and the architecture/technical specifications. Where the technical specification §19 listed parallel-capable tasks, this plan preserves that parallelism and maps it to Codex/Antigravity workstreams.

## IMPORTANT LIMITATIONS

1. This plan does not resolve P1 blocking conditions — it tracks them and stages work accordingly.
2. All time references ("Day 0", "Day 2", "Day 4–5") are ordering guidance based on dependency ordering, not guaranteed clock hours.
3. No capability claim is made by this plan. Claims require GATE-4 (validation gate) to pass with observed experimental results.
4. The plan does not authorize implementation to begin until PRE-01, PRE-04, and PRE-05 are resolved at minimum.

## ARCHITECTURE IMPLICATIONS

None. Architecture is locked. This plan translates the architecture into implementation tasks without modifying it. Any implementation agent finding that a task description requires an architectural change must raise a formal proposed change per §09 §23.

## IMPLEMENTATION IMPLICATIONS

1. Implementation begins with TASK-001 (P1 condition resolution) — this is not optional.
2. TASK-009 (hostile fixtures) is a P0 task and must not be deferred to make room for feature work.
3. TASK-026 (vertical slice integration) must pass before the demo can be prepared.
4. grep checks (weights_only=False, risk_score field, CLEAN constants) must be automated in CI from Day 1 and never pass with a match.
5. The evidence store is the single source of truth for all output; no CLI or dashboard output may be fabricated outside the evidence store.

## VALIDATION IMPLICATIONS

1. All §10 §18 experiment/validation contracts must be executed with OBSERVED RESULTS before any capability claim.
2. All fixture-derived results must carry is_synthetic=True.
3. Offline claim requires TASK-027 to pass on the actual target host.
4. UNAVAILABLE propagation (FIX-013) must pass at all 4 injection points before integration is declared complete.

## DO-NOT-INFER

- Do not infer that this plan authorizes implementation before P1 conditions are resolved.
- Do not infer that GATE-2 passing means capabilities broader than the vertical slice are validated.
- Do not infer that task descriptions in this plan authorize architecture changes — they translate the architecture into tasks.
- Do not infer that the "SHOULD BUILD" status of the dashboard means it is optional for the demo — it is preferred but cuttable if GATE-2 is threatened.
- Do not infer that TASK-019 shipping as a shell (SIGNING_UNAVAILABLE) means provenance binding claims can be made — provenance claims require signing to complete.

## NEXT STAGE INPUTS

For Implementation (Codex / Antigravity), the following must be available:

1. `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md` — this document
2. `10_TECHNICAL_SPECIFICATION_SIH26228.md` — build-level contract (authoritative)
3. `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` — architecture (governing authority)
4. `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` — binding reuse decisions
5. P1 condition resolution records (must be produced before implementation begins)
6. New GitHub repository created and initialized per TASK-002

## NEXT STAGE

**Implementation** (Codex / Antigravity)

Work proceeds in the TASK order defined in Section 7, following the dependency graph in Section 8, respecting the integration gates in Section 14, and enforcing the stopping/cut policy in Section 16.

Codex begins with TASK-002 through TASK-009 (foundation + schema + fixtures).
Antigravity begins after GATE-2 with TASK-024 (dashboard).
Both push to the same repository; branches = tasks per Section 13.

---

# QUALITY CONTROL — STAGE 12 SELF-CHECK

- [x] Every architecture component (COMP-SUP through COMP-FIX, 16 total) is accounted for in MUST BUILD
- [x] Every MUST BUILD has task ID, purpose, source spec, dependencies, expected output, reuse decision (or N/A), tests, acceptance criteria, risk/blockers, and completion state
- [x] SHOULD BUILD, DEFER, and NOT BUILD are explicitly classified with reasons
- [x] Mandatory security/evidence requirements are preserved and appear in every relevant task (coverage_gap_clean_label, PF-002, UNAVAILABLE propagation, no risk score, weights_only=True enforcement)
- [x] Optional features (dashboard, Pipeline Visualization) cannot block the core path — cut policy is explicit
- [x] Reuse decisions (REUSE-001 through REUSE-023) are reflected in tasks
- [x] Critical dependencies are explicit in the dependency graph (Section 8)
- [x] Vertical slice is defined before capability expansion (Section 11)
- [x] Acceptance criteria are testable (unit test IDs mapped to assertions)
- [x] Codex and Antigravity responsibilities are clear and non-overlapping at the semantic boundary
- [x] Branches represent workstreams/tasks, not devices
- [x] No unsupported time estimate is stated as fact — ordering guidance only
- [x] NOT BUILD and DEFER are explicit with reasons and authorities
- [x] NEXT_STAGE_HANDOFF is complete with all required sections
- [x] P1 blocking conditions are tracked throughout every affected task
- [x] GATE-1 through GATE-5 are defined with testable criteria
- [x] Five-day constraint is respected — optional features cut when they threaten the core path
- [x] Architecture change control rule is stated at the top of this document
- [x] UNAVAILABLE ≠ CLEAN invariant is enforced in every relevant task and in the cut policy
- [x] weights_only=False grep check is automated from Day 1 and appears in GATE-1
- [x] risk_score field prohibition is enforced via schema validator (TASK-008) and appears in GATE-3
- [x] TASK-009 (hostile fixtures) positioned as Tier 2 P0 — not deferrable
- [x] TASK-027 (offline validation) correctly blocked on PRE-01
- [x] R01 benchmark metrics prohibition preserved — no R01 metrics appear anywhere in tasks
- [x] License attribution requirements noted for R17 (REUSE-018) and R27 (REUSE-020)
- [x] R01 Fabric client, aggregate risk score, first-box analysis, fail-open audit chain in NOT BUILD
- [x] T05d permanent NON_CLAIM handled in TASK-013 (C2D), TASK-020 (CAP), and TASK-021 (C5)
- [x] PF-002 non-claim required on every TASK-014, TASK-015, TASK-016, TASK-017, TASK-019 output

---

**End of document — 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md**
**Stage:** 12 — MVP Implementation Plan
**Status:** COMPLETE (pending P1 condition resolution before implementation may begin)
**Next stage:** Implementation (Codex + Antigravity on shared repository)
