# CODEX_BUILD_PROTOCOL.md
## SIH 2026 · PS 26228 — Codex Implementation Workflow

This file defines the mandatory workflow for every implementation task.  
Follow every step in order. Do not skip steps.

---

## THE WORKFLOW

```
READ
  ↓
INSPECT
  ↓
PLAN
  ↓
IMPLEMENT
  ↓
TEST
  ↓
REVIEW
  ↓
UPDATE STATE
  ↓
COMMIT
```

---

## STEP 1 — READ

At the start of every session:

1. Read `AGENTS.md` (standing instructions and security rules).
2. Read `PROJECT_STATE.md` (where the implementation is now; current task; blockers; last validated commit).
3. Identify the **current TASK-###** from `PROJECT_STATE.md`.
4. Locate the task definition in `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md` § Section 7.
5. Note the task's:
   - Source specification references (architecture spec section + technical spec section)
   - Dependencies (which tasks must be complete first)
   - Expected output (files/modules to produce)
   - Reuse decision (from `07_REUSE_AND_ARCHITECTURE_DECISION_MATRIX_SIH26228_UPDATED.md`)
   - Tests (unit test IDs mapped to assertions)
   - Acceptance criteria

**Do not begin implementation until you have confirmed all dependencies are complete.**  
If a dependency is not complete, note the blocker in `PROJECT_STATE.md` and stop.

---

## STEP 2 — INSPECT

Before writing or modifying any file:

### A. Task identification

State the TASK-### you are implementing. Confirm it matches `PROJECT_STATE.md`.

### B. Specification references

Identify and read the exact sections:
- **Architecture spec section(s):** from `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` (primary authority)
- **Technical spec section(s):** from `10_TECHNICAL_SPECIFICATION_SIH26228.md` (build-level contract)
- **MVP plan task entry:** from `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md` § Section 7

If the technical specification provides a method signature or pseudocode, follow it exactly.  
If the technical specification and architecture specification conflict, the architecture specification wins — raise the conflict as a proposed change, do not resolve it silently.

### C. Repository inspection

Before modifying any file:
- View the file's current contents.
- Check whether the module already exists (partial or complete).
- Confirm the task branch is checked out and up to date: `git pull origin <branch>`.
- Check `PROJECT_STATE.md` for any notes from prior sessions on this task.

### D. Reuse inspection

If this task involves external code or patterns:

1. Identify the reuse decision ID (e.g., REUSE-018, REUSE-020) from the task definition.
2. Confirm the approved decision:
   - `KEEP` / `HARDEN` / `EXTRACT` / `REIMPLEMENT` / `REPLACE` / `REMOVE` / `REFERENCE ONLY`
3. For `REIMPLEMENT` decisions: write the code from scratch without copying source from the external repository. Use the external code as a behavioral reference only.
4. For `EXTRACT` / `ADOPT/ADAPT` decisions: extract only the specific pattern identified. Do not pull in surrounding architecture, dependencies, or design assumptions.
5. Do **not** copy code from a repository without a confirmed compatible license. When in doubt, `REIMPLEMENT`.
6. Add attribution comment to source files that extract MIT/BSD patterns (required by REUSE-018 and REUSE-020).

---

## STEP 3 — PLAN

Before writing any code, state a brief plan:

- Which files will be created or modified.
- What the implementation boundary is (what this task touches; what it does NOT touch).
- Which security invariants this task must preserve.
- Which tests must pass after implementation.

**Implementation boundary statement (required before coding begins):**

> "This task modifies: [list of files/modules]  
> This task does NOT touch: [list of out-of-scope files]  
> Security invariants preserved: [list relevant rules from AGENTS.md]"

If any planned change requires touching a file outside the expected boundary, stop and evaluate whether this constitutes an architecture change. If it does, follow the change-control process rather than proceeding.

---

## STEP 4 — IMPLEMENT

Write the code according to the technical specification.

### Mandatory implementation rules

