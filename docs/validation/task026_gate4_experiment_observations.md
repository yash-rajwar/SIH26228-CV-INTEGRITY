# TASK-026 — Gate-4 experiment observations

Validation date: 2026-10-02. Starting HEAD:
`8ce7569da5a4e88ccc575ff11593245f9af7a3c2`, clean, synchronized
`feature/vertical-slice`. Authority: Architecture §20, Technical Specification
§§17–18 and MVP TASK-026 / §14 Gate-4. This record supplies observations, not
new assessment semantics or a broader capability claim.

Approved target/runtime: Windows build 22631 / AMD64, CPython 3.13.12,
pytest 9.1.1, ONNX 1.23.0, protobuf 7.36.2, Torch 2.10.0+cpu,
pycocotools 2.0.11. The existing adjacent
`SIH26228-CV-INTEGRITY.venv-torch-test` interpreter was used; nothing was
installed or downloaded. No offline/network test was executed.

## Observation method and synthetic acceptance

`tests/integration/test_gate4_validation.py::test_experiment_and_synthetic_export`
uses existing seed-pinned fixture generators, real production subprocess
dispatch, schema validation, supervisor-owned SQLite writes, C5 and the existing
read-only six-document exporter. No worker result is mocked in these ten runs.
Each submission declares the generator's synthetic origin before dispatch;
no persisted record is relabelled afterward.

Every persisted evidence record and applicable C5 finding is synthetic, and
every exported `evidence_records.json` / `findings.json` preserves that label,
nonempty limitations/non-claims and coverage gap. Audit chains verify intact,
terminal `PIPELINE_RUN_COMPLETE` events exist, all 15 explicit missing-coverage
declarations remain exported, and worker temporary directories are cleaned.
SQLite labels are `is_synthetic=1`; finding schema boolean representations are
retained, not replaced by a new schema.

Raw observations in ignored `build/task026-gate4/observations/<fixture-id>.json`
include each fixture manifest (seed, synthetic flag, expected result), the
actual persisted worker record, pipeline summary and complete exported documents.
The standalone runs produce 28 evidence records and 10 findings; additional
combined-asset/injection runs produce 17 evidence records and 5 findings. All
45 evidence records / 15 findings pass the same synthetic propagation checks.
Raw artifacts are local evidence, not claimed to be remotely archived.

## §18.1 — M01 geometry

Seed: **26228** for all three hostile cases and the benign control.
Ground truth comes from the unchanged fixture manifests; all-box coverage is
the exact checked count, not an invented `all_boxes_processed` output field.

| Fixture | Expected violations | Actual result | All-box observation | Synthetic |
|---|---|---|---|---|
| FIX-008 | 9, one of each injected type | COMPLETED; exactly 9; exact manifest type/count map | 10/10 annotations checked | 1 |
| FIX-009-D | 6, one of each injected type | COMPLETED; exactly 6; exact manifest type/count map | 7/7 non-comment labels checked | 1 |
| FIX-009-S | 6, including two polygon-format violations | COMPLETED; exactly 6; exact manifest type/count map | 7/7 non-comment labels checked | 1 |
| FIX-008-CONTROL | 0 | COMPLETED; exactly 0 | 1/1 annotation checked | 1 |

FIX-008 observed types: MISSING_ANNOTATION_FIELD, INVALID_BBOX_FORMAT,
INVALID_NUMERIC_VALUE, NEGATIVE_COORDINATE, NON_POSITIVE_WIDTH,
NON_POSITIVE_HEIGHT, OUT_OF_RANGE_CATEGORY_ID, ORPHAN_ANNOTATION_IMAGE_ID,
NON_POSITIVE_AREA — each count 1.

FIX-009-D observed types: INVALID_CLASS_ID, NEGATIVE_CLASS_ID,
WRONG_FIELD_COUNT, INVALID_NUMERIC_VALUE, OUT_OF_RANGE_COORDINATE,
NON_POSITIVE_DIMENSION — each count 1.

FIX-009-S observed types: INVALID_CLASS_ID 1, NEGATIVE_CLASS_ID 1,
INVALID_POLYGON_FORMAT 2, INVALID_NUMERIC_VALUE 1,
OUT_OF_RANGE_COORDINATE 1.

C5: each hostile geometry run is ANOMALY_DETECTED /
REQUIRES_INVESTIGATION / ESCALATE with the intent non-claim; the benign COCO
control is COMPLETED_STATISTICS_ONLY / STATISTICS_REPORTED /
ACCEPT_WITH_CONTEXT because C2C statistics are present. The frozen vocabulary
is used; stale MVP WITHIN_EXPECTED_PARAMETERS/DETECT aliases are not invented.

**Conclusion:** M01 detects the injected structural/geometry types in these
FIX-008/FIX-009 fixtures. This synthetic population establishes neither
real-world coverage nor semantic poisoning, T05d, or format-conforming abuse
detection. YOLO pose/OBB remain out of MVP scope.

## §18.2 — C3D restricted load

Seed **26228**; manifests specify hostile FIX-001 and benign FIX-015 controls.

| Fixture | Expected | Actual persisted C3D result | Fallback | Synthetic |
|---|---|---|---|---|
| FIX-001 | LOAD_BLOCKED | LOAD_BLOCKED | false | 1 |
| FIX-015 | LOAD_SUCCESS | LOAD_SUCCESS | false | 1 |

