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
- C3A artifact-unit resolution, C3B model hashing, and C3C ONNX structural-validation contracts, with their named ONNX blockers retained.
- C3D PyTorch safe-loading gate using one restricted `torch.load` path with `weights_only=True` and `map_location="cpu"`, with no unsafe fallback.
- COMP-REF reference registration, approved R0–R7 gate enforcement, FORMAT_ASSET boundaries, and audited staleness transitions.
- COMP-C4 unsigned provenance records with canonicalization, replay rejection, sequence recovery, and explicit `SIGNING_UNAVAILABLE` status.
- COMP-CAP bounded capability declarations and persisted missing-coverage records with required limitations and non-claims.
- COMP-C5 interpretation, supervisor orchestration, analyst CLI, and read-only evidence export.

## Current Status

Gate-2 is PASS. The supervisor, interpretation, CLI and exporter are implemented; VS-001 through VS-007 have passing evidence. Full TASK-026 validation and Gate-3/Gate-4 remain incomplete.

SEC-003 now passes controlled real-subprocess timeout/termination, persistence, unavailable propagation and pipeline continuation. SEC-002 remains OPEN because the validated Windows host has no enforced child memory cap. A bounded injected MemoryError test is not OOM containment evidence. See [the focused acceptance record](docs/validation/task026_c3d_dispatch_acceptance.md).

TASK-019 Part B signing remains deferred on PRE-08; no signing material or runtime signing is implemented. Capability declarations remain bounded and explicitly deny malware detection, model safety guarantees and complete integrity assurance.

## Validation Evidence

- Focused TASK-022/C3D/base regression: 70 passed, 1 host-blocked skip.
- Security suite: 89 passed, 5 skips, 0 failures.
- Non-offline regression: 485 passed, 12 skips, 0 failures. Offline tests were explicitly excluded; OFF-002 was not rerun.
- Prior full Gate-2 checkpoint: 483 passed, 20 skipped, 0 failures (historical evidence, not this run).
- Target-host TASK-027 offline acceptance is recorded as TESTED for the frozen Windows AMD64 / CPython 3.13.12 tuple. OFF-002's original recovery-marker FAIL and independent restored-state PASS remain distinct.
- Test execution evidence: 2026-09-29; public status reconciled 2026-10-02. Skips are not counted as passed.

## Security Boundaries

- All submitted artifacts are untrusted and must be processed by workers, not the supervisor.
- `weights_only=True` is mandatory; no fallback to unrestricted PyTorch loading is permitted.
- `UNAVAILABLE`, `ASSESSMENT_ERROR`, and `DEFERRED_IN_SCOPE` never mean clean or safe.
- Anomaly and load-block signals do not prove malicious intent.
- Aggregate risk scores and compromise probabilities are prohibited.
- Signing keys and evidence/audit-store write paths remain supervisor-only.
- A successful load or hash match does not establish behavioral safety, semantic equivalence, global backdoor absence, or causal execution proof.

## Known Limitations

- SEC-002 OOM containment remains OPEN under HOST-CAP-002. SEC-003 controlled timeout dispatch is PASS; it does not establish natural hostile-checkpoint hangs or process-tree containment.
- The ONNX artifact-unit definition ID is not frozen, blocking final C3A/C3B ONNX identity acceptance.
- Genuine C3A/C3C ONNX runtime tests pass after descriptor compatibility repair; HOST-CAP-003 formal procedural reconciliation remains pending, separate from E-2 identity-definition acceptance.
- Windows does not provide the Unix `resource.setrlimit` controls used on supported Unix hosts.
- Operational signing awaits target-host key-path and ACL provisioning.
- Capability CLI display is accepted by TASK-023 integration coverage; the historical UT-CAP-003 placeholder remains untouched.
- Capability record and audit writes retain their existing separate commit boundaries; a failure propagates and may leave earlier committed records.
- Target-host offline evidence is bounded to its frozen environment and staged binary set, not a portable deployment claim.
- T05d clean-label poisoning detection is a permanent non-claim under the current baseline.

## Research Documentation

Six protected evaluator-facing research dossiers are tracked under `docs/research/`, covering mission/threat context, data integrity, model security, provenance/cryptography, assurance/drift/evidence, and engineering validation.

## Future Roadmap

Future work requires task-specific authorization: approved resource-containment validation for SEC-002, remaining §18/Gate-4 evidence, operational signing, ONNX identity-definition resolution, and separately authorized dashboard/demo work. Gate-2 does not establish Gate-3 or Gate-4.

For current implementation evidence and blockers, see `PROJECT_STATUS.md` and `PROJECT_STATE.md`.
