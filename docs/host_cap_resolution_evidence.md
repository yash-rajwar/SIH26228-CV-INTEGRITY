# HOST-CAP Resolution Phase Evidence

**Date:** 2026-09-28
**Branch:** `feature/vertical-slice`
**Result:** `BLOCKED — no capability blocker closed`

This phase evaluated only the existing host-capability blockers. It did not
download or install a dependency, change production/test code, run GATE-2
scenarios, execute OFF-001 through OFF-004, or alter architecture semantics.

## Approved environment

| Field | Observed value |
|---|---|
| Operating system | Windows build 22631 |
| Architecture | AMD64 |
| Python | 3.13.12 |
| Interpreter | Repository-relative `.venv-torch-test\Scripts\python.exe` |
| Wheelhouse | Repository-relative `wheelhouse/` |

## Phase 1 — HOST-CAP-001

| Required evidence | Observed value |
|---|---|
| Package filename | `NONE` |
| Version | `UNAVAILABLE` |
| Required ABI/platform | CPython 3.13 / Windows AMD64 |
| Approved local source | `NONE` |
| SHA-256 | `UNAVAILABLE` |
| Offline installation | `NOT ATTEMPTED` — no staged wheel exists |
| `import pycocotools` | `FAIL` — `ModuleNotFoundError` |
| Capability decision | `UNAVAILABLE` |

The dependency-exists prerequisite was not satisfied. GATE-2.1 and GATE-2.2
were therefore not rerun, and HOST-CAP-001 remains open.

## Phase 2 — HOST-CAP-003

| Required evidence | Observed value |
|---|---|
| ONNX package filename | `NONE` |
| Version | `UNAVAILABLE` |
| Required ABI/platform | CPython 3.13 / Windows AMD64 |
| Approved local source | `NONE` |
| SHA-256 | `UNAVAILABLE` |
| Offline installation | `NOT ATTEMPTED` — no staged wheel exists |
| `import onnx` | `FAIL` — `ModuleNotFoundError` |
| Capability decision | `UNAVAILABLE` |

ONNX Runtime is not required by the approved implementation: C3A/C3C use the
`onnx` protobuf/checker package and explicitly do not import or execute ORT.
No ONNX or ONNX Runtime capability is inferred.

## Phase 3 — wheelhouse inventory and closure

The wheelhouse contains 10 wheels. Sources/provenance beyond their existing
repository-local staging are not recorded, so no external source is inferred.

| Wheel | Size (bytes) | SHA-256 |
|---|---:|---|
| `filelock-3.32.3-py3-none-any.whl` | 98,901 | `7f0ca4bcc0e181c60dbbd8aa9ab5b120ebb99e4e064e83636340056f833a1f09` |
| `fsspec-2026.7.0-py3-none-any.whl` | 206,583 | `b57ddbafedfaef7018c1ecab32aa200a9d7ca26b77965f64e48b70061249d279` |
| `jinja2-3.1.6-py3-none-any.whl` | 134,899 | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` |
| `markupsafe-3.0.3-cp313-cp313-win_amd64.whl` | 15,113 | `9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5` |
| `mpmath-1.3.0-py3-none-any.whl` | 536,198 | `a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c` |
| `networkx-3.6.1-py3-none-any.whl` | 2,068,504 | `d47fbf302e7d9cbbb9e2555a0d267983d2aa476bac30e90dfbe5669bd57f3762` |
| `setuptools-78.1.0-py3-none-any.whl` | 1,256,108 | `3e386e96793c8702ae83d17b853fb93d3e09ef82ec62722e61da5cd22376dcd8` |
| `sympy-1.14.0-py3-none-any.whl` | 6,299,353 | `e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5` |
| `torch-2.10.0+cpu-cp313-cp313-win_amd64.whl` | 113,670,411 | `b719da5af01b59126ac13eefd6ba3dd12d002dc0e8e79b8b365e55267a8189d3` |
| `typing_extensions-4.16.0-py3-none-any.whl` | 45,571 | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |

Observed availability:

- Torch: `AVAILABLE` in the approved environment, version 2.10.0+cpu.
- ONNX: `MISSING`.
- pycocotools: `MISSING`.
- Active `requirements.txt` entries: none (comments only).

Fresh `scripts/verify_wheelhouse.py` result:

```text
torch>=2.10.0: STAGED
onnx: MISSING
pycocotools: MISSING
INSTALL STATUS: FAIL
ERROR: No matching distribution found for onnx
IMPORT STATUS: onnx FAIL; torch FAIL; pycocotools FAIL
exit code: 1
```

The isolated aggregate Torch import is marked FAIL because the complete install
aborts on the missing ONNX requirement. The separate approved-environment Torch
import passes. Overall wheelhouse closure is `BLOCKED`.

## Phase 4 — offline-validation re-entry

`NOT EXECUTED`. Phase 4 is conditional on complete wheelhouse closure, which was
not achieved. No OFF-001, OFF-002, OFF-003, or OFF-004 status is upgraded by this
phase; the TASK-027-B results remain authoritative.

## Phase 5 — HOST-CAP-002

| Check | Result |
|---|---|
| `subprocess(..., close_fds=True)` | PASS |
| Python `resource` module | UNAVAILABLE (`ModuleNotFoundError`) |
| Authorized Windows replacement for RLIMIT controls | NONE |
| Capability decision | `PARTIAL` |

No unsupported Windows resource-enforcement mechanism was attempted.

## Security review

- Raw `requests` scan finds only local worker-request variable names in
  `supervisor/orchestrator.py`; there is no `requests` import.
- Raw `urllib` and `socket` production scans: zero matches.
- Production imports of `requests`, `urllib`, or `socket`: zero matches.
- `weights_only=False`: zero production matches.
- `risk_score`: zero production matches.
- Production pip-install/`ensurepip` logic: zero matches.

## Final decision

- HOST-CAP-001: `UNAVAILABLE` — unchanged.
- HOST-CAP-003: `UNAVAILABLE` — unchanged.
- HOST-CAP-002: `PARTIAL` — unchanged.
- Wheelhouse closure: `BLOCKED`.
- Offline-validation re-entry: `NOT AUTHORIZED BY PREREQUISITE`.
- GATE-2 impact: unchanged; GATE-2.1/GATE-2.2 remain blocked.
- PRE-08 and E-2: open and unchanged.
- TASK-024: not authorized.

## Superseding HOST-CAP-002 decision — 2026-10-02

The Phase 5 finding above remains historical evidence: at that checkpoint no
authorized Windows replacement existed. Project-owner change control
ACC-2026-10-02-01 subsequently approved Windows Job Objects for per-process
committed-memory containment using the existing `memory_limit_mb` contract.

The approved bounded capability probe configured 128 MiB plus
KILL_ON_JOB_CLOSE, assigned a suspended child before resume, observed MemoryError
at the boundary, exit code 42 and 127.05 MiB peak committed process memory. Probe
result: PASS. This supersedes the prior "mechanism unavailable" conclusion for
the current Windows target but does not itself establish SEC-002 acceptance.

The subsequent real supervisor/FIX-002 acceptance completed on 2026-10-02 with
a bounded 768 MiB ceiling, `MEMORY_LIMIT_EXCEEDED` persistence, C5 unavailable
propagation, intact audit/cleanup, and a successful following FIX-015 asset.
SEC-002 and HOST-CAP-002 are therefore closed for this frozen Windows mechanism
and target; the 128 MiB probe remains capability evidence rather than being
relabelled as the acceptance test.
