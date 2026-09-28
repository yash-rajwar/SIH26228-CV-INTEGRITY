# TASK-027-E Dependency-Contract Closure Evidence

**Date:** 2026-09-28
**Branch:** `feature/vertical-slice`
**Integrated compatibility commit:** `81bfd369ef611553556546a6c311ccd253308b13`
**Status:** `DEPENDENCY CLOSURE VERIFIED; OFFLINE/GATE VALIDATION NOT EXECUTED`

## 1. Executive state

TASK-027-E fast-forwarded `feature/vertical-slice` from `94501ba` to the
unchanged C3A/C3C compatibility commit `81bfd36`. The production dependency
contract now declares PyYAML 6.0.3, and its exact CPython 3.13 / Windows AMD64
binary wheel is staged and verified. The wheelhouse verifier passes with
PyYAML included through the active `requirements.txt` declaration.

This is dependency readiness evidence only. OFF-001 through OFF-004 and
Gate-2 were not executed. No offline capability claim is made.

## 2. Production import evidence

PyYAML is a direct production dependency:

- `assurance_system/config/loader.py` imports `yaml` and calls
  `yaml.safe_load()` for `system_config.yaml`, `resource_limits.yaml`, and
  `supported_formats.yaml`.
- `assurance_system/supervisor/orchestrator.py` imports `yaml` and calls
  `yaml.safe_load()` for submitted `.yaml` and `.yml` manifests.
- Production callers include C2A configuration loading, supervisor and CLI
  configuration, worker resource-limit loading, and YAML manifest ingestion.

TASK-027-C demonstrated the omitted dependency as both
`ModuleNotFoundError: No module named 'yaml'` and a fail-closed C2A
`CONFIGURATION_ERROR` before COCO parsing.

## 3. Dependency-contract omission

The architecture, technical specification, and MVP configuration task require
runtime YAML files, while the previous dependency table and inactive
`requirements.txt` stub omitted the parser used by the implemented runtime.
There is no stdlib YAML parser and JSON manifest support does not eliminate the
three required YAML configuration files.

## 4. Dependency declaration

The existing dependency declaration mechanism is `requirements.txt`, which is
already consumed by `scripts/verify_wheelhouse.py`. It now contains the single
active declaration:

```text
PyYAML==6.0.3
```

The architecture and technical dependency tables record the same pinned
production dependency. No competing dependency manifest was created.

## 5. PyYAML version decision

| Field | Decision |
|---|---|
| Package | PyYAML |
| Selected version | 6.0.3 |
| Reason | Stable release with an official native CPython 3.13 / Windows AMD64 wheel; matches the frozen interpreter without a source build; supports the existing `safe_load` API; no declared dependencies |
| Wheel | `pyyaml-6.0.3-cp313-cp313-win_amd64.whl` |
| Python tag | `cp313` |
| ABI tag | `cp313` |
| Platform tag | `win_amd64` |
| Requires-Python | `>=3.8` |
| Requires-Dist | none |

No ONNX, protobuf, NumPy, Torch, ml_dtypes, or pycocotools version changed.

## 6. Wheel compatibility

The selected file is a binary wheel (`bdist_wheel`) from official PyPI. Its
embedded `WHEEL` metadata declares `Root-Is-Purelib: false` and
`Tag: cp313-cp313-win_amd64`. Its embedded `METADATA` declares PyYAML 6.0.3,
`Requires-Python: >=3.8`, and no `Requires-Dist` entries. ZIP integrity passed.
No compiler or source distribution is involved.

## 7. SHA-256

| Field | Value |
|---|---|
| Source | Official PyPI JSON API and `files.pythonhosted.org` artifact host |
| Source URL | `https://files.pythonhosted.org/packages/97/c9/39d5b874e8b28845e4ec2202b5da735d0199dbe5b8fb85f91398814a9a46/pyyaml-6.0.3-cp313-cp313-win_amd64.whl` |
| Size | 154,090 bytes |
| Locally computed SHA-256 | `79005a0d97d5ddabfeeea4cf676af11e647e41d81c9a7722a193022accdb6b7c` |
| Official PyPI SHA-256 | `79005a0d97d5ddabfeeea4cf676af11e647e41d81c9a7722a193022accdb6b7c` |
| Hash match | PASS |
| PyPI upload UTC | `2025-09-25T21:32:33.659120Z` |
| Acquisition UTC | `2026-09-28T13:08:20Z` |

## 8. Provenance

The artifact was obtained from official PyPI, and its locally computed digest
matches the digest published by the official JSON API. PyPI's Integrity API
returned HTTP 404 with `No provenance available` for this exact wheel, so no
PEP 740 attestation was available to verify. Provenance is therefore
`PARTIAL`, not authenticated supply-chain proof.

## 9. Complete wheelhouse closure

