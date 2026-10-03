# Project Status

## Current Milestone

SIH26228 MVP / Demo Gate complete (2026-10-03). Gate-2, Gate-3, Gate-4 and
Gate-5 are PASS; TASK-024/026/027 remain TESTED. E-2 / SP-002-ONNX remains
RESOLVED; C3A/B/C/D and SEC-001..012 functional acceptance remain PASS.
ACC-2026-10-02-03 retains read-only audit inspection and trusted corruption
diagnostics. [Gate-5 evidence](docs/validation/gate5_demo_acceptance.md) records
all seven criteria; [demo guide](docs/DEMO_GUIDE.md) provides the presentation
command. Completion is for approved MVP/demo scope, not deferred capabilities.

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
- TASK-024: premium dark, six-view stdlib dashboard; loopback-only default, self-contained/offline with zero npm/CDN dependencies, GET/HEAD-only, manual refresh, text-only untrusted rendering and hash-based CSP. Explicit unavailable/deferred/signing/corruption display; no assurance scoring. Observed pipeline is stored observation only. Visual acceptance is static/CSS review, not browser-rendered inspection (Windows input access denied).
- TASK-026: VS-001..007, all §18 observations, synthetic pipeline/export labels, REPRO-001..006 and INT-001..005 accepted; Gate-4 PASS with existing target-host OFF evidence.
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
| VS / experiment / REPRO / INT / synthetic-export batteries | 7 / 17 / 15 / 6 / 17 passed |
| Audit unit / SEC-010 / CLI | 12 / 1 / 9 passed |
| Dashboard / store / exporter | 27 / 7 / 27 passed |
| Gate-5 focused / real automated demo | 8 passed / PASS, exit 0 |
| Relevant integration/negative regression | 115 passed, 4 skipped, 0 failed |
| Security suite | 92 passed, 4 skipped, 0 failed |
| Non-offline regression | 596 passed, 11 skipped, 0 failed |
| Prior full Gate-2 checkpoint | 483 passed, 20 skipped, 0 failed (historical) |

The current non-offline run explicitly excludes tests/offline and executes no OFF-002/network isolation. All TASK-024 acceptance tests pass, with real-store writes forbidden during display/refresh. The remaining skips are unchanged historical/conditional placeholders, including PRE-08-gated HMAC and non-applicable Ed25519; none count as passes. The prior 552 passed/11 skipped Gate-4 checkpoint and its 22 added validation cases remain historical evidence. [Gate-4 criterion review](docs/validation/task026_gate4_evaluation.md), [§18 observations](docs/validation/task026_gate4_experiment_observations.md), [ONNX identity / Gate-3](docs/validation/e2_onnx_identity_acceptance.md), [SEC-008](docs/validation/task026_sec008_windows_acl.md) and [C3D history](docs/validation/task026_c3d_dispatch_acceptance.md) are unchanged.

## Pending Components

- TASK-019 Part B operational signing (blocked on PRE-08).
- Historical HOST-CAP-003 procedural re-entry remains pending; actual ONNX
  runtime capability passes. Explicit deferred/post-MVP methods remain deferred.

Gate-5 is complete: the real scripts/demo.py run creates two synthetic assets,
retains explicit unavailable/coverage states, verifies read-only HTTP/API and
exports a valid six-document ZIP. Controlled test stores prove CHAIN_CORRUPT
visibility; no live audit chain is damaged. C2B is reconciled to TESTED from its
actual acceptance evidence. R17/R27 notices and REPRO release rows are current.
No production semantics or protected research were changed. Browser-rendered
visual QA is still not claimed. OFF-002 was not rerun.

Each pending task requires its own dependency review and execution packet.

## Current Blockers

- HOST-CAP-003: factual ONNX capability passes, but formal TASK-027-C re-entry remains procedural-pending; its recorded Required Next Action specifies full re-entry with zero-egress evidence, outside this packet. This is not an E-2 or C3 component runtime blocker.
- PRE-08: operational signing key path and supervisor-only ACL provisioning remain unresolved.

The former §18/Gate-4 evidence blocker is closed by the complete criterion
evaluation. PRE-08 and the historical HOST-CAP-003 procedural note remain open;
neither is an invented additional Gate-4 criterion. The accepted OFF-002
acceptance PASS / original recovery-marker FAIL / independent restored-state
PASS remain separate; no offline run or network control was touched.

## Public Evidence Boundaries

The project does not claim that successful loading, matching hashes, or finite tests establish behavioral safety or global backdoor absence. Unavailable or deferred coverage is reported explicitly and is never converted to a positive assurance state.

Capability declarations explicitly deny malware detection, a model safety guarantee, and complete integrity assurance. M11 remains reference-unavailable and audit-tail completeness remains unavailable. T05d is a permanent non-claim, not a future detection capability.
