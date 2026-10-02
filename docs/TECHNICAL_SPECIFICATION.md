# 10_TECHNICAL_SPECIFICATION_SIH26228.md

## SIH 2026 · PS 26228
### Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines

**Document class:** Build-level technical specification. NOT an implementation authorization. NOT a validation record.
**Stage:** Stage 11 — Technical Specification
**Status:** COMPLETE — awaiting P1 condition resolution before implementation may begin
**Input artifacts:**
- `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` — approved architecture blueprint (primary source)
- `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` — binding reuse decisions

**Governing invariants (inherited from architecture — absolute; no exception):**
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
C6 ERROR → C5 UNAVAILABLE (no compression to PASS or omission)
```

---

# 1. TECHNICAL SPECIFICATION STATUS

## 1.1 Architecture lock confirmation

The architecture was approved as **Option A — Deterministic Integrity Spine + Signed Evidence Governance + Offline-First Supervisor-Worker Architecture** (project-owner verbal approval 2026-09-25, documented in `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` §1.1).

This specification proceeds on that basis. The architecture specification is the primary authority; this document adds build-level precision. Any conflict between this document and the architecture specification must be resolved in favour of the architecture specification and treated as a defect in this document.

## 1.2 Specification scope

This document translates the approved architecture into build-level implementation detail:
- Exact Python module/file structure and class/function signatures
- SQLite table DDL with constraints and check conditions
- JSON field-level data contracts with types, required/optional, allowed values, and security significance
- Pseudocode-level algorithm specifications per worker
- IPC mechanism and subprocess invocation parameters
- Cryptographic construction details (design frozen pending XREG-002)
- C5 rule-engine mapping logic
- Test case requirements per component
- Experiment/validation contract
- Implementation dependency graph

## 1.3 What this document does NOT do

- It does NOT authorize implementation to begin. That requires the MVP Implementation Plan (Stage 12) and resolution of the blocking P1 conditions listed in Section 1.4.
- It does NOT resolve PRE-01 through PRE-09 blocking conditions. Those remain open.
- It does NOT finalize library versions except for the hard-constrained PyTorch ≥ 2.10.0 floor (XREG-005).
- It does NOT constitute validation evidence for any capability.
- It does NOT produce project results or performance metrics.

## 1.4 P1 blocking conditions (inherited; must be resolved before implementation)

| ID | Condition | Blocks |
|---|---|---|
| PRE-01 | Target host (OS / CPU / Python version / RAM) not confirmed | All offline claims; ABI closure; subprocess isolation mechanism; resource-limit mechanism selection |
| PRE-02 | XREG-002 (HMAC-SHA256 vs Ed25519) not decided | COMP-C4 signing module implementation; `cryptography` package requirement |
| PRE-03 | SP-002 (artifact-unit definitions) not produced | COMP-W-C3A PyTorch path; COMP-W-C3B |
| PRE-04 | SP-003 (vocabulary contract) not produced | COMP-SCHEMA finalization; COMP-C5; COMP-C4; evidence schema version freeze |
| PRE-05 | Mandatory format list not confirmed | YOLO task-variant scope for COMP-W-C2A; PyTorch scope for COMP-W-C3D |
| PRE-06 | SP-001 (reference-health gate procedure) not produced | COMP-REF health-gate enforcement |
| PRE-07 | GAP-011 (inference record source) not decided | Inference-record ingestion path |
| PRE-08 | SP-004 (crypto profile) not produced | Signing algorithm parameters in COMP-C4 |
| PRE-09 | SP-006 (C3→C4 adapter schema) not produced | Evidence-to-provenance binding field list in COMP-C4 |

**Where P1 conditions block a specific component section below, they are marked inline with `[BLOCKED: PRE-xx]`.**

---

# 2. SYSTEM IMPLEMENTATION OVERVIEW

## 2.1 Technology stack

| Layer | Technology | Rationale |
|---|---|---|
| Runtime language | Python 3.x (target version pending PRE-01) | Stdlib-first; subprocess isolation supported; R17/R27 reuse |
| Supervisor architecture | Single OS process; no threads for evidence-critical paths | Eliminates race conditions on the evidence store write path |
| Worker architecture | Separate OS subprocess per worker invocation via `subprocess.Popen` | B2 trust boundary enforcement; hostile artifact isolation |
| IPC mechanism | Named temp file (task JSON → worker; result JSON ← worker) | Avoids stdout buffering issues for large outputs; output size is measurable before parsing |
| Persistence | SQLite with WAL mode; Python stdlib `sqlite3` | Fully offline; atomic commits; R17 storage patterns |
| Hashing | Python stdlib `hashlib` SHA-256 | Offline; no external dependency |
| Signing — Ed25519 path | `cryptography` Python package (pre-staged wheel) | If XREG-002 → Ed25519 |
| Signing — HMAC path | Python stdlib `hmac` | If XREG-002 → HMAC-SHA256; zero additional dependency |
| ONNX structural check | `onnx` Python package (pre-staged wheel) | Structural validation + path check; no ORT required |
| PyTorch safe loading | `torch` CPU-only (pre-staged wheel, ≥ 2.10.0) | `weights_only=True`; no ORT; no Ultralytics |
| COCO parsing | `pycocotools` (R27 ADOPT/ADAPT; BSD; pre-staged wheel with C extension) | Reduces COCO parsing implementation effort; geometry validation layer added on top |
| CLI | Python stdlib `argparse` | No additional dependency |
| Dashboard (MVP value feature) | Lightweight stdlib `http.server` serving a single self-contained HTML file | Fully offline; no npm; no React; no CDN |

## 2.2 Project module structure (authoritative)

Implementation agents must follow this structure exactly. They must not invent alternative layouts without architecture change control.

```
assurance_system/
├── __init__.py
├── exceptions.py                    # Project exception hierarchy
├── constants.py                     # Enum strings for all state values
│
├── config/
│   ├── __init__.py
│   ├── loader.py                    # Config loader and startup validator
│   ├── system_config.yaml           # Runtime configuration (Section 15)
│   ├── resource_limits.yaml         # Per-worker resource caps
│   └── supported_formats.yaml       # Format/variant scope declaration
│
├── schema/
│   ├── evidence_record_v1.schema.json
│   ├── worker_input_v1.schema.json
│   ├── worker_output_v1.schema.json
│   ├── provenance_record_v1.schema.json
│   ├── finding_v1.schema.json
│   └── deferred_record_v1.schema.json
│
├── supervisor/
│   ├── __init__.py
│   ├── orchestrator.py              # COMP-SUP — pipeline controller
│   ├── schema_validator.py          # COMP-SCHEMA — evidence schema enforcer
│   ├── reference_manager.py         # COMP-REF — reference health state machine
│   ├── audit_chain.py               # COMP-AUDIT — hash-chained audit trail writer
│   ├── evidence_store.py            # COMP-STORE — SQLite persistence layer
│   ├── provenance.py                # COMP-C4 — provenance record builder + signing
│   ├── interpretation.py            # COMP-C5 — assurance interpretation rule engine
│   └── capability_declaration.py    # DEFERRED_IN_SCOPE emitter; capability matrix
│
├── workers/
│   ├── __init__.py
│   ├── base.py                      # Worker entry-point boilerplate; IPC pattern
│   ├── c2a_structural.py            # COMP-W-C2A — all-box structural/geometry
│   ├── c2b_exact_hash.py            # COMP-W-C2B — SHA-256 exact duplicate detector
│   ├── c2c_concentration.py         # COMP-W-C2C — source concentration statistics
│   ├── c2d_image_hash.py            # COMP-W-C2D — image-level hash floor (M15)
│   ├── c3a_artifact_unit.py         # COMP-W-C3A — artifact-unit resolver
│   ├── c3b_model_hash.py            # COMP-W-C3B — model identity hasher
│   ├── c3c_onnx_structural.py       # COMP-W-C3C — ONNX structural validator
│   └── c3d_safe_load.py             # COMP-W-C3D — PyTorch safe-loading gate
│
├── interfaces/
│   ├── __init__.py
│   ├── cli.py                       # COMP-IFACE — CLI entry points
│   ├── dashboard.py                 # COMP-IFACE — read-only dashboard (MVP value feature)
│   └── exporter.py                  # Evidence bundle export (ZIP)
│
└── fixtures/
    ├── __init__.py
    ├── generator.py                 # COMP-FIX — fixture generator CLI
    └── hostile/
        ├── __init__.py
        ├── pickle_payload.py        # Hostile pickle fixture generator
        ├── onnx_path_traversal.py   # ONNX external-data path-traversal fixture
        ├── archive_bomb.py          # Archive bomb fixture
        ├── coco_geometry.py         # All-box COCO geometry violation corpus
        └── yolo_geometry.py         # All-box YOLO geometry violation corpus

cli.py                               # Top-level entry point (delegates to interfaces/cli.py)
setup.py / pyproject.toml           # Package setup
requirements.txt                     # Pin list (frozen after PRE-01 confirmed)
wheelhouse/                          # Pre-staged offline wheels (empty at repo creation)
artifact_unit_defs/                  # SP-002 output (empty until PRE-03 resolved)
tests/
├── unit/
├── integration/
├── negative/
├── security/
└── offline/
```

## 2.3 Deployment directories (Linux primary; CONDITIONAL PRE-01)

```
/opt/assurance-system/               # Supervisor code; schema; config (trusted zone)
/var/assurance/evidence-store/       # SQLite DB  [ACL: supervisor rw; others: none]
/var/assurance/audit-trail/          # Audit log  [ACL: supervisor rw; analyst r; workers: none]
/var/assurance/references/           # Reference registry  [ACL: supervisor rw; others: none]
/var/assurance/keys/                 # Signing key + sequence state  [ACL: supervisor r; others: none]
/tmp/assurance-workers/<run_id>/     # Ephemeral worker temp dirs (per subprocess; cleaned after run)
/opt/assurance-wheelhouse/           # Pre-staged Python wheels
/opt/assurance-fixtures/             # Hostile fixture suite (test-only; not on production path)
```

## 2.4 Entry points

| Entry point | Command | Effect |
|---|---|---|
| Full pipeline | `python cli.py assess --submission <manifest_path>` | Runs end-to-end pipeline; writes all records; prints summary |
| Show finding | `python cli.py show-finding --asset-id <id>` | All C5 fields printed including UNAVAILABLE states |
| Show evidence | `python cli.py show-evidence --asset-id <id> --method <method-id>` | Evidence record |
| Audit trail | `python cli.py show-audit-trail` | Read-only chain display; CHAIN_CORRUPT reported if detected |
| Export bundle | `python cli.py export-bundle --asset-id <id> --output <path>` | Structured ZIP |
| List deferred | `python cli.py list-deferred` | All DEFERRED_IN_SCOPE records listed |
| Dashboard | `python cli.py dashboard --port <port>` | Read-only evidence dashboard |
| Fixtures | `python -m assurance_system.fixtures.generator <fixture-type> --output <dir>` | Hostile fixture generation |

---

# 3. COMPONENT SPECIFICATIONS

This section defines build-level detail for every approved architecture component. The architecture component table in `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` §6 is the primary source; this section adds exact module paths, method signatures, IPC parameters, algorithm pseudocode, and error-handling requirements.

## 3.1 COMP-SUP — Supervisor Orchestrator

**Module:** `assurance_system/supervisor/orchestrator.py`
**Primary class:** `SupervisorOrchestrator`

**Key method signatures:**

```python
class SupervisorOrchestrator:

    def run_pipeline(self, manifest_path: str) -> PipelineRunSummary:
        """
        Entry point for a full assessment pipeline run.
        Sequence: validate manifest → emit capability declarations and DEFERRED_IN_SCOPE records
                  → dispatch C2 workers → dispatch C3 workers → run C4 binding
                  → run C5 interpretation → write PIPELINE_RUN_COMPLETE audit event → return summary.
        On any unrecoverable error: write PIPELINE_RUN_ERROR audit event; raise PipelineError.
        Never silently continues past a critical component failure that affects evidence integrity.
        """

    def _dispatch_worker(
        self,
        worker_module: str,         # e.g. 'assurance_system.workers.c2a_structural'
        task_spec: dict,            # Validated task JSON per Section 4.1
        resource_limits: ResourceLimits
    ) -> dict:
        """
        IPC mechanism: named temp file.
        Spawns worker subprocess.
        Writes task_spec JSON to task_path.
        Invokes: [sys.executable, '-m', worker_module,
                  '--task-file', str(task_path),
                  '--result-file', str(result_path)]
        Waits up to resource_limits.timeout_seconds.
        Reads result JSON from result_path.
        Passes result to COMP-SCHEMA before returning.
        On timeout: kills worker; returns ASSESSMENT_ERROR record.
        On crash (non-zero exit): returns ASSESSMENT_ERROR record.
        On missing result file: returns ASSESSMENT_ERROR record.
        On schema violation: returns SCHEMA_VIOLATION audit record.
        Always cleans up temp directory after every code path.
        NEVER returns a CLEAN or positive-assurance result for a failed worker invocation.
        """

    def _build_assessment_error(
        self, task_spec: dict, reason: str, detail: str = ''
    ) -> dict:
        """
        Constructs a standards-compliant ASSESSMENT_ERROR evidence record
        when a worker fails. All fields populated: UNAVAILABLE defaults,
        limitations non-empty, non_claims non-empty, coverage_gap_clean_label=True.
        """

    def _emit_deferred_in_scope_records(self, asset_id: str) -> None:
        """
        Called immediately after capability declaration.
        Supervisor emits DEFERRED_IN_SCOPE records directly (no worker invocation) for:
          - Behavioral battery (M07 class)
          - PDQ near-duplicate (M03-PDQ)
          - Statistical drift / OOD (M04, M05)
          - Reference-relative comparison (M11)
          - TorchScript loading
          - External tail completeness
          - Sybil-resistant contributor identity authentication
          - T05d clean-label detection
        """

    def _accept_worker_result(self, raw_result: dict, asset_id: str,
                               method_id: str) -> str:
        """
        Schema-validates raw_result via COMP-SCHEMA.
        On VALID: supervisor assigns record_id (UUID4); computes record_digest;
                  writes evidence record to COMP-STORE;
                  appends EVIDENCE_RECORD_WRITTEN audit event.
        On INVALID: appends WORKER_RESULT_REJECTED_SCHEMA_VIOLATION audit event;
                    does NOT write to evidence store; raises SchemaViolationError.
        Returns record_id on success.
        """
```

**Subprocess invocation (implementation template):**

```python
import subprocess, sys, os, json, uuid, shutil, pathlib

