# Setup Guide — SIH26228 CV Integrity Assurance System

**Status:** SKELETON — environment not yet validated.
**Authority:** 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md §3 MB-28; Stage 13 Setup

---

## Prerequisites

> **NOTE:** Target host specification is BLOCKED on PRE-01. The values below
> are best-effort defaults. Do not treat them as offline-validated.

| Requirement | Value | Status |
|-------------|-------|--------|
| Python | ≥ 3.9 (target version pending PRE-01) | CONDITIONAL |
| OS | Linux preferred (subprocess isolation confirmed) | CONDITIONAL: PRE-01 |
| RAM | ≥ 4 GB recommended | CONDITIONAL: PRE-01 |
| Disk | ≥ 10 GB for wheels + evidence store | CONDITIONAL: PRE-01 |
| Network at runtime | NONE (offline / air-gapped target) | CONDITIONAL: PRE-01 |

**Hard constraint:** PyTorch ≥ 2.10.0 (XREG-005; not negotiable).

---

## Offline Preparation (air-gapped deployment)

> The system is designed for offline deployment. Wheels must be pre-staged
> before transferring to the target host.

### Step 1 — Stage wheels on a networked machine

```bash
# After PRE-01 confirms target host OS + Python version:
pip download \
    onnx \
    "torch>=2.10.0" --index-url https://download.pytorch.org/whl/cpu \
    pycocotools \
    -d wheelhouse/
# If XREG-002 → Ed25519:
pip download cryptography -d wheelhouse/
```

### Step 2 — Verify wheelhouse (SHOULD BUILD script — TASK-SB-02)

```bash
python scripts/verify_wheelhouse.py
```

> This script does not exist yet. It will be implemented as part of SB-02.
> **Offline claim cannot be made until this verification passes on the target host.**

### Step 3 — Transfer repository to target host

Transfer the full repository including `wheelhouse/` to the air-gapped target.

### Step 4 — Install from wheelhouse (on target host)

```bash
pip install --no-index --find-links=wheelhouse/ -r requirements.txt
```

---

## Repository Initialization

```bash
git clone <this-repo> SIH26228-CV-INTEGRITY
cd SIH26228-CV-INTEGRITY
# Install in editable mode (after wheelhouse staged):
pip install --no-index --find-links=wheelhouse/ -e .
```

---

## Running Tests

```bash
# Structure test (runs immediately; no implementation required):
python -m pytest tests/test_repository_structure.py -v

# Security invariant tests (weights_only=False and risk_score grep — Day 1):
python -m pytest tests/security/test_security_invariants.py -v

# All tests (skipped stubs will be shown; no failures expected on skeleton):
python -m pytest tests/ -v
```

---

## Development Workflow

1. **Never work directly on `main`.**
2. Check out the relevant feature branch: `git checkout -b feature/<workstream-name>`
3. Branch naming follows the workstream plan in `docs/MVP_IMPLEMENTATION_PLAN.md §13`.
4. Merge to `main` only after the relevant gate criteria pass.
5. See `BRANCH_NAMING.md` for the complete branch convention.

---

## Entry Points (after implementation — STUB)

```bash
# Full pipeline assessment
python cli.py assess --submission <manifest_path>

# Show finding for an asset
python cli.py show-finding --asset-id <id>

# Show evidence record
python cli.py show-evidence --asset-id <id> --method <method-id>

# Audit trail (read-only)
python cli.py show-audit-trail

# Export evidence bundle (ZIP)
python cli.py export-bundle --asset-id <id> --output <path>

# List all deferred-in-scope records
python cli.py list-deferred

# Start read-only dashboard
python cli.py dashboard --port 8080
```

---

## Important Limitations

- **No offline claim is yet permissible.** PRE-01 is unresolved; wheelhouse has
  not been staged or verified on any target host.
- **No capability claim is yet permissible.** Implementation has not begun.
- **P1 blocking conditions (PRE-01 through PRE-09) must be resolved** before
  implementation begins. See `docs/MVP_IMPLEMENTATION_PLAN.md` §18.