| Rule | Verification |
|---|---|
| Follow method signatures from §10 exactly | Compare against `10_TECHNICAL_SPECIFICATION_SIH26228.md` |
| Follow module structure from §10 §2.2 exactly | No alternative layouts |
| All submitted data/models enter via worker subprocesses only | No direct parse in supervisor |
| `weights_only=True` always; no fallback | `grep weights_only=False .` → 0 matches |
| LIMITATIONS and NON_CLAIMS fields non-empty on every worker output | Enforced by `workers/base.py` `build_worker_output()` |
| `coverage_gap_clean_label=True` on all C2 and C3 records | Enforced by `base.py`; schema validator rejects False |
| No `risk_score` field at any code path | Schema validator rejects; grep check must pass |
| UNAVAILABLE is the default for all assessment fields | Positive states require active assessment to be promoted |
| Temp directories cleaned on all code paths | `try/finally` pattern in `_dispatch_worker()` |
| Key path stripped from worker subprocess environment | `env` dict passed to `Popen` must not contain `ASSURANCE_KEY_PATH` |
| Attribution comments in MIT/BSD reuse | Source file header |
| No `jsonschema` package import in schema validator | Custom validator by design (§10 §2.1) |
| No CDN URLs in dashboard HTML | Offline requirement |

### PF-002 non-claim (required on all C3 and C4 records)

Every provenance record and every C3 evidence record must include:
```
pf_002_non_claim: "digest_match ≠ causal_execution_proof"
hash_match_not_safe: true
hash_match_not_semantically_equivalent: true
hash_match_not_causal_execution_proof: true
```

### DEFERRED_IN_SCOPE records (required before any capability claim)

The supervisor must emit DEFERRED_IN_SCOPE records for all of the following before any finding is produced:
- Behavioral model consistency battery (M07 class)
- PDQ near-duplicate detection (M03-PDQ)
- Statistical drift / OOD detection (M04, M05)
- Reference-relative comparison (M11)
- TorchScript loading
- External tail completeness
- Sybil-resistant contributor identity
- T05d clean-label detection (permanent NON_CLAIM — not a future capability)
- Activation-space analysis, Neural Cleanse, B3D, ABS, AC

---

## STEP 5 — TEST

Run tests before committing.

### Required test execution per task

Every task specifies its test IDs in `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`. Run them all.

```bash
# From repository root — adjust path to specific test file as needed
python -m pytest tests/unit/test_<module>.py -v
python -m pytest tests/security/test_<security_area>.py -v
```

### Universal security grep checks (run on every task from TASK-007 onward)

```bash
# Must return 0 matches — any match is a critical defect
grep -r "weights_only=False" assurance_system/
grep -rn "risk_score" assurance_system/ --include="*.py"   # in output-producing paths
grep -rn "\"CLEAN\"\|\"SAFE\"\|\"HEALTHY\"" assurance_system/constants.py  # as positive constants
```

### Acceptance criteria gate

Read the task's acceptance criteria from `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`.  
Confirm every criterion is met before marking the task complete.  
If a criterion cannot be confirmed (e.g., blocked on PRE-01), document why in `PROJECT_STATE.md`.

### Handling test failures

- Fix the root cause — do not suppress or skip the test.
- If a test failure reveals an architecture issue (not an implementation bug), follow the change-control process.
- Do not commit with failing tests unless they are explicitly marked as blocked on a named P1 condition, with a `pytest.mark.skip` and a documented reason string.

---

## STEP 6 — REVIEW

Before committing, self-review against the Universal Definition of Done:

```
[ ] All task-specific unit tests pass
[ ] No import of a prohibited package (jsonschema, ORT in non-designated components, unlicensed packages)
[ ] No CLEAN/SAFE/HEALTHY as a positive assurance constant
[ ] No risk_score field produced or consumed
[ ] No weights_only=False in any code path
[ ] LIMITATIONS and NON_CLAIMS non-empty on every worker output
[ ] coverage_gap_clean_label=True on all C2 and C3 evidence records
[ ] Attribution comments present for MIT/BSD reused patterns (REUSE-018, REUSE-020)
[ ] All temp files and worker directories cleaned after every code path
[ ] No network call in any code path
[ ] Task completion state ready to update in PROJECT_STATE.md
```

---

## STEP 7 — UPDATE STATE

Update `PROJECT_STATE.md` before committing:

1. Move the current task from `Current task` → `Completed work`.
2. Set the next recommended task (follow the dependency graph in §11 Section 8).
3. Update `Current implementation status` for the completed component (e.g., `IN PROGRESS` → `IMPLEMENTED`).
4. Record `Last test status` (what passed, what is still pending).
5. Record any new blockers discovered during implementation.
6. Record any pending decisions surfaced during implementation.

---

## STEP 8 — COMMIT

```bash
git add <changed files>
git commit -m "TASK-###: <short description> [tests: PASS/PARTIAL/BLOCKED-PRE-xx]"
git push origin feature/<workstream-name>
```

### Commit message rules