def _dispatch_worker(self, worker_module, task_spec, resource_limits):
    run_id = uuid.uuid4().hex
    worker_tmp = pathlib.Path(f'/tmp/assurance-workers/{run_id}')
    worker_tmp.mkdir(parents=True, mode=0o700)
    task_path   = worker_tmp / 'task.json'
    result_path = worker_tmp / 'result.json'
    task_path.write_text(json.dumps(task_spec), encoding='utf-8')

    cmd = [sys.executable, '-m', worker_module,
           '--task-file',   str(task_path),
           '--result-file', str(result_path)]

    # Strip credentials from env; CWD isolated to temp dir
    clean_env = {k: v for k, v in os.environ.items()
                 if k not in ('ASSURANCE_KEY_PATH', 'ASSURANCE_DB_PATH')}

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,   # Workers MUST NOT write meaningful output to stdout
            stderr=subprocess.PIPE,
            close_fds=True,
            cwd=str(worker_tmp),
            env=clean_env,
        )
        _, stderr_bytes = proc.communicate(
            timeout=resource_limits.timeout_seconds)

    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait()
        return self._build_assessment_error(
            task_spec, 'TIMEOUT',
            f'Exceeded {resource_limits.timeout_seconds}s')

    except Exception as e:
        return self._build_assessment_error(task_spec, 'SPAWN_ERROR', str(e))

    finally:
        shutil.rmtree(str(worker_tmp), ignore_errors=True)  # Always clean up

    if proc.returncode != 0:
        return self._build_assessment_error(
            task_spec, 'NONZERO_EXIT',
            stderr_bytes.decode('utf-8', errors='replace')[:2048])

    if not result_path.exists():
        return self._build_assessment_error(task_spec, 'NO_RESULT_FILE')

    try:
        raw = json.loads(result_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return self._build_assessment_error(task_spec, 'INVALID_JSON', str(e))

    return raw   # Caller (self._accept_worker_result) validates via COMP-SCHEMA
```

**Security requirements:**
- Signing key path is loaded only within supervisor; never passed in task_spec to workers.
- Evidence store path is not passed in task_spec.
- Worker CWD is the ephemeral temp directory, not the asset directory root.
- Environment variables containing credentials are stripped from subprocess env.

**Failure behavior:**

| Condition | Supervisor action |
|---|---|
| Worker timeout | Kill worker; emit ASSESSMENT_ERROR evidence record; continue pipeline for other assets |
| Worker crash (non-zero exit) | Emit ASSESSMENT_ERROR; log stderr excerpt in audit event; continue |
| Schema violation on worker output | Emit SCHEMA_VIOLATION audit event; do NOT write evidence record; continue |
| Evidence store write failure | Raise StorageWriteError; attempt to write ERROR audit event; halt pipeline for affected record |
| Signing key unavailable | Record SIGNING_UNAVAILABLE in provenance record; record is not silently treated as signed |
| Audit chain write failure | Attempt secondary error log; supervisor raises alert; pipeline halts for the affected record |

---

## 3.2 COMP-SCHEMA — Schema Validator

**Module:** `assurance_system/supervisor/schema_validator.py`
**Primary class:** `EvidenceSchemaValidator`

**Implementation note:** Custom validation without `jsonschema` package (not in approved dependency list). All validation is pure Python structural checks.

```python
class EvidenceSchemaValidator:

    REQUIRED_WORKER_OUTPUT_FIELDS = [
        'schema_version', 'worker_id', 'assessment_status',
        'raw_signal', 'access_mode', 'artifact_unit_id',
        'coverage_gap_clean_label', 'limitations', 'non_claims',
        'dependency_declaration', 'assessment_timestamp', 'error_detail'
    ]

    PROHIBITED_FIELDS = {
        'risk_score', 'aggregate_assurance', 'compromise_probability',
        'overall_score', 'threat_score', 'malicious_probability',
        'confidence_score', 'trust_score', 'safety_score'
    }

    VALID_ASSESSMENT_STATUS_VALUES = {
        'COMPLETED', 'ASSESSMENT_ERROR', 'UNAVAILABLE', 'UNSUPPORTED',
        'DEFERRED_IN_SCOPE', 'ARTIFACT_UNIT_AMBIGUOUS',
        'LOAD_BLOCKED', 'LOAD_SUCCESS', 'LOAD_ERROR',
        'ONNX_PATH_CONTAINMENT_VIOLATION', 'STRUCTURAL_VALID', 'STRUCTURAL_INVALID',
        'REFERENCE_UNAVAILABLE'
    }

    C3_WORKER_IDS = {'COMP-W-C3A', 'COMP-W-C3B', 'COMP-W-C3C', 'COMP-W-C3D'}
    C2_WORKER_IDS = {'COMP-W-C2A', 'COMP-W-C2B', 'COMP-W-C2C', 'COMP-W-C2D'}

    def validate_worker_output(self, raw: dict, task_type: str) -> ValidationResult:
        """
        Checks in order (first failure returns immediately):
        1. All REQUIRED_WORKER_OUTPUT_FIELDS present.
        2. No field in PROHIBITED_FIELDS anywhere in the object tree (recursive scan).
        3. assessment_status in VALID_ASSESSMENT_STATUS_VALUES.
        4. coverage_gap_clean_label is exactly True (not absent, not False, not 0).
           → On C2 and C3 records this is enforced without exception.
        5. access_mode is a non-null, non-empty string on C3 records.
        6. limitations is a list with at least one non-empty string.
        7. non_claims is a list with at least one non-empty string.
        8. assessment_timestamp parses as ISO 8601.
        9. schema_version matches the active declared schema version.
        Returns ValidationResult(valid=True) or ValidationResult(valid=False, reason=<str>).
        NEVER raises an exception that the caller could accidentally treat as a valid result.
        """

    def _recursive_prohibited_scan(self, obj, path='') -> list[str]:
        """Recursively scans obj for keys in PROHIBITED_FIELDS. Returns list of violation paths."""

    def validate_finding(self, finding: dict) -> ValidationResult:
        """Validates C5 structured finding before persistence."""

    def validate_provenance_record(self, record: dict) -> ValidationResult:
        """Validates provenance record before persistence. Checks PF-002 field present."""
```

**Hardcoded enforcement (not configurable by any parameter):**

| Check | Failure condition | Result |
|---|---|---|
| `coverage_gap_clean_label` | absent OR `False` OR `0` on any C2/C3 record | SCHEMA_VIOLATION |
| `access_mode` | null or empty string on C3 record | SCHEMA_VIOLATION |
| Any key in PROHIBITED_FIELDS | anywhere in object tree | SCHEMA_VIOLATION |
| `limitations` or `non_claims` | empty list | SCHEMA_VIOLATION |
| `assessment_status` | not in valid set | SCHEMA_VIOLATION |

---

## 3.3 COMP-W-C2A — All-Box Structural / Geometry Validator

**Module:** `assurance_system/workers/c2a_structural.py`

**Worker entry point pattern (base.py):**

```python
# All workers follow this pattern via workers/base.py:
import argparse, json, sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task-file', required=True)
    parser.add_argument('--result-file', required=True)
    args = parser.parse_args()
    task = json.loads(open(args.task_file).read())
    result = run_assessment(task)   # Worker-specific function
    open(args.result_file, 'w').write(json.dumps(result))

if __name__ == '__main__':
    main()
```

**Algorithm — COCO path:**

```
Input: annotation_file_path, asset_directory

Pre-condition check: annotation_file_path must be within asset_directory.

1. Check file size ≤ configured limit (default 2 GB).
2. Open and load as UTF-8 JSON.
   → JSONDecodeError → ASSESSMENT_ERROR with error_detail.
3. Check required root fields: ['images', 'annotations', 'categories'].
   → Missing field → violation: {type: MISSING_ROOT_FIELD, field: <name>}
4. Build category_id_set = {cat['id'] for cat in data.get('categories', [])}
5. Build image_id_set = {img['id'] for img in data.get('images', [])}
6. Initialise violations = [], total_checked = 0
7. For EACH annotation in data.get('annotations', []):   ← ALL BOX REQUIREMENT
   total_checked += 1
   ann_id = ann.get('id', f'index_{index}')
   a. Check required fields: ['id', 'image_id', 'category_id', 'bbox']
      → missing → {type: MISSING_ANNOTATION_FIELD, annotation_id: ann_id, field: <name>}
   b. bbox = ann.get('bbox', [])
      len(bbox) ≠ 4 → {type: INVALID_BBOX_FORMAT, annotation_id: ann_id}; continue
   c. x, y, w, h = bbox
      for each value: if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        → {type: INVALID_NUMERIC_VALUE, annotation_id: ann_id, field: <x|y|w|h>, value: str(v)}
   d. x < 0 or y < 0 → {type: NEGATIVE_COORDINATE, annotation_id: ann_id}
   e. w <= 0 → {type: NON_POSITIVE_WIDTH, annotation_id: ann_id, value: w}
   f. h <= 0 → {type: NON_POSITIVE_HEIGHT, annotation_id: ann_id, value: h}
   g. ann.get('category_id') not in category_id_set
      → {type: OUT_OF_RANGE_CATEGORY_ID, annotation_id: ann_id}
   h. ann.get('image_id') not in image_id_set
      → {type: ORPHAN_ANNOTATION_IMAGE_ID, annotation_id: ann_id}
   i. 'area' in ann and ann['area'] <= 0
      → {type: NON_POSITIVE_AREA, annotation_id: ann_id, area: ann['area']}
      Note: area ≠ w*h is NOT flagged (legitimate for polygon masks)
8. Return worker output record (see Section 4.2) with:
   assessment_status: 'COMPLETED'
   raw_signal.total_annotations_checked: total_checked
   raw_signal.violations: violations
   raw_signal.violation_count: len(violations)
   raw_signal.format: 'COCO'
```

**Algorithm — YOLO path [CONDITIONAL: PRE-05]:**

```
Input: label_file_path, task_variant

For each non-empty, non-comment line:
  parts = line.strip().split()
  class_id_str = parts[0]
  Try int(class_id_str); if fails → {type: INVALID_CLASS_ID, line: line_num}; continue
  class_id = int(class_id_str)
  class_id < 0 → {type: NEGATIVE_CLASS_ID, line: line_num}

  YOLO_DETECTION (expected: 5 fields):
    len(parts) ≠ 5 → {type: WRONG_FIELD_COUNT, expected: 5, found: len(parts), line: line_num}
    for each of [cx=parts[1], cy=parts[2], w=parts[3], h=parts[4]]:
      parse float; NaN/Inf → INVALID_NUMERIC_VALUE
      not in [0.0, 1.0] → OUT_OF_RANGE_COORDINATE
      w or h ≤ 0 → NON_POSITIVE_DIMENSION

  YOLO_SEG (class_id + even number of coordinates ≥ 6):
    coord_count = len(parts) - 1
    coord_count < 6 → INVALID_POLYGON_FORMAT (too few points; minimum 3 pairs)
    coord_count % 2 ≠ 0 → INVALID_POLYGON_FORMAT (odd coordinate count)
    for each coordinate: parse float; check [0.0, 1.0]; check no NaN/Inf

  YOLO_POSE (class_id cx cy w h + triples of kp_x kp_y kp_visibility):
    kp_count = len(parts) - 5
    kp_count < 0 → WRONG_FIELD_COUNT
    kp_count % 3 ≠ 0 → INVALID_KEYPOINT_FORMAT
    cx, cy, w, h: float; [0,1]; positive dimensions
    for each keypoint triple: kp_x, kp_y in [0,1]; kp_v in {0,1,2}
      kp_v not in {0,1,2} → INVALID_VISIBILITY_VALUE

  YOLO_OBB (class_id cx cy w h angle — 6 fields):
    len(parts) ≠ 6 → WRONG_FIELD_COUNT
    cx, cy, w, h: float; [0,1]; positive dimensions
    angle: float; no range restriction; NaN/Inf check only

  Unknown task_variant → UNSUPPORTED_TASK_VARIANT; worker returns UNSUPPORTED record
```

**Limitations field (hardcoded, non-suppressible):**
```python
C2A_LIMITATIONS = [
    "Structural/geometry validation detects format violations only; it does not detect "
    "semantic poisoning, adversarial examples, or mislabelling that conforms to the format spec.",
    "Clean-label attacks (T05d) are not detectable by this method; they conform to valid format.",
    "Violation count is a structural observation; it does not imply attack count or attacker intent.",
    "Area-field check identifies non-positive declared area only; it does not verify polygon mask correctness.",
    "Category and image ID range validation requires all categories and images to be present "
    "in the same annotation file."
]
C2A_NON_CLAIMS = [
    "STRUCTURAL_VALID does not imply annotation labels are semantically correct.",
    "STRUCTURAL_VALID does not imply the training distribution is unmanipulated.",
    "T05d (clean-label poisoning) is NOT covered by this method; no detection claim is made.",
    "Violation count does not imply attack attribution or malicious intent."
]
```

---

## 3.4 COMP-W-C2B — SHA-256 Exact Duplicate Detector

**Module:** `assurance_system/workers/c2b_exact_hash.py`

**Algorithm:**

```python
def run_assessment(task: dict) -> dict:
    asset_paths = task['asset_paths']
    asset_directory = task['asset_directory']
    digest_map = {}      # digest_hex → [path_str]
    error_files = []

    for path_str in asset_paths:
        # Path containment re-check
        if not is_within_directory(path_str, asset_directory):
            error_files.append({'path': path_str, 'error': 'PATH_CONTAINMENT_VIOLATION'})
            continue
        try:
            h = hashlib.sha256()
            with open(path_str, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            digest = h.hexdigest()
            digest_map.setdefault(digest, []).append(path_str)
        except (IOError, OSError) as e:
            error_files.append({'path': path_str, 'error': str(e)})

    file_digest_map = {path: digest
                       for digest, paths in digest_map.items()
                       for path in paths}
    duplicate_groups = {d: paths for d, paths in digest_map.items()
                        if len(paths) > 1}

    all_failed = len(error_files) == len(asset_paths)
    status = 'ASSESSMENT_ERROR' if all_failed else 'COMPLETED'

    return build_worker_output(
        worker_id='COMP-W-C2B',
        assessment_status=status,
        raw_signal={
            'file_digest_map': file_digest_map,
            'duplicate_groups': duplicate_groups,
            'duplicate_group_count': len(duplicate_groups),
            'total_duplicated_files': sum(len(p) for p in duplicate_groups.values()),
            'read_errors': error_files,
            'total_files_processed': len(asset_paths) - len(error_files),
            'pdq_status': 'DEFERRED_IN_SCOPE'
        },
        limitations=[
            "Detects byte-level exact duplicates only; near-duplicate detection (PDQ) is DEFERRED_IN_SCOPE.",
            "Read errors for individual files exclude those files; remaining files are assessed.",
            "Does not attribute duplicate pairs to any specific attack category.",
            "Large corpora are subject to the configured wall-clock timeout."
        ],
        non_claims=[
            "Exact duplicate presence does not imply flooding attack or malicious intent.",
            "Non-duplicate files may still be adversarially manipulated.",
            "Near-duplicate detection (PDQ) is DEFERRED_IN_SCOPE and is not covered here."
        ]
    )
```

---

## 3.5 COMP-W-C2C — Source Concentration Statistics

**Module:** `assurance_system/workers/c2c_concentration.py`

```python
def run_assessment(task: dict) -> dict:
    contributor_metadata = task.get('contributor_metadata', [])
    identity_quality = task.get('identity_quality', 'UNTRUSTED')

    if not contributor_metadata:
        return build_worker_output(
            worker_id='COMP-W-C2C',
            assessment_status='ASSESSMENT_ERROR',
            error_detail='No contributor metadata available',
            raw_signal=None,
            limitations=["No contributor metadata supplied."],
            non_claims=["No statistics can be reported without metadata."]
        )

    source_counts = {}
    for record in contributor_metadata:
        source = (record.get('contributor_id') or
                  record.get('source_batch') or 'UNKNOWN')
        source_counts[source] = source_counts.get(source, 0) + 1

    total = sum(source_counts.values())
    shares = {s: c / total for s, c in source_counts.items()}

    # Herfindahl-Hirschman Index: range [1/n, 1]
    hhi = sum(s ** 2 for s in shares.values())

    # Shannon entropy in bits: range [0, log2(n)]
    entropy = -sum(s * math.log2(s) for s in shares.values() if s > 0)

    # SYBIL_UNRELIABLE defaults True unless external authenticated identity provided
    sybil_unreliable = (identity_quality != 'TRUSTED')

    return build_worker_output(
        worker_id='COMP-W-C2C',
        assessment_status='COMPLETED',
        raw_signal={
            'hhi': hhi,
            'shannon_entropy_bits': entropy,
            'per_source_shares': shares,
            'per_source_counts': source_counts,
            'total_items': total,
            'unique_sources': len(source_counts),
            'identity_quality': identity_quality,
            'sybil_unreliable': sybil_unreliable
        },
        limitations=[
            "Contributor identity is self-asserted (path/metadata-derived) unless "
            "external authenticated identity is provided via TRUSTED identity_quality.",
            "SYBIL_UNRELIABLE=True means fragmentation cannot be attributed to Sybil "
            "attack vs. legitimate multi-source distribution.",
            "High HHI indicates concentration; it does not establish attack type or intent.",
            "No external identity authentication mechanism is currently established."
        ],
        non_claims=[
            "Source concentration statistics do not prove data poisoning.",
            "High HHI does not imply malicious intent.",
            "SYBIL_UNRELIABLE=True does not mean a Sybil attack is occurring.",
            "No aggregate risk score is produced by this method."
        ]
    )
```

---

## 3.6 COMP-W-C2D — Image-Level Hash Floor (M15 hash tier)

**Module:** `assurance_system/workers/c2d_image_hash.py`

```python
def run_assessment(task: dict) -> dict:
    # SHA-256 per image file; streaming; same algorithm as C2B
    # Duplicate group detection at image level (separate from annotation-level C2B)
    # PDQ tier: always emits 'DEFERRED_IN_SCOPE' in raw_signal.pdq_status
    ...
    return build_worker_output(
        worker_id='COMP-W-C2D',
        assessment_status='COMPLETED',
        raw_signal={
            'per_image_digests': {path: digest for path, digest in ...},
            'duplicate_groups': {...},
            'pdq_status': 'DEFERRED_IN_SCOPE'
        },
        limitations=[
            "SHA-256 hash equality establishes byte-level identity only.",
            "PDQ near-duplicate detection is DEFERRED_IN_SCOPE; visually similar "
            "images with different bytes are not detected by this method."
        ],
        non_claims=[
            "Hash equality does not establish visual or semantic near-duplicate relationship.",
            "PDQ near-duplicate detection (M03-PDQ) is DEFERRED_IN_SCOPE."
        ]
    )
```

---

## 3.7 COMP-W-C3A — Artifact-Unit Resolver

**Module:** `assurance_system/workers/c3a_artifact_unit.py`
**[BLOCKED: PRE-03 for PyTorch path]**

**Algorithm — ONNX path (containment-first):**

```python
def resolve_onnx_artifact_unit(model_path: str, asset_directory: str) -> dict:
    asset_dir_real = os.path.realpath(asset_directory)
    model_real     = os.path.realpath(model_path)

    # Step 1: model file itself must be within asset_directory
    if not model_real.startswith(asset_dir_real + os.sep):
        return _path_containment_violation(model_path, 'MODEL_FILE_OUTSIDE_ASSET_DIR')

    # Step 2: Load protobuf header only (no external data loading)
    import onnx
    try:
        model_proto = onnx.load(model_path, load_external_data=False)
    except Exception as e:
        return _assessment_error(f'ONNX_LOAD_HEADER_FAILED: {e}')

    # Step 3: Extract external tensor file references
    external_refs = []
    for init in model_proto.graph.initializer:
        if init.data_location == onnx.TensorProto.EXTERNAL:
            for kv in init.external_data:
                if kv.key == 'location':
                    external_refs.append(kv.value)

    # Step 4: Containment check for each external ref
    violations = []
    resolved_paths = []
    for ref in external_refs:
        # Check A: absolute path
        if os.path.isabs(ref):
            violations.append({'ref': ref, 'reason': 'ABSOLUTE_PATH'})
            continue
        # Check B: traversal string pattern
        norm_ref = ref.replace('\\', '/')
        if '..' in norm_ref.split('/'):
            violations.append({'ref': ref, 'reason': 'TRAVERSAL_PATTERN'})
            continue
        # Check C: resolved canonical path still within asset_directory
        candidate = os.path.realpath(os.path.join(asset_dir_real, ref))
        if not candidate.startswith(asset_dir_real + os.sep):
            violations.append({'ref': ref, 'reason': 'RESOLVES_OUTSIDE_ASSET_DIR'})
            continue
        # Check D: symlink resolution
        if os.path.islink(os.path.join(asset_dir_real, ref)):
            link_target = os.path.realpath(os.path.join(asset_dir_real, ref))
            if not link_target.startswith(asset_dir_real + os.sep):
                violations.append({'ref': ref, 'reason': 'SYMLINK_ESCAPE'})
                continue
        resolved_paths.append(candidate)

    if violations:
        return build_worker_output(
            worker_id='COMP-W-C3A',
            assessment_status='ONNX_PATH_CONTAINMENT_VIOLATION',
            raw_signal={'violations': violations, 'model_path': model_path},
            access_mode='UNAVAILABLE',
            limitations=["Path containment violation detected; model pipeline is BLOCKED."],
            non_claims=["ONNX_PATH_CONTAINMENT_VIOLATION does not prove malicious intent; "
                        "it indicates an external data path outside the asset directory."]
        )

    return build_worker_output(
        worker_id='COMP-W-C3A',
        assessment_status='COMPLETED',
        raw_signal={
            'artifact_unit': {
                'main_file': model_real,
                'external_files': resolved_paths,
                'artifact_unit_definition_id': 'UNAVAILABLE'  # SP-002 pending
            }
        },
        access_mode='BLACK_BOX',
        limitations=["Artifact-unit definition ID is UNAVAILABLE pending SP-002 resolution."],
        non_claims=["ONNX path containment check does not establish safe content of the model."]
    )
```

**Algorithm — PyTorch path [BLOCKED: PRE-03]:**

```python
def resolve_pytorch_artifact_unit(model_path: str, asset_directory: str,
                                   artifact_unit_def: dict | None) -> dict:
    if artifact_unit_def is None:
        return build_worker_output(
            worker_id='COMP-W-C3A',
            assessment_status='ARTIFACT_UNIT_AMBIGUOUS',
            raw_signal={'reason': 'SP-002 artifact-unit definition not loaded'},
            access_mode='UNAVAILABLE',
            artifact_unit_id='UNAVAILABLE',
            limitations=["Artifact-unit for PyTorch models is undefined pending SP-002."],
            non_claims=["ARTIFACT_UNIT_AMBIGUOUS means hash-dependent methods are UNAVAILABLE."]
        )
    # Apply SP-002 file list rules (implementation deferred to PRE-03 resolution)
    ...
```

**Algorithm — TorchScript path:**

```python
def resolve_torchscript_artifact_unit(model_path: str) -> dict:
    return build_worker_output(
        worker_id='COMP-W-C3A',
        assessment_status='DEFERRED_IN_SCOPE',
        raw_signal=None,
        access_mode='UNAVAILABLE',
        deferral_reason='TorchScript loading: isolated worker not demonstrated on target host',
        limitations=["TorchScript format is DEFERRED_IN_SCOPE at MVP."],
        non_claims=["DEFERRED_IN_SCOPE does not mean TorchScript was assessed and found acceptable."]
    )
```

---

## 3.8 COMP-W-C3B — Model Identity Hasher

**Module:** `assurance_system/workers/c3b_model_hash.py`
**[BLOCKED: PRE-03 for PyTorch artifact-unit definition]**

```python
def run_assessment(task: dict) -> dict:
    artifact_unit = task.get('artifact_unit')   # dict from C3A result
    reference_digest = task.get('reference_digest')  # str | None

    if artifact_unit is None or artifact_unit.get('artifact_unit_definition_id') == 'UNAVAILABLE':
        # SP-002 not frozen; cannot produce reproducible combined digest
        return build_worker_output(
            worker_id='COMP-W-C3B',
            assessment_status='ARTIFACT_UNIT_AMBIGUOUS',
            raw_signal={'reason': 'artifact_unit undefined or SP-002 not resolved'},
            access_mode='UNAVAILABLE',
            ...
        )

    all_files = ([artifact_unit['main_file']] +
                 artifact_unit.get('external_files', []))

    per_file_digests = {}
    for file_path in all_files:
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        per_file_digests[file_path] = h.hexdigest()

    # Combined digest: lexicographic sort of paths, concatenate digests, outer SHA-256
    sorted_paths = sorted(per_file_digests.keys())
    combined_input = ''.join(per_file_digests[p] for p in sorted_paths)
    combined_digest = hashlib.sha256(combined_input.encode('ascii')).hexdigest()

    comparison_result = 'UNAVAILABLE'
    if reference_digest is not None:
        comparison_result = 'MATCH' if combined_digest == reference_digest else 'DIFFERENT'

    return build_worker_output(
        worker_id='COMP-W-C3B',
        assessment_status='COMPLETED',
        raw_signal={
            'combined_artifact_unit_digest': combined_digest,
            'per_file_digests': per_file_digests,
            'sorted_path_order_used': sorted_paths,
            'artifact_unit_definition_id': artifact_unit.get('artifact_unit_definition_id'),
            'reference_digest_provided': reference_digest is not None,
            'comparison_result': comparison_result
        },
        access_mode='BLACK_BOX',
        artifact_unit_id=artifact_unit.get('artifact_unit_definition_id', 'UNAVAILABLE'),
        limitations=[
            "SHA-256 digest match establishes byte-level identity only (PF-002).",
            "MATCH does not imply the model is free of backdoors or adversarial modifications.",
            "DIFFERENT does not establish malicious modification; legitimate updates also produce DIFFERENT."
        ],
        non_claims=[
            "Hash match ≠ safe; hash match ≠ semantically equivalent; hash match ≠ causal execution proof (PF-002).",
            "MATCH does not establish global backdoor absence.",
            "DIFFERENT does not prove malicious intent."
        ]
    )
```

---

## 3.9 COMP-W-C3C — ONNX Structural Validator

**Module:** `assurance_system/workers/c3c_onnx_structural.py`

```python
def run_assessment(task: dict) -> dict:
    onnx_path = task['asset_paths'][0]
    asset_directory = task['asset_directory']

    # Defense-in-depth path containment re-check
    if not is_within_directory(onnx_path, asset_directory):
        return _path_containment_violation(onnx_path)

    import onnx

    # Load without external data (containment already verified by C3A)
    try:
        model = onnx.load(onnx_path, load_external_data=False)
    except Exception as e:
        return build_worker_output(
            worker_id='COMP-W-C3C',
            assessment_status='STRUCTURAL_INVALID',
            raw_signal={'violation_detail': f'LOAD_FAILED: {str(e)[:512]}',
                        'ef_004_non_claim': 'structural_validity_does_not_establish_semantic_equivalence'},
            access_mode='BLACK_BOX', ...
        )

    # Structural check: no execution
    try:
        onnx.checker.check_model(model)
        structural_status = 'STRUCTURAL_VALID'
        violation_detail = None
    except onnx.checker.ValidationError as e:
        structural_status = 'STRUCTURAL_INVALID'
        violation_detail = str(e)[:1024]
    except Exception as e:
        structural_status = 'STRUCTURAL_INVALID'
        violation_detail = f'UNEXPECTED: {str(e)[:512]}'

    # Collect non-executable metadata
    try:
        opset = model.opset_import[0].version if model.opset_import else None
        node_count = len(model.graph.node)
        input_names = [i.name for i in model.graph.input]
        output_names = [o.name for o in model.graph.output]
    except Exception:
        opset = node_count = None
        input_names = output_names = []

    return build_worker_output(
        worker_id='COMP-W-C3C',
        assessment_status=structural_status,
        raw_signal={
            'structural_status': structural_status,
            'opset_version': opset,
            'graph_node_count': node_count,
            'graph_input_names': input_names,
            'graph_output_names': output_names,
            'violation_detail': violation_detail,
            'ef_004_non_claim': 'structural_validity_does_not_establish_semantic_equivalence'
        },
        access_mode='BLACK_BOX',
        limitations=[
            "Structural validity is checked via onnx.checker; no model execution occurs.",
            "EF-004: structural validity does not establish semantic equivalence with source model.",
            "Runtime compatibility with a specific inference engine is not tested here."
        ],
        non_claims=[
            "STRUCTURAL_VALID ≠ semantically equivalent to source model (EF-004).",
            "STRUCTURAL_VALID ≠ safe to execute.",
            "STRUCTURAL_VALID ≠ behavioral battery passed (behavioral battery is DEFERRED_IN_SCOPE)."
        ]
    )
```

---

## 3.10 COMP-W-C3D — Safe-Loading Gate Worker

**Module:** `assurance_system/workers/c3d_safe_load.py`

**Absolute constraints (enforced in code review and security test):**
- The string `weights_only=False` MUST NOT appear anywhere in this file.
- The string `weights_only=False` MUST NOT appear in any import chain of this file.
- No Ultralytics automatic unsafe fallback (RC-013 REJECTED).
- A grep for `weights_only.*False` or `weights_only.*=.*False` across the entire codebase must return zero results.

```python
def run_assessment(task: dict) -> dict:
    model_path = task['asset_paths'][0]
    asset_directory = task['asset_directory']
    resource_limits = task['resource_limits']

    # Path containment re-check (defense in depth)
    if not is_within_directory(model_path, asset_directory):
        return _path_containment_violation(model_path)

    # Resource limiting (Linux; CONDITIONAL on PRE-01)
    try:
        import resource
        mem_bytes = resource_limits['memory_limit_mb'] * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, resource.RLIM_INFINITY))
        fd_limit = resource_limits['max_file_descriptors']
        resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
        resource_limits_applied = True
    except (ImportError, ValueError, resource.error):
        resource_limits_applied = False
        # Limitation: resource limiting unavailable on this platform; record in evidence

    import torch

    # Safe-loading attempt — weights_only=True is MANDATORY with NO fallback
    load_attempt = {
        'weights_only_flag_used': True,
        'map_location': 'cpu',
        'fallback_attempted': False,   # RC-013: this must always be False
    }

    try:
        _ = torch.load(model_path, weights_only=True, map_location='cpu')
        load_result = 'LOAD_SUCCESS'
        load_detail = None
    except (RuntimeError, pickle.UnpicklingError) as e:
        load_result = 'LOAD_BLOCKED'
        load_detail = str(e)[:1024]
    except Exception as e:
        load_result = 'LOAD_ERROR'
        load_detail = str(e)[:1024]

    # NOTE: There is NO except clause here that retries with weights_only=False.
    # RC-013 REJECTED. Any code reviewer who sees such a clause must treat it as
    # a critical security defect.

    return build_worker_output(
        worker_id='COMP-W-C3D',
        assessment_status=load_result,
        raw_signal={
            **load_attempt,
            'pytorch_version': torch.__version__,
            'load_result': load_result,
            'load_detail': load_detail,
            'resource_limits_applied': resource_limits_applied,
            'resource_limits': resource_limits
        },
        access_mode='BLACK_BOX',
        limitations=[
            "weights_only=True is necessary but not sufficient; subprocess isolation and "
            "path restrictions are also required security controls.",
            "LOAD_SUCCESS does not establish the model is free of backdoors or adversarial weights.",
            "LOAD_BLOCKED may occur on some legitimate models that use unsupported Python classes.",
            f"Resource limiting was {'applied' if resource_limits_applied else 'NOT applied (platform limitation)'}."
        ],
        non_claims=[
            "LOAD_BLOCKED ≠ PROVEN_MALICIOUS; ANOMALY ≠ PROVEN ATTACK.",
            "LOAD_SUCCESS ≠ behavioral safety; LOAD_SUCCESS ≠ global backdoor absence.",
            "weights_only=True does not establish semantic equivalence with source training code."
        ]
    )
