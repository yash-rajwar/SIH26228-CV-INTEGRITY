# Changelog

## TASK-026 — Focused C3D Dispatch Acceptance (2026-10-02 reconciliation)

- SEC-003 passes real child timeout/termination, schema-gated evidence persistence,
  audit integrity, UNAVAILABLE finding propagation and subsequent-asset completion.
- Corrected timeout cleanup at the existing dispatcher: drain/reap communication
  after kill before removing the child working directory. No timeout, memory-cap,
  worker, schema or trust-boundary redesign.
- Added bounded MemoryError integration coverage explicitly distinguished from
  SEC-002 OOM acceptance. SEC-002 remains OPEN under HOST-CAP-002; no over-limit
  fixture was loaded without enforced containment.
- Preserved 2026-09-29 validation: relevant 70 passed/1 skipped; security 89 passed/5
  skipped; non-offline regression 485 passed/12 skipped, zero failures. Existing
  Git grep was exposed in the test-shell PATH; no packages were installed.
- Gate-2 PASS preserved. Gate-3/Gate-4, PRE-08, E-2 and HOST-CAP-003 remain open.
  No offline execution, network changes, dashboard work or research-doc edits.
- Updated public status summaries from their stale Stage 8 checkpoint. Historical
  entries below remain unchanged. Detailed observations are in
  docs/validation/task026_c3d_dispatch_acceptance.md.

## Stage 8 — Component Implementation Complete

### Added

- TASK-020 COMP-CAP bounded scope declarations with an `UNAVAILABLE` default, explicit method selection, immutable limitations/non-claims, and unsupported-request rejection.
- Schema-gated persistence of 15 coverage-gap records through the existing store API, with capability-declaration and per-record audit events.
- TASK-020 unit/security coverage for schema conformance, permanent T05d non-claims, unavailable states, unsupported assurance claims, and write/audit failures.
- Public documentation of previously committed TASK-018 reference management and TASK-019 Part A unsigned provenance acceptance.

### Changed

- Completed the Stage 8 component exit review: TASK-018, TASK-019 Part A, and TASK-020 are TESTED; TASK-019 Part B is DEFERRED on PRE-08.
- Synchronized public status with the current Stage 8 component evidence.
- Preserved architecture-specific reference/tail unavailable states and permanent T05d semantics in the existing deferred-record schema.
- Workers, provenance, signing, schemas, constants, and protected research documentation were unchanged by TASK-020.

### Validation

- TASK-018 tests: 7 passed, 0 failed.
- TASK-019 Part A tests: 7 passed, 0 failed, 2 expected conditional signing skips.
- TASK-020 unit/security tests: 53 passed, 0 failed, 1 named TASK-023 CLI skip.
- Prerequisite constants/store/schema regression: 21 passed.
- Full security suite: 61 passed, 0 failed, 6 expected skips.
- Full regression: 385 passed, 0 failed, 28 expected skips.
- Universal production security scans, import audit, and protected-file scope checks passed.

### Remaining

- UT-CAP-003 `list-deferred` integration requires TASK-023 and is not counted as passed.
- TASK-019 Part B operational signing remains blocked on PRE-08; TASK-020 implemented no signing logic.
- TASK-021 interpretation, TASK-022 orchestration, CLI/export, end-to-end integration, and offline acceptance remain pending.
- E-2 and HOST-CAP-003 retain their ONNX identity/runtime blockers; C3C is excluded from declared supported capabilities.
- Existing store/audit commit boundaries are unchanged; write failures propagate without claiming batch atomicity.
- Stage 8 component implementation is complete; deferred signing, CLI, orchestrator, ONNX, and integration blockers remain explicitly open.

## Stage 7 — C3D PyTorch Safe-Loading Gate

### Added

- COMP-W-C3D worker for restricted PyTorch artifact loading.
- Worker-level tests for hostile, benign, error, validation, and security-boundary paths.
- Non-skippable SEC-007 guards for exact and broad unsafe-loading patterns.

### Changed

- Corrected the TASK-017 subprocess test harness to validate both process return codes and emitted fail-closed result JSON.
- Updated public status documentation to reflect the implemented C2/C3 worker state and current evidence boundaries.
- Production C3D semantics were not changed during the test-harness correction.

### Validation

- TASK-017 unit suite: 29 passed, 0 failed, 0 skipped.
- TASK-017 security suite: 9 passed, 0 failed, 2 TASK-022 skips.
- SEC-007: 3 passed, 0 failed.
- Full regression: 318 passed, 0 failed, 25 expected skips.
- FIX-001 returned `LOAD_BLOCKED`; FIX-015 returned `LOAD_SUCCESS`; deterministic empty-file input returned `LOAD_ERROR`.
- Universal production security guards passed.

### Remaining

- SEC-002 and SEC-003 remain deferred until TASK-022 implements real supervisor dispatch, timeout, and OOM handling.
- E-2 and HOST-CAP-003 continue to block final ONNX identity/runtime acceptance.
- PRE-08 continues to block operational signing-key provisioning.
- Offline installation and zero-egress validation remain pending.
