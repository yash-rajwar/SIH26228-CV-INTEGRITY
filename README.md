# SIH26228-CV-INTEGRITY

SIH 2026 Problem Statement 26228 — Trustworthy Computer Vision Integrity Assurance for Data, Models, and Inference Outputs in Multi-Contributor Pipelines.

## Project Overview

This repository implements an offline-first, evidence-first integrity-assurance pipeline for computer-vision datasets and model artifacts. Deterministic workers examine untrusted inputs in subprocess boundaries and produce schema-controlled evidence without converting unavailable coverage or anomalous signals into positive safety claims.

## Problem Statement

Multi-contributor computer-vision pipelines can receive corrupted labels, duplicated or concentrated data, substituted models, unsafe serialized artifacts, and incomplete provenance. The project provides bounded, reproducible evidence for those conditions while preserving the distinction between an observed anomaly and proof of malicious intent.

## Proposed Solution

The approved design is Option A: Deterministic Integrity Spine + Signed Evidence Governance + Offline-First Supervisor-Worker Architecture. It combines:

- deterministic dataset and artifact checks;
- isolated worker execution for untrusted parsing and loading;
- fail-closed schema validation and audit handling;
- explicit limitations and non-claims on every assessment;
- hash-based identity and provenance evidence without aggregate risk scoring.

## Architecture

The repository follows a supervisor-worker architecture. Workers receive named-file IPC tasks, enforce path containment, and return structured evidence. The supervisor owns persistence, orchestration, signing-key access, audit-chain writes, and timeout/OOM handling. Workers cannot write to the evidence or audit stores.

The architectural authority is `docs/ARCHITECTURE_SPECIFICATION.md`; the build contract is `docs/TECHNICAL_SPECIFICATION.md`; live implementation state is maintained in `PROJECT_STATE.md`.

## Implemented Components

- Repository, exception/constants, configuration, evidence-store, and audit-chain foundations.
- Worker IPC/output base and schema validation.
- Seed-pinned hostile and benign fixture families.
- C2A structural geometry validation, C2B exact duplicate hashing, C2C source-concentration statistics, and C2D image-level SHA-256 identity.
- Tested C3A artifact-unit resolution, C3B ordered whole-member hashing under the frozen ONNX definition, and C3C structural-only ONNX validation; historical procedural reconciliation remains separately documented.
- C3D PyTorch safe-loading gate using one restricted `torch.load` path with `weights_only=True` and `map_location="cpu"`, with no unsafe fallback.
- COMP-REF reference registration, approved R0–R7 gate enforcement, FORMAT_ASSET boundaries, and audited staleness transitions.
- COMP-C4 unsigned provenance records with canonicalization, replay rejection, sequence recovery, and explicit `SIGNING_UNAVAILABLE` status.
- COMP-CAP bounded capability declarations and persisted missing-coverage records with required limitations and non-claims.
- COMP-C5 interpretation, supervisor orchestration, analyst CLI, and read-only evidence export.

## Current Status

Gate-2, Gate-3 and Gate-4 are PASS. TASK-026 is TESTED: VS-001..007, all §18 experiment observations, synthetic storage/export propagation, REPRO-001..006, INT-001..005 and accepted target-host OFF evidence satisfy the all-of Gate-4 checklist. [Gate-4 evaluation](docs/validation/task026_gate4_evaluation.md) and [observations](docs/validation/task026_gate4_experiment_observations.md) bound every conclusion to actual evidence. Gate-5 is NOT PASSED; TASK-024 is NOT STARTED.

E-2 is RESOLVED: `onnx-main-referenced-external-data-v1` freezes the existing referenced-file membership contract. C3A/C3B real ONNX identity and restricted Windows supervisor acceptance pass; all Gate-3 criteria are supported by observed evidence. SEC-002 Job containment, SEC-003 timeout and SEC-008 evidence-store ACL denial remain PASS. See [ONNX identity and final Gate-3 evidence](docs/validation/e2_onnx_identity_acceptance.md), the [historical SEC-008 checkpoint](docs/validation/task026_sec008_windows_acl.md) and [C3D acceptance history](docs/validation/task026_c3d_dispatch_acceptance.md).

TASK-019 Part B signing remains deferred on PRE-08; no signing material or runtime signing is implemented. Capability declarations remain bounded and explicitly deny malware detection, model safety guarantees and complete integrity assurance.

