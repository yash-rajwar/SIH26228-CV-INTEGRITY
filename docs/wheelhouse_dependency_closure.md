# Controlled Online Dependency Acquisition Evidence

**Date:** 2026-09-28

**Branch:** `feature/vertical-slice`

**Scope:** HOST-CAP-001 / HOST-CAP-003 artifact acquisition only

**Status:** `DEPENDENCY CLOSURE COMPLETE; RUNTIME VALIDATION NOT EXECUTED`

This record supersedes the missing-artifact inventory previously stored at this
path. The project owner explicitly authorized a bounded online acquisition from
official PyPI for compatible CPython 3.13 / Windows AMD64 binary wheels and
their required transitive dependencies. The authorization did not include
installation into the approved runtime, Gate-2, TASK-027-B, OFF-001 through
OFF-004, product or test changes, or closure of HOST-CAP-001/HOST-CAP-003.

## Acquisition Environment

| Field | Value |
|---|---|
| Host | Windows 11 Pro build 22631, AMD64 |
| Approved target interpreter | `C:\Users\master\AppData\Local\Programs\Python\Python313\python.exe` |
| Python | CPython 3.13.12, 64-bit, GIL-enabled |
| Package index | Official PyPI Simple API: `https://pypi.org/simple` |
| Artifact host | `https://files.pythonhosted.org` |
| Wheelhouse | Repository-relative `wheelhouse/` |
| Acquisition UTC | 2026-09-28T12:15:44Z |
| Build policy | Binary wheels only; no source distribution or local build |

## Version Selection

Resolution used pip 26.2.1 with `--only-binary=:all:` against official PyPI
and the existing wheelhouse. The initially resolved ONNX 1.23.1 was rejected
because PyPI reported its upload as 2026-09-29T15:48:54.092469Z, later than
this acquisition. ONNX 1.23.0 was the highest compatible, non-yanked release
available by the acquisition timestamp. No future-dated artifact was staged.

| Package | Selected version | Wheel tag | Target compatibility |
|---|---:|---|---|
| onnx | 1.23.0 | `cp312-abi3-win_amd64` | PASS: stable ABI supports CPython 3.13 / Windows AMD64 |
| pycocotools | 2.0.11 | `cp312-abi3-win_amd64` | PASS: stable ABI supports CPython 3.13 / Windows AMD64 |
| numpy | 2.5.3 | `cp313-cp313-win_amd64` | PASS |
| protobuf | 7.36.2 | `cp310-abi3-win_amd64` | PASS: stable ABI supports CPython 3.13 / Windows AMD64 |
| ml_dtypes | 0.6.0 | `cp313-cp313-win_amd64` | PASS |
| typing_extensions | 4.16.0 | `py3-none-any` | PASS; identical wheel was already staged |

## Dependency Closure

| Root / dependency | Declared requirement | Resolution |
|---|---|---|
| onnx 1.23.0 | Python >=3.10 | Python 3.13.12 |
| onnx → numpy | `numpy>=1.23.2` | numpy 2.5.3 |
| onnx → protobuf | `protobuf>=6.31.1` | protobuf 7.36.2 |
| onnx → typing_extensions | `typing_extensions>=4.7.1` | typing_extensions 4.16.0, already staged |
| onnx → ml_dtypes | `ml_dtypes>=0.5.4` | ml_dtypes 0.6.0 |
| pycocotools 2.0.11 | Python >=3.9 | Python 3.13.12 |
| pycocotools → numpy | `numpy` | numpy 2.5.3 |

Pillow (ONNX `reference` extra) and matplotlib (pycocotools `all` extra) are
optional extras and are not part of the requested runtime closure. An offline
dry-run combining the existing Torch 2.10.0+cpu set with ONNX 1.23.0 and
pycocotools 2.0.11 completed without conflict and selected 15 staged wheels.
No source distribution was selected.

## Wheel Metadata Review

| Package | METADATA name/version | Requires-Python | WHEEL generator | Purelib | Required dependencies |
|---|---|---|---|---|---|
| onnx | onnx 1.23.0 | >=3.10 | scikit-build-core 1.0.3 | false | numpy, protobuf, typing_extensions, ml_dtypes |
| pycocotools | pycocotools 2.0.11 | >=3.9 | setuptools 80.9.0 | false | numpy |
| numpy | numpy 2.5.3 | >=3.12 | meson | false | none |
| protobuf | protobuf 7.36.2 | >=3.10 | bazel-wheelmaker 1.0 | false | none |
| ml_dtypes | ml_dtypes 0.6.0 | >=3.10 | scikit-build-core 1.0.3 | false | numpy (version conditioned by Python) |
| typing_extensions | typing_extensions 4.16.0 | >=3.9 | flit 3.12.0 | true | none |

All six wheel archives passed ZIP integrity checks. Embedded METADATA
name/version values matched their filenames.

## Hash Verification and Provenance

Every SHA-256 below was recomputed locally and matched the official PyPI file
digest exactly.

