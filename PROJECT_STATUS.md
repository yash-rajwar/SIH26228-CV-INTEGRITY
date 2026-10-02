# Project Status

## Current Milestone

Gate-2 is PASS. TASK-026 remains IN PROGRESS; Gate-3 and Gate-4 are not passed. SEC-002 Windows Job Object containment and SEC-003 controlled supervisor timeout acceptance both pass. Gate-3 remains blocked by pending SEC-008 OS ACL denial evidence.

The dispatcher now creates Windows workers suspended, assigns them to a per-worker Job Object using the existing memory-limit contract, then resumes them. Real FIX-002 enforcement, schema/store/audit/C5 integration, cleanup, and a subsequent benign asset complete without converting failure into positive assurance. This is committed-memory enforcement, not an RSS/RLIMIT_AS claim.

## Completed Components

- TASK-001 through TASK-009: project decisions, repository foundations, configuration, persistence, worker base, schema validation, and fixture infrastructure.
- TASK-010 through TASK-013: C2 data-integrity workers for geometry, exact duplicates, source concentration, and image-level hashing.
- TASK-014: C3A artifact-unit resolver, implemented with ONNX blockers.
- TASK-015: C3B model hasher, implemented with the unresolved ONNX identity-definition blocker.
- TASK-016: C3C ONNX structural validator, tested after ONNX/protobuf compatibility repair; formal host-capability reconciliation remains pending.
- TASK-017: C3D restricted-load worker tested; SEC-002 and SEC-003 controlled supervisor integration PASS on the validated Windows target.
- TASK-018: reference manager with approved R0–R7 gates, FORMAT_ASSET enforcement, staleness transitions, and audited health updates.
- TASK-019 Part A: unsigned provenance construction, canonicalization, replay rejection, sequence recovery, and explicit signing-unavailable handling.
- TASK-020: bounded capability declaration tested; downstream CLI display accepted by TASK-023 integration coverage.
- TASK-021, TASK-022, TASK-023 and TASK-025: interpretation, supervisor, CLI and read-only exporter tested.
- TASK-027: offline validation recorded TESTED for the frozen Windows AMD64 / CPython 3.13.12 tuple. OFF-002 acceptance PASS, historical recovery-marker FAIL and independent final-state PASS remain separate.

## Validation Summary

| Area | Result |
|---|---|
| Windows Job Object unit/capability | 6 passed |
| SEC-002 exact containment | 1 passed |
| SEC-003 targeted dispatch | 1 passed |
| TASK-022/C3D regression | 51 passed, 0 failed |
| Security suite | 90 passed, 4 skipped, 0 failed |
| Non-offline regression | 492 passed, 11 skipped, 0 failed |
| Prior full Gate-2 checkpoint | 483 passed, 20 skipped, 0 failed (historical) |

The non-offline run explicitly excludes tests/offline and executes no OFF-002/network isolation. SEC-002 is no longer skipped; the remaining skips are unchanged historical/conditional placeholders, including PRE-08-gated HMAC and non-applicable Ed25519. Skips are not passed. [Focused observations, limitations and hashes](docs/validation/task026_c3d_dispatch_acceptance.md) are committed; raw local JUnit/SQLite evidence remains in ignored `build/task027-sec002/`.

## Pending Components

- TASK-019 Part B operational signing (blocked on PRE-08).
- TASK-024 dashboard: dependency-eligible after Gate-2, not authorized by this packet.
- TASK-026: SEC-008 ACL acceptance and §18/Gate-4 observed-result reconciliation remain incomplete.

Each pending task requires its own dependency review and execution packet.

## Current Blockers

- SEC-008: no accepted target-host evidence yet demonstrates that an OS-level evidence-store ACL denies a non-supervisor process; this blocks Gate-3.
- E-2 / SP-002-ONNX: no frozen ONNX artifact-unit definition ID.
- HOST-CAP-003: genuine ONNX tests pass, but formal procedural reconciliation remains pending.
- PRE-08: operational signing key path and supervisor-only ACL provisioning remain unresolved.
- §18/Gate-4: remaining observed-result records and full validation acceptance require separate reconciliation.

## Public Evidence Boundaries

The project does not claim that successful loading, matching hashes, or finite tests establish behavioral safety or global backdoor absence. Unavailable or deferred coverage is reported explicitly and is never converted to a positive assurance state.

Capability declarations explicitly deny malware detection, a model safety guarantee, and complete integrity assurance. M11 remains reference-unavailable and audit-tail completeness remains unavailable. T05d is a permanent non-claim, not a future detection capability.