## Validation Evidence

- Windows Job Object unit/capability tests: 6 passed; targeted SEC-002 and retained SEC-003: 1 passed each.
- Restricted-token tests: 14 passed; explicit ACL verification and real SEC-008 acceptance: 2 passed.
- Real ONNX identity acceptance: 10 passed; restricted supervisor acceptance: 2 passed. C3A/C3B/C3C targeted suites: 30/18/18 passed.
- Gate-4 batteries: VS 7, experiments 17, REPRO 15, INT/secret-environment 6, synthetic/export 17 passed. All 22 new validation cases pass; no production change was needed.
- Relevant integration/negative regression: 79 passed, 4 unchanged skips, 0 failures.
- Security suite: 92 passed, 4 historical skips, 0 failures.
- Non-offline regression: 552 passed, 11 unchanged skips, 0 failures. Offline tests were explicitly excluded; OFF-002 was not rerun and no network/PktMon control was touched.
- Prior full Gate-2 checkpoint: 483 passed, 20 skipped, 0 failures (historical evidence, not this run).
- Target-host TASK-027 offline acceptance is recorded as TESTED for the frozen Windows AMD64 / CPython 3.13.12 tuple. OFF-002's original recovery-marker FAIL and independent restored-state PASS remain distinct.
- Current test execution and public status: 2026-10-02. Historical 2026-09-29 timeout evidence is retained. Skips are not counted as passed.

## Security Boundaries

- All submitted artifacts are untrusted and must be processed by workers, not the supervisor.
- `weights_only=True` is mandatory; no fallback to unrestricted PyTorch loading is permitted.
- `UNAVAILABLE`, `ASSESSMENT_ERROR`, and `DEFERRED_IN_SCOPE` never mean clean or safe.
- Anomaly and load-block signals do not prove malicious intent.
- Aggregate risk scores and compromise probabilities are prohibited.
- Signing keys and evidence/audit-store write paths remain supervisor-only.
- A successful load or hash match does not establish behavioral safety, semantic equivalence, global backdoor absence, or causal execution proof.

## Known Limitations

- Windows SEC-002 is bounded to the approved Job Object per-process committed-memory mechanism and validated target; it is not an RSS/RLIMIT_AS or cross-platform claim. SEC-003 controlled timeout dispatch does not establish natural hostile-checkpoint hangs.
- SEC-008 is bounded to the explicitly provisioned evidence-store path on the validated Windows target. Deny-only privileged groups and reduced privileges are not a whole-host filesystem/GUI sandbox; unrelated user-owned paths and trusted elevated administrators are outside this acceptance claim. Audit/reference/key ACLs were not provisioned by this task.
- ONNX membership is frozen for byte identity only: main `.onnx` plus unique canonical referenced whole external files; no behavioral safety, semantic equivalence or trusted-provenance claim.
- Genuine C3A/C3B/C3C ONNX runtime acceptance passes; HOST-CAP-003 formal TASK-027-C procedural re-entry remains pending separately. This packet authorizes no offline/network rerun.
- Windows does not provide the Unix `resource.setrlimit` controls used on supported Unix hosts.
- Operational signing awaits target-host key-path and ACL provisioning.
- Capability CLI display is accepted by TASK-023 integration coverage; the historical UT-CAP-003 placeholder remains untouched.
- Capability record and audit writes retain their existing separate commit boundaries; a failure propagates and may leave earlier committed records.
- Target-host offline evidence is bounded to its frozen environment and staged binary set, not a portable deployment claim.
- T05d clean-label poisoning detection is a permanent non-claim under the current baseline.

## Research Documentation

Six protected evaluator-facing research dossiers are tracked under `docs/research/`, covering mission/threat context, data integrity, model security, provenance/cryptography, assurance/drift/evidence, and engineering validation.

## Future Roadmap

Next logical candidate: TASK-024 dashboard / analyst visual interface preparation for Gate-5, under its own implementation packet; it was not started by Gate-4 reconciliation. Formal host-capability procedural history and operational signing remain separately pending. Gate-4 PASS does not establish demo/Gate-5 acceptance or authorize automatic dashboard/signing work.

For current implementation evidence and blockers, see `PROJECT_STATUS.md` and `PROJECT_STATE.md`.