| Artifact | Bytes | SHA-256 | Official digest |
|---|---:|---|---|
| `onnx-1.23.0-cp312-abi3-win_amd64.whl` | 7,872,197 | `70a2f930b221f9dbdff62704838ce8bf81442787b25048f8b9cdc9118168799e` | MATCH |
| `pycocotools-2.0.11-cp312-abi3-win_amd64.whl` | 77,570 | `ffe806ce535f5996445188f9a35643791dc54beabc61bd81e2b03367356d604f` | MATCH |
| `numpy-2.5.3-cp313-cp313-win_amd64.whl` | 12,560,965 | `71cad2b2a7451ab79d8f5e71b453485b6775963d5cf794179144a7463fe6e8ec` | MATCH |
| `protobuf-7.36.2-cp310-abi3-win_amd64.whl` | 456,514 | `a300819d441e078a5608c0d3c709796bb548136058fda017ae51d425b44fd353` | MATCH |
| `ml_dtypes-0.6.0-cp313-cp313-win_amd64.whl` | 439,357 | `fb87f46b4f7ad7b5d3ad8f4b452b024bd4229d44c8ff934798c1fe656210387a` | MATCH |
| `typing_extensions-4.16.0-py3-none-any.whl` | 45,571 | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | MATCH; pre-existing |

Official artifact URLs and upload timestamps:

| Package | Official artifact URL | PyPI upload UTC |
|---|---|---|
| onnx | `https://files.pythonhosted.org/packages/81/5a/766abb1411b9f9b06dc4e8fe9ff195d3b715535677c362ab3d950fa0e93f/onnx-1.23.0-cp312-abi3-win_amd64.whl` | 2026-09-18T19:30:20.619654Z |
| pycocotools | `https://files.pythonhosted.org/packages/83/b4/f6708404ff494706b80e714b919f76dc4ec9845a4007affd6d6b0843f928/pycocotools-2.0.11-cp312-abi3-win_amd64.whl` | 2025-12-15T22:31:17.703037Z |
| numpy | `https://files.pythonhosted.org/packages/f3/ec/100f2b1794ede74a9b3d7ec6b9736927f56713414c1dfe19ab6c383494bf/numpy-2.5.3-cp313-cp313-win_amd64.whl` | 2026-09-06T16:25:26.602903Z |
| protobuf | `https://files.pythonhosted.org/packages/8a/55/b77bda4e5e5f5971fb51b07663694690e9afdb9402136c16a522bd621cad/protobuf-7.36.2-cp310-abi3-win_amd64.whl` | 2026-09-17T20:07:57.188171Z |
| ml_dtypes | `https://files.pythonhosted.org/packages/e2/55/4561acefa00fa4bcbfb82ca6a48578b41f372cd7dd7cdd6eb4720abc2e5f/ml_dtypes-0.6.0-cp313-cp313-win_amd64.whl` | 2026-08-13T14:14:12.172352Z |
| typing_extensions | `https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl` | 2026-07-02 |

PyPI Integrity API records were present for ONNX, pycocotools, numpy,
ml_dtypes, and typing_extensions; every returned statement subject matched the
selected filename and SHA-256. The protobuf endpoint returned no attestation.
Attestation cryptography was not independently verified. Provenance is therefore
`PARTIAL` and `PROVENANCE_ATTESTATION_NOT_VERIFIED`, not authenticated
supply-chain proof.

## Final Wheelhouse Inventory

Five wheels were newly copied: ONNX, pycocotools, numpy, protobuf, and
ml_dtypes. The identical typing_extensions dependency was already present. All
15 wheelhouse files were SHA-256 hashed after staging.

| Filename | SHA-256 |
|---|---|
| `filelock-3.32.3-py3-none-any.whl` | `7f0ca4bcc0e181c60dbbd8aa9ab5b120ebb99e4e064e83636340056f833a1f09` |
| `fsspec-2026.7.0-py3-none-any.whl` | `b57ddbafedfaef7018c1ecab32aa200a9d7ca26b77965f64e48b70061249d279` |
| `jinja2-3.1.6-py3-none-any.whl` | `85ece4451f492d0c13c5dd7c13a64681a86afae63a5f347908daf103ce6d2f67` |
| `markupsafe-3.0.3-cp313-cp313-win_amd64.whl` | `9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5` |
| `ml_dtypes-0.6.0-cp313-cp313-win_amd64.whl` | `fb87f46b4f7ad7b5d3ad8f4b452b024bd4229d44c8ff934798c1fe656210387a` |
| `mpmath-1.3.0-py3-none-any.whl` | `a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c` |
| `networkx-3.6.1-py3-none-any.whl` | `d47fbf302e7d9cbbb9e2555a0d267983d2aa476bac30e90dfbe5669bd57f3762` |
| `numpy-2.5.3-cp313-cp313-win_amd64.whl` | `71cad2b2a7451ab79d8f5e71b453485b6775963d5cf794179144a7463fe6e8ec` |
| `onnx-1.23.0-cp312-abi3-win_amd64.whl` | `70a2f930b221f9dbdff62704838ce8bf81442787b25048f8b9cdc9118168799e` |
| `protobuf-7.36.2-cp310-abi3-win_amd64.whl` | `a300819d441e078a5608c0d3c709796bb548136058fda017ae51d425b44fd353` |
| `pycocotools-2.0.11-cp312-abi3-win_amd64.whl` | `ffe806ce535f5996445188f9a35643791dc54beabc61bd81e2b03367356d604f` |
| `setuptools-78.1.0-py3-none-any.whl` | `3e386e96793c8702ae83d17b853fb93d3e09ef82ec62722e61da5cd22376dcd8` |
| `sympy-1.14.0-py3-none-any.whl` | `e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5` |
| `torch-2.10.0+cpu-cp313-cp313-win_amd64.whl` | `b719da5af01b59126ac13eefd6ba3dd12d002dc0e8e79b8b365e55267a8189d3` |
| `typing_extensions-4.16.0-py3-none-any.whl` | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |

`wheelhouse/` remains ignored by Git as required; acquisition does not add
large binaries to version control.

## Wheelhouse Verifier

The existing verifier ran with the approved CPython 3.13.12 executable. It
used an isolated temporary `pip --target` operation and did not install into
the approved interpreter environment.

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

This proves binary dependency closure and temporary isolated importability. It
does not replace separately authorized TASK-027-B target-runtime and
zero-egress validation.

## Security and Scope Controls

- Acquisition used only official PyPI endpoints and only for artifact and
  provenance retrieval.
- No runtime network path, downloader, dependency installer, product source,
  test, architecture, requirements, or protected `docs/research/**` content was
  changed.
- No package was installed into the approved Python environment.
- No Gate-2, TASK-027-B, OFF-001 through OFF-004, TASK-024, or Stage 13 work was
  executed.
- E-2 and PRE-08 remain unchanged.

## Current Blocker Disposition

| Blocker | Current disposition |
|---|---|
| HOST-CAP-001 | `ARTIFACT STAGED / RUNTIME NOT VERIFIED` |
| HOST-CAP-003 | `ARTIFACT STAGED / RUNTIME NOT VERIFIED` |
| HOST-CAP-002 | unchanged / PARTIAL |
| OFFLINE-001 | OPEN; revalidation required |
| E-2 | OPEN |
| PRE-08 | PARTIAL / unresolved operational provisioning |
| GATE-2 | BLOCKED; not rerun |

The next authorized action requires a separate validation re-entry packet. It
must explicitly authorize offline installation/import verification in the
approved validation environment, affected regression, Gate-2.1/Gate-2.2, and
OFF-001 through OFF-004 in prerequisite order. Artifact staging alone does not
close either host capability blocker.

---

## TASK-027-E Subsequent Production Dependency Closure

TASK-027-C subsequently proved that the implemented runtime requires PyYAML:
`assurance_system/config/loader.py` parses the three mandatory configuration
files, and `assurance_system/supervisor/orchestrator.py` parses YAML submission
manifests. Both paths use `yaml.safe_load()`. The dependency had not been
declared in `requirements.txt` or the architecture/technical dependency
tables.

TASK-027-E corrected that omission by declaring `PyYAML==6.0.3` through the
existing `requirements.txt` mechanism and updating the authoritative
dependency tables. No second dependency source was created.

### Added artifact

| Field | Value |
|---|---|
| Package | PyYAML 6.0.3 |
| Wheel | `pyyaml-6.0.3-cp313-cp313-win_amd64.whl` |
| Compatibility | CPython 3.13 / CPython 3.13 ABI / Windows AMD64 |
| Requires-Python | `>=3.8` |
| Required dependencies | none |
| Bytes | 154,090 |
| SHA-256 | `79005a0d97d5ddabfeeea4cf676af11e647e41d81c9a7722a193022accdb6b7c` |
| Official digest | MATCH |
| Provenance | PARTIAL — official PyPI source and digest verified; Integrity API returned no provenance object |

The updated wheelhouse contains 16 package wheels. The verifier consumed the
new requirement automatically from `requirements.txt` and reported:

```text
torch>=2.10.0: STAGED
onnx: STAGED
pycocotools: STAGED
PyYAML==6.0.3: STAGED
INSTALL STATUS: PASS
onnx: PASS
torch: PASS
pycocotools: PASS
WHEELHOUSE_VERIFIER_EXIT=0
```

The repository-local CPython 3.13.12 environment separately passed
`import yaml`, `yaml.safe_load`, the committed `ConfigLoader` configuration
set, and the supervisor YAML submission-manifest path. Complete evidence,
including security and regression results, is recorded in
`docs/task027e_dependency_contract_closure.md`.

This update does not rewrite the historical TASK-027-C result. OFF-001 through
OFF-004 and Gate-2 were not rerun. OFF-002 remains blocked because a candidate
Windows Packet Monitor tool is present but no project-approved capture and
acceptance procedure has been frozen. E-2 remains OPEN, PRE-08 remains
PARTIAL, HOST-CAP-002 remains PARTIAL, and TASK-024 remains unauthorized.
