# Project Status

## Current Milestone

Stage 8 component acceptance includes TASK-018, TASK-019 Part A, and TASK-020. The complete Stage 8 exit gate is not yet accepted.

COMP-CAP now produces bounded scope declarations and 15 explicit missing-coverage records. Its default is `UNAVAILABLE`, and unsupported capabilities are rejected. Operational signing and downstream CLI/orchestrator integration remain pending. The prior Stage 7 exit remains `PASS-WITH-DEFERRED-TASK-022`.

## Completed Components

- TASK-001 through TASK-009: project decisions, repository foundations, configuration, persistence, worker base, schema validation, and fixture infrastructure.
- TASK-010 through TASK-013: C2 data-integrity workers for geometry, exact duplicates, source concentration, and image-level hashing.
- TASK-014: C3A artifact-unit resolver, implemented with ONNX blockers.
- TASK-015: C3B model hasher, implemented with the unresolved ONNX identity-definition blocker.
- TASK-016: C3C ONNX structural validator, implemented with ONNX runtime verification blocked.
- TASK-017: C3D PyTorch safe-loading gate, tested at worker level with TASK-022 integration deferred.
- TASK-018: reference manager with approved R0–R7 gates, FORMAT_ASSET enforcement, staleness transitions, and audited health updates.
- TASK-019 Part A: unsigned provenance construction, canonicalization, replay rejection, sequence recovery, and explicit signing-unavailable handling.
- TASK-020: capability declaration component tested; limitations/non-claims, unsupported requests, schema gating, and store/audit integration verified. CLI acceptance remains conditional on TASK-023.

## Validation Summary

| Area | Result |
|---|---|
| TASK-017 unit tests | 29 passed, 0 failed, 0 skipped |
| TASK-017 security tests | 9 passed, 0 failed, 2 TASK-022 skips |
| SEC-007 guards | 3 passed, 0 failed |
| TASK-020 unit/security tests | 53 passed, 0 failed, 1 TASK-023 CLI skip |
| Full security suite | 61 passed, 0 failed, 6 expected skips |
| Full regression | 385 passed, 0 failed, 28 expected skips |
| FIX-001 hostile pickle | `LOAD_BLOCKED` |
| FIX-015 benign PyTorch model | `LOAD_SUCCESS` |
| Deterministic empty-file case | `LOAD_ERROR` |
| TASK-017 security review | 24 passed, 1 blocked on TASK-022 |

The two TASK-017 skips are SEC-002 and SEC-003. UT-CAP-003 requires the TASK-023 CLI. Skipped cases are not counted as passed.

## Pending Components

- TASK-019 Part B operational signing (blocked on PRE-08).
- TASK-021 interpretation engine.
- TASK-022 supervisor/orchestrator.
- TASK-023 CLI entry points.
- TASK-024 dashboard after GATE-2.
- TASK-025 evidence bundle exporter.
- TASK-026 end-to-end integration.
- TASK-027 target-host offline validation.

Each pending task requires its own dependency review and execution packet.

## Current Blockers

- TASK-022: required for C3D OOM termination/continuation and timeout/responsiveness verification.
- E-2 / SP-002-ONNX: no frozen ONNX artifact-unit definition ID.
- HOST-CAP-003: ONNX is unavailable in the validated repository-local environment.
- PRE-08: operational signing key path and supervisor-only ACL provisioning remain unresolved.
- HOST-CAP-001: native-extension compatibility remains unverified on the target host.
- HOST-CAP-002: Unix resource-limit controls are unavailable on Windows.
- OFFLINE-001: offline installation and zero-egress deployment validation remain pending.
- TASK-023: UT-CAP-003 `list-deferred` display acceptance is unverified until the analyst CLI exists.

## Public Evidence Boundaries

The project does not claim that successful loading, matching hashes, or finite tests establish behavioral safety or global backdoor absence. Unavailable or deferred coverage is reported explicitly and is never converted to a positive assurance state.

Capability declarations explicitly deny malware detection, a model safety guarantee, and complete integrity assurance. M11 remains reference-unavailable and audit-tail completeness remains unavailable. T05d is a permanent non-claim, not a future detection capability.
