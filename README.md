# SIH26228-CV-INTEGRITY

**SIH 2026 · Problem Statement 26228**
**Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines**

---

## Status

**Repository skeleton — implementation has not begun.**

This repository was initialized as Stage 13 of the project workflow.
Implementation follows the approved architecture and technical specification.

| Stage | Document | Status |
|-------|----------|--------|
| Architecture Specification | `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` | APPROVED |
| Technical Specification | `10_TECHNICAL_SPECIFICATION_SIH26228.md` | COMPLETE |
| MVP Implementation Plan | `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md` | COMPLETE |
| Repository Setup | This repository | SKELETON |
| Implementation | — | NOT STARTED — pending P1 conditions |

---

## Approved Architecture

**Option A — Deterministic Integrity Spine + Signed Evidence Governance + Offline-First Supervisor-Worker Architecture**

Approval: Project-owner verbal confirmation, 2026-09-25.

---

## Governing Invariants (Absolute — No Exception)

```
UNAVAILABLE ≠ CLEAN
NOT_ASSESSED ≠ CLEAN
DEFERRED_IN_SCOPE ≠ CLEAN
anomaly ≠ malicious intent
ANOMALY ≠ PROVEN_ATTACK
raw detector score ≠ compromise probability
hash match ≠ safe ≠ semantically equivalent (PF-002)
finite test coverage ≠ global backdoor absence
```

---

## Before Implementation Begins

**P1 conditions must be resolved first (TASK-001):**

- PRE-01: Target host (OS, Python version, CPU, RAM) — hard gate
- PRE-04: SP-003 vocabulary contract — hard gate
- PRE-05: Mandatory format list — hard gate
- PRE-02, PRE-03, PRE-06, PRE-07, PRE-08, PRE-09: See §10 §1.4

---

## Quick Start (after P1 conditions resolved)

```bash
# Structure verification (works now, on skeleton):
python -m pytest tests/test_repository_structure.py -v

# Security invariant checks (weights_only=False and risk_score grep):
python -m pytest tests/security/test_security_invariants.py -v

# All tests (skipped stubs expected; 0 failures on skeleton):
python -m pytest tests/ -v
```

See `docs/SETUP.md` for full setup instructions.

---

## Project Documents

Place copies of the following in `docs/`:
- `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`
- `10_TECHNICAL_SPECIFICATION_SIH26228.md`
- `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`

Do not edit these copies. The master documents are the authorities.

---

## What This System Does NOT Claim

- Does not produce an aggregate risk score or compromise probability (absolutely prohibited).
- Does not claim T05d clean-label poisoning detection (permanent non-claim).
- Does not claim global backdoor absence from any finite fixture test.
- Does not claim that UNAVAILABLE or DEFERRED_IN_SCOPE means no threat is present.
- Does not claim that a valid provenance signature proves the model executed the assessed inferences (PF-002).

---

## Branch Convention

See `docs/BRANCH_NAMING.md`. Branches represent tasks — not devices, locations, or agents.
