# TASK-001 — P1 Condition Decision Register

Date: 2026-09-27
Branch: `task/task-001-p1-decisions`
Authority: TASK-001 in `docs/MVP_IMPLEMENTATION_PLAN.md`

This register records the disposition of PRE-01 through PRE-09. It does not
claim that an unresolved condition has been satisfied. Components named below
remain constrained by any unresolved condition or unverified host capability.

## Decision summary

| ID | Decision | Status | Consequence |
|---|---|---|---|
| PRE-01 | Primary development and SIH demonstration target: Windows 10 Pro (version 2009, build 22631), AMD64, Python 3.13.12, 16 GB RAM. | **RESOLVED** | Target platform is identified. Native-extension, wheelhouse, resource-limit, and offline capabilities remain separately unverified and must not be claimed. |
| PRE-02 | Use **HMAC-SHA256** for MVP provenance signing. | **RESOLVED** | No `cryptography` dependency is required. HMAC provides integrity/authenticity under a shared-secret assumption, but not public verification or asymmetric non-repudiation. |
| PRE-03 | A PyTorch artifact unit is one contained regular `.pt` or `.pth` file; companion configuration is not part of the MVP unit. | **RESOLVED** | See `artifact_unit_defs/pytorch_artifact_unit_spec.md`. |
| PRE-04 | Freeze schema version `v1.0`, active worker output ID `worker-output-v1`, the §3.2 worker assessment vocabulary, and canonicalization ID `json-canonical-utf8-sort-keys-v1`. | **RESOLVED** | TASK-002 may begin. See `docs/sp003_vocabulary_contract.md`. |
| PRE-05 | MVP formats: COCO JSON, YOLO detection, YOLO segmentation, PyTorch `.pt/.pth`, ONNX with or without external data. YOLO pose and OBB are not in MVP. | **RESOLVED** | Unsupported variants must emit `UNSUPPORTED`; target-dependent libraries remain conditional on Windows AMD64 / Python 3.13.12 compatibility verification. |
| PRE-06 | R0–R7 fail-closed reference-health procedure is defined. | **RESOLVED** | See `docs/sp001_reference_health_gates.md`. All references still start `UNAVAILABLE`; none is promoted merely by this decision. |
| PRE-07 | Organizer-supplied inference records are not available for MVP; ingestion is excluded from MVP. | **RESOLVED — EXCLUDED FROM MVP** | No inference-record ingestion path is built. This does not weaken the PF-002 non-claim. |
| PRE-08 | HMAC parameters and hex signature encoding are frozen; the host-specific absolute key path is not. | **PARTIALLY RESOLVED / PATH UNRESOLVED** | COMP-C4 remains a `SIGNING_UNAVAILABLE` shell until a Windows absolute key path and supervisor-only ACL are provisioned. See `docs/sp004_crypto_profile.md`. |
| PRE-09 | The C3→C4 adapter mapping is frozen. | **RESOLVED** | See `docs/sp006_c3_c4_adapter_schema.md`. |

## PRE-01 — target host record

**Decision status:** RESOLVED

**Purpose:** Identify the concrete platform against which subprocess isolation,
dependency compatibility, wheel staging, and eventual offline validation must
be evaluated. This decision identifies the platform; it does not validate
capabilities that were not observed on that platform.

The project owner has designated the measured machine below as the project's
current primary development and SIH demonstration target environment.

| Required fact | Recorded value |
|---|---|
| WindowsProductName | `Windows 10 Pro` |
| WindowsVersion | `2009` |
| OsBuildNumber | `22631` |
| OsArchitecture | `64-bit` |
| CPU architecture | `AMD64` |
| Python version | `Python 3.13.12` |
| Available physical RAM | `16 GB` |
| Microsoft `cl.exe` | `NOT DETECTED` |
| `gcc` | `NOT DETECTED` |
| `clang` | `NOT DETECTED` |
| Python `resource` module available | `False` |
| `resource.setrlimit` and Linux RLIMIT controls | `NOT AVAILABLE` |
| `subprocess.Popen(..., close_fds=True)` | `SUPPORTED — verified` |

### Verification summary

The project owner executed the target-host measurements and supplied the
following results:

- Windows product/version/build and architecture queries returned Windows 10
  Pro, version 2009, build 22631, 64-bit, with AMD64 CPU architecture.