- Always cite the TASK-### at the start.
- Include test status in brackets.
- If work is incomplete: suffix `[WIP]` and explain what remains.
- Do not push knowingly broken code without `[WIP]` and an explanation.

### Example commit messages

```
TASK-005: Implement SQLite evidence store with WAL mode and ACL enforcement [tests: PASS]
TASK-009: Build hostile fixture suite — all 14 fixture types; seed reproducibility confirmed [tests: PASS]
TASK-017: PyTorch safe-loading gate — LOAD_BLOCKED on hostile pickle confirmed [tests: PARTIAL - PRE-01 BLOCKED for torch wheel]
```

---

## INTEGRATION GATE CHECKPOINTS

Before the branch can be merged to `main`, the relevant integration gate must pass.  
Gates are defined in `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md` § Section 14.

| Gate | Trigger | Key criteria |
|---|---|---|
| GATE-1 — Foundation | After TASK-002 through TASK-008 | Repository structure; evidence store; audit chain; schema validator; worker base; config |
| GATE-2 — Vertical Slice (P0) | After vertical slice criteria all pass | End-to-end COCO submission; DEFERRED_IN_SCOPE records; UNAVAILABLE propagation; no risk_score |
| GATE-3 — Capability | After all C2/C3 workers + C5 complete | All-box coverage; SEC-001–SEC-012; UNAVAILABLE at 4 injection points; CHAIN_CORRUPT; replay nonce |
| GATE-4 — Validation | After TASK-026 vertical-slice test battery | All VS-001–VS-007; all §10 §18 experiment contracts with observed results |
| GATE-5 — Demo | After GATE-4 + demo script | Demo runs offline; dashboard visible; export bundle valid; all DEFERRED records visible |

**No capability expansion may begin until GATE-2 passes.**

---

## BLOCKED-TASK PROTOCOL

If a task is blocked on a P1 condition (PRE-01 through PRE-09):

1. Build as much of the task as possible without the blocked input.
2. Add `pytest.mark.skip(reason="BLOCKED: PRE-xx — <description>")` to tests that require the missing input.
3. Implement a stub that emits the correct UNAVAILABLE or BLOCKED state rather than a fabricated result.
4. Document the blocker in `PROJECT_STATE.md` under `Current blockers`.
5. Do not remove the `[BLOCKED]` completion state from the task in MVP plan until the P1 condition is resolved and tests pass.

---

## ARCHITECTURE CHANGE CONTROL

If during implementation you discover that the specification is:
- Ambiguous or contradictory
- Impossible to implement as written
- Requiring a change to a trust boundary, interface contract, or schema

**Stop. Do not resolve it silently in code.**

```
1. Record the conflict or required change in PROJECT_STATE.md under "Pending Decisions"
2. Write a brief description: what you found, why it requires a change, what change you propose
3. Stop work on the affected component
4. Await project review and explicit decision
5. If approved: specification document is updated first, then implementation resumes
```

Prohibited changes without change control (from §09 §23):
- Adding any aggregate risk score or compromise probability field
- Adding fail-open audit chain handling
- Adding a second write path to the evidence store that bypasses COMP-SCHEMA
- Removing `coverage_gap_clean_label` or `access_mode` as required fields
- Removing PF-002 non-claim from provenance records
- Removing DEFERRED_IN_SCOPE records for any currently deferred method
- Changing trust boundary definitions (B1–B5)

---

## ANTIGRAVITY COORDINATION

Antigravity works on the dashboard (`feature/dashboard` branch).  
Codex and Antigravity share one repository. Branches represent tasks, not devices.

**Contract between Codex and Antigravity:**

| Codex provides | Antigravity consumes |
|---|---|
| Read-only evidence store query API (defined in `supervisor/evidence_store.py`) | Calls only the defined read-only methods |
| Evidence schema (field names and types) | Renders fields as defined; does not rename or reinterpret them |
| Assessment state vocabulary (in `constants.py`) | Displays state strings as-is; does not convert UNAVAILABLE to positive language |

Antigravity must not touch `supervisor/`, `workers/`, `schema/`, or `tests/security/` without Codex review.  
If Antigravity raises a backend-contract question, Codex addresses it in a task branch, not by having Antigravity patch the backend.

---

*This file is a process-control document. It does not modify the architecture.*  
*Architecture authority: `09_ARCHITECTURE_SPECIFICATION_SIH26228.md`*  
*Build authority: `10_TECHNICAL_SPECIFICATION_SIH26228.md`*  
*Task authority: `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`*
