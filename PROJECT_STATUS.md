# Project Status

## Current Milestone

Gate-2 and Gate-3 are PASS. TASK-026 remains IN PROGRESS; Gate-4 is NOT PASSED and was not adjudicated here. E-2 / SP-002-ONNX is RESOLVED by the owner-frozen definition and real C3A/C3B identity acceptance. SEC-002, SEC-003 and SEC-008 real target-host acceptance remain PASS.

The dispatcher creates Windows workers suspended under a restricted primary token, assigns the existing configured Job, then resumes them without an unrestricted fallback. Explicit deployment-only evidence ACLs deny real worker writes while supervisor persistence and normal IPC succeed. Memory/timeout semantics remain unchanged. This is committed-memory enforcement and a scoped evidence-path DACL boundary, not an RSS/RLIMIT_AS or whole-host sandbox claim.

## Completed Components

- TASK-001 through TASK-009: project decisions, repository foundations, configuration, persistence, worker base, schema validation, and fixture infrastructure.
- TASK-010 through TASK-013: C2 data-integrity workers for geometry, exact duplicates, source concentration, and image-level hashing.
- TASK-014: C3A artifact-unit resolver TESTED; frozen `onnx-main-referenced-external-data-v1`, complete recursive reference discovery and containment/incomplete-unit checks pass.
- TASK-015: C3B model hasher TESTED; real ONNX whole-member identity acceptance passes with the unchanged ordered inner/outer SHA-256 algorithm.
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
| Restricted primary-token tests | 14 passed |
| Deployment ACL / real SEC-008 | 2 passed |
| SEC-002 exact containment | 1 passed |
| SEC-003 targeted dispatch | 1 passed |
| Definition/configuration | 18 passed |
| C3A / C3B / C3C targeted | 30 / 18 / 18 passed |
| Real ONNX identity / restricted supervisor | 10 / 2 passed |
| Relevant integration/negative regression | 57 passed, 4 skipped, 0 failed |
| Security suite | 92 passed, 4 skipped, 0 failed |
| Non-offline regression | 530 passed, 11 skipped, 0 failed |
| Prior full Gate-2 checkpoint | 483 passed, 20 skipped, 0 failed (historical) |

The non-offline run explicitly excludes tests/offline and executes no OFF-002/network isolation. The remaining skips are unchanged historical/conditional placeholders, including PRE-08-gated HMAC and non-applicable Ed25519; none count as passes. [ONNX identity and final Gate-3 adjudication](docs/validation/e2_onnx_identity_acceptance.md) accompanies ignored `build/e2-onnx/` reports. [SEC-008 observations and prior Gate-3 decision](docs/validation/task026_sec008_windows_acl.md), [earlier C3D observations](docs/validation/task026_c3d_dispatch_acceptance.md) and their local reports remain historical evidence.

## Pending Components

- TASK-019 Part B operational signing (blocked on PRE-08).
- TASK-024 dashboard: dependency-eligible after Gate-2, not authorized by this packet.
- TASK-026: §18/Gate-4 observed-result reconciliation remains incomplete; E-2 and the all-C3-complete Gate-3 trigger are now satisfied.

Each pending task requires its own dependency review and execution packet.

## Current Blockers

- HOST-CAP-003: factual ONNX capability passes, but formal TASK-027-C re-entry remains procedural-pending; its recorded Required Next Action specifies full re-entry with zero-egress evidence, outside this packet. This is not an E-2 or C3 component runtime blocker.
- PRE-08: operational signing key path and supervisor-only ACL provisioning remain unresolved.
- §18/Gate-4: remaining observed-result records and full validation acceptance require separate reconciliation.

## Public Evidence Boundaries

The project does not claim that successful loading, matching hashes, or finite tests establish behavioral safety or global backdoor absence. Unavailable or deferred coverage is reported explicitly and is never converted to a positive assurance state.

Capability declarations explicitly deny malware detection, a model safety guarantee, and complete integrity assurance. M11 remains reference-unavailable and audit-tail completeness remains unavailable. T05d is a permanent non-claim, not a future detection capability.