PyYAML declares no additional dependencies. The existing Torch 2.10.0+cpu,
ONNX 1.23.0, protobuf 7.36.2, NumPy 2.5.3, ml_dtypes 0.6.0,
pycocotools 2.0.11, and supporting wheels remain unchanged. The wheelhouse now
contains 16 package wheels. It remains ignored by Git as required for binary
deployment artifacts.

## 10. Verifier result

The approved CPython 3.13.12 interpreter executed
`scripts/verify_wheelhouse.py` with `--no-index`, a local `--find-links`, and
an isolated temporary install target.

```text
PACKAGE STATUS
torch>=2.10.0: STAGED
onnx: STAGED
pycocotools: STAGED
PyYAML==6.0.3: STAGED
INSTALL STATUS: PASS
IMPORT STATUS
onnx: PASS
torch: PASS
pycocotools: PASS
WHEELHOUSE_VERIFIER_EXIT=0
```

PyYAML is included automatically from `requirements.txt`; it is not hard-coded
in verifier code. The direct production import checks below separately verify
the distribution-to-import-name mapping (`PyYAML` → `yaml`).

## 11. Configuration-load verification

The repository-local `.venv-torch-test` uses CPython 3.13.12. PyYAML 6.0.3,
ONNX 1.23.0, and pycocotools 2.0.11 were installed into it using only the
approved wheelhouse with `--no-index` and binary-only policy.

- `import yaml`: PASS; origin is the repository-local environment.
- `yaml.safe_load('enabled: true')`: PASS.
- `ConfigLoader.load()` against the committed three-file configuration set:
  PASS.
- Configuration and supervisor manifest regression: 24 passed.
- The supervisor `.yaml` manifest path is covered by a focused integration
  test through `SupervisorOrchestrator._load_manifest()`.

The first focused test run exposed an over-strict test equality assertion
because the established manifest validator adds normalized asset defaults.
The test was corrected to assert the stable manifest fields; production logic
was not changed.

## 12. C3A/C3C regression

- Complete C3A/C3C suite: 48 passed.
- C3A: 30 passed.
- C3C: 18 passed.
- C3B/schema/orchestrator affected regression: 42 passed.

Recursive protobuf-reachable TensorProto traversal, external-reference
extraction, absolute/traversal/symlink containment, malformed protobuf
handling, checker-only structural validation, `load_external_data=False`,
PF-002, EF-004, and the no-ORT/no-execution boundary remain intact.

E-2 remains open: valid ONNX C3A output remains
`ARTIFACT_UNIT_AMBIGUOUS` with definition ID `UNAVAILABLE`.

## 13. Security regression

- Security suite: 87 passed, 6 pre-existing task-gated skips.
- Zero production matches: `weights_only=False`, `risk_score`,
  `aggregate_assurance`, `compromise_probability`, `confidence_score`,
  `trust_score`, `shell=True`, `load_external_data=True`, prohibited positive
  assurance constants, ONNX Runtime imports, production network imports,
  runtime pip-install logic, and unsafe YAML APIs.
- The only production YAML parse calls are `yaml.safe_load()` in the approved
  configuration loader and supervisor manifest path.

## 14. Zero-egress capability

Windows Packet Monitor (`pktmon.exe`) is installed and the session is elevated,
but the host currently has an active 1 Gbps Ethernet adapter. No project-
approved capture/filter procedure or acceptance rule has yet been frozen.
Consequently, the presence of PktMon is only a candidate mechanism, not
OFF-002 evidence.

An acceptable future OFF-002 procedure must, at minimum, approve the exact
PktMon capture configuration, reset counters, capture the entire full-pipeline
run at the NIC layer, retain ETL/PCAPNG plus counters, and define the assertion
that outbound bytes are zero. Network isolation or firewall denial may be an
additional control, but `--no-index` alone is insufficient.

**ZERO-EGRESS MECHANISM:** `UNAVAILABLE — candidate tool present, evidence procedure not approved`
**OFF-002:** `BLOCKED`

## 15. E-2

`OPEN`. No ONNX artifact-unit definition ID was created or inferred.

## 16. PRE-08

`PARTIAL`. Operational signing key-path and ACL provisioning are unchanged.

## 17. Gate-2 state

Gate-2 was not run. Gate-2.1 and Gate-2.2 remain `BLOCKED`; Gate-2.3 through
Gate-2.7 retain their previously recorded `PASS` evidence. Overall Gate-2
remains `BLOCKED`.

## 18. TASK-024 state

`NOT STARTED / NOT AUTHORIZED`. No dashboard file or test was touched.

## 19. Remaining blockers

1. OFF-002 lacks an approved zero-egress evidence procedure.
2. OFF-001 through OFF-004 require a separately authorized fresh validation
   run; this dependency-closure task did not rewrite their historical results.
3. HOST-CAP-001 and HOST-CAP-003 require formal revalidation against the now-
   prepared dependency/runtime state.
4. HOST-CAP-002 remains `PARTIAL`.
5. E-2 remains `OPEN`.
6. PRE-08 remains `PARTIAL`.
7. Gate-2 remains `BLOCKED`, and TASK-024 remains unauthorized.
