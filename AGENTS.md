# AGENTS.md
## SIH 2026 · PS 26228 — Coding Agent Standing Instructions

Read this file at the start of every coding session.

---

## PROJECT IDENTITY

This repository implements the **Trustworthy Computer Vision Integrity Assurance System** for SIH 2026 Problem Statement 26228.

It is an **offline / air-gapped**, **supervisor-worker**, **evidence-first** assurance pipeline for computer vision assets (COCO/YOLO data, ONNX/PyTorch models) in multi-contributor pipelines.

---

## SOURCE-OF-TRUTH HIERARCHY

When any two sources conflict, the higher-ranked source wins. Never resolve a conflict silently.

```
1. Official SIH PS 26228
2. Approved project requirements and constraints
3. Approved threat model and trust model
4. Verified research findings (Master Research Bible)
5. 09_ARCHITECTURE_SPECIFICATION_SIH26228.md  ← primary architectural authority
6. 10_TECHNICAL_SPECIFICATION_SIH26228.md    ← build-level contract
7. 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md    ← task authority
8. Repository implementation (this codebase)
9. PROJECT_STATE.md                           ← live implementation state
```

Repository code does **not** override the architecture specification.
If the codebase diverges from the specification, the specification is the authority.

---

## ARCHITECTURE RULES

- Follow the approved architecture: **Option A — Deterministic Integrity Spine + Signed Evidence Governance + Offline-First Supervisor-Worker Architecture**.
- Do **not** silently redesign any component, interface, or trust boundary.
- Do **not** change trust boundaries (B1–B5) without a formal architecture change-control decision.
- Do **not** invent new security semantics, assessment states, or evidence field values.
- Preserve all explicit scope: DEFERRED_IN_SCOPE items must remain deferred unless a formal change-control decision authorizes them.
- If you believe an architecture change is required, follow the change-control process (see below). Do not silently implement the change.

### Architecture change-control process
```
Identify the conflict or required change
  → Record it as a proposed change (in PROJECT_STATE.md under "Pending Decisions")
  → STOP — do not implement the change
  → Await project review and explicit decision
  → If approved: specification is updated first, then implementation follows
```

---

## CODING RULES

