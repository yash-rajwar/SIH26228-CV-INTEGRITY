# Changelog

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