```

---

## 3.11 COMP-C4 — Provenance Record Builder / Signing Module

**Module:** `assurance_system/supervisor/provenance.py`
**[BLOCKED: PRE-02, PRE-04, PRE-08, PRE-09]**

```python
PF_002_NON_CLAIM = (
    "Cryptographic signature establishes that this record was produced and not modified "
    "after signing under accepted-key assumptions. It does NOT establish: (a) that the named "
    "model executed the assessed inferences (PF-002); (b) that the assessment was accurate; "
    "(c) that the signing key was not compromised; or (d) that the system producing this "
    "record was not itself compromised."
)

CANONICALIZATION_ALGORITHM_ID = 'json-canonical-utf8-sort-keys-v1'
# [BLOCKED: SP-003 must confirm or revise this algorithm ID before implementation]

class ProvenanceBuilder:

    def canonicalize(self, record: dict) -> bytes:
        """
        Deterministic serialization:
          json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        Encoded as UTF-8.
        Algorithm ID: CANONICALIZATION_ALGORITHM_ID (pending SP-003 confirmation).
        """
        import json
        return json.dumps(
            record, sort_keys=True, separators=(',', ':'), ensure_ascii=True
        ).encode('utf-8')

    def build_and_sign(
        self,
        artifact_unit_digest: str,
        evidence_record_digests: list[str],
        sequence_state: SequenceState,
        timestamp: str,
        signing_key_material: bytes
    ) -> dict:
        """
        1. Validate sequence_state.sequence_number == last_sequence_number + 1;
           if gap → emit SEQUENCE_GAP_DETECTED audit event; continue.
        2. Generate replay_nonce = uuid.uuid4().hex.
        3. Build unsigned_record dict with all fields including pf_002_non_claim.
        4. Canonicalize unsigned_record.
        5. Compute signature using XREG-002-selected mechanism.
        6. Attach signature and algorithm_id to record.
        7. Update sequence_state (increment sequence_number; store last_record_digest).
        8. Persist sequence_state to /var/assurance/keys/sequence_state.json.
        9. Write signed record to evidence store (COMP-STORE).
        10. Append PROVENANCE_RECORD_WRITTEN audit event.
        Returns signed provenance record dict.
        On signing failure: return record with signing_status='SIGNING_UNAVAILABLE';
          do NOT raise; do NOT treat unsigned record as signed.
        """

    def _sign(self, record_bytes: bytes, key_material: bytes,
               algorithm: str) -> tuple[str, bytes]:
        """
        Ed25519 path (if XREG-002 → Ed25519):
          from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
          key = Ed25519PrivateKey.from_private_bytes(key_material)
          sig = key.sign(record_bytes)
          return ('Ed25519', sig)
        HMAC-SHA256 path (if XREG-002 → HMAC-SHA256):
          import hmac, hashlib
          sig = hmac.new(key_material, record_bytes, hashlib.sha256).digest()
          return ('HMAC-SHA256', sig)
        [BLOCKED: PRE-02 — XREG-002 not decided]
        """
```

**Sequence state management:**

```python
@dataclasses.dataclass
class SequenceState:
    sequence_number: int     # Monotonically increasing; starts at 1
    last_record_digest: str  # SHA-256 of last successfully signed provenance record

    # Storage: /var/assurance/keys/sequence_state.json (supervisor-only readable)
    # Durability: persisted after every successful signing.
    # Recovery on restart: if state file missing, recover from last audit chain entry.
    # Gap detection: on load, compare stored sequence_number against audit chain.
    #   If gap detected: emit SEQUENCE_GAP_DETECTED; log gap; continue from recovered value.
```

---

## 3.12 COMP-C5 — Assurance Interpretation Engine

**Module:** `assurance_system/supervisor/interpretation.py`
**[BLOCKED: PRE-04]**

**Rule engine (mapping logic):**

```python
class C5InterpretationEngine:

    def produce_finding(
        self,
        asset_id: str,
        method_id: str,
        evidence_records: list[dict],
        c4_binding: dict | None,
        reference_health: str,
        access_mode: str
    ) -> dict:
        """
        Applies C5 mapping rules in Section 9.
        Returns validated finding dict.
        Raises if schema validation fails (finding is not written to store in that case).
        """

    def _derive_detection_status(self, evidence_records: list[dict]) -> str:
        """
        Priority order:
        1. If ANY record has assessment_status in
           {ASSESSMENT_ERROR, UNAVAILABLE, ARTIFACT_UNIT_AMBIGUOUS}:
           → return 'UNAVAILABLE'
        2. If ANY record has assessment_status == 'ONNX_PATH_CONTAINMENT_VIOLATION':
           → return 'ANOMALY_DETECTED'
        3. If ANY record has assessment_status == 'LOAD_BLOCKED':
           → return 'ANOMALY_DETECTED'
        4. If ANY record has assessment_status == 'STRUCTURAL_INVALID':
           → return 'ANOMALY_DETECTED'
        5. If C2A record with violation_count > 0: → 'ANOMALY_DETECTED'
        6. If C2B record with duplicate_group_count > 0: → 'ANOMALY_DETECTED'
        7. If C3B record with comparison_result == 'DIFFERENT': → 'IDENTITY_DIFFERENT'
        8. If C3B record with comparison_result == 'MATCH': → 'IDENTITY_MATCH'
        9. If C3B record with comparison_result == 'UNAVAILABLE': → 'UNAVAILABLE'
        10. If C2C record with assessment_status == 'COMPLETED':
            → 'COMPLETED_STATISTICS_ONLY'  (statistics only; no anomaly claim)
        11. All records COMPLETED, no anomaly condition above:
            → 'NO_ANOMALY_DETECTED'
        """

    def _derive_interpretation_status(self, detection_status: str) -> str:
        mapping = {
            'UNAVAILABLE': 'UNAVAILABLE',
            'ANOMALY_DETECTED': 'REQUIRES_INVESTIGATION',
            'IDENTITY_MATCH': 'CONSISTENT_WITH_EXPECTED',
            'IDENTITY_DIFFERENT': 'IDENTITY_DEVIATION_DETECTED',
            'COMPLETED_STATISTICS_ONLY': 'STATISTICS_REPORTED',
            'NO_ANOMALY_DETECTED': 'NO_ANOMALY_DETECTED',
        }
        return mapping.get(detection_status, 'UNAVAILABLE')

    def _derive_analyst_disposition(self, detection_status: str,
                                     assessment_status: str) -> str:
        if detection_status == 'UNAVAILABLE':
            return 'UNAVAILABLE_NO_DECISION'
        if detection_status == 'ANOMALY_DETECTED':
            return 'ESCALATE'
        if detection_status == 'IDENTITY_DIFFERENT':
            return 'ESCALATE'
        if detection_status == 'IDENTITY_MATCH':
            return 'ACCEPT'
        if detection_status == 'NO_ANOMALY_DETECTED':
            return 'ACCEPT'
        return 'UNAVAILABLE_NO_DECISION'
```

**Mandatory non-claim fields on every C5 finding:**

| Field | Value | Condition |
|---|---|---|
| `coverage_gap_clean_label` | `True` (always) | All findings without exception |
| `anomaly_not_malicious_non_claim` | `True` | When `detection_status == 'ANOMALY_DETECTED'` |
| `global_backdoor_absence_not_established` | `True` | All C3 findings without exception |
| `pf_002_non_claim` | PF_002_NON_CLAIM constant text | All findings (from C4 binding or default) |

**Absolute prohibited outputs:**
- `detection_status` must NEVER be `'CONFIRMED_MALICIOUS'`, `'PROVEN_ATTACK'`, `'CLEAN'`, `'SAFE'`, `'HEALTHY'`.
- `interpretation_status` must NEVER be `'PROVEN_MALICIOUS'`, `'CONFIRMED_SAFE'`, `'APPROVED'`.
- No field named `risk_score` or any variant thereof may appear.

---

## 3.13 COMP-REF — Reference Manager

**Module:** `assurance_system/supervisor/reference_manager.py`

```python
class ReferenceManager:

    HEALTH_STATES = frozenset({
        'UNAVAILABLE', 'HEALTH_UNVERIFIED', 'FORMAT_ASSET',
        'HEALTH_VERIFIED', 'CONTAMINATION_SUSPECTED', 'STALE_SUSPECTED'
    })

    def __init__(self, evidence_store: EvidenceStore, audit_chain: AuditChainWriter):
        self._store = evidence_store
        self._audit = audit_chain

    def get_reference_health(self, reference_id: str) -> str:
        """
        Returns current health state.
        Default at MVP start: 'UNAVAILABLE' for all references.
        Never returns 'HEALTH_VERIFIED' unless all R0–R7 gate records exist.
        """
        row = self._store.query_reference_health(reference_id)
        return row['health_state'] if row else 'UNAVAILABLE'

    def attempt_health_promotion(self, reference_id: str,
                                  gate_records: dict) -> str:
        """
        Checks R0–R7 gate completion records.
        On all R0–R7 present and passed: promotes to HEALTH_VERIFIED.
        On any gate missing or failed: stays HEALTH_UNVERIFIED.
        NEVER promotes FORMAT_ASSET to HEALTH_VERIFIED.
        Emits REFERENCE_HEALTH_TRANSITION audit event on state change.
        [BLOCKED: PRE-06 — SP-001 gate procedure not yet produced]
        """

    def register_staleness_event(self, reference_id: str, reason: str) -> None:
        """
        Downgrades to STALE_SUSPECTED.
        Emits REFERENCE_HEALTH_TRANSITION audit event.
        """
```

**MVP start state:** All references UNAVAILABLE. Every reference-relative method (M11) emits `REFERENCE_UNAVAILABLE` records. No reference health gate enforcement is required at MVP because no reference has been registered.

---

## 3.14 COMP-AUDIT — Audit Chain Writer

**Module:** `assurance_system/supervisor/audit_chain.py`

```python
class AuditChainWriter:

    def append_event(self, event_type: str, payload: dict) -> str:
        """
        1. Serialize payload as canonical JSON (sort_keys=True).
        2. payload_digest = SHA-256(canonical_payload_bytes).
        3. Read chain_state from DB: last_chain_link_hash.
        4. previous_event_digest = last_chain_link_hash.
        5. Build event_record:
             {event_id: None (autoincrement), event_type, payload_digest,
              previous_event_digest, timestamp: utcnow().isoformat(),
              supervisor_version_id: VERSION_STRING}
        6. chain_link_hash = SHA-256(canonical(event_record)).
        7. Write event_record + chain_link_hash to audit_events table (atomic WAL commit).
        8. Update chain_state: last_chain_link_hash = chain_link_hash.
        Returns inserted event_id.
        On write failure: raises AuditWriteError (NEVER swallows).
        """

    def verify_chain_integrity(self) -> ChainVerificationResult:
        """
        Reads all events in event_id ascending order.
        For event i (i > 1): recompute SHA-256(canonical(event[i-1]_record))
          compare to event[i].previous_event_digest
          mismatch → record violation {event_id: i, ...}
        Returns ChainVerificationResult(intact=bool, violations=[...]).
        NEVER resets chain on corruption.
        If corruption detected: emits CHAIN_CORRUPT audit event (appended to end).
        """

    GENESIS_HASH = 'GENESIS'  # Sentinel for first event's previous_event_digest
