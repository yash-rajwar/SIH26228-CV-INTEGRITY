# PROJECT_STATE.md
## SIH 2026 · PS 26228 — Live Implementation State

**This file describes where the implementation is now.**  
**It does NOT redefine what the architecture is.**  
Architecture authority remains `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`.

Update this file at the end of every coding session before committing.

---

## PROJECT

**Name:** Trustworthy Computer Vision Integrity Assurance — SIH 2026 PS 26228  
**Current stage:** Implementation (Codex + Antigravity)  
**Repository created:** [DATE TO BE FILLED ON REPO INIT]  
**Five-day window start:** [DATE — begins after P1 conditions resolved]

---

## CURRENT ARCHITECTURE REFERENCE

**Approved architecture:** Option A — Deterministic Integrity Spine + Signed Evidence Governance + Offline-First Supervisor-Worker Architecture  
**Architecture specification:** `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` (approved 2026-09-25)  
**Technical specification:** `10_TECHNICAL_SPECIFICATION_SIH26228.md`  
**MVP implementation plan:** `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`  
**Reuse matrix:** `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md`  
**Architecture change control:** ACTIVE — no silent redesign permitted

---

## CURRENT IMPLEMENTATION STATUS

Status codes: `NOT STARTED` | `IN PROGRESS` | `IMPLEMENTED` | `TESTED` | `VALIDATED` | `BLOCKED` | `DEFERRED`

| Component | Module | Status | Notes |
|---|---|---|---|
| P1 condition resolution | TASK-001 | `BLOCKED` | PRE-01, PRE-04, PRE-05 are hard gates; must complete before implementation begins |
| Repository skeleton | TASK-002 | `NOT STARTED` | Awaiting PRE-04 minimum |
| exceptions.py + constants.py | TASK-003 | `NOT STARTED` | |
| Config system | TASK-004 | `NOT STARTED` | |
| Evidence store (SQLite, WAL) | TASK-005 | `NOT STARTED` | BLOCKED until PRE-04 (schema version) |
| Audit chain writer | TASK-006 | `NOT STARTED` | |
| Worker base (IPC, resource limits) | TASK-007 | `NOT STARTED` | |
| Schema validator + JSON schemas | TASK-008 | `NOT STARTED` | BLOCKED until PRE-04 |
| Hostile fixture suite (P0) | TASK-009 | `NOT STARTED` | Must build before any security test |
| COMP-W-C2A (all-box structural) | TASK-010 | `NOT STARTED` | BLOCKED on PRE-05 for YOLO variants |
| COMP-W-C2B (exact hash) | TASK-011 | `NOT STARTED` | |
| COMP-W-C2C (concentration) | TASK-012 | `NOT STARTED` | |
| COMP-W-C2D (image hash) | TASK-013 | `NOT STARTED` | |
| COMP-W-C3A (artifact-unit resolver) | TASK-014 | `NOT STARTED` | BLOCKED on PRE-03 for PyTorch path |
| COMP-W-C3B (model hasher) | TASK-015 | `NOT STARTED` | Depends on TASK-014 |
| COMP-W-C3C (ONNX structural) | TASK-016 | `NOT STARTED` | |
| COMP-W-C3D (PyTorch safe-load gate) | TASK-017 | `NOT STARTED` | BLOCKED on PRE-01 (torch wheel), PRE-05 |
| COMP-REF (reference manager) | TASK-018 | `NOT STARTED` | All references UNAVAILABLE at MVP start |
| COMP-C4 (provenance + signing) | TASK-019 | `NOT STARTED` | BLOCKED on PRE-02 + PRE-04 + PRE-08 + PRE-09 |
| COMP-CAP (capability declaration) | TASK-020 | `NOT STARTED` | |
| COMP-C5 (interpretation engine) | TASK-021 | `NOT STARTED` | BLOCKED on PRE-04 |
| COMP-SUP (orchestrator) | TASK-022 | `NOT STARTED` | Depends on all workers and supervisor components |
| CLI entry points | TASK-023 | `NOT STARTED` | |
| Dashboard (SHOULD BUILD) | TASK-024 | `NOT STARTED` | Antigravity — begins after GATE-2 |
| Evidence bundle exporter | TASK-025 | `NOT STARTED` | |
| End-to-end integration test | TASK-026 | `NOT STARTED` | Gate task |
| Offline validation (target host) | TASK-027 | `BLOCKED` | Hard-blocked on PRE-01 |

---

## CURRENT TASK