FIX-001 C5 is ANOMALY_DETECTED / ESCALATE, not a malicious-intent finding.
FIX-015 C5 remains UNAVAILABLE because reference identity comparison is
unavailable; successful loading is not substituted for assurance. Production
unsafe-load scans remain zero-match; dedicated SEC-007 assertions also run.

**Conclusion:** C3D blocks this hostile pickle class without unsafe fallback.
LOAD_BLOCKED is not proof of attack; LOAD_SUCCESS is not behavioral safety.
These observations are not new SEC-002/003 adjudications; their accepted
target-host memory/timeout results are retained and regression-tested normally.

## §18.3 — C3A containment

Seed **26228**, genuine ONNX protobufs generated by the existing fixture system.

| Fixture / ground truth | Expected | Actual persisted C3A result | Synthetic |
|---|---|---|---|
| FIX-004: absolute external-data location | ONNX_PATH_CONTAINMENT_VIOLATION | ONNX_PATH_CONTAINMENT_VIOLATION | 1 |
| FIX-005: `../../../` traversal location | ONNX_PATH_CONTAINMENT_VIOLATION | ONNX_PATH_CONTAINMENT_VIOLATION | 1 |
| FIX-006: external.bin symlink to a test-owned file outside the asset directory | ONNX_PATH_CONTAINMENT_VIOLATION | ONNX_PATH_CONTAINMENT_VIOLATION | 1 |

The real FIX-006 link setup follows the generator manifest's required setup;
it is not a fake reference/path result. Each run dispatches/persists only C3A:
the containment signal stops the C3 chain and no C3B digest is manufactured.
The seed-26228 FIX-016 benign ONNX control independently reaches C3C
STRUCTURAL_VALID, with all three C3 worker results persisted and labelled.

**Conclusion:** These three injected escape classes are detected. Path-string
and canonical/symlink containment do not prove coverage of every traversal
variant, model behavior, or complete integrity. Existing containment-before-read
and full recursive protobuf traversal tests remain intact.

## §18.4 — Audit corruption

Sources: `tests/unit/test_audit_chain.py::test_ut_aud_002_corruption_is_flagged_without_deletion`,
`test_ut_aud_004_no_destructive_recovery_methods`, and
`tests/security/test_audit_security.py::test_sec_010_modified_event_detected_without_reset`.

Actual observation: deliberately modified chain link/payload digest in
test-owned SQLite stores is detected; integrity becomes false, CHAIN_CORRUPT
is appended, all original event IDs remain, and the modified historical event
is not silently overwritten. No reset/clear/truncate recovery API exists.
The corrupt test chain is intentionally preserved as corrupt, not reported intact.

**Conclusion:** Modification inside the chain body is detected. Tail truncation
cannot be established by this chain alone: COMPLETENESS_UNAVAILABLE remains
explicit. These are test-owned audit fault injections, not application fixture
worker evidence, and no deployed historical audit event was corrupted.

## §18.5 — Unavailable propagation

Sources: `tests/integration/test_vertical_slice.py::test_vs_004_unavailable_propagates_at_every_declared_layer`
and `tests/negative/test_unavailable_propagation.py`. Existing FIX-013 helpers
inject the required ingestion, C2, C3 and C4 failures (plus C5 supplemental
coverage). Ground truth: intentional unavailable evidence, not asset safety.

| Injection point | Expected | Actual |
|---|---|---|
| Ingestion | UNAVAILABLE / UNAVAILABLE_NO_DECISION | UNAVAILABLE / UNAVAILABLE_NO_DECISION |
| C2 | UNAVAILABLE / UNAVAILABLE_NO_DECISION | UNAVAILABLE / UNAVAILABLE_NO_DECISION |
| C3 | UNAVAILABLE / UNAVAILABLE_NO_DECISION | UNAVAILABLE / UNAVAILABLE_NO_DECISION |
| C4 | UNAVAILABLE / UNAVAILABLE_NO_DECISION | UNAVAILABLE / UNAVAILABLE_NO_DECISION |

`test_int_003_c3_unavailable_through_supervisor` additionally injects C3B
UNAVAILABLE after real collection, then uses the actual schema/store/audit/C5
path; evidence, finding and export remain synthetic and UNAVAILABLE. Its raw
report explicitly marks `test_only_injection=true`; it is not misrepresented
as a naturally failing ONNX runtime.

**Conclusion:** At these tested injection points unavailability is not converted
to positive assurance, even when lower-priority anomaly evidence exists.
This is bounded fail-closed rule/contract coverage, not proof about all faults.

## Reproducibility and integration

The separate [Gate-4 evaluation](task026_gate4_evaluation.md) maps every
REPRO-001..006 and INT-001..005 criterion to executed tests. C5 reproducibility
excludes ONLY finding_id and created_at; every other field, including nested
semantics, must match. No UUID or clock code changed. Canonicalization uses the
frozen sorted-key compact JSON / ensure_ascii=True / UTF-8 contract on the
same approved Python version. Unsigned provenance remains SIGNING_UNAVAILABLE;
PRE-08 is not resolved and no key/signature is created.
