# TASK-027-C / Gate-2 Validation Re-entry Evidence

**Date:** 2026-09-28

**Branch:** `feature/vertical-slice`

**Result:** `STOPPED — DEPENDENCY ARTIFACT MISSING AND PRODUCTION COMPATIBILITY DEFECT`

**Gate-2 result:** `BLOCKED`

This record reports the controlled offline validation authorized after commit
`e6985ed`. No package index was used, no additional artifact was acquired, and
no production or test file was changed. Validation stopped under the packet's
mandatory rules when the real project paths exposed a missing approved PyYAML
artifact and an ONNX/protobuf compatibility defect.

## Environment

| Field | Observed value |
|---|---|
| OS | Windows 11 build 22631 |
| Architecture | AMD64 / 64-bit |
| Base interpreter | `C:\Users\master\AppData\Local\Programs\Python\Python313\python.exe` |
| Python | CPython 3.13.12 |
| Isolated environment | Temporary venv `sih26228-task027c-validation-e6985ed` |
| Approved wheelhouse | `C:\Users\master\Desktop\SIH26228-CV-INTEGRITY\wheelhouse` |
| Initial repository state | clean, `feature/vertical-slice`, HEAD `e6985ed` |

## Pre-install Wheelhouse Verification

The existing verifier ran with the approved base interpreter and returned exit
zero:

```text
PACKAGE STATUS
torch>=2.10.0: STAGED
onnx: STAGED
pycocotools: STAGED
INSTALL STATUS: PASS
IMPORT STATUS
onnx: PASS
torch: PASS
pycocotools: PASS
WHEELHOUSE_VERIFIER_EXIT=0
```

This verifier covers its three declared core requirements. The later real C2A
path established that the full application closure also requires PyYAML, which
is absent from the approved wheelhouse and inactive stub `requirements.txt`.

## Complete Wheel Inventory

| Package | Version | Filename | Python | ABI | Platform | SHA-256 | Bytes |
|---|---:|---|---|---|---|---|---:|
| filelock | 3.32.3 | `filelock-3.32.3-py3-none-any.whl` | py3 | none | any | `7f0ca4bcc0e181c60dbbd8aa9ab5b120ebb99e4e064e83636340056f833a1f09` | 98,901 |
| fsspec | 2026.7.0 | `fsspec-2026.7.0-py3-none-any.whl` | py3 | none | any | `b57ddbafedfaef7018c1ecab32aa200a9d7ca26b77965f64e48b70061249d279` | 206,583 |
| jinja2 | 3.1.6 | `jinja2-3.1.6-py3-none-any.whl` | py3 | none | any | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` | 134,899 |
| markupsafe | 3.0.3 | `markupsafe-3.0.3-cp313-cp313-win_amd64.whl` | cp313 | cp313 | win_amd64 | `9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5` | 15,113 |
| ml_dtypes | 0.6.0 | `ml_dtypes-0.6.0-cp313-cp313-win_amd64.whl` | cp313 | cp313 | win_amd64 | `fb87f46b4f7ad7b5d3ad8f4b452b024bd4229d44c8ff934798c1fe656210387a` | 439,357 |
| mpmath | 1.3.0 | `mpmath-1.3.0-py3-none-any.whl` | py3 | none | any | `a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c` | 536,198 |
| networkx | 3.6.1 | `networkx-3.6.1-py3-none-any.whl` | py3 | none | any | `d47fbf302e7d9cbbb9e2555a0d267983d2aa476bac30e90dfbe5669bd57f3762` | 2,068,504 |
| numpy | 2.5.3 | `numpy-2.5.3-cp313-cp313-win_amd64.whl` | cp313 | cp313 | win_amd64 | `71cad2b2a7451ab79d8f5e71b453485b6775963d5cf794179144a7463fe6e8ec` | 12,560,965 |
| onnx | 1.23.0 | `onnx-1.23.0-cp312-abi3-win_amd64.whl` | cp312 | abi3 | win_amd64 | `70a2f930b221f9dbdff62704838ce8bf81442787b25048f8b9cdc9118168799e` | 7,872,197 |
| protobuf | 7.36.2 | `protobuf-7.36.2-cp310-abi3-win_amd64.whl` | cp310 | abi3 | win_amd64 | `a300819d441e078a5608c0d3c709796bb548136058fda017ae51d425b44fd353` | 456,514 |
| pycocotools | 2.0.11 | `pycocotools-2.0.11-cp312-abi3-win_amd64.whl` | cp312 | abi3 | win_amd64 | `ffe806ce535f5996445188f9a35643791dc54beabc61bd81e2b03367356d604f` | 77,570 |
| setuptools | 78.1.0 | `setuptools-78.1.0-py3-none-any.whl` | py3 | none | any | `3e386e96793c8702ae83d17b853fb93d3e09ef82ec62722e61da5cd22376dcd8` | 1,256,108 |
| sympy | 1.14.0 | `sympy-1.14.0-py3-none-any.whl` | py3 | none | any | `e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5` | 6,299,353 |
| torch | 2.10.0+cpu | `torch-2.10.0+cpu-cp313-cp313-win_amd64.whl` | cp313 | cp313 | win_amd64 | `b719da5af01b59126ac13eefd6ba3dd12d002dc0e8e79b8b365e55267a8189d3` | 113,670,411 |
| typing_extensions | 4.16.0 | `typing_extensions-4.16.0-py3-none-any.whl` | py3 | none | any | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | 45,571 |

## Offline Installation

The temporary venv was created from the approved interpreter. For the install
process, `PIP_CONFIG_FILE=NUL`, `PIP_NO_INDEX=1`, and
`PIP_DISABLE_PIP_VERSION_CHECK=1`; index and proxy environment variables were
removed. No global or venv pip configuration file existed.

```text
python -m pip install --disable-pip-version-check --no-index
  --find-links=<approved-wheelhouse> --only-binary=:all:
  torch==2.10.0+cpu onnx==1.23.0 pycocotools==2.0.11