```
TASK: TASK-001 — P1 Condition Resolution
Owner: Project owner / team
Branch: (no implementation branch — decisions, not code)
Started: [DATE]
Status: BLOCKED — must complete before implementation begins

Required decisions:
  PRE-01: Target host (OS, Python version, CPU arch, RAM)
  PRE-02: XREG-002 — HMAC-SHA256 vs Ed25519 signing mechanism
  PRE-03: SP-002 — PyTorch artifact-unit definitions
  PRE-04: SP-003 — Evidence vocabulary contract + schema version freeze
  PRE-05: Mandatory format list (YOLO task variants; PyTorch in/out of scope)
  PRE-06: SP-001 — Reference-health gate procedure
  PRE-07: GAP-011 — Inference record source
  PRE-08: SP-004 — Crypto profile (signing algorithm parameters)
  PRE-09: SP-006 — C3→C4 adapter schema

Hard gates (PRE-01, PRE-04, PRE-05): implementation MUST NOT begin until these are resolved.
Secondary gates (PRE-02, PRE-03, PRE-06 through PRE-09): can be resolved by Day 1 end;
  affected components begin with placeholder shells.
```

---

## COMPLETED WORK

*(None — repository just created)*

| Task | What was done | Tests | Commit |
|---|---|---|---|
| — | — | — | — |

---

## CURRENT BLOCKERS

| Blocker ID | Description | Affects | Resolution owner |
|---|---|---|---|
| PRE-01 | Target host not confirmed — no offline claim permissible; wheel staging impossible; subprocess isolation mechanism TBD | TASK-027; TASK-017; TASK-010 (pycocotools); all offline claims | Project owner / organizer |
| PRE-02 | XREG-002 signing mechanism not decided (HMAC-SHA256 vs Ed25519) | TASK-019 (C4 signing) | Project owner |
| PRE-03 | SP-002 artifact-unit definitions not produced | TASK-014 (C3A PyTorch path); TASK-015 (C3B) | Project team |
| PRE-04 | SP-003 vocabulary contract not produced; schema version not frozen | TASK-005; TASK-008; TASK-019; TASK-021; all cross-layer integration | Project team (pre-implementation design session) |
| PRE-05 | Mandatory format list not confirmed — YOLO task variants and PyTorch scope unknown | TASK-010 (YOLO variants); TASK-017 (C3D scope) | Project owner / organizer |
| PRE-06 | SP-001 reference-health gate procedure not produced | TASK-018 (full gate enforcement) | Project team |
| PRE-07 | GAP-011 inference record source not decided | Inference-record ingestion path | Organizer |
| PRE-08 | SP-004 crypto profile not produced | TASK-019 signing algorithm parameters | Project team |
| PRE-09 | SP-006 C3→C4 adapter schema not produced | TASK-019 evidence-to-provenance binding | Project team |

---

## KNOWN LIMITATIONS

*(At repository creation — to be updated as implementation progresses)*

- No capabilities are implemented yet. All assessment states are `NOT STARTED`.
- Offline capability claim is not permissible until PRE-01 is resolved and TASK-027 passes on the actual target host.
- T05d clean-label poisoning coverage gap is a **permanent** non-claim. This will never change under the current baseline.
- All references are UNAVAILABLE at MVP start. No reference-relative assessments are possible.
- TorchScript loading is DEFERRED_IN_SCOPE — isolated worker not yet demonstrated on any target.
- C4 signing will ship as SIGNING_UNAVAILABLE shell until PRE-02 + PRE-04 + PRE-08 + PRE-09 are all resolved.
- Analyst authentication is UNAVAILABLE — `analyst_id = 'UNAVAILABLE'` on all analyst disposition events until OQ-017 is resolved.

---

## LATEST VALIDATED COMMIT

```
Commit: (none — repository just created)
Branch: main
Date: [REPO INIT DATE]
Tests: N/A
```

---

## LAST TEST STATUS

```
Date: N/A — no tests run yet
Tests passed: 0 / 0
Tests blocked: All (no implementation; P1 conditions unresolved)
Security grep checks: N/A

Integration gates:
  GATE-1 (Foundation):       NOT PASSED
  GATE-2 (Vertical Slice):   NOT PASSED
  GATE-3 (Capability):       NOT PASSED
  GATE-4 (Validation):       NOT PASSED
  GATE-5 (Demo):             NOT PASSED
```

---

## NEXT TASK

**Recommended next task after TASK-001 resolution:** TASK-002 (Repository Skeleton)

