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

## Current Status

Stage 8 component implementation is complete: TASK-018, TASK-019 Part A, and TASK-020 are tested. Capability declarations default to `UNAVAILABLE`, accept only explicit bounded operations, and report 15 coverage gaps, including permanent T05d non-claims. They do not establish malware detection, model safety, or complete integrity assurance.

The Stage 8 component exit review passed with carried blockers. TASK-019 Part B operational signing remains deferred on PRE-08; no signing key material or runtime signature generation is present. Capability CLI display awaits TASK-023. The pipeline orchestrator and end-to-end integration remain pending, and C3D supervisor-level OOM/timeout verification still requires TASK-022.

## Validation Evidence

- TASK-017 unit tests: 29 passed, 0 failed, 0 skipped.
- TASK-017 security tests: 9 passed, 0 failed, 2 TASK-022 skips.
- SEC-007 unsafe-fallback guards: 3 passed, 0 failed.
- TASK-018 tests: 7 passed, 0 failed.
- TASK-019 Part A tests: 7 passed, 0 failed, 2 expected conditional signing skips.
- TASK-020 unit/security tests: 53 passed, 0 failed, 1 TASK-023 CLI skip.
- Full security suite: 61 passed, 0 failed, 6 expected skips.
- Full repository regression: 385 passed, 0 failed, 28 expected dependency/task-gated skips.
- FIX-001: `LOAD_BLOCKED` through the restricted worker path.
- FIX-015: `LOAD_SUCCESS` through the restricted worker path.
- Deterministic empty-file case: `LOAD_ERROR`.

## Security Boundaries

- All submitted artifacts are untrusted and must be processed by workers, not the supervisor.
- `weights_only=True` is mandatory; no fallback to unrestricted PyTorch loading is permitted.
- `UNAVAILABLE`, `ASSESSMENT_ERROR`, and `DEFERRED_IN_SCOPE` never mean clean or safe.
- Anomaly and load-block signals do not prove malicious intent.
- Aggregate risk scores and compromise probabilities are prohibited.
- Signing keys and evidence/audit-store write paths remain supervisor-only.
- A successful load or hash match does not establish behavioral safety, semantic equivalence, global backdoor absence, or causal execution proof.

## Known Limitations

- SEC-002 OOM dispatch and SEC-003 timeout dispatch require TASK-022 and remain unverified.
- The ONNX artifact-unit definition ID is not frozen, blocking final C3A/C3B ONNX identity acceptance.
- ONNX is unavailable in the validated repository-local environment, so genuine C3A/C3C protobuf runtime tests remain skipped with a named blocker.
- Windows does not provide the Unix `resource.setrlimit` controls used on supported Unix hosts.
- Operational signing awaits target-host key-path and ACL provisioning.
- UT-CAP-003 `list-deferred` CLI acceptance awaits TASK-023; capability declarations and store records are tested at component level.
- Capability record and audit writes retain their existing separate commit boundaries; a failure propagates and may leave earlier committed records.
- Offline installation and zero-egress deployment validation remain future acceptance work.
- T05d clean-label poisoning detection is a permanent non-claim under the current baseline.

## Research Documentation

Six protected evaluator-facing research dossiers are tracked under `docs/research/`, covering mission/threat context, data integrity, model security, provenance/cryptography, assurance/drift/evidence, and engineering validation.

## Future Roadmap

Future work remains subject to task-specific entry gates. Pending work includes operational signing, interpretation, supervisor orchestration, CLI integration, evidence export, end-to-end validation, and target-host offline validation.

For current implementation evidence and blockers, see `PROJECT_STATUS.md` and `PROJECT_STATE.md`.
