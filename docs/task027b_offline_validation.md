# TASK-027-B Target-Host Offline Validation Evidence

**Date:** 2026-09-28  
**Branch:** `feature/vertical-slice`  
**Result:** `TESTED WITH BLOCKERS`  
**Offline capability claim:** `NOT ESTABLISHED`

This record reports only observed TASK-027-B results. No package was downloaded,
no package index was accessed, no production code was changed, and no unavailable
capability is represented as available. The mandatory repository synchronization
step contacted the configured Git origin before validation; this is additional
evidence that the session was not network-isolated and cannot establish OFF-002.

## Environment

| Field | Observed value |
|---|---|
| Operating system | Microsoft Windows NT 10.0.22631.0 |
| Approved host record | Windows 10 Pro build 22631 |
| CPU architecture | AMD64 |
| Python | 3.13.12 |
| Interpreter | Repository-relative `.venv-torch-test\Scripts\python.exe` |
| Wheelhouse | Repository-relative `wheelhouse\` |
| Wheel count | 10 |
| Network status | `NOT ISOLATED` — Ethernet0 3 was UP at 1 Gbps |

The target tuple matches the resolved PRE-01 record. The required network-disabled
precondition was not met: an Ethernet adapter was active and no approved egress
monitor was supplied. The pre-validation Git synchronization contacted the
configured origin. The validation commands themselves used local inputs and did
not contact a package index or dependency source.

## Wheelhouse evidence

The wheelhouse contains the Torch CPU wheel and its staged dependencies:

- `torch-2.10.0+cpu-cp313-cp313-win_amd64.whl`
- `filelock-3.32.3-py3-none-any.whl`
- `fsspec-2026.7.0-py3-none-any.whl`
- `jinja2-3.1.6-py3-none-any.whl`
- `markupsafe-3.0.3-cp313-cp313-win_amd64.whl`
- `mpmath-1.3.0-py3-none-any.whl`
- `networkx-3.6.1-py3-none-any.whl`
- `setuptools-78.1.0-py3-none-any.whl`
- `sympy-1.14.0-py3-none-any.whl`
- `typing_extensions-4.16.0-py3-none-any.whl`

No ONNX or pycocotools wheel is staged. `requirements.txt` has no active
requirement entry beyond comments.

| Package | Verifier status | Wheel found | Compatibility | Direct approved-environment import |
|---|---|---|---|---|
| `torch>=2.10.0` CPU | `STAGED` / available | Yes | PASS for CPython 3.13 Windows AMD64 | PASS — 2.10.0+cpu |
| `onnx` | `MISSING` | No | NOT AVAILABLE | FAIL — `ModuleNotFoundError` |
| `pycocotools` | `MISSING` | No | NOT AVAILABLE | FAIL — `ModuleNotFoundError` |

## Local-only installation and import attempt

Command contract:

```text
python scripts/verify_wheelhouse.py --wheelhouse-dir <local-wheelhouse> --python <approved-interpreter>
```

The verifier invoked pip only with `--no-index`, local `--find-links`, and a
temporary installation target. The target was cleaned automatically.

Observed result:

```text
torch>=2.10.0: STAGED
onnx: MISSING
pycocotools: MISSING
INSTALL STATUS: FAIL
ERROR: No matching distribution found for onnx
onnx: FAIL
torch: FAIL
pycocotools: FAIL
exit code: 1
```

The isolated aggregate import result is a failure because the required package
closure cannot be installed. The separate direct import check confirms that the
already-approved repository environment can import Torch, but not ONNX or
pycocotools. This does not make the aggregate wheelhouse complete.

## Offline test execution

`pytest tests/offline/ -v` collected seven pre-existing/new stubs and reported
seven skips, zero failures, and zero passes. Four are the TASK-027-A OFF-001
through OFF-004 contracts; three are legacy skipped stubs. A skipped contract is
not acceptance evidence.

| Test | Status | Evidence boundary |
|---|---|---|
| OFF-001 wheelhouse installation | `FAIL` | Local-only aggregate installation failed because ONNX and pycocotools wheels are missing |
| OFF-002 zero network egress | `BLOCKED` | Network adapter was active; no approved egress monitor or isolated-network evidence was available; test stub skipped |
| OFF-003 offline imports | `FAIL` | Torch imports, but ONNX and pycocotools imports fail; test stub skipped |
| OFF-004 SQLite evidence store | `BLOCKED` | Dedicated OFF-004 stub skipped. Supporting local `UT-STORE-001` round-trip passed, but is not relabeled as OFF-004 target-host acceptance |

## Host capability review

| Capability | Status | Evidence |
|---|---|---|
| HOST-CAP-001 — COCO / pycocotools | `UNAVAILABLE` | No wheel; direct import fails |
| HOST-CAP-002 — resource enforcement | `PARTIAL` | Existing Windows limitation remains: `close_fds=True` is available; Unix RLIMIT controls are unavailable and no replacement is authorized |
| HOST-CAP-003 — ONNX | `UNAVAILABLE` | No wheel; direct import fails |

PRE-08 and E-2 remain open and are not affected by this validation.

## Security validation

- Production Python imports of `requests`, `urllib`, or `socket`: zero.
- Production pip-install/`ensurepip` logic: zero.
- `weights_only=False`: zero production matches.
- `risk_score`: zero production matches.
- Quoted positive-assurance constants `CLEAN`, `SAFE`, and `HEALTHY`: zero.
- Plain-text `requests` matches in `orchestrator.py` are local worker-request
  variable names, not imports or network calls.

## Final result

TASK-027 is `TESTED WITH BLOCKERS`. Offline deployment validation does not pass.
OFFLINE-001 remains open because the required wheel closure is incomplete,
zero-egress evidence is absent, and the four dedicated offline contracts remain
skip-only stubs. GATE-2 remains blocked and TASK-024 remains unauthorized.
