# Changelog

## Stage 8 — Supervisor Component Milestones

### Added

- TASK-020 COMP-CAP bounded scope declarations with an `UNAVAILABLE` default, explicit method selection, immutable limitations/non-claims, and unsupported-request rejection.
- Schema-gated persistence of 15 coverage-gap records through the existing store API, with capability-declaration and per-record audit events.
- TASK-020 unit/security coverage for schema conformance, permanent T05d non-claims, unavailable states, unsupported assurance claims, and write/audit failures.
- Public documentation of previously committed TASK-018 reference management and TASK-019 Part A unsigned provenance acceptance.

### Changed

- Synchronized public status with the current Stage 8 component evidence.
- Preserved architecture-specific reference/tail unavailable states and permanent T05d semantics in the existing deferred-record schema.
- Workers, provenance, signing, schemas, constants, and protected research documentation were unchanged by TASK-020.

### Validation

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
- The complete Stage 8 exit gate remains unaccepted.

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