```

**Audit event types (defined in `constants.py`):**

```python
class AuditEventType(str, enum.Enum):
    PIPELINE_RUN_START                     = 'PIPELINE_RUN_START'
    PIPELINE_RUN_COMPLETE                  = 'PIPELINE_RUN_COMPLETE'
    PIPELINE_RUN_ERROR                     = 'PIPELINE_RUN_ERROR'
    WORKER_DISPATCHED                      = 'WORKER_DISPATCHED'
    WORKER_RESULT_ACCEPTED                 = 'WORKER_RESULT_ACCEPTED'
    WORKER_RESULT_REJECTED_SCHEMA_VIOLATION = 'WORKER_RESULT_REJECTED_SCHEMA_VIOLATION'
    EVIDENCE_RECORD_WRITTEN                = 'EVIDENCE_RECORD_WRITTEN'
    FINDING_WRITTEN                        = 'FINDING_WRITTEN'
    PROVENANCE_RECORD_WRITTEN              = 'PROVENANCE_RECORD_WRITTEN'
    DEFERRED_IN_SCOPE_EMITTED              = 'DEFERRED_IN_SCOPE_EMITTED'
    REFERENCE_HEALTH_TRANSITION            = 'REFERENCE_HEALTH_TRANSITION'
    SIGNING_UNAVAILABLE                    = 'SIGNING_UNAVAILABLE'
    SEQUENCE_GAP_DETECTED                  = 'SEQUENCE_GAP_DETECTED'
    CHAIN_CORRUPT                          = 'CHAIN_CORRUPT'
    ANALYST_DISPOSITION                    = 'ANALYST_DISPOSITION'
    CAPABILITY_DECLARATION_EMITTED         = 'CAPABILITY_DECLARATION_EMITTED'
    UNAVAILABLE_PROPAGATED                 = 'UNAVAILABLE_PROPAGATED'
    REPLAY_ATTEMPT_DETECTED                = 'REPLAY_ATTEMPT_DETECTED'