- The Python version check returned `Python 3.13.12`.
- The physical-memory check reported 16 GB available RAM.
- Command-discovery checks for `cl.exe`, `gcc`, and `clang` detected no C
  compiler.
- The Python module probe reported `resource` unavailable; consequently
  `resource.setrlimit`, `RLIMIT_AS`, `RLIMIT_NOFILE`, and `RLIMIT_NPROC` are not
  available on this Windows target.
- A `subprocess.Popen` compatibility probe using `close_fds=True` completed
  successfully with return code `0` and child stdout `123`.

### Supported and unavailable capabilities

Supported on the confirmed target:

- `subprocess.Popen(..., close_fds=True)` may be used as directly verified.

Unavailable or not yet validated:

- Python `resource.setrlimit` and the Unix `RLIMIT_AS`, `RLIMIT_NOFILE`, and
  `RLIMIT_NPROC` controls are unavailable and must not be claimed.
- No C compiler is currently detected. Components requiring native compilation
  must not assume one exists.
- `pycocotools` and all other native-extension support require separate
  target-host verification before support is claimed.
- Offline dependency and wheel support must be validated specifically for
  Windows AMD64 and Python 3.13.12 before any offline deployment claim.
- Linux-specific isolation mechanisms must not be silently substituted on this
  Windows host. A different isolation mechanism, if required later, must follow
  architecture change control; PRE-01 does not select or invent one.

Support for any other operating system, Python version, CPU architecture, or
hardware configuration is not claimed until that environment is separately
validated.

## PRE-02 — signing mechanism

Decision: **HMAC-SHA256**.

Rationale:

- It uses the Python standard library and therefore minimizes target-specific
  air-gapped wheel closure.
- It matches the integrity/authenticity requirement for a single offline
  supervisor holding the key.
- Verification requires the shared secret. It does not provide public
  verification or asymmetric non-repudiation; those properties are not claimed.
- A later change to Ed25519 is a crypto-profile change and must use the normal
  architecture change-control process; it is not an automatic fallback.

## PRE-05 — mandatory MVP formats

The declarative configuration is in
`assurance_system/config/supported_formats.yaml`, the authoritative location
from Technical Specification §2.2. The TASK-001 prompt's shorthand
`config/supported_formats.yaml` is interpreted as that module-relative path,
not as authority to create a second configuration tree.

| Format | MVP decision | Qualification |
|---|---|---|
| COCO JSON | In scope | Runtime availability remains conditional on a compatible `pycocotools` wheel or separately approved native-extension path; no C compiler is currently detected. |
| YOLO_DETECTION | In scope | All-box structural validation required. |
| YOLO_SEG | In scope | Polygon structural validation only; no semantic correctness claim. |
| YOLO_POSE | Not in MVP | Must produce `UNSUPPORTED`, never a positive finding. |
| YOLO_OBB | Not in MVP | Must produce `UNSUPPORTED`, never a positive finding. |
| PyTorch `.pt/.pth` | In scope | Runtime availability remains conditional on a Windows AMD64 / Python 3.13.12 CPU wheel for `torch >= 2.10.0`; `weights_only=True` only, with no fallback. |
| ONNX without external data | In scope | Required by Technical Specification §13.1/§13.5. |
| ONNX with external data | In scope | Required with C3A containment checks. |
| TorchScript | Deferred in scope | Emits `DEFERRED_IN_SCOPE`; it is not treated as assessed. |

## PRE-07 — inference record source

Decision: no organizer-supplied inference-record source is established for the
MVP. The ingestion path is excluded from MVP and no synthetic substitute is
presented as organizer evidence. Provenance records bind artifact and evidence
record digests only. The mandatory PF-002 statement remains present: a signed
binding does not prove that the named model executed assessed inferences.

## Implementation release boundary

PRE-01 and PRE-04 are complete, so target-independent Stage 3 work may proceed
after its entry-state check. This decision does not release:

- offline deployment, `pycocotools`, ONNX-wheel, or torch-wheel claims until
  each is separately verified on Windows AMD64 with Python 3.13.12;
- Unix RLIMIT enforcement or any unapproved replacement isolation mechanism;
- operational signing (PRE-08 key storage path/provisioning remains unresolved);
- TASK-027 offline validation, which must still execute and pass before any
  offline capability claim.
