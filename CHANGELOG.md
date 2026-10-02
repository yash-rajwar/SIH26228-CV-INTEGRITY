# Changelog

## E-2 / SP-002-ONNX — Frozen Identity and Gate-3 (validation 2026-10-02)

- Recorded the owner-specified 2026-10-05 decision freezing the existing AC-03
  contract under `onnx-main-referenced-external-data-v1`; execution and decision
  dates are explicit. Complete recursive TensorProto discovery is unchanged.
- C3A now accepts complete contained regular `.onnx` units. The supervisor
  supplies the approved format ID and rejects mismatches. A real missing-file
  test exposed partial diagnostic membership reaching C3B; the handoff now
  requires COMPLETED resolution. No incomplete-unit digest is produced.
- C3B's whole-file ordered inner/outer SHA-256, containment, PF-002 and all
  non-claims are unchanged. No execution, ONNX Runtime or schema change.
- Validation: definition/config 18; C3A/B/C 30/18/18; real identity 10; real
  restricted supervisor 2; SEC-004/005/006 6; SEC-002/003 1 each; SEC-008 2;
  security 92 passed/4 skipped; integration/negative 57 passed/4 skipped;
  non-offline 530 passed/11 skipped, zero failures; universal guards clean.
- C3A/C3B TESTED, E-2 RESOLVED and Gate-3 PASS from the complete MVP checklist.
  Gate-2 PASS preserved; Gate-4 NOT PASSED/not adjudicated; TASK-026 IN PROGRESS;
  PRE-08 PARTIAL; HOST-CAP-003 distinct procedural re-entry pending;
  TASK-024 NOT STARTED. Historical records and protected research retained.
  No OFF/network rerun, package installation or subsequent task execution.

## TASK-026 — Windows Evidence-Store ACL Isolation (2026-10-02)

- Recorded ACC-2026-10-02-02 before implementation: supported Win32 restricted
  primary-token launch, required privileged groups deny-only, maximum privilege
  removal, suspended creation and configured Job assignment before resume.
  Windows has no unrestricted fallback; Unix launch is unchanged.
- Added explicit, reversible deployment-only ACL provisioning for the evidence
  directory/database, preserving SYSTEM recovery, correct SQLite inheritance
  and the original ACL snapshot. No startup provisioning or key/audit ACL changes.
- SEC-008 PASS: trusted supervisor write ALLOWED; production-restricted worker
  marker/database/live-sidecar write and WRITE_DAC attempts DENIED by Windows
  (WinError 5), with unchanged database/sidecar hashes. The original ordinary
  child ALLOWED result is retained, not rewritten.
- Corrected derived-token startup defaults for this Administrator host and the
  assigned-Job termination/reap race. Tests retain IPC, timeout, memory, schema,
  audit, unavailable-state, continuation and no-fallback assertions.
- Validation: token 14 passed; ACL/SEC-008 2 passed; SEC-002 and SEC-003 1 passed
  each; relevant 71 passed; security 92 passed/4 skipped; non-offline regression
  508 passed/11 skipped, zero failures. Universal guards and diff check clean.
- Gate-2 PASS preserved. Gate-3 NOT PASSED: E-2 blocks final C3A/C3B ONNX identity
  acceptance and the all-C3-complete trigger. Gate-4 NOT PASSED; PRE-08 PARTIAL;
  HOST-CAP-003 procedural reconciliation pending; TASK-024 not started.
  No whole-host sandbox claim. No OFF/network operation, package install,
  worker/schema/constant/fixture change or protected research edit.

## TASK-026 — Windows C3D Memory Containment (2026-10-02)

- Formally recorded ACC-2026-10-02-01: Windows workers use per-process
  committed-memory Job Object limits sourced from the existing
  `ResourceLimits.memory_limit_mb` contract; Unix behavior is unchanged.
- Added suspended worker creation, assignment before execution, completion-port
  memory-limit detection, fail-closed Job termination, and
  `KILL_ON_JOB_CLOSE` cleanup to COMP-SUP.
- Replaced the historical SEC-002 capability skip with a bounded real FIX-002
  supervisor acceptance test at 768 MiB. The persisted result is
  `ASSESSMENT_ERROR/MEMORY_LIMIT_EXCEEDED`; C5 remains
  `UNAVAILABLE/UNAVAILABLE_NO_DECISION`; a following FIX-015 asset succeeds.
- Preserved the existing SEC-003 timeout semantics while aligning its harness
  with suspended-create/assign/resume ordering.
- Made two legacy security literal scans platform-neutral; their zero-match
  assertions were not weakened.
- Validation: Job tests 6 passed; SEC-002 1 passed; SEC-003 1 passed; relevant
  regression 51 passed; security 90 passed/4 skipped; non-offline regression
  492 passed/11 skipped, zero failures.
- Gate-2 remains PASS. Gate-3 remains NOT PASSED because SEC-008 OS ACL denial
  evidence is pending; Gate-4 remains NOT PASSED. OFF-002, network state,
  TASK-024, workers, schemas, constants, fixtures and protected research were
  untouched.

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