- **Inspect before modifying.** Read the current state of any file before editing it.
- **Task-scoped changes only.** Each branch implements one task (TASK-###). Do not touch unrelated files.
- **No unrelated refactors.** If you see something that could be improved in an unrelated module, note it in PROJECT_STATE.md but do not change it in the current task branch.
- **Preserve tests.** Do not delete, skip, or weaken existing tests. If a test must change, explain why in the commit message.
- **Test your changes.** Run the relevant test suite before committing. Do not push knowingly broken code unless explicitly marked `[WIP]` in the commit message.
- **Document significant changes.** Non-trivial implementation decisions that go beyond what the specification states should be noted in a code comment or commit message.
- **No magic numbers.** Every threshold, limit, and configurable parameter must be named in the configuration system (`assurance_system/config/`).
- **Attribution required.** Source files reusing MIT/BSD patterns must carry the attribution comment as required by REUSE-018 (R17 patterns) and REUSE-020 (R27 pycocotools).

---

## SECURITY RULES

These rules are **absolute**. Violating any of them is a critical defect that must be fixed before any other work continues.

| Rule | Enforcement |
|---|---|
| All submitted data and model artifacts are **untrusted** | Never parse or load them in the supervisor process; use worker subprocesses only |
| `weights_only=True` is **mandatory** — no fallback path of any kind | `grep weights_only=False .` must return 0 matches at all times |
| `UNAVAILABLE ≠ CLEAN` | No code path may convert an UNAVAILABLE or ASSESSMENT_ERROR result to a clean/positive state |
| `ANOMALY ≠ PROVEN_MALICIOUS` | LOAD_BLOCKED and ONNX_PATH_CONTAINMENT_VIOLATION are detection signals, not proof of attack |
| No aggregate risk score | No `risk_score`, `aggregate_assurance`, or `compromise_probability` field may appear anywhere |
| Signing key inaccessible to workers | The key path must be stripped from worker subprocess environments |
| Evidence store is supervisor-only writes | No worker and no analyst interface component may write to the evidence store |
| Fail-closed audit chain | `AuditWriteError` must never be silently swallowed |
| DEFERRED_IN_SCOPE ≠ CLEAN | Deferred methods produce explicit DEFERRED_IN_SCOPE records; their absence is not a no-issue finding |

**Automated guards** (must pass on every commit):
- `grep -r "weights_only=False" assurance_system/` → 0 matches
- `grep -r "risk_score" assurance_system/` (in evidence/finding output paths) → 0 matches
- `grep -r "CLEAN\|SAFE\|HEALTHY" assurance_system/constants.py` (as positive assurance constants) → 0 matches

---

## REPOSITORY RULES

- **No secrets** in any committed file. Keys, tokens, passwords, and HMAC secrets must never appear in version-controlled files.
- **No large binary artifacts** (model weights, full datasets). The `wheelhouse/` directory is exempt (pre-staged wheels) but must be listed in `.gitignore` for CI.
- **No machine-specific paths.** All paths must be configurable via `config/system_config.yaml` or relative to the project root.
- **Reproducibility.** All fixture generation must be seed-pinned. All deterministic operations must produce the same output on the same input on any conforming host.
- **Offline.** No code path may make a network call at runtime. `pip install` must never be called by the system at runtime.

---

## PROHIBITED COMPONENTS (permanent; no exceptions)

The following must never appear in this codebase:

| Prohibited item | Authority |
|---|---|
| R01 Fabric client or any fake-CONNECTED blockchain façade | §09 §1.4; REUSE-015 |
| Aggregate risk score / compromise probability (any form) | §09 §1.4; G-07 — absolutely prohibited |
| First-box-only label analysis | §09 §1.4; REUSE-003 |
| `weights_only=False` at any code path (including exception handlers) | RC-013 REJECTED |
| Fail-open audit chain (silent swallow of AuditWriteError) | AF-004 |
| Second write path to evidence store bypassing COMP-SCHEMA | §09 §23 |
| R13 Alibi-Detect, R04 BackdoorBench code, R05 BackdoorBox code | License gates |

---

## ANTIGRAVITY-SPECIFIC RULES

Antigravity works on the dashboard (`assurance_system/interfaces/dashboard.py`) and visual QA after GATE-2 passes.

- Pull latest from `main` or the relevant feature branch before starting any session.
- Read `PROJECT_STATE.md` before starting any work.
- **Do not** define new security semantics, assessment states, or evidence field values.
- **Do not** add any write path to the evidence store from the dashboard.
- Read evidence via the read-only query API that Codex defines — do not build a parallel query path.
- **Do not** display assurance confidence levels, risk scores, or green/red safe/unsafe color coding.
- UNAVAILABLE and DEFERRED_IN_SCOPE findings must be **visible** in the dashboard — never hidden, collapsed, or converted to positive language.
- Any change touching `supervisor/`, `workers/`, `schema/`, or `tests/security/` requires Codex review before merge.
- Backend contract changes must be routed through a Codex engineering task — do not silently adjust frontend expectations to match a changed backend assumption.

---

## SYNCHRONIZATION PROTOCOL

```
Before starting work:
  git pull origin <branch>
  Read PROJECT_STATE.md → identify current task, blockers, last validated commit

During work:
  Work in the designated feature branch for the current TASK-###
  Branches = tasks, not devices

After completing work:
  Run all relevant tests
  Update PROJECT_STATE.md (current task → completed; update test status; set next task)
  git add, git commit (meaningful message citing TASK-### and test status)
  git push origin <branch>

GitHub is the single source of truth.
The office machine and the home machine must never maintain separate undocumented project states.
```

---

*This file is a control document. It does not modify the architecture.*
*Architecture authority: `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`*
*Build authority: `10_TECHNICAL_SPECIFICATION_SIH26228.md`*
*Task authority: `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`*
*Live state: `PROJECT_STATE.md`*