Critical path reminder:
```
PRE-04 resolved
  → TASK-002 (repository skeleton)
  → TASK-003 (exceptions + constants)
  → TASK-004 (config system)
  → TASK-005 (evidence store) [+ TASK-007 worker base, TASK-009 fixtures in parallel]
  → TASK-008 (schema validator)
  → TASK-010–TASK-013 (C2 workers, parallel)
  → TASK-014–TASK-017 (C3 workers)
  → TASK-018–TASK-021 (supervisor components)
  → TASK-022 (orchestrator)
  → TASK-023 (CLI)
  → TASK-026 (vertical slice integration — GATE-2)
```

**After GATE-2 passes:** Antigravity begins TASK-024 (dashboard). Codex continues with TASK-025, TASK-026 security battery, TASK-027.

---

## PENDING DECISIONS

*(Only genuine project decisions — not implementation questions)*

| Decision | Description | Owner | Priority |
|---|---|---|---|
| PRE-01 | Target host specification | Project owner / organizer | P0 — hard gate |
| PRE-02 / XREG-002 | Signing mechanism: HMAC-SHA256 vs Ed25519 | Project owner | P1 |
| PRE-03 / SP-002 | PyTorch artifact-unit definitions | Project team | P1 |
| PRE-04 / SP-003 | Evidence vocabulary contract + schema version freeze | Project team | P0 — hard gate |
| PRE-05 / GAP-013 | Mandatory format list | Project owner / organizer | P0 — hard gate |
| PRE-06 / SP-001 | Reference-health gate procedure (R0–R7) | Project team | P1 |
| PRE-07 / GAP-011 | Inference record source | Organizer | P1 |
| PRE-08 / SP-004 | Crypto profile (algorithm parameters) | Project team | P1 |
| PRE-09 / SP-006 | C3→C4 adapter schema | Project team | P1 |
| OQ-017 | Analyst authentication and authority hierarchy | Project owner | Post-MVP |
| OQ-018 | Evidence retention policy | Project owner | Post-MVP |
| AF-003 | Trusted clock source | Deployment environment | Post-MVP |
| GAP-010 / XREG-010 | M15 (image hash) evidence ownership — C2 or C3? | Project owner | Before TASK-013 completes |

---

## HANDOFF NOTES

*(To be filled by the agent ending a session — for the agent starting the next session)*

**Current session:** Repository just created. No implementation has begun.

**What the next agent needs to know:**
- Implementation MUST NOT begin until PRE-01, PRE-04, and PRE-05 are resolved (hard gates).
- TASK-001 is the first and only current task. It produces written decision records, not code.
- After P1 conditions are resolved, start with TASK-002 through TASK-009 in dependency order (Tier 1 and Tier 2 in §11 Section 8).
- TASK-009 (hostile fixture suite) is a P0 task and must not be deferred to make room for feature work.
- The weights_only=False grep check (SEC-007) must be set up in CI from Day 1 and must never pass with a match.
- Signing (TASK-019) will ship as SIGNING_UNAVAILABLE shell until PRE-02 + PRE-04 + PRE-08 + PRE-09 are all resolved. This is expected and does not block the pipeline.
- Antigravity begins AFTER GATE-2 passes — not before.

**Architecture change control:** ACTIVE. Any conflict between implementation and specification must be raised as a proposed change here before being resolved in code.

---

## STATE UPDATE INSTRUCTIONS

When updating this file:

1. **CURRENT TASK** — update to reflect what task is actively being worked.
2. **COMPLETED WORK** — add a row for every task that was finished (including commit hash).
3. **CURRENT IMPLEMENTATION STATUS** — update the status column for every component touched.
4. **LATEST VALIDATED COMMIT** — update after every passing test run.
5. **LAST TEST STATUS** — update after every test run (pass or fail).
6. **NEXT TASK** — set to the next task in dependency order.
7. **CURRENT BLOCKERS** — add new blockers discovered; remove blockers that are resolved.
8. **PENDING DECISIONS** — add new decisions surfaced; mark resolved decisions as resolved and date them.
9. **HANDOFF NOTES** — always fill this section before ending a session.

**Do NOT use this file to redefine what the architecture is.**  
Architecture authority remains `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`.

---

*Architecture authority: `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`*  
*Build authority: `10_TECHNICAL_SPECIFICATION_SIH26228.md`*  
*Task authority: `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`*  
*Agent instructions: `AGENTS.md`*  
*Workflow: `CODEX_BUILD_PROTOCOL.md`*
