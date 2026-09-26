# NOTICES — Third-Party Attribution

**Status:** ACTIVE — updated as reuse decisions are implemented.

## Required attributions (per Reuse Matrix 07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md)

### R17 — Storage patterns (REUSE-018)
License: MIT
Attribution: Required in source files where R17 patterns are used.
Source: https://github.com/clay-good/origin
Adaptation: SHA-256 streaming and SQLite/WAL setup patterns only; project schema,
supervisor-only write isolation, hash-chain integration, and CHECK constraints are
project-specific.
Status: IMPLEMENTED — TASK-005 source header carries the required attribution.

### R27 — COCO parsing via pycocotools (REUSE-020)
License: BSD
Attribution: Required in source files where pycocotools is used or adapted.
Status: PENDING — TASK-010 (C2A structural worker) will add attribution comment.

## Explicitly excluded packages (no attribution required — not used)

| Package | Reason excluded |
|---------|----------------|
| R13 Alibi-Detect | BSL 1.1 — not open source (NB-06) |
| R04 BackdoorBench | CC BY-NC 4.0 — non-commercial (NB-07) |
| R05 BackdoorBox | GPL-2.0 — copyleft (NB-08) |
| R01 Fabric client | Unconditionally excluded (NB-01, REUSE-015) |

## Verification requirement

Before release: `grep -r 'Fabric\|HyperLedger' assurance_system/ → 0 matches`
See: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md §17 release-critical checklist.