```

Pip processed every artifact from the local wheelhouse and returned exit 0.
It installed filelock 3.32.3, fsspec 2026.7.0, Jinja2 3.1.6, MarkupSafe
3.0.3, ml_dtypes 0.6.0, mpmath 1.3.0, networkx 3.6.1, numpy 2.5.3, ONNX
1.23.0, protobuf 7.36.2, pycocotools 2.0.11, setuptools 78.1.0, sympy
1.14.0, Torch 2.10.0+cpu, and typing_extensions 4.16.0.

The selected three-package command passed, but full application installation
validation is `FAIL`: C2A's existing `ConfigLoader` requires `yaml`, and no
PyYAML wheel is present in the approved wheelhouse. The packet requires an
immediate stop when an application dependency is missing; no download or
workaround was attempted.

## Runtime Import Results

Every listed package originated inside the fresh temporary venv.

| Import | Version | Result |
|---|---:|---|
| onnx | 1.23.0 | PASS |
| pycocotools | 2.0.11 | PASS |
| `pycocotools.coco.COCO` | 2.0.11 distribution | PASS |
| numpy | 2.5.3 | PASS |
| google.protobuf | 7.36.2 | PASS |
| ml_dtypes | 0.6.0 | PASS |
| torch | 2.10.0+cpu | PASS |
| typing_extensions | 4.16.0 | PASS |
| yaml / PyYAML | unavailable | FAIL — `ModuleNotFoundError: No module named 'yaml'` |
| onnxruntime | not installed | expected; not required |

## Actual Project-path Results

### C2A / pycocotools

The production module imported pycocotools successfully and selected the real
`pycocotools.coco.COCO` class. Both the valid COCO control and FIX-008 stopped
before parsing because `ConfigLoader.load()` returned fail-closed
`ASSESSMENT_ERROR`:

```text
CONFIGURATION_ERROR: ConfigError: PyYAML not available. Ensure it is
pre-staged in wheelhouse/ and installed.
```

Therefore the valid fixture, all-annotation geometry path, and Gate-2.1/2.2
supervisor/audit lifecycle cannot be accepted. HOST-CAP-001 remains unresolved.

### C3A/C3C / ONNX

ONNX imports and a seed-pinned benign ONNX model is generated without ONNX
Runtime. The actual C3A/C3C external-reference scan fails before structural
checking. Direct diagnostic evidence is:

```text
assurance_system/workers/c3a_artifact_unit.py:169
if field.label == field.LABEL_REPEATED:
AttributeError: 'google._upb._message.FieldDescriptor' object has no attribute 'label'
```

C3A maps this to `ASSESSMENT_ERROR`; C3C maps it to `STRUCTURAL_INVALID` with
`EXTERNAL_REFERENCE_SCAN_FAILED: AttributeError`. A valid model therefore does
not reach `STRUCTURAL_VALID`. This is a production compatibility defect exposed
by ONNX 1.23.0 / protobuf 7.36.2 and requires a separately authorized fix.
No fix was made in this validation packet. HOST-CAP-003 remains unresolved.

## OFF Contracts

| Contract | Result | Evidence |
|---|---|---|
| OFF-001 | FAIL | The core wheel command installed locally, but the real application path proved the approved wheelhouse lacks required PyYAML; complete application closure is not installable from the approved wheelhouse. |
| OFF-002 | BLOCKED | Commands used `--no-index` and local paths, but no approved target-host network monitor/zero-egress evidence was available. No stronger zero-egress claim is inferred. |
| OFF-003 | FAIL | Requested native imports pass, but required application import `yaml` fails; the ONNX package is importable but its production path is incompatible. |
| OFF-004 | BLOCKED | Not executed after the packet-mandated stop; the existing dedicated test remains a skipped contract and is not converted to PASS. |

The repository's seven offline pytest contracts remain skip-only stubs. They
were not rewritten and were not represented as passing.

## Regression and Gate Results

Affected regression was not run after the mandatory stop. No existing test was
changed, skipped, or weakened.

| Item | Result | Reason |
|---|---|---|
| Affected regression | BLOCKED / NOT RUN | Missing PyYAML artifact and ONNX production compatibility defect |
| GATE-2.1 valid COCO | BLOCKED | HOST-CAP-001 unresolved; real C2A path fails before COCO parsing |
| GATE-2.2 FIX-008 | BLOCKED | Gate-2.1 prerequisites fail; real geometry path does not execute |
| GATE-2.3 | PRESERVED PASS | No new evidence invalidated the committed result |
| GATE-2.4 | PRESERVED PASS | No new evidence invalidated the committed result |
| GATE-2.5 | PRESERVED PASS | No new evidence invalidated the committed result |
| GATE-2.6 | PRESERVED PASS | No new evidence invalidated the committed result |
| GATE-2.7 | PRESERVED PASS | No new evidence invalidated the committed result |
| Overall Gate-2 | BLOCKED | Gate-2.1 and Gate-2.2 remain blocked |

## Preserved Decisions and Remaining Blockers

- HOST-CAP-001: `UNRESOLVED`.
- HOST-CAP-003: `UNRESOLVED`.
- HOST-CAP-002: remains `PARTIAL`.
- E-2: remains `OPEN`; no ONNX artifact-unit definition ID was invented.
- PRE-08: remains `PARTIAL` / operational provisioning open.
- OFFLINE-001: remains open.
- TASK-024 remains unauthorized.
- No ONNX Runtime dependency was introduced and no model was executed.

## Security Review

- `weights_only=False`, `risk_score`, `confidence_score`, and `trust_score`:
  zero production matches.
- `HEALTHY`: zero production matches.
- `CLEAN`, `SAFE`, `CONFIRMED_MALICIOUS`, and `PROVEN_ATTACK` occurrences are
  limited to schema rejection literals, capability/method identifiers such as
  `NEURAL_CLEANSE` and `SAFETENSORS`, safe-load identifiers, and cleanup error
  names. They are not positive production output states.
- Production/test changed-file count: zero.
- Protected `docs/research/**` changed-file count: zero.
- No secret, credential, runtime network path, fallback loader, or ONNX Runtime
  dependency was added.

## Required Next Action

The dependency/deployment owner must provide an approved, provenance-recorded,
hash-verified CPython 3.13-compatible PyYAML wheel in the wheelhouse. Separately,
a production defect-fix packet must authorize repair and tests for the ONNX
1.23.0 / protobuf 7.36.2 FieldDescriptor compatibility failure in the shared
C3A/C3C traversal. After both prerequisites are satisfied, TASK-027-C must be
rerun from the beginning with approved zero-egress evidence. No later gate or
dashboard task is authorized by this stopped result.