```

---

## 3.15 COMP-STORE — Evidence Store

**Module:** `assurance_system/supervisor/evidence_store.py`

**SQLite DDL (complete; applied at database initialisation):**

```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS evidence_records (
    record_id               TEXT PRIMARY KEY NOT NULL,
    schema_version          TEXT NOT NULL,
    asset_id                TEXT NOT NULL,
    method_id               TEXT NOT NULL,
    assessment_status       TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                            CHECK (assessment_status IN (
                              'COMPLETED','ASSESSMENT_ERROR','UNAVAILABLE','UNSUPPORTED',
                              'DEFERRED_IN_SCOPE','ARTIFACT_UNIT_AMBIGUOUS',
                              'LOAD_BLOCKED','LOAD_SUCCESS','LOAD_ERROR',
                              'ONNX_PATH_CONTAINMENT_VIOLATION',
                              'STRUCTURAL_VALID','STRUCTURAL_INVALID','REFERENCE_UNAVAILABLE')),
    raw_signal              TEXT,
    access_mode             TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    artifact_unit_id        TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    coverage_gap_clean_label INTEGER NOT NULL DEFAULT 1
                            CHECK (coverage_gap_clean_label = 1),
    limitations             TEXT NOT NULL,
    non_claims              TEXT NOT NULL,
    dependency_declaration  TEXT,
    assessment_timestamp    TEXT NOT NULL,
    worker_id               TEXT NOT NULL DEFAULT 'SUPERVISOR',
    record_digest           TEXT,
    is_synthetic            INTEGER NOT NULL DEFAULT 0 CHECK (is_synthetic IN (0,1)),
    created_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id                           TEXT PRIMARY KEY NOT NULL,
    schema_version                       TEXT NOT NULL,
    asset_id                             TEXT NOT NULL,
    method_id                            TEXT NOT NULL,
    detection_status                     TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    interpretation_status                TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    applicability_status                 TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    raw_signal                           TEXT,
    reference_health                     TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    limitations                          TEXT NOT NULL,
    non_claims                           TEXT NOT NULL,
    dependency_declaration               TEXT NOT NULL,
    coverage_gap_clean_label             INTEGER NOT NULL DEFAULT 1
                                         CHECK (coverage_gap_clean_label = 1),
    anomaly_not_malicious_non_claim      INTEGER NOT NULL DEFAULT 0
                                         CHECK (anomaly_not_malicious_non_claim IN (0,1)),
    global_backdoor_absence_not_established INTEGER NOT NULL DEFAULT 0
                                         CHECK (global_backdoor_absence_not_established IN (0,1)),
    pf_002_non_claim                     TEXT NOT NULL DEFAULT 'C4_BINDING_UNAVAILABLE',
    analyst_disposition_prompt           TEXT NOT NULL DEFAULT 'UNAVAILABLE_NO_DECISION',
    is_synthetic                         INTEGER NOT NULL DEFAULT 0 CHECK (is_synthetic IN (0,1)),
    created_at                           TEXT NOT NULL
                                         DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS provenance_records (
    provenance_id               TEXT PRIMARY KEY NOT NULL,
    schema_version              TEXT NOT NULL,
    artifact_unit_digest        TEXT NOT NULL,
    evidence_record_digests     TEXT NOT NULL,
    signing_key_id              TEXT NOT NULL,
    signature                   TEXT,
    signature_algorithm         TEXT,
    canonicalization_algorithm  TEXT NOT NULL DEFAULT 'json-canonical-utf8-sort-keys-v1',
    sequence_number             INTEGER NOT NULL,
    replay_nonce                TEXT NOT NULL UNIQUE,
    pf_002_non_claim            TEXT NOT NULL,
    signing_status              TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                                CHECK (signing_status IN ('SIGNED','SIGNING_UNAVAILABLE')),
    timestamp                   TEXT NOT NULL,
    created_at                  TEXT NOT NULL
                                DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS deferred_records (
    record_id               TEXT PRIMARY KEY NOT NULL,
    schema_version          TEXT NOT NULL,
    asset_id                TEXT NOT NULL,
    method_id               TEXT NOT NULL,
    assessment_status       TEXT NOT NULL DEFAULT 'DEFERRED_IN_SCOPE'
                            CHECK (assessment_status IN (
                              'DEFERRED_IN_SCOPE','REFERENCE_UNAVAILABLE',
                              'COMPLETENESS_UNAVAILABLE')),
    deferral_reason         TEXT NOT NULL,
    finite_battery_non_claim INTEGER NOT NULL DEFAULT 0 CHECK (finite_battery_non_claim IN (0,1)),
    limitations             TEXT NOT NULL,
    non_claims              TEXT NOT NULL,
    created_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS reference_health (
    reference_id            TEXT PRIMARY KEY NOT NULL,
    reference_name          TEXT NOT NULL,
    health_state            TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                            CHECK (health_state IN (
                              'UNAVAILABLE','HEALTH_UNVERIFIED','FORMAT_ASSET',
                              'HEALTH_VERIFIED','CONTAMINATION_SUSPECTED','STALE_SUSPECTED')),
    format_category         TEXT,
    gate_completion_record  TEXT,
    last_verified_timestamp TEXT,
    updated_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type             TEXT NOT NULL,
    payload_digest         TEXT NOT NULL,
    previous_event_digest  TEXT NOT NULL DEFAULT 'GENESIS',
    chain_link_hash        TEXT NOT NULL,
    timestamp              TEXT NOT NULL,
    supervisor_version_id  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chain_state (
    id                      INTEGER PRIMARY KEY CHECK (id = 1),
    last_event_id           INTEGER NOT NULL DEFAULT 0,
    last_chain_link_hash    TEXT    NOT NULL DEFAULT 'GENESIS',
    last_sequence_number    INTEGER NOT NULL DEFAULT 0,
    updated_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

INSERT OR IGNORE INTO chain_state
  (id, last_event_id, last_chain_link_hash, last_sequence_number)
  VALUES (1, 0, 'GENESIS', 0);

CREATE INDEX IF NOT EXISTS idx_ev_asset_method ON evidence_records(asset_id, method_id);
CREATE INDEX IF NOT EXISTS idx_finding_asset   ON findings(asset_id);
CREATE INDEX IF NOT EXISTS idx_prov_artifact   ON provenance_records(artifact_unit_digest);
CREATE INDEX IF NOT EXISTS idx_audit_type      ON audit_events(event_type);
```

**Python write isolation:**

```python
class EvidenceStore:
    def __init__(self, db_path: str):
        # Connection opened ONLY in supervisor process; workers have no db_path reference
        self._conn = sqlite3.connect(db_path, check_same_thread=True)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute('PRAGMA journal_mode=WAL')
        self._conn.execute('PRAGMA foreign_keys=ON')

    def write_evidence_record(self, record: dict) -> str:
        # Only called after COMP-SCHEMA validation passes
        with self._conn:   # Atomic commit or rollback
            self._conn.execute(
                """INSERT INTO evidence_records
                   (record_id, schema_version, asset_id, method_id, assessment_status,
                    raw_signal, access_mode, artifact_unit_id, coverage_gap_clean_label,
                    limitations, non_claims, dependency_declaration, assessment_timestamp,
                    worker_id, record_digest, is_synthetic)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (record['record_id'], ...)
            )
        return record['record_id']
    # Raises StorageWriteError wrapping sqlite3.Error on failure; never swallowed
```

---

## 3.16 COMP-IFACE — Analyst Interface

**Module:** `assurance_system/interfaces/cli.py`

**Display invariants (non-negotiable):**
- `UNAVAILABLE` states are always displayed as-is; never converted to blank or positive message.
- `DEFERRED_IN_SCOPE` records are listed by `list-deferred`; never silently absent.
- `LIMITATIONS` and `NON_CLAIMS` are always displayed in `show-finding` output.
- No output field may be named `risk_score`, `overall_score`, `confidence`, or variant thereof.
- `show-audit-trail` always reports `CHAIN_CORRUPT` if detected; never suppresses it.

**Dashboard (MVP value feature):** Lightweight Python stdlib HTTP server serving a self-contained single-file HTML page. The HTML page:
- Reads from evidence store via a local read-only HTTP endpoint (supervisor-provided).
- Displays DETECTION_STATUS, INTERPRETATION_STATUS, LIMITATIONS, NON_CLAIMS for each finding.
- Never displays a scalar risk score or aggregate assurance indicator.
- Distinguishes PASS / ANOMALY_DETECTED / UNAVAILABLE / DEFERRED_IN_SCOPE visually.

---

## 3.17 COMP-FIX — Hostile Fixture Suite

**Module:** `assurance_system/fixtures/`
**Priority:** P0 — must be built before any security capability claim is made.

| Fixture ID | Type | Generator location | Purpose | Test assertion |
|---|---|---|---|---|
| FIX-001 | Hostile pickle (PyTorch .pt) | fixtures/hostile/pickle_payload.py | LOAD_BLOCKED trigger | C3D returns LOAD_BLOCKED; fallback_attempted=False |
| FIX-002 | OOM-triggering model | fixtures/hostile/pickle_payload.py | Resource exhaustion | C3D returns LOAD_ERROR; worker terminates; supervisor continues |
| FIX-003 | Hang-triggering model | fixtures/hostile/pickle_payload.py | Timeout trigger | ASSESSMENT_ERROR after timeout_seconds; supervisor not hung |
| FIX-004 | ONNX absolute external path | fixtures/hostile/onnx_path_traversal.py | Path containment | C3A returns ONNX_PATH_CONTAINMENT_VIOLATION |
| FIX-005 | ONNX `../` traversal path | fixtures/hostile/onnx_path_traversal.py | Path traversal | ONNX_PATH_CONTAINMENT_VIOLATION |
| FIX-006 | ONNX symlink to /etc | fixtures/hostile/onnx_path_traversal.py | Symlink escape | ONNX_PATH_CONTAINMENT_VIOLATION |
| FIX-007 | ZIP archive bomb | fixtures/hostile/archive_bomb.py | Resource exhaustion | ASSESSMENT_ERROR; no supervisor OOM |
| FIX-008 | COCO all-box geometry violations | fixtures/hostile/coco_geometry.py | All C2A violation types | Each expected violation_type present in violations list |
| FIX-009-D | YOLO_DETECTION violations | fixtures/hostile/yolo_geometry.py | All YOLO_DETECTION violations | Each expected violation_type present |
| FIX-009-S | YOLO_SEG violations | fixtures/hostile/yolo_geometry.py | All YOLO_SEG violations | Each expected violation_type present |
| FIX-009-P | YOLO_POSE violations | fixtures/hostile/yolo_geometry.py | All YOLO_POSE violations | Each expected violation_type present |
| FIX-009-O | YOLO_OBB violations | fixtures/hostile/yolo_geometry.py | All YOLO_OBB violations | Each expected violation_type present |
| FIX-010 | Exact duplicate image set (N pairs) | fixtures/generator.py | Known duplicate corpus | duplicate_group_count == N |
| FIX-011 | Non-duplicate control set | fixtures/generator.py | Hard negative | duplicate_group_count == 0 |
| FIX-012 | Sybil contributor fragmentation corpus | fixtures/generator.py | HHI/entropy test | sybil_unreliable=True; expected hhi and entropy values within tolerance |
| FIX-013 | UNAVAILABLE injection per layer | fixtures/generator.py | Propagation test | Each injection point produces UNAVAILABLE evidence record; C5 produces UNAVAILABLE_NO_DECISION |
| FIX-014 | Schema violation injection | fixtures/generator.py | Rejected record test | SCHEMA_VIOLATION audit event; zero evidence records written |
| FIX-015 | Benign PyTorch model | fixtures/generator.py | Clean control | LOAD_SUCCESS; fallback_attempted=False |
| FIX-016 | Valid ONNX (no external data) | fixtures/generator.py | Clean control | STRUCTURAL_VALID |
| FIX-017 | Malformed COCO JSON | fixtures/hostile/coco_geometry.py | Parse error | ASSESSMENT_ERROR with error_detail |
| FIX-018 | Worker output with risk_score field | fixtures/generator.py | Prohibited field test | SCHEMA_VIOLATION; no evidence record written |
| FIX-019 | Worker output with coverage_gap_clean_label=False | fixtures/generator.py | Invariant enforcement | SCHEMA_VIOLATION |
| FIX-020 | Synthetic-labelled end-to-end run | fixtures/generator.py | SYNTHETIC propagation | is_synthetic=1 on every record produced from synthetic assets |

All fixtures carry `is_synthetic = True` in provenance; every evidence record produced from a fixture must have `is_synthetic = 1`.

---

## 3.18 Exception hierarchy

**Module:** `assurance_system/exceptions.py`

```python
class AssuranceSystemError(Exception):     pass
class PipelineError(AssuranceSystemError): pass
class SchemaViolationError(AssuranceSystemError): pass
class StorageWriteError(AssuranceSystemError):    pass
class AuditWriteError(AssuranceSystemError):      pass
class SigningKeyUnavailableError(AssuranceSystemError): pass
class WorkerTimeoutError(AssuranceSystemError):   pass
class WorkerCrashError(AssuranceSystemError):     pass
class PathContainmentError(AssuranceSystemError): pass
class ArtifactUnitAmbiguousError(AssuranceSystemError): pass
class ChainCorruptError(AssuranceSystemError):    pass
class ReferenceHealthError(AssuranceSystemError): pass
class ReplayAttemptError(AssuranceSystemError):   pass
class SequenceGapError(AssuranceSystemError):     pass
class CapabilityDeclarationError(AssuranceSystemError): pass
```

---

# 4. DATA CONTRACTS

## 4.1 Worker input JSON (supervisor → worker via named temp file)

```
FIELD                         TYPE            REQ  NOTES
schema_version                string          YES  "worker-input-v1"
task                          string (enum)   YES  C2A_STRUCTURAL|C2B_EXACT_HASH|C2C_CONCENTRATION|
                                                   C2D_IMAGE_HASH|C3A_ARTIFACT_UNIT|C3B_MODEL_HASH|
                                                   C3C_ONNX_STRUCTURAL|C3D_SAFE_LOAD
asset_paths                   array<string>   YES  Absolute paths; all within asset_directory
format                        string (enum)   YES  COCO|YOLO_DETECTION|YOLO_SEG|YOLO_POSE|YOLO_OBB|
                                                   ONNX|PYTORCH|TORCHSCRIPT
task_variant                  string          NO   Task-sub-type where needed
asset_directory               string          YES  Root of submitted asset directory; workers must
                                                   verify all paths against this before reading
artifact_unit_definition_id   string          YES  "UNAVAILABLE" until SP-002 resolved (PRE-03)
resource_limits.timeout_s     integer         YES  Wall-clock timeout in seconds
resource_limits.memory_mb     integer         YES  RSS cap in MB
resource_limits.max_fds       integer         YES  File descriptor cap
identity_quality              string (enum)   YES  TRUSTED|UNTRUSTED|UNAVAILABLE; default UNTRUSTED
reference_digest              string|null     NO   SHA-256 hex of reference; null = no reference
contributor_metadata          array<object>   NO   C2C only
artifact_unit                 object|null     NO   C3B only; dict from C3A result
```

Security: Workers must reject inputs with unrecognised `schema_version`. Workers must re-verify path containment for every `asset_paths` entry before reading, even though supervisor pre-checked.

Prohibited input fields (if present, worker rejects): `key_path`, `db_path`, any field containing the word "password", "secret", or "credential".

## 4.2 Worker output JSON (worker → supervisor via named temp file)

```
FIELD                         TYPE            REQ  CONSTRAINT
schema_version                string          YES  "worker-output-v1"
worker_id                     string (enum)   YES  COMP-W-C2A|C2B|C2C|C2D|C3A|C3B|C3C|C3D
assessment_status             string (enum)   YES  See valid set in Section 3.2
raw_signal                    object|null     YES  null only for ASSESSMENT_ERROR/DEFERRED_IN_SCOPE;
                                                   no prohibited subfields at any depth
access_mode                   string (enum)   YES  BLACK_BOX|GREY_BOX|WHITE_BOX|
                                                   INTERNAL_ACTIVATION|UNAVAILABLE;
                                                   MUST NOT be null on C3 records
artifact_unit_id              string          YES  default "UNAVAILABLE"
coverage_gap_clean_label      boolean         YES  MUST be true on C2 and C3 records;
                                                   false or absent → SCHEMA_VIOLATION
limitations                   array<string>   YES  min 1 element; empty → SCHEMA_VIOLATION
non_claims                    array<string>   YES  min 1 element; empty → SCHEMA_VIOLATION
dependency_declaration        object          YES  {co_firing_detectors:[], independence_established:bool}
assessment_timestamp          string          YES  ISO 8601 UTC; future timestamps >5min → SCHEMA_VIOLATION
error_detail                  string|null     YES  Non-null when ASSESSMENT_ERROR; null otherwise
```

Prohibited output fields (schema validator rejects if found anywhere in the tree):
`risk_score`, `aggregate_assurance`, `compromise_probability`, `overall_score`,
`threat_score`, `malicious_probability`, `confidence_score`, `trust_score`, `safety_score`

## 4.3 Evidence record (persisted in evidence_records table)

Supervisor adds these fields — they are NEVER accepted from workers:

```
FIELD               SOURCE          SECURITY NOTE
record_id           Supervisor      UUID4 generated by supervisor; never from worker
asset_id            Supervisor      Assigned at ingestion gate; never from worker
record_digest       Supervisor      SHA-256(canonical(record)) computed post-validation
is_synthetic        Supervisor      1 if asset came from COMP-FIX fixture corpus; 0 otherwise
created_at          SQLite DEFAULT  Database timestamp; not from worker
```

## 4.4 C5 finding schema

```
FIELD                                    TYPE        CONSTRAINT
finding_id                               string      UUID4; supervisor-generated
detection_status                         string      UNAVAILABLE|ANOMALY_DETECTED|IDENTITY_MATCH|
                                                     IDENTITY_DIFFERENT|NO_ANOMALY_DETECTED|
                                                     COMPLETED_STATISTICS_ONLY|DEFERRED_IN_SCOPE
                                                     NEVER: CONFIRMED_MALICIOUS|CLEAN|SAFE|PROVEN_ATTACK
interpretation_status                    string      UNAVAILABLE|REQUIRES_INVESTIGATION|
                                                     CONSISTENT_WITH_EXPECTED|IDENTITY_DEVIATION_DETECTED|
                                                     STATISTICS_REPORTED|NO_ANOMALY_DETECTED|DEFERRED
                                                     NEVER: PROVEN_MALICIOUS|CONFIRMED_SAFE|APPROVED
applicability_status                     string      APPLICABLE|NOT_APPLICABLE|UNSUPPORTED|
                                                     DEFERRED_IN_SCOPE|REFERENCE_UNAVAILABLE
reference_health                         string      From COMP-REF; not derived from assessment
coverage_gap_clean_label                 integer     Always 1 (true); CHECK enforced
anomaly_not_malicious_non_claim          integer     1 when detection_status=ANOMALY_DETECTED
global_backdoor_absence_not_established  integer     Always 1 on C3 findings
pf_002_non_claim                         string      PF_002_NON_CLAIM text or "C4_BINDING_UNAVAILABLE"
analyst_disposition_prompt               string      ACCEPT|ACCEPT_WITH_CONTEXT|ESCALATE|
                                                     CONTAIN_HOLD|OVERRIDE|UNAVAILABLE_NO_DECISION
```

## 4.5 Provenance record schema

```
FIELD                      TYPE        CONSTRAINT
provenance_id              string      UUID4; supervisor-generated
artifact_unit_digest       string      SHA-256 hex from C3B; never from external input
evidence_record_digests    JSON array  SHA-256 hex of each evidence record (supervisor-computed)
signing_key_id             string      Identifier of key used; never the key material itself
signature                  string|null Hex-encoded; null if SIGNING_UNAVAILABLE
signature_algorithm        string|null "Ed25519"|"HMAC-SHA256"|null [BLOCKED: XREG-002]
canonicalization_algorithm string      "json-canonical-utf8-sort-keys-v1" [pending SP-003]
sequence_number            integer     Monotonically increasing; gaps trigger SEQUENCE_GAP event
replay_nonce               string      UUID4 hex; UNIQUE constraint in DB prevents replay
pf_002_non_claim           string      PF_002_NON_CLAIM constant; never null or absent
signing_status             string      "SIGNED"|"SIGNING_UNAVAILABLE"; never absent
timestamp                  string      Local system clock ISO 8601 (AF-003: trusted clock not established)
```

---

# 5. TECHNICAL METHOD SPECIFICATIONS

## 5.1 Method M01 — All-Box Structural/Geometry Validation

| | |
|---|---|
| **Method ID** | M01 |
| **Threat addressed** | T05a — annotation manipulation; structural format violations |
| **Required input** | All COCO JSON or YOLO label files in dataset |
| **Required reference** | None |
| **Algorithm** | Rule-based parse-and-validate; pycocotools for COCO load layer |
| **Thresholds** | None — structural; not statistical |
| **Evidence output** | violations list; total_annotations_checked; violation_count |
| **Failure conditions** | Malformed JSON → ASSESSMENT_ERROR; file size limit exceeded → ASSESSMENT_ERROR |
| **Offline dependencies** | stdlib json; pycocotools (C extension pre-staged) |
| **False-positive conditions** | Polygon masks where declared area ≠ w×h may produce area-flag notes (not violations) |
| **False-negative / evasion** | T05d clean-label attacks conform to valid format; not detectable. Adversarial images with valid annotations not detectable |
| **Scope** | COCO; YOLO detection/seg/pose/OBB [CONDITIONAL: PRE-05] |
| **Does NOT prove** | Label semantic correctness; clean distribution; absence of T05d; absence of T05b |
| **Implementation status** | Literature method: established. Approved project method: YES. Implemented: NOT YET. Validated: NOT YET |

## 5.2 Method M02 — SHA-256 Exact Duplicate Detection

| | |
|---|---|
| **Method ID** | M02 |
| **Threat addressed** | T06 — byte-level duplicate injection flooding |
| **Algorithm** | SHA-256 streaming; 64 KB chunks; digest_map grouping |
| **Thresholds** | None — exact match is deterministic |
| **Evidence output** | file_digest_map; duplicate_groups; duplicate_group_count; error_files |
| **False-negative / evasion** | Any byte-level modification evades; near-duplicate (PDQ) DEFERRED_IN_SCOPE |
| **Does NOT prove** | Near-duplicate relationships; source of duplication; malicious intent |

## 5.3 Method M06 — Source Concentration Statistics

| | |
|---|---|
| **Method ID** | M06 |
| **Threat addressed** | T10 — Sybil attack / contributor concentration (statistical signal only) |
| **Algorithm** | HHI = Σ share²; Shannon entropy = −Σ p log₂ p |
| **Thresholds** | None — raw statistics only; no threshold → risk classification |
| **Evidence output** | hhi; shannon_entropy_bits; per_source_shares; sybil_unreliable flag |
| **False-positive conditions** | High HHI legitimate for single-source datasets |
| **False-negative / evasion** | Sybil attacker spreading across many fake identities produces low HHI |
| **Does NOT prove** | Sybil attack presence; poisoning; malicious intent; causal attribution |

## 5.4 Method M15 (hash tier) — Image-Level Hash

| | |
|---|---|
| **Method ID** | M15 (hash tier) |
| **Algorithm** | SHA-256 streaming; same as M02; applied at image-file level |
| **PDQ tier** | DEFERRED_IN_SCOPE — native build spike not yet executed |
| **Does NOT prove** | Near-duplicate relationships; visual similarity |

## 5.5 Method C3A — Artifact-Unit Resolution + Path Containment

| | |
|---|---|
| **Method ID** | C3A |
| **Threat addressed** | T07 — model artifact tampering; G-08 path traversal via ONNX external data |
| **Algorithm** | ONNX: protobuf header inspection + 4-check containment (absolute path / traversal string / canonical path escape / symlink escape) |
| **PRE-03 dependency** | PyTorch artifact-unit definition → ARTIFACT_UNIT_AMBIGUOUS until SP-002 |
| **Does NOT prove** | Path containment ≠ safe content; no execution occurs |

## 5.6 Method C3B — Model Identity Hashing (REQ-05)

| | |
|---|---|
| **Method ID** | C3B |
| **Threat addressed** | T07 — model substitution/tampering |
| **Algorithm** | Per-file SHA-256; combined via lexicographic sort + concatenation + outer SHA-256 |
| **Canonical order** | Lexicographic sort of file paths; deterministic across runs on same artifact-unit |
| **Does NOT prove** | MATCH ≠ safe; MATCH ≠ behavioral equivalence; MATCH ≠ backdoor absence (PF-002) |

## 5.7 Method C3C — ONNX Structural Validation

| | |
|---|---|
| **Method ID** | C3C |
| **Threat addressed** | Malformed ONNX protobuf; invalid opset |
| **Algorithm** | onnx.checker.check_model only; no execution |
| **Does NOT prove** | Semantic equivalence with source model (EF-004); runtime behavior; backdoor absence |

## 5.8 Method C3D — PyTorch Safe-Loading Gate (REQ-07)

| | |
|---|---|
| **Method ID** | C3D |
| **Threat addressed** | T08 — hostile pickle; arbitrary code execution via PyTorch deserialization |
| **Algorithm** | torch.load(path, weights_only=True, map_location='cpu') inside isolated subprocess |
| **Version floor** | PyTorch ≥ 2.10.0 (XREG-005) |
| **Fallback** | NONE — RC-013 REJECTED |
| **False-negative / evasion** | weights_only=True blocks pickle opcode execution; does not detect behavioral backdoors in weights |
| **Does NOT prove** | LOAD_SUCCESS ≠ safe; LOAD_SUCCESS ≠ backdoor absence; LOAD_SUCCESS ≠ behavioral battery passed |

---

# 6. DATA-INTEGRITY IMPLEMENTATION

Data-integrity assessment covers C2 domain. Implementation details supplement Section 3.3–3.6.

## 6.1 COCO format-parsing integration (R27 pycocotools ADOPT/ADAPT)

- Use `pycocotools.coco.COCO(annotation_file)` for initial JSON load and index building.
- Geometry validation layer is implemented on top of pycocotools in `c2a_structural.py`.
- The geometry validation loop must iterate `coco.anns.values()` (all annotations), not `coco.loadAnns([first_id])`.
- Malformed JSON that pycocotools raises `Exception` on → catch → return `ASSESSMENT_ERROR`.
- File-size limit is enforced before calling pycocotools load.
- pycocotools is a CONDITIONAL dependency (C extension must build on target host — PRE-01).

## 6.2 YOLO parser implementation

YOLO format is fully reimplemented (no external library). Line-by-line streaming:

```python
def _parse_yolo_label_file(path: str, task_variant: str,
                            asset_dir: str) -> list[dict]:
    violations = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            violations.extend(
                _check_yolo_line(line, line_num, task_variant))
    return violations
```

No pycocotools involvement for YOLO. YOLO parsing is 100% Python stdlib.

## 6.3 Coverage gap — T05d clean-label poisoning

T05d is permanently non-detectable under the current scope. Every C2 evidence record and every C5 finding derived from C2 evidence must carry:
- `coverage_gap_clean_label = True` (integer 1 in SQLite)
- Non-claims text: "T05d (clean-label poisoning) is NOT covered by any method in this assessment."

This field is enforced by `COMP-SCHEMA` and by the SQLite CHECK constraint. Any attempt to set it to `False` or `0` is rejected at both layers.

## 6.4 Multi-object annotation requirement

The architecture requires all-box validation (REUSE-003). This is enforced by the loop structure in `c2a_structural.py`: every annotation is processed without any early-exit or first-box-only shortcut. A code review check must confirm: there is no `break` or `return` inside the annotation loop before the loop completes.

---

# 7. MODEL-INTEGRITY IMPLEMENTATION

## 7.1 Worker invocation sequence for C3 domain

```
Submission manifest lists model artifact
          ↓
COMP-SUP dispatches COMP-W-C3A (artifact-unit resolver + path containment)
          ↓ [if ONNX_PATH_CONTAINMENT_VIOLATION: stop; emit ESCALATE finding]
COMP-SUP dispatches COMP-W-C3B (model identity hasher)  [BLOCKED: PRE-03]
          ↓
COMP-SUP dispatches COMP-W-C3C (ONNX structural validator)  [ONNX only]
          ↓
COMP-SUP dispatches COMP-W-C3D (PyTorch safe-loading gate)  [PyTorch only]
          ↓
COMP-C4 binds all C3 evidence records to provenance record
          ↓
COMP-C5 interprets C3 evidence → C5 structured finding
```

Behavioral battery (M07 class) is not in this sequence. It emits a `DEFERRED_IN_SCOPE` record immediately after capability declaration.

## 7.2 Access-mode declaration

Every C3 evidence record must have a non-null `access_mode` field. Default is `BLACK_BOX` (model submitted as binary; no source code or internal activations available). This field is set by the worker, validated by COMP-SCHEMA, and carried through to C5 findings and provenance records.

## 7.3 ARTIFACT_UNIT_AMBIGUOUS propagation

If COMP-W-C3A returns `ARTIFACT_UNIT_AMBIGUOUS`:
- COMP-W-C3B cannot run (no defined artifact-unit to hash).
- COMP-W-C3C may still run if the ONNX file path is unambiguous.
- COMP-W-C3D may still run if the PyTorch file path is unambiguous.
- C5 finding for hash-dependent methods carries `detection_status = 'UNAVAILABLE'`.
- C5 finding notes: "Artifact-unit ambiguity prevents identity hash computation."

## 7.4 TorchScript status

TorchScript is `DEFERRED_IN_SCOPE` at MVP. When a TorchScript artifact is submitted:
1. COMP-SUP records format as `TORCHSCRIPT`.
2. COMP-W-C3A returns `DEFERRED_IN_SCOPE`.
3. All downstream C3 methods emit `DEFERRED_IN_SCOPE` records.
4. C5 finding carries `applicability_status = 'DEFERRED_IN_SCOPE'`.

---

# 8. PROVENANCE / CRYPTOGRAPHIC IMPLEMENTATION

**[BLOCKED: PRE-02, PRE-04, PRE-08, PRE-09]**

## 8.1 Canonicalization

```
Algorithm ID: "json-canonical-utf8-sort-keys-v1"  [pending SP-003 confirmation]

Python implementation:
  canonical_bytes = json.dumps(
      record_dict,
      sort_keys=True,
      separators=(',', ':'),
      ensure_ascii=True
  ).encode('utf-8')
```

This algorithm is deterministic for any given dict (assuming no float NaN/Inf and no non-string keys). Floats must be serialized using Python's default float repr, which is deterministic within a Python version.

## 8.2 Ed25519 path (if XREG-002 → Ed25519)

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def sign_ed25519(record_bytes: bytes, private_key_bytes: bytes) -> bytes:
    key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
    return key.sign(record_bytes)          # Returns 64-byte signature

def verify_ed25519(record_bytes: bytes, signature: bytes,
                   public_key_bytes: bytes) -> bool:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        key.verify(signature, record_bytes)
        return True
    except InvalidSignature:
        return False
```

Key storage: private key stored as 32 raw bytes in `/var/assurance/keys/signing_key.bin`. Key file permissions: 0o400 (supervisor read-only). Public key stored separately in `/var/assurance/keys/signing_key.pub` for verification.

## 8.3 HMAC-SHA256 path (if XREG-002 → HMAC-SHA256)

```python
import hmac, hashlib

def sign_hmac_sha256(record_bytes: bytes, key: bytes) -> bytes:
    return hmac.new(key, record_bytes, hashlib.sha256).digest()  # 32 bytes

def verify_hmac_sha256(record_bytes: bytes, provided_mac: bytes,
                       key: bytes) -> bool:
    expected = hmac.new(key, record_bytes, hashlib.sha256).digest()
    return hmac.compare_digest(expected, provided_mac)  # timing-safe comparison
```

Key storage: 32+ byte random secret in `/var/assurance/keys/hmac_key.bin`. Permissions: 0o400.

## 8.4 Signature encoding

Signatures are stored as hex-encoded strings in the `signature` column of `provenance_records`. Ed25519: 128 hex chars (64 bytes). HMAC-SHA256: 64 hex chars (32 bytes).

## 8.5 Replay protection

- `replay_nonce` = `uuid.uuid4().hex` (32 hex chars) — generated fresh for every provenance record.
- SQLite `UNIQUE` constraint on `replay_nonce` in `provenance_records` table enforces non-reuse.
- On attempted insert with duplicate nonce: raises `sqlite3.IntegrityError` → supervisor catches → emits `REPLAY_ATTEMPT_DETECTED` audit event → raises `ReplayAttemptError`.

## 8.6 Sequence gap detection

```python
def _check_sequence(self, new_seq: int, last_seq: int) -> None:
    if new_seq != last_seq + 1:
        self._audit.append_event('SEQUENCE_GAP_DETECTED', {
            'expected': last_seq + 1, 'received': new_seq,
            'gap_size': new_seq - last_seq - 1
        })
        # Do not raise; proceed with the record; gap is logged
```

## 8.7 Signing failure handling

If signing raises any exception:
1. Set `signing_status = 'SIGNING_UNAVAILABLE'` in the provenance record.
2. Set `signature = None` and `signature_algorithm = None`.
3. Write the record to evidence store with `SIGNING_UNAVAILABLE` status.
4. Emit `SIGNING_UNAVAILABLE` audit event.
5. Do NOT raise to the pipeline orchestrator — other evidence records are not affected.
6. Do NOT treat the unsigned record as signed.

## 8.8 Audit chain hash construction

```python
def _compute_chain_link_hash(self, event_record: dict) -> str:
    canonical = json.dumps(event_record, sort_keys=True,
                            separators=(',',':'), ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()
```

The `chain_link_hash` stored in `audit_events` is the SHA-256 of the canonical representation of the event record itself (excluding the `chain_link_hash` field, which is added after computation).

## 8.9 PF-002 non-claim (mandatory on every provenance record)

```python
PF_002_NON_CLAIM = (
    "Cryptographic signature establishes that this record was produced and not modified "
    "after signing under accepted-key assumptions. It does NOT establish: "
    "(a) that the named model executed the assessed inferences (PF-002); "
    "(b) that the assessment was accurate; "
    "(c) that the signing key was not compromised; or "
    "(d) that the system producing this record was not itself compromised."
)
```

This constant is defined in `assurance_system/constants.py` and referenced in `provenance.py`. It must not be truncated or paraphrased in the stored record.

---

# 9. ASSURANCE / FINDING IMPLEMENTATION

## 9.1 C5 rule engine (complete mapping)

```python
# STEP 1 — Collect all evidence records for this asset
# STEP 2 — Determine detection_status
def _derive_detection_status(evidence_records):
    statuses = {r['assessment_status'] for r in evidence_records}

    # Priority rule 1: Any upstream failure → UNAVAILABLE
    fail_states = {'ASSESSMENT_ERROR', 'UNAVAILABLE', 'ARTIFACT_UNIT_AMBIGUOUS',
                   'LOAD_ERROR', 'REFERENCE_UNAVAILABLE'}
    if statuses & fail_states:
        return 'UNAVAILABLE'

    # Priority rule 2: Containment violation → ANOMALY_DETECTED
    if 'ONNX_PATH_CONTAINMENT_VIOLATION' in statuses:
        return 'ANOMALY_DETECTED'

    # Priority rule 3: Hostile pickle blocked → ANOMALY_DETECTED
    if 'LOAD_BLOCKED' in statuses:
        return 'ANOMALY_DETECTED'

    # Priority rule 4: Structural invalid → ANOMALY_DETECTED
    if 'STRUCTURAL_INVALID' in statuses:
        return 'ANOMALY_DETECTED'

    # Priority rule 5: C2A violations present
    for r in evidence_records:
        if r['worker_id'] == 'COMP-W-C2A':
            raw = json.loads(r['raw_signal'] or '{}')
            if raw.get('violation_count', 0) > 0:
                return 'ANOMALY_DETECTED'

    # Priority rule 6: C2B duplicates present
    for r in evidence_records:
        if r['worker_id'] == 'COMP-W-C2B':
            raw = json.loads(r['raw_signal'] or '{}')
            if raw.get('duplicate_group_count', 0) > 0:
                return 'ANOMALY_DETECTED'

    # Priority rule 7: Identity comparison
    for r in evidence_records:
        if r['worker_id'] == 'COMP-W-C3B':
            raw = json.loads(r['raw_signal'] or '{}')
            cr = raw.get('comparison_result', 'UNAVAILABLE')
            if cr == 'DIFFERENT':
                return 'IDENTITY_DIFFERENT'
            if cr == 'MATCH':
                return 'IDENTITY_MATCH'
            return 'UNAVAILABLE'

    # Rule 8: C2C statistics only
    for r in evidence_records:
        if r['worker_id'] == 'COMP-W-C2C' and r['assessment_status'] == 'COMPLETED':
            return 'COMPLETED_STATISTICS_ONLY'

    # Default: all completed, no anomaly
    if all(r['assessment_status'] in ('COMPLETED', 'STRUCTURAL_VALID', 'LOAD_SUCCESS')
           for r in evidence_records):
        return 'NO_ANOMALY_DETECTED'

    return 'UNAVAILABLE'

# STEP 3 — interpretation_status mapping
INTERPRETATION_MAP = {
    'UNAVAILABLE':              'UNAVAILABLE',
    'ANOMALY_DETECTED':         'REQUIRES_INVESTIGATION',
    'IDENTITY_MATCH':           'CONSISTENT_WITH_EXPECTED',
    'IDENTITY_DIFFERENT':       'IDENTITY_DEVIATION_DETECTED',
    'COMPLETED_STATISTICS_ONLY':'STATISTICS_REPORTED',
    'NO_ANOMALY_DETECTED':      'NO_ANOMALY_DETECTED',
}

# STEP 4 — analyst_disposition_prompt mapping
DISPOSITION_MAP = {
    'UNAVAILABLE':              'UNAVAILABLE_NO_DECISION',
    'ANOMALY_DETECTED':         'ESCALATE',
    'IDENTITY_DIFFERENT':       'ESCALATE',
    'IDENTITY_MATCH':           'ACCEPT',
    'NO_ANOMALY_DETECTED':      'ACCEPT',
    'COMPLETED_STATISTICS_ONLY':'ACCEPT_WITH_CONTEXT',
}

# STEP 5 — mandatory non-claim fields
def _set_mandatory_non_claims(finding, detection_status, worker_ids):
    finding['coverage_gap_clean_label'] = 1            # Always
    finding['anomaly_not_malicious_non_claim'] = (
        1 if detection_status == 'ANOMALY_DETECTED' else 0)
    finding['global_backdoor_absence_not_established'] = (
        1 if any(w.startswith('COMP-W-C3') for w in worker_ids) else 0)
```

## 9.2 UNAVAILABLE propagation (enforced mechanically)

The rule engine has no path that converts `UNAVAILABLE` or `ASSESSMENT_ERROR` to any positive assurance state. The priority ordering ensures: if the first rule matches (any fail state in the evidence), `'UNAVAILABLE'` is returned before any positive-state rules are evaluated.

Test hook: `FIX-013` injects UNAVAILABLE at each pipeline layer and confirms `UNAVAILABLE_NO_DECISION` is produced. This test must pass before any capability claim is made.

## 9.3 T05d permanent non-claim

Every C5 finding (regardless of `detection_status`) must include in its `non_claims` list:
```
"T05d (clean-label poisoning) is NOT detectable under the current assessment scope; 
no detection claim is made for this attack class."
```

The C5 engine adds this string unconditionally.

## 9.4 Multi-detector dependency declaration

When a finding aggregates evidence from more than one worker, `dependency_declaration.co_firing_detectors` must list all worker IDs that contributed. `independence_established` must be `false` unless the project has formally established and documented detector independence, which it has not.

## 9.5 Analyst disposition audit event

When an analyst records a disposition via the CLI:
```python
store.write_audit_event('ANALYST_DISPOSITION', {
    'finding_id': finding_id,
    'asset_id': asset_id,
    'disposition': disposition,
    'analyst_id': 'UNAVAILABLE',   # OQ-017 open; no authentication established
    'rationale': rationale_text,
    'timestamp': datetime.utcnow().isoformat()
})
```
The disposition is recorded as an audit event only. It does NOT modify the finding record. The finding remains immutable after its initial write.

---

# 10. FAILURE / STATE MODEL

## 10.1 Assessment state machine

All possible assessment states and their transitions:

| State | Meaning | Entry condition | C5 disposition | Downstream |
|---|---|---|---|---|
| APPLICABLE | Method dispatched | Format + method in scope; prerequisites met | — | Worker executing |
| COMPLETED | Worker returned valid result | Schema-validated output received | Per C5 rule engine | Continue to C5 |
| ASSESSMENT_ERROR | Worker failed | Timeout / crash / no result file | UNAVAILABLE_NO_DECISION | Other methods continue |
| UNAVAILABLE | Prerequisite absent | Reference absent; access mode insufficient; SP-002 undefined | UNAVAILABLE_NO_DECISION | Continue; do not block others |
| UNSUPPORTED | Format not in scope | Format/variant not in supported_formats.yaml | No finding produced | Continue |
| DEFERRED_IN_SCOPE | Method known but excluded from MVP | Method in deferred list | Analyst sees explicit notice | Continue |
| ARTIFACT_UNIT_AMBIGUOUS | Artifact-unit unresolvable | SP-002 absent or external-data inconsistent | UNAVAILABLE for hash methods | Hash methods blocked; structural continues |
| SCHEMA_VIOLATION | Worker output fails validation | COMP-SCHEMA rejects output | UNAVAILABLE | Record in audit chain; evidence store NOT written |
| LOAD_BLOCKED | Hostile checkpoint detected | weights_only=True blocked deserialization | ESCALATE (not CLEAN) | Assessment stopped for this model |
| LOAD_SUCCESS | Model loaded safely | weights_only=True succeeded | Per C5 rule engine | Continue |
| LOAD_ERROR | Unexpected loading failure | Exception other than pickle/runtime | UNAVAILABLE_NO_DECISION | Continue |
| ONNX_PATH_CONTAINMENT_VIOLATION | External data path escapes asset dir | Path check in C3A failed | ESCALATE | Model assessment stopped |
| STRUCTURAL_VALID | ONNX structure passes checker | onnx.checker.check_model succeeded | Per C5 rule engine | Continue |
| STRUCTURAL_INVALID | ONNX structure fails checker | onnx.checker.ValidationError or parse error | REQUIRES_INVESTIGATION | Continue |
| REFERENCE_UNAVAILABLE | Reference not HEALTH_VERIFIED | COMP-REF returns UNAVAILABLE | UNAVAILABLE_NO_DECISION | Other methods unaffected |
| SIGNING_UNAVAILABLE | Key unavailable at signing time | Key access failed | UNAVAILABLE for binding claim | Evidence record exists; binding claim not supported |

## 10.2 Enforced invariants (no exception path bypasses these)

```
UNAVAILABLE ≠ CLEAN
ASSESSMENT_ERROR ≠ CLEAN
DEFERRED_IN_SCOPE ≠ CLEAN
REFERENCE_UNAVAILABLE ≠ CLEAN
SCHEMA_VIOLATION result → evidence store NOT written (never partial write)
LOAD_BLOCKED → ESCALATE (never CLEAN, never CONFIRMED_MALICIOUS)
ANOMALY_DETECTED → REQUIRES_INVESTIGATION (never PROVEN_MALICIOUS)
C5 ERROR → UNAVAILABLE_NO_DECISION (no compression to PASS)
```

## 10.3 Supervisor state on critical failures

| Failure | Supervisor state | Recovery |
|---|---|---|
| Evidence store write failure | PipelineError raised; current record not written; audit event attempted | Operator restarts supervisor; re-runs assessment for affected asset |
| Audit chain write failure | AuditWriteError raised; secondary error log attempted; pipeline halts for affected record | Operator inspects audit trail; chain integrity check run on restart |
| Signing key not found at startup | Supervisor logs warning; signing_status=SIGNING_UNAVAILABLE for all records in this run | Operator provisions key; restart |
| Chain corruption detected on startup | CHAIN_CORRUPT event emitted; verification report generated; NO chain reset | Operator reviews; chain must not be reset without explicit operator decision |
| Worker OOM | Worker killed by OS; supervisor receives non-zero exit; ASSESSMENT_ERROR emitted | No supervisor impact; continue |

---

# 11. SAFE-LOADING / ISOLATION IMPLEMENTATION

## 11.1 Trust-boundary enforcement checklist

| Check | Mechanism | Implemented in |
|---|---|---|
| Workers cannot write to evidence store path | OS file ACL; path not in task_spec | Deployment; orchestrator.py |
| Workers cannot access signing key | Key path not in task_spec; env var stripped | orchestrator.py |
| Workers cannot communicate with supervisor except via result file | IPC is file-only; stdout/stderr suppressed | orchestrator.py subprocess.Popen |
| Workers have no network access | OS firewall or network namespace [CONDITIONAL: PRE-01] | Deployment |
| Workers have limited filesystem write (temp dir only) | CWD set to temp dir; OS ACL on evidence store | orchestrator.py |
| No runtime module loading from submitted assets | Workers import only from installed packages; no exec() or importlib.import_module(path) | Code review |

## 11.2 Resource limits implementation

```python
@dataclasses.dataclass
class ResourceLimits:
    timeout_seconds: int    # Default: 120 for dataset scans; 60 for model loading
    memory_limit_mb: int    # Default: 2048
    max_file_descriptors: int  # Default: 64

# Limits are applied inside the worker process pre-exec (Linux):
# resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, RLIM_INFINITY))
# resource.setrlimit(resource.RLIMIT_NOFILE, (max_fds, max_fds))
# resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))   # No subprocess spawning from workers
```

On Unix/Linux, worker-side `resource.setrlimit` behavior is unchanged. Workers
must log whether those worker-side limits were applied.

On Windows (ACC-2026-10-02-01), the supervisor additionally and independently
enforces `ResourceLimits.memory_limit_mb` as a per-process committed-memory
ceiling using a Job Object with `JOB_OBJECT_LIMIT_PROCESS_MEMORY` and
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. The worker is created suspended, assigned
to the Job, and resumed only after successful assignment. Setup failure is
fail-closed. The Job handle is retained through collection and closed on every
path. A Job completion-port process-memory-limit notification terminates the Job;
kill-on-close remains the cleanup backstop. This Windows mechanism must not be
described as `RLIMIT_AS` or exact RSS;
the worker's existing `resource_limits_applied` field continues to describe its
worker-side Unix limit application, not supervisor Job containment.

Approved HOST-CAP-002 probe evidence: 128 MiB configured, 127.05 MiB peak
committed process memory, MemoryError at the boundary, child exit 42, PASS.
This capability probe does not replace SEC-002's real supervisor/FIX-002 test.

## 11.3 weights_only=True enforcement (C3D)

Implementation must pass these automated tests before any safe-loading claim:

```
grep_test_1: grep -r "weights_only=False" assurance_system/ → must return 0 matches
grep_test_2: grep -r "weights_only.*False" assurance_system/ → must return 0 matches
grep_test_3: grep -r "weights_only.*=.*False" assurance_system/ → must return 0 matches
```

These grep tests must be run as part of CI and must fail the build if any match is found.

## 11.4 ONNX external-data path-containment implementation

Four-layer check in COMP-W-C3A (see Section 3.7). Defense in depth: COMP-W-C3C re-verifies the model file path before calling onnx.load, even though C3A already confirmed containment. The re-check uses `os.path.realpath` to defeat any symlink manipulation that may have occurred between C3A and C3C execution.

## 11.5 Temp directory lifecycle

```python
# Created: just before worker subprocess is spawned
# Permissions: 0o700 (owner-only read/write)
# Contents: task.json (input) + result.json (output, created by worker)
# Cleaned: in the finally: block of _dispatch_worker, even if worker crashed
# If cleanup fails: logged; pipeline continues; orphan temp dirs are
#   cleaned on next supervisor startup via a startup sweep
```

---

# 12. OFFLINE / DEPENDENCY SPECIFICATION

## 12.1 Required packages

| Package | Purpose | Offline status | Condition |
|---|---|---|---|
| Python stdlib (hashlib, subprocess, sqlite3, json, hmac, uuid, math, pathlib, shutil, argparse, http.server) | Core functionality | FULLY_OFFLINE — no staging needed | None |
| `PyYAML==6.0.3` | Parse the required runtime configuration files and supported YAML submission manifests using `yaml.safe_load` | CONDITIONAL — pre-staged binary wheel required | CPython 3.13 / Windows AMD64 wheel verified on target; no source build |
| `onnx` | ONNX structural validation (C3A, C3C) | CONDITIONAL — pre-staged wheel required | Must install and import on target |
| `torch` (CPU-only) | PyTorch safe-loading gate (C3D) | CONDITIONAL — large wheel; CPU-only variant required | PRE-01 (target OS/arch); PRE-05 (PyTorch in scope) |
| `pycocotools` (R27) | COCO JSON parsing (C2A) | CONDITIONAL — C extension build required on target | PRE-01 (compiler present); C extension must compile |
| `cryptography` | Ed25519 signing (C4) | CONDITIONAL — only if XREG-002 → Ed25519 | PRE-02 (XREG-002 decision) |

## 12.2 Wheelhouse composition procedure

The offline dependency claim requires this procedure to be executed on the **confirmed target host** (PRE-01 required):

```
1. On target host (no internet):
   pip install --no-index --find-links /opt/assurance-wheelhouse PyYAML==6.0.3
   pip install --no-index --find-links /opt/assurance-wheelhouse onnx
   pip install --no-index --find-links /opt/assurance-wheelhouse pycocotools
   pip install --no-index --find-links /opt/assurance-wheelhouse torch --index-url file:///opt/assurance-wheelhouse
   pip install --no-index --find-links /opt/assurance-wheelhouse cryptography   [if Ed25519]

2. Verify imports:
   python -c "import yaml; print(yaml.__version__)"
   python -c "import onnx; print(onnx.__version__)"
   python -c "import pycocotools; print('ok')"
   python -c "import torch; print(torch.__version__)"
   python -c "from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey; print('ok')"

3. Zero-egress confirmation:
   Run pip check (no network call)
   Monitor network traffic during step 2 (must be zero bytes egress)

4. Record: {package: version, wheel_file: sha256, install_verified: true, egress_bytes: 0, host: ..., date: ...}
```

No offline claim is made until all four steps complete successfully on the actual target host.

## 12.3 Package version pinning

All package versions are pinned in `requirements.txt` after successful wheelhouse verification on target (PRE-01). Hard constraints already established:
- `torch >= 2.10.0` (XREG-005 floor — cannot be relaxed without architecture change control)
- `PyYAML == 6.0.3` (production configuration and YAML manifest parser; CPython 3.13 / Windows AMD64 binary wheel verified)

All other versions: pending PRE-01 resolution.

## 12.4 No-network runtime assertion

At startup, the supervisor runs a network-availability assertion:

```python
def _assert_no_network():
    """Called at supervisor startup. Confirms no inadvertent network dependency."""
    import socket
    try:
        socket.setdefaulttimeout(1)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
        # If we reach here, network is available — log WARNING but do not halt
        # (The system may legitimately be running on a host with network for dev purposes)
        logger.warning("NETWORK_AVAILABLE: system is not operating in fully offline mode")
    except (socket.timeout, OSError):
        logger.info("OFFLINE_CONFIRMED: no network connectivity detected")
```

Production deployment must confirm this assertion produces `OFFLINE_CONFIRMED` on the target host.

## 12.5 ORT binary telemetry (EF-003)

ONNX Runtime (ORT) is NOT used in the MVP scope. ORT is not in the dependency list. EF-003 (telemetry confirmation) is therefore not required for MVP. If ORT is added in future, EF-003 verification must be completed before any offline claim is made.

---

# 13. TARGET-FORMAT IMPLEMENTATION

## 13.1 Supported formats at MVP

| Format | Component | Status | Condition |
|---|---|---|---|
| COCO JSON (standard) | COMP-W-C2A | SUPPORTED — implementation planned | pycocotools C extension builds on target (PRE-01) |
| YOLO_DETECTION | COMP-W-C2A | CONDITIONAL | PRE-05 format-list decision |
| YOLO_SEG | COMP-W-C2A | CONDITIONAL | PRE-05 |
| YOLO_POSE | COMP-W-C2A | CONDITIONAL | PRE-05 |
| YOLO_OBB | COMP-W-C2A | CONDITIONAL | PRE-05 |
| ONNX (external-data + no-external-data variants) | COMP-W-C3A, C3C | SUPPORTED | onnx wheel on target |
| PyTorch .pt/.pth | COMP-W-C3D | CONDITIONAL | PRE-01; PRE-05; torch CPU wheel on target |
| TorchScript | COMP-W-C3A | DEFERRED_IN_SCOPE | Isolated worker not demonstrated on target |

## 13.2 Unsupported format handling

If a submitted asset's format does not match any entry in `supported_formats.yaml`:
1. COMP-SUP emits `UNSUPPORTED` evidence record for the asset.
2. No worker is dispatched.
3. C5 finding carries `applicability_status = 'UNSUPPORTED'`.
4. No `CLEAN` or `SAFE` result is produced; the asset is not assessed.

## 13.3 COCO variant coverage

pycocotools handles: instance segmentation annotations; keypoint annotations; panoptic annotations (if in the same COCO JSON format). The geometry validator loop is format-agnostic at the annotation level: it processes all annotations regardless of task type. Annotation type is identified by the presence of `segmentation`, `keypoints`, or `bbox` fields; each is validated for the relevant field structure.

## 13.4 YOLO variant configuration

The supported YOLO task variant(s) are declared in `config/supported_formats.yaml`:

```yaml
yolo_task_variants:
  - YOLO_DETECTION    # active if PRE-05 confirms
  - YOLO_SEG          # active if PRE-05 confirms
  # YOLO_POSE: conditional
  # YOLO_OBB: conditional
```

On startup, `config/loader.py` reads this file and populates the supported-variant set used by COMP-W-C2A. Variants absent from this set produce `UNSUPPORTED` records.

## 13.5 ONNX external-data support

Both ONNX variants are handled by C3A:
- No-external-data ONNX: `model_proto.graph.initializer` has no `EXTERNAL` data_location entries. `external_files = []`.
- External-data ONNX: references resolved and containment-checked per Section 3.7.

Both variants produce the same evidence record schema. The external_files list is empty vs. non-empty.

---

# 14. APPROVED REUSE INTEGRATION

| Reuse ID | Source | Source path | Destination module | Modification | License | Attribution |
|---|---|---|---|---|---|---|
| REUSE-018 | R17 (SHA-256/SQLite patterns) | Various | supervisor/evidence_store.py; supervisor/audit_chain.py | Add supervisor-only write enforcement; WAL mode; project schema; hash-chain | MIT | Required in NOTICE file |
| REUSE-019 | R18 (data-lineage patterns) | Various | supervisor/evidence_store.py (supplementary) | Adapt to COCO/YOLO; supervisor-write enforcement | MIT | Required in NOTICE file |
| REUSE-020 | R27 pycocotools | PyPI | workers/c2a_structural.py | Used as library dependency; geometry validation layer added on top | BSD-style permissive | Required in NOTICE file |

**All other components: REIMPLEMENT.** No R01 code may enter the codebase (license unresolved).

## 14.1 R17 patterns integration (REUSE-018)

Extract patterns from R17 for:
- SQLite connection setup (WAL mode, foreign_keys=ON)
- Parameterised query pattern (prevents SQL injection)
- SHA-256 streaming hash pattern (64 KB chunks)

Do NOT copy verbatim. Re-implement in project code with project-specific schema and supervisor-write enforcement. Attribution: `# SHA-256 streaming pattern adapted from R17 (MIT); see NOTICE`.

## 14.2 pycocotools integration (REUSE-020)

```python
# In workers/c2a_structural.py:
from pycocotools.coco import COCO  # R27 ADOPT/ADAPT — BSD; attribution in NOTICE

def load_coco_annotations(annotation_path: str) -> dict:
    coco = COCO(annotation_path)   # Handles JSON load and index building
    return {
        'annotations': list(coco.anns.values()),
        'categories': list(coco.cats.values()),
        'images': list(coco.imgs.values())
    }
```

Geometry validation loop operates on `coco.anns.values()` — ALL annotations, not a subset.

## 14.3 What must NOT enter the codebase

Per REUSE-015 and project invariants:
- Any file from R01 VIKASHL25/SIH-26228 (license unresolved; unconditionally excluded)
- R01 Fabric client (fake CONNECTED; excluded unconditionally)
- R01 first-box label detector (replaced by all-box validator; excluded unconditionally)
- R01 aggregate risk score module (prohibited by project invariant; excluded unconditionally)
- R13 Alibi-Detect (BSL 1.1 — not open source)
- R04 BackdoorBench (CC BY-NC)
- R05 BackdoorBox (GPL-2.0 copyleft)
- R09 backdoor_detection (no license; unsafe torch.load without weights_only=True)

Code review must confirm these exclusions via grep/import checks.

---

# 15. CONFIGURATION / THRESHOLD SPECIFICATION

## 15.1 Fixed parameters (hardcoded; not configurable)

| Parameter | Fixed value | Enforcement |
|---|---|---|
| PyTorch safe-loading mode | `weights_only=True` always | RC-013; grep test required |
| PyTorch version floor | `>= 2.10.0` | requirements.txt; XREG-005 |
| Evidence field defaults | `UNAVAILABLE` / `NOT_ASSESSED` | SQLite DEFAULT; AR-003 |
| Contributor identity default | `UNTRUSTED` | AR-011; hardcoded in task_spec builder |
| SYBIL_UNRELIABLE default | `True` | DF-005; hardcoded in C2C worker |
| coverage_gap_clean_label | `True` always on C2+C3 | COMP-SCHEMA; SQLite CHECK |
| Worker unsafe fallback | PROHIBITED | RC-013; grep test |
| First-box-only label analysis | PROHIBITED | REUSE-003; code review |
| Aggregate risk score | PROHIBITED | COMP-SCHEMA prohibits field; SQLite schema has no such column |
| Fail-open audit chain | PROHIBITED | AF-004; AuditWriteError never swallowed |

## 15.2 Configurable parameters (in system_config.yaml)

```yaml
# system_config.yaml
schema_version: "v1.0"
schema_active_version_id: "worker-output-v1"   # Must match all worker outputs

evidence_store:
  path: "/var/assurance/evidence-store/evidence.db"

audit_trail:
  path: "/var/assurance/audit-trail/audit.db"

signing:
  key_path: "/var/assurance/keys/signing_key.bin"
  public_key_path: "/var/assurance/keys/signing_key.pub"   # Ed25519 only
  sequence_state_path: "/var/assurance/keys/sequence_state.json"
  algorithm: "PENDING_XREG_002"    # Replaced with Ed25519 or HMAC-SHA256 post-PRE-02

supported_formats_config: "config/supported_formats.yaml"
artifact_unit_defs_dir: "artifact_unit_defs/"    # SP-002 output dir

supervisor_version_id: "0.1.0-mvp"

# resource_limits.yaml (per-worker-type overrides):
resource_limits:
  default:
    timeout_seconds: 120
    memory_limit_mb: 2048
    max_file_descriptors: 64
  C3D_SAFE_LOAD:
    timeout_seconds: 60
    memory_limit_mb: 4096     # PyTorch model loading may need more
    max_file_descriptors: 32
  C2A_STRUCTURAL:
    timeout_seconds: 300      # Large annotation files may take longer
    memory_limit_mb: 2048
    max_file_descriptors: 32
```

## 15.3 Policy-controlled settings (owner decision required)

| Setting | Owner | Default |
|---|---|---|
| Analyst authentication method | Project owner (OQ-017) | Not established; analyst_id = "UNAVAILABLE" |
| Analyst override authority | Project owner (OQ-017) | Not established |
| Evidence retention period | Project owner (OQ-018) | Indefinite at MVP |
| Trusted-clock source | Deployment environment (AF-003) | Local system clock; AF-003 caveat in records |
| Reference staleness trigger conditions | Project owner (COMP-REF) | Not defined at MVP |

## 15.4 Threshold documentation rule

Every numeric value used in assessments must be:
1. Named in system_config.yaml or resource_limits.yaml.
2. Documented with the parameter name, what it controls, and why the default was chosen.
3. Recorded in the relevant evidence record or audit event (e.g., `timeout_seconds` in ASSESSMENT_ERROR records).
4. Never embedded as an unnamed literal (e.g., `time.sleep(60)` without referencing `config.resource_limits.timeout_seconds`).

---

# 16. API / INTERNAL INTERFACES

## 16.1 Worker subprocess contract (B2 boundary)

Defined in Sections 4.1, 4.2, and 3.1. Summary:
- Input via named temp file (JSON).
- Output via named temp file (JSON).
- Supervisor reads result file; validates via COMP-SCHEMA; cleans up temp dir.
- Workers must not write to stdout (suppressed). Stderr captured for error logging only.
- Workers must exit with code 0 on success and non-zero on any error.

## 16.2 Evidence store API (COMP-STORE — supervisor internal)

```python
class EvidenceStore:
    def write_evidence_record(self, record: dict) -> str: ...       # raises StorageWriteError
    def write_finding(self, finding: dict) -> str: ...              # raises StorageWriteError
    def write_provenance_record(self, record: dict) -> str: ...     # raises StorageWriteError
    def write_audit_event(self, event_type: str, payload: dict) -> str: ...  # raises AuditWriteError
    def write_deferred_record(self, record: dict) -> str: ...       # raises StorageWriteError
    def query_findings(self, asset_id: str = None) -> list[dict]: ...
    def query_evidence(self, asset_id: str, method_id: str) -> dict | None: ...
    def query_audit_trail(self, limit: int = None) -> list[dict]: ...
    def query_deferred(self) -> list[dict]: ...
    def export_bundle(self, asset_id: str) -> bytes: ...            # Returns ZIP bytes
    def verify_chain_integrity(self) -> ChainVerificationResult: ...
```

No method may:
- Return `None` where the caller could interpret it as a clean/empty-assessment result.
- Swallow `sqlite3.Error` exceptions.
- Write from any code path other than the supervisor process.

## 16.3 Signing module interface (COMP-C4)

```python
class ProvenanceBuilder:
    def sign_record(self, record_bytes: bytes, key_material: bytes) -> tuple[str, bytes]:
        """Returns (algorithm_id, signature_bytes). Raises SigningKeyUnavailableError."""

    def verify_record(self, record_bytes: bytes, signature: bytes,
                       key_material: bytes, algorithm_id: str) -> bool:
        """Returns True if valid. PF-002: True does not establish causal execution."""

    def build_and_sign(self, artifact_unit_digest: str,
                        evidence_record_digests: list[str],
                        sequence_state: SequenceState,
                        timestamp: str,
                        key_material: bytes) -> dict:
        """Returns signed provenance record dict. On failure: SIGNING_UNAVAILABLE record."""
```

## 16.4 CLI contract (COMP-IFACE)

```
assess --submission <path>
  Required: submission manifest path (JSON or YAML)
  Effect: full pipeline run
  Output: summary table to stdout; all records written to evidence store

show-finding --asset-id <uuid>
  Required: asset_id
  Effect: reads finding from store; prints all fields including UNAVAILABLE states

show-evidence --asset-id <uuid> --method <method-id>
  Required: asset_id, method_id
  Effect: prints evidence record

show-audit-trail [--limit N]
  Effect: prints audit events in order; reports CHAIN_CORRUPT if detected

export-bundle --asset-id <uuid> --output <path>
  Effect: writes findings.json + evidence.json + provenance.json + audit.json to ZIP at path

list-deferred
  Effect: lists all DEFERRED_IN_SCOPE and REFERENCE_UNAVAILABLE records

analyst-disposition --finding-id <uuid> --disposition <enum> --rationale <text>
  Required: finding_id; disposition (ACCEPT|ACCEPT_WITH_CONTEXT|ESCALATE|CONTAIN_HOLD|OVERRIDE)
  Effect: writes ANALYST_DISPOSITION audit event; does NOT modify finding record

dashboard [--port N]
  Effect: starts read-only HTTP server at localhost:N; serves evidence dashboard page
```

## 16.5 Interface failure contracts

| Interface | Failure | Required behaviour |
|---|---|---|
| Worker → supervisor (timeout) | Worker process killed | ASSESSMENT_ERROR evidence record emitted; pipeline continues |
| Worker → supervisor (schema violation) | COMP-SCHEMA rejects output | SCHEMA_VIOLATION audit event; no evidence record written |
| Supervisor → evidence store (write fail) | StorageWriteError raised | Audit event attempted; PipelineError raised; current record halted |
| Supervisor → signing module (key missing) | SigningKeyUnavailableError | SIGNING_UNAVAILABLE recorded; not raised to pipeline |
| Analyst → evidence store (record absent) | query returns None | UNAVAILABLE displayed; never substituted with CLEAN |
| Audit chain → store (write fail) | AuditWriteError raised | Secondary log attempted; pipeline halts for affected record |

---

# 17. TESTING SPECIFICATION

## 17.1 Unit tests

| Component | Test ID | Test type | Assertion |
|---|---|---|---|
| COMP-W-C2A | UT-C2A-001 | Positive | Valid COCO JSON → 0 violations; assessment_status=COMPLETED |
| COMP-W-C2A | UT-C2A-002 | Negative | FIX-008 COCO geometry violations → all expected violation_types present |
| COMP-W-C2A | UT-C2A-003 | Negative | Missing root field → MISSING_ROOT_FIELD violation |
| COMP-W-C2A | UT-C2A-004 | Coverage | Loop processes ALL annotations, not only first |
| COMP-W-C2A | UT-C2A-005 | Negative | FIX-017 malformed JSON → ASSESSMENT_ERROR |
| COMP-W-C2A | UT-C2A-006 | YOLO | FIX-009-D violations → expected YOLO_DETECTION violation_types |
| COMP-W-C2A | UT-C2A-007 | YOLO | Valid YOLO_DETECTION file → 0 violations |
| COMP-W-C2B | UT-C2B-001 | Positive | FIX-011 non-duplicate set → duplicate_group_count=0 |
| COMP-W-C2B | UT-C2B-002 | Negative | FIX-010 N duplicate pairs → duplicate_group_count=N |
| COMP-W-C2B | UT-C2B-003 | Algorithm | Same file hashed twice → same digest |
| COMP-W-C2C | UT-C2C-001 | Algorithm | 2 equal-share sources → HHI=0.5; entropy=1.0 bit |
| COMP-W-C2C | UT-C2C-002 | Algorithm | 1 source → HHI=1.0; entropy=0.0 |
| COMP-W-C2C | UT-C2C-003 | Invariant | identity_quality≠TRUSTED → sybil_unreliable=True always |
| COMP-W-C3A | UT-C3A-001 | Security | FIX-004 absolute external path → ONNX_PATH_CONTAINMENT_VIOLATION |
| COMP-W-C3A | UT-C3A-002 | Security | FIX-005 traversal pattern → ONNX_PATH_CONTAINMENT_VIOLATION |
| COMP-W-C3A | UT-C3A-003 | Security | FIX-006 symlink escape → ONNX_PATH_CONTAINMENT_VIOLATION |
| COMP-W-C3A | UT-C3A-004 | Positive | Valid ONNX no external data → COMPLETED; external_files=[] |
| COMP-W-C3B | UT-C3B-001 | Algorithm | Same artifact-unit hashed twice → same combined_digest |
| COMP-W-C3B | UT-C3B-002 | Algorithm | Reference_digest = combined_digest → MATCH |
| COMP-W-C3B | UT-C3B-003 | Algorithm | reference_digest ≠ combined_digest → DIFFERENT |
| COMP-W-C3B | UT-C3B-004 | Invariant | No reference_digest → comparison_result=UNAVAILABLE |
| COMP-W-C3C | UT-C3C-001 | Positive | FIX-016 valid ONNX → STRUCTURAL_VALID |
| COMP-W-C3C | UT-C3C-002 | Negative | Corrupted ONNX protobuf → STRUCTURAL_INVALID |
| COMP-W-C3C | UT-C3C-003 | Non-claim | ef_004_non_claim field present on every record |
| COMP-W-C3D | UT-C3D-001 | Security | FIX-001 hostile pickle → LOAD_BLOCKED; fallback_attempted=False |
| COMP-W-C3D | UT-C3D-002 | Positive | FIX-015 benign model → LOAD_SUCCESS; fallback_attempted=False |
| COMP-W-C3D | UT-C3D-003 | Security | grep test: weights_only=False not in codebase → 0 matches |
| COMP-SCHEMA | UT-SCH-001 | Invariant | FIX-018 risk_score field → SCHEMA_VIOLATION |
| COMP-SCHEMA | UT-SCH-002 | Invariant | FIX-019 coverage_gap_clean_label=False → SCHEMA_VIOLATION |
| COMP-SCHEMA | UT-SCH-003 | Invariant | access_mode=null on C3 record → SCHEMA_VIOLATION |
| COMP-SCHEMA | UT-SCH-004 | Invariant | limitations=[] → SCHEMA_VIOLATION |
| COMP-SCHEMA | UT-SCH-005 | Invariant | non_claims=[] → SCHEMA_VIOLATION |
| COMP-C5 | UT-C5-001 | Invariant | FIX-013 UNAVAILABLE injection → finding.detection_status=UNAVAILABLE |
| COMP-C5 | UT-C5-002 | Invariant | LOAD_BLOCKED → detection_status=ANOMALY_DETECTED; anomaly_not_malicious_non_claim=1 |
| COMP-C5 | UT-C5-003 | Invariant | No risk_score field in any C5 output |
| COMP-C5 | UT-C5-004 | Invariant | T05d non-claim in non_claims list on every finding |
| COMP-AUDIT | UT-AUD-001 | Integrity | 3 events → chain_link_hash of event 2 = SHA-256(canonical(event 1)) |
| COMP-AUDIT | UT-AUD-002 | Failure | Modified event 1 → chain integrity check fails at event 2 |
| COMP-AUDIT | UT-AUD-003 | Failure | Chain corruption → CHAIN_CORRUPT event emitted; no reset |
| COMP-C4 | UT-C4-001 | Replay | Duplicate replay_nonce → ReplayAttemptError; REPLAY_ATTEMPT_DETECTED audit event |
| COMP-C4 | UT-C4-002 | Sequence | Gap in sequence_number → SEQUENCE_GAP_DETECTED audit event |
| COMP-C4 | UT-C4-003 | Non-claim | pf_002_non_claim present on every provenance record |
| COMP-C4 | UT-C4-004 | Failure | Key unavailable → SIGNING_UNAVAILABLE record; not raised to pipeline |

## 17.2 Integration tests

| Test ID | Scenario | Assertion |
|---|---|---|
| IT-001 | Full pipeline: clean COCO dataset + valid ONNX model | All evidence records COMPLETED; finding=NO_ANOMALY_DETECTED; audit chain intact |
| IT-002 | Full pipeline: FIX-008 dataset + FIX-001 hostile pickle | C2A: ANOMALY_DETECTED; C3D: LOAD_BLOCKED; C5: REQUIRES_INVESTIGATION; no CLEAN outputs |
| IT-003 | FIX-013 UNAVAILABLE injection at C2A layer | C5 finding: UNAVAILABLE_NO_DECISION; UNAVAILABLE_PROPAGATED audit event present |
| IT-004 | FIX-013 UNAVAILABLE injection at C3B layer | C5 finding: UNAVAILABLE_NO_DECISION |
| IT-005 | FIX-014 schema violation injection | SCHEMA_VIOLATION audit event; zero evidence records written; pipeline continues for other assets |
| IT-006 | FIX-004 ONNX path traversal | ONNX_PATH_CONTAINMENT_VIOLATION; C5 disposition=ESCALATE; no further C3 assessment |
| IT-007 | DEFERRED_IN_SCOPE emission | list-deferred returns records for all 9 deferred method categories |
| IT-008 | Evidence bundle export | export-bundle produces ZIP; ZIP contains findings.json + evidence.json + provenance.json + audit.json |
| IT-009 | FIX-020 synthetic-labelled run | All evidence records have is_synthetic=1; C5 finding is_synthetic=1 |
| IT-010 | Analyst disposition recording | ANALYST_DISPOSITION audit event written; finding record unchanged |

## 17.3 Security tests

| Test ID | Test | Pass condition |
|---|---|---|
| SEC-001 | FIX-001 hostile pickle | LOAD_BLOCKED; no code execution in supervisor; fallback_attempted=False |
| SEC-002 | FIX-002 OOM trigger | Worker killed; ASSESSMENT_ERROR emitted; supervisor continues |
| SEC-003 | FIX-003 hang trigger | ASSESSMENT_ERROR after timeout_seconds; supervisor not hung |
| SEC-004 | FIX-004 ONNX absolute path | ONNX_PATH_CONTAINMENT_VIOLATION; no file outside asset_dir read |
| SEC-005 | FIX-005 ONNX traversal | ONNX_PATH_CONTAINMENT_VIOLATION |
| SEC-006 | FIX-006 symlink escape | ONNX_PATH_CONTAINMENT_VIOLATION |
| SEC-007 | grep: weights_only=False | 0 matches in codebase |
| SEC-008 | Evidence store ACL | Non-supervisor process cannot write to evidence store path |
| SEC-009 | Replay attack | Duplicate replay_nonce rejected; REPLAY_ATTEMPT_DETECTED emitted |
| SEC-010 | Chain corruption | Modified audit event detected; CHAIN_CORRUPT emitted; no reset |
| SEC-011 | FIX-018 prohibited field | Schema validator rejects risk_score; no evidence record written |
| SEC-012 | FIX-019 coverage_gap false | Schema validator rejects; no evidence record written |

## 17.4 Offline tests

| Test ID | Test | Pass condition |
|---|---|---|
| OFF-001 | Install from wheelhouse on target host | All packages install with no network access |
| OFF-002 | Zero-egress run | Full pipeline run with network monitor shows 0 bytes egress |
| OFF-003 | Import verification | python -c "import onnx, torch, pycocotools" succeeds offline |
| OFF-004 | sqlite3 operation offline | Evidence store read/write succeeds with no network |

## 17.5 Reproducibility tests

| Test ID | Test | Pass condition |
|---|---|---|
| REPRO-001 | M01 structural validation | Same annotation file → same violations list on two runs |
| REPRO-002 | M02 exact hash | Same image → same SHA-256 on two runs |
| REPRO-003 | C3B identity hash | Same artifact-unit → same combined_digest on two runs |
| REPRO-004 | C5 finding | Same evidence records → same finding on two runs |
| REPRO-005 | Canonicalization | Same dict → same canonical bytes on two runs (same Python version) |
| REPRO-006 | Fixture reproducibility | Fixture generator with same seed → same fixture files |

---

# 18. EXPERIMENT / VALIDATION CONTRACT

For every major capability claim, the following contract defines the required evidence before the claim may be made:

## 18.1 M01 — Structural/geometry validation capability claim

| | |
|---|---|
| **Requirement** | Detect all-box geometry violations in COCO/YOLO annotation files |
| **Method** | COMP-W-C2A structural/geometry validator |
| **Test condition** | FIX-008/FIX-009 hostile fixtures (seeded; reproducible) |
| **Ground truth** | Known violations injected into fixture corpus; violation types and counts recorded in fixture manifest |
| **Expected result** | All injected violation types appear in evidence record violations list; violation_count matches injected count |
| **Observed result** | NOT YET OBTAINED |
| **Evidence** | COMP-W-C2A evidence record from fixture run; is_synthetic=1 |
| **Bounded conclusion** | "M01 detects the injected structural and geometry violation types in FIX-008/FIX-009 fixtures. It does NOT establish detection of semantic poisoning, T05d, or violations that conform to the annotation format spec." |
| **Limitations on conclusion** | Fixture population is synthetic; conclusion bounded to fixture types; does not establish real-world detection coverage |

## 18.2 C3D — Safe-loading gate capability claim

| | |
|---|---|
| **Requirement** | Block hostile PyTorch pickle artifacts; no unsafe fallback |
| **Method** | COMP-W-C3D safe-loading gate |
| **Test condition** | FIX-001 hostile pickle (LOAD_BLOCKED test); FIX-015 benign model (LOAD_SUCCESS test) |
| **Ground truth** | FIX-001: known hostile pickle that triggers UnpicklingError with weights_only=True. FIX-015: benign PyTorch model that loads cleanly |
| **Expected result** | FIX-001 → LOAD_BLOCKED; FIX-015 → LOAD_SUCCESS; fallback_attempted=False in both |
| **Observed result** | NOT YET OBTAINED |
| **Evidence** | C3D evidence records from fixture runs; grep test output (0 matches for weights_only=False) |
| **Bounded conclusion** | "C3D blocks the FIX-001 hostile pickle class. weights_only=False was not invoked in any test path. LOAD_BLOCKED ≠ PROVEN_MALICIOUS; LOAD_SUCCESS ≠ behavioral safety." |

## 18.3 C3A — Path containment capability claim

| | |
|---|---|
| **Test condition** | FIX-004 (absolute path), FIX-005 (traversal), FIX-006 (symlink) |
| **Expected result** | ONNX_PATH_CONTAINMENT_VIOLATION for all three fixture types |
| **Observed result** | NOT YET OBTAINED |
| **Bounded conclusion** | "C3A detects FIX-004/005/006 path containment violation types. Detection is based on path string analysis and os.path.realpath resolution; it does not establish that all path traversal variants are covered." |

## 18.4 Audit chain integrity claim

| | |
|---|---|
| **Test condition** | UT-AUD-002 modified-event test |
| **Expected result** | Chain integrity check detects modification; CHAIN_CORRUPT emitted |
| **Observed result** | NOT YET OBTAINED |
| **Bounded conclusion** | "The hash chain detects modification of events within the chain body. Tail truncation (events appended after the last legitimate event) is not detectable by the chain alone; COMPLETENESS_UNAVAILABLE applies." |

## 18.5 UNAVAILABLE propagation claim

| | |
|---|---|
| **Test condition** | FIX-013: UNAVAILABLE injected at each of 4 pipeline layers |
| **Expected result** | C5 finding: detection_status=UNAVAILABLE; analyst_disposition_prompt=UNAVAILABLE_NO_DECISION for each injection point |
| **Observed result** | NOT YET OBTAINED |
| **Bounded conclusion** | "UNAVAILABLE propagates through the pipeline without conversion to any positive assurance state, at the tested injection points." |

## 18.6 Validation evaluation procedure

For all experiment contracts above:
1. Freeze all thresholds before running the evaluation (no post-hoc tuning).
2. Run against fixture population only (no real third-party data until licensing confirmed).
3. Use `is_synthetic=1` labelling on all fixture-derived evidence.
4. Record observed result in the evidence record.
5. Derive bounded conclusion from observed result; do not extrapolate beyond tested scope.
6. Store fixture manifest (seed, fixture ID, expected violations) alongside evidence records.
7. Do NOT fabricate project results. If a test fails, record the failure as the observed result.

---

# 19. IMPLEMENTATION DEPENDENCY GRAPH

The following dependency order must be followed. Parallel-capable tasks are grouped in the same tier.

```
TIER 0 — PREREQUISITE DECISIONS (must complete before any code is written)
  PI-01: GAP-001 resolved (target host confirmed) → PRE-01
  PI-02: SP-002 produced (artifact-unit definitions) → PRE-03
  PI-03: SP-003 produced (vocabulary contract) → PRE-04
  PI-04: XREG-002 decided (HMAC vs Ed25519) → PRE-02
  PI-05: Mandatory format list confirmed → PRE-05

TIER 1 — FOUNDATION (can proceed in parallel once PRE-04 resolved)
  T1-A: assurance_system/exceptions.py
  T1-B: assurance_system/constants.py
  T1-C: assurance_system/config/loader.py + system_config.yaml + resource_limits.yaml
  T1-D: assurance_system/supervisor/evidence_store.py  (SQLite DDL; write methods)
  T1-E: assurance_system/supervisor/audit_chain.py
  T1-F: assurance_system/workers/base.py  (IPC boilerplate)

  Dependency: T1-D requires PRE-04 (schema version freeze)
              T1-A, T1-B, T1-C, T1-F have no P1 dependencies

TIER 2 — SCHEMA + FIXTURE SUITE (P0 priority; parallel where possible)
  T2-A: assurance_system/supervisor/schema_validator.py  [requires PRE-04]
  T2-B: assurance_system/fixtures/  (ALL fixtures — P0 PRIORITY)
         Fixtures must be ready before any security tests are run.

TIER 3 — DATA-INTEGRITY WORKERS (parallel)
  T3-A: workers/c2b_exact_hash.py   [no P1 blockers]
  T3-B: workers/c2c_concentration.py [no P1 blockers]
  T3-C: workers/c2d_image_hash.py   [no P1 blockers]
  T3-D: workers/c2a_structural.py   [CONDITIONAL on pycocotools (PRE-01); YOLO CONDITIONAL on PRE-05]

TIER 4 — MODEL-INTEGRITY WORKERS (parallel within tier)
  T4-A: workers/c3a_artifact_unit.py  [BLOCKED on PRE-03 for PyTorch path; ONNX path can proceed]
  T4-B: workers/c3c_onnx_structural.py [requires onnx wheel on target (PRE-01)]
  T4-C: workers/c3d_safe_load.py   [requires torch wheel (PRE-01, PRE-05); PRE-03 independent]
  T4-D: workers/c3b_model_hash.py  [BLOCKED on PRE-03 for PyTorch; ONNX path requires T4-A]

TIER 5 — PROVENANCE + INTERPRETATION
  T5-A: supervisor/provenance.py (COMP-C4)  [BLOCKED on PRE-02, PRE-04, PRE-08, PRE-09]
  T5-B: supervisor/reference_manager.py     [BLOCKED on PRE-06; MVP shell can be built earlier]
  T5-C: supervisor/capability_declaration.py [requires PRE-04]
  T5-D: supervisor/interpretation.py (COMP-C5) [requires T3-D and T4-A through T4-D; PRE-04]

TIER 6 — ORCHESTRATOR
  T6-A: supervisor/orchestrator.py (COMP-SUP)
         Requires: T1-D, T1-E, T2-A, T5-A, T5-C, T5-D

TIER 7 — ANALYST INTERFACE
  T7-A: interfaces/cli.py     [requires T6-A]
  T7-B: interfaces/exporter.py [requires T6-A]
  T7-C: interfaces/dashboard.py [requires T6-A; MVP value feature; lowest priority]

TIER 8 — INTEGRATION + END-TO-END TESTS
  T8-A: tests/integration/ full pipeline run
  T8-B: tests/security/ hostile fixture battery
  T8-C: tests/offline/ wheelhouse + zero-egress tests [requires PRE-01 confirmed]
  T8-D: tests/negative/ UNAVAILABLE propagation + schema rejection

CRITICAL PATH:
  PRE-04 → T1-D → T2-A → T5-D → T6-A → T7-A
  PRE-03 → T4-A → T4-D
  PRE-02 → T5-A → T6-A
  T2-B (fixtures) must be complete before T8-B (security tests)

PARALLEL-SAFE PAIRS (can run simultaneously):
  T3-A + T3-B + T3-C (all independent; no shared state)
  T4-A (ONNX path) + T4-C (after PRE-01 confirmed)
  T7-A + T7-B (after T6-A complete)
```

---

# 20. LOCKED / CONDITIONAL / DEFERRED ITEMS

## 20.1 Locked (approved; no further decision required)

- Option A architecture selected (project-owner approval 2026-09-25)
- All-box validation replaces first-box (REUSE-003)
- SHA-256 for all hashing (no substitution without architecture change control)
- Supervisor-only evidence store writes (AR-002)
- Hash-chained fail-closed audit trail (AR-008, AF-004)
- No aggregate risk score at any layer (G-07)
- COVERAGE_GAP_CLEAN_LABEL required on C2+C3 (AR-010)
- access_mode non-nullable on C3 (AR-013)
- DEFERRED_IN_SCOPE records for all out-of-scope methods (EF-010)
- UNAVAILABLE propagation enforced by schema (AR-003)
- PF-002 non-claim on every provenance record (PF-002)
- ANOMALY ≠ PROVEN_ATTACK on every applicable finding
- weights_only=True with no fallback (RC-013 REJECTED)
- PyTorch ≥ 2.10.0 floor (XREG-005)
- R27 pycocotools ADOPT/ADAPT (REUSE-020; BSD)
- R17 storage patterns EXTRACT (REUSE-018; MIT)
- R01 Fabric client excluded unconditionally (REUSE-015)
- Blockchain/DLT deferred for MVP (D-AD-004)
- Behavioral battery deferred for MVP (D-AD-005)
- PDQ near-duplicate deferred for MVP (D-AD-006)
- Named temp file IPC mechanism (this document §3.1)
- SQLite DDL as defined in this document §3.15
- Canonicalization algorithm: json-canonical-utf8-sort-keys-v1 (pending SP-003 confirmation)

## 20.2 Conditional (can proceed when stated condition is met)

| Item | Condition | Status |
|---|---|---|
| Offline deployment claim | PRE-01 + wheelhouse verified + zero-egress confirmed | BLOCKING |
| pycocotools COCO parsing | C extension builds on target host (PRE-01) | BLOCKING |
| torch CPU wheel | Target OS/arch confirmed (PRE-01); PRE-05 format list confirms PyTorch | BLOCKING |
| YOLO format support | PRE-05 format list confirmed | BLOCKING |
| PyTorch artifact-unit definition | SP-002 produced (PRE-03) | BLOCKING |
| C4 signing implementation | XREG-002 (PRE-02), SP-003 (PRE-04), SP-004 (PRE-08), SP-006 (PRE-09) all resolved | BLOCKING |
| ONNX behavioral battery as MVP extension | Reference model + canonicalization + ORT telemetry all confirmed | Currently UNAVAILABLE |
| Any offline capability claim | Target-host execution evidence (EVF-001 Layer 1) | Post-implementation |

## 20.3 Deferred (post-MVP; explicit DEFERRED_IN_SCOPE records required)

| Deferred item | Deferral reason | Record type |
|---|---|---|
| Behavioral battery (M07 class) | Reference artifact UNAVAILABLE; isolated worker not demonstrated on target | DEFERRED_IN_SCOPE |
| PDQ near-duplicate (M03-PDQ) | Native build spike not executed; calibration corpus not prepared | DEFERRED_IN_SCOPE |
| Statistical drift / OOD (M04, M05) | Calibration corpus and reference UNAVAILABLE | DEFERRED_IN_SCOPE |
| Reference-relative comparison (M11) | No HEALTH_VERIFIED reference available | REFERENCE_UNAVAILABLE |
| TorchScript loading | Isolated worker not demonstrated on target | DEFERRED_IN_SCOPE |
| T05d clean-label detection | Not detectable under current baseline | permanent NON_CLAIM |
| External tail completeness witness | Not in MVP | COMPLETENESS_UNAVAILABLE |
| Sybil-resistant identity authentication | External mechanism not established | SYBIL_UNRELIABLE flag |
| Activation-space analysis, Neural Cleanse, B3D, ABS, AC | Post-MVP research candidates | DEFERRED_IN_SCOPE |
| Analyst authentication | OQ-017 open | analyst_id='UNAVAILABLE' |
| Blockchain / DLT | GAP-009 pending | Not represented |

---

# 21. NEXT_STAGE_HANDOFF

## CURRENT STAGE
Stage 11 — Technical Specification

## ARTIFACT
`10_TECHNICAL_SPECIFICATION_SIH26228.md` (this document)

## ESTABLISHED FACTS
- Python module structure is authoritative (Section 2.2)
- SQLite DDL is authoritative (Section 3.15)
- IPC mechanism is named temp file (Section 3.1 subprocess template)
- Canonicalization algorithm ID is `json-canonical-utf8-sort-keys-v1` (pending SP-003 confirmation)
- Both signing paths (Ed25519 and HMAC-SHA256) are specified (Section 8.2–8.3); XREG-002 decision selects the branch
- All worker algorithms are specified to pseudocode level (Sections 3.3–3.10)
- C5 rule engine is fully specified (Section 9.1)
- All test requirements are specified (Section 17)
- Experiment/validation contracts defined (Section 18)
- Implementation dependency graph is defined (Section 19)

## DECISIONS
- Named temp file IPC mechanism (supersedes stdout option in architecture spec §17.1 which listed both)
- Custom schema validation without jsonschema package (Section 3.2)
- Exception hierarchy defined in exceptions.py (Section 3.18)
- Dashboard implemented as lightweight stdlib http.server (Section 3.16)
- SQLite CHECK constraint on coverage_gap_clean_label enforces integer=1 (Section 3.15)
- SQLite UNIQUE constraint on replay_nonce enforces replay protection at DB layer (Section 3.15)
- SQLite chain_state table (single-row) stores last audit chain hash and sequence number (Section 3.15)

## OPEN QUESTIONS (all P1 blockers; no implementation begins without resolution)
- PRE-01: Target host OS / CPU / Python version / RAM
- PRE-02: XREG-002 signing mechanism (HMAC-SHA256 vs Ed25519)
- PRE-03: SP-002 artifact-unit definitions (PyTorch)
- PRE-04: SP-003 vocabulary contract + schema version freeze
- PRE-05: Mandatory format list (YOLO variants; PyTorch scope)
- PRE-06: SP-001 reference-health gate procedure
- PRE-07: GAP-011 inference record source
- PRE-08: SP-004 crypto profile
- PRE-09: SP-006 C3→C4 adapter schema

## CONTRADICTIONS
None identified between this specification and the architecture specification. Where architecture spec §17.1 listed "stdout JSON or named temp file" as two options, this specification selects named temp file as the single mechanism; this does not contradict the architecture, it resolves an open choice.

## IMPORTANT LIMITATIONS
- All capability claims in this specification are DESIGN CLAIMS; no validation evidence exists yet.
- Offline claims remain BLOCKED until PRE-01 is confirmed and wheelhouse verification is executed on the actual target host.
- PyTorch and COCO parsing conditional capabilities remain BLOCKED until PRE-01 and PRE-05 are resolved.
- The C4 signing module remains BLOCKED until all four of PRE-02, PRE-04, PRE-08, PRE-09 are resolved.

## ARCHITECTURE IMPLICATIONS
None. Architecture is locked. This document adds implementation detail only.

## IMPLEMENTATION IMPLICATIONS
- COMP-FIX (hostile fixture suite) must be built as Tier 2 P0 task before any security test or claim.
- COMP-SCHEMA must be built before any other supervisor component (no evidence record can enter the store without schema validation).
- The weights_only=False grep test must be automated in CI from Day 1.
- The all-box coverage requirement for COMP-W-C2A must be enforced by a specific unit test (UT-C2A-004) before any data-integrity claim is made.
- Implementation must proceed in dependency order per Section 19; parallel-safe tiers may be parallelised across team members.

## VALIDATION IMPLICATIONS
- Every experiment/validation contract in Section 18 must be completed with OBSERVED RESULTS before the corresponding capability claim is made publicly.
- All results must use fixture corpus (is_synthetic=1); no claim may be made on unlicensed third-party data.
- The UNAVAILABLE propagation test (FIX-013) must pass before any integration claim is made.

## DO-NOT-INFER
- Do not infer that this specification authorises implementation to begin. That requires Stage 12 (MVP Implementation Plan) and P1 condition resolution.
- Do not infer that algorithm specifications in this document constitute implementation evidence.
- Do not infer that LOAD_SUCCESS, STRUCTURAL_VALID, or NO_ANOMALY_DETECTED from any fixture test establishes global safety claims.
- Do not infer that the signed canonicalization algorithm ID (`json-canonical-utf8-sort-keys-v1`) is final until SP-003 confirms it.
- Do not infer that REUSE decisions in this document override the Reuse Matrix (07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md).
- Do not infer that any DEFERRED_IN_SCOPE item was assessed and found acceptable.

## NEXT STAGE INPUTS
1. This document: `10_TECHNICAL_SPECIFICATION_SIH26228.md` (complete)
2. `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` — remains the authority on architecture
3. P1 condition resolution records (PRE-01 through PRE-09) — required before MVP plan can be finalised
4. `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md` — binding reuse decisions

## NEXT STAGE
**Stage 12 — MVP Implementation Plan**

The MVP Implementation Plan should:
1. Derive a day-by-day implementation task sequence from the dependency graph in Section 19 of this document.
2. Map each tier to implementation days given the five-day constraint.
3. Name assignees or roles for each task tier.
4. Define testability gates that must pass before a task is considered complete.
5. Identify which P1 conditions must be resolved by Day 0 (before implementation begins).
6. Budget COMP-FIX (hostile fixture suite) as Day 1 P0 task.
7. Budget UNAVAILABLE propagation test suite as Day 1 P0 task alongside fixtures.
8. Define the GitHub repository structure and branching model (one repo; branches = tasks).
9. Identify which tiers can be parallelised across team members.
10. Specify a demo script that exercises the end-to-end pipeline on COMP-FIX synthetic fixtures.

---

# QUALITY CONTROL — STAGE 11 SELF-CHECK

- [x] Architecture matches the approved Option A decision; no new major architecture invented
- [x] All 16 approved components have module paths, class names, method signatures specified
- [x] IPC mechanism specified (named temp file); no ambiguity between two options
- [x] Worker algorithms specified to pseudocode level (Sections 3.3–3.10)
- [x] SQLite DDL complete with CHECK constraints for all invariants (Section 3.15)
- [x] JSON schemas field-by-field with types, required/optional, allowed values (Section 4)
- [x] C5 rule engine fully specified with priority ordering (Section 9.1)
- [x] UNAVAILABLE propagation enforced by priority rule 1 in C5 engine
- [x] ANOMALY ≠ PROVEN ATTACK enforced in C5 output validation
- [x] No aggregate risk score field anywhere in any schema
- [x] weights_only=True enforcement specified with grep test requirement
- [x] RC-013 (no fallback) explicitly implemented in C3D pseudocode
- [x] PF-002 non-claim constant defined; required on every provenance record
- [x] T05d non-claim hardcoded in C2A limitations/non_claims and in C5 engine
- [x] DEFERRED_IN_SCOPE records specified for all 9 deferred method categories
- [x] Signing module specified for both XREG-002 paths (BLOCKED on PRE-02)
- [x] Canonicalization algorithm defined (pending SP-003)
- [x] Replay nonce protection specified (UUID4 + UNIQUE DB constraint)
- [x] Sequence gap detection specified
- [x] Audit chain fail-closed enforcement specified (no swallow of AuditWriteError)
- [x] Safe-loading subprocess isolation specified (resource limits; CWD; env strip)
- [x] All offline dependency requirements specified with CONDITIONAL status (Section 12)
- [x] Target format coverage bounded (Section 13; CONDITIONAL/DEFERRED distinguished)
- [x] Approved reuse integration specified with source paths and attribution requirements (Section 14)
- [x] All configurations named in system_config.yaml; no magic numbers (Section 15)
- [x] Test requirements specified (unit / integration / security / offline / reproducibility) (Section 17)
- [x] Experiment/validation contracts defined with bounded conclusions (Section 18)
- [x] Implementation dependency graph complete (Section 19)
- [x] P1 blocking conditions acknowledged throughout and in NEXT_STAGE_HANDOFF
- [x] No unsupported project result invented
- [x] No claim made beyond demonstrated fixture scope
- [x] NEXT_STAGE_HANDOFF complete

---

**End of document — 10_TECHNICAL_SPECIFICATION_SIH26228.md**
**Stage:** 11 — Technical Specification
**Status:** COMPLETE
**Next stage:** Stage 12 — MVP Implementation Plan (requires P1 conditions resolved first)
