# TASK-001 — P1 Condition Decision Register

Date: 2026-09-27
Branch: `task/task-001-p1-decisions`
Authority: TASK-001 in `docs/MVP_IMPLEMENTATION_PLAN.md`

This register records the disposition of PRE-01 through PRE-09. It does not
claim that an unresolved condition has been satisfied. Implementation may
begin at TASK-002 because PRE-04 is resolved, but components named below
remain blocked by their unresolved conditions.

## Decision summary

| ID | Decision | Status | Consequence |
|---|---|---|---|
| PRE-01 | The target deployment host has not been identified by the project owner. | **UNRESOLVED** | No offline capability claim; no target wheelhouse/ABI closure; TASK-027 and target-dependent portions of TASK-010/TASK-017 remain blocked. |
| PRE-02 | Use **HMAC-SHA256** for MVP provenance signing. | **RESOLVED** | No `cryptography` dependency is required. HMAC provides integrity/authenticity under a shared-secret assumption, but not public verification or asymmetric non-repudiation. |
| PRE-03 | A PyTorch artifact unit is one contained regular `.pt` or `.pth` file; companion configuration is not part of the MVP unit. | **RESOLVED** | See `artifact_unit_defs/pytorch_artifact_unit_spec.md`. |
| PRE-04 | Freeze schema version `v1.0`, active worker output ID `worker-output-v1`, the §3.2 worker assessment vocabulary, and canonicalization ID `json-canonical-utf8-sort-keys-v1`. | **RESOLVED** | TASK-002 may begin. See `docs/sp003_vocabulary_contract.md`. |
| PRE-05 | MVP formats: COCO JSON, YOLO detection, YOLO segmentation, PyTorch `.pt/.pth`, ONNX with or without external data. YOLO pose and OBB are not in MVP. | **RESOLVED** | Unsupported variants must emit `UNSUPPORTED`; target-dependent implementations remain conditional on PRE-01. |
| PRE-06 | R0–R7 fail-closed reference-health procedure is defined. | **RESOLVED** | See `docs/sp001_reference_health_gates.md`. All references still start `UNAVAILABLE`; none is promoted merely by this decision. |
| PRE-07 | Organizer-supplied inference records are not available for MVP; ingestion is excluded from MVP. | **RESOLVED — EXCLUDED FROM MVP** | No inference-record ingestion path is built. This does not weaken the PF-002 non-claim. |
| PRE-08 | HMAC parameters and hex signature encoding are frozen; the host-specific absolute key path is not. | **PARTIALLY RESOLVED / PATH UNRESOLVED** | COMP-C4 remains a `SIGNING_UNAVAILABLE` shell until PRE-01 identifies a target and the supervisor-only key path is provisioned. See `docs/sp004_crypto_profile.md`. |
| PRE-09 | The C3→C4 adapter mapping is frozen. | **RESOLVED** | See `docs/sp006_c3_c4_adapter_schema.md`. |

## PRE-01 — target host record

No statement supplied with TASK-001 identifies the machine on which the
offline deliverable will be judged or deployed. The current development
machine is not silently treated as that target.

| Required fact | Recorded value |
|---|---|
| Operating system and version | `UNRESOLVED` |
| CPU architecture | `UNRESOLVED` |
| Python version | `UNRESOLVED` |
| Available RAM (MB) | `UNRESOLVED` |
| C compiler present for pycocotools | `UNRESOLVED` |
| `resource.setrlimit` / `RLIMIT_AS` / `RLIMIT_NOFILE` / `RLIMIT_NPROC` | `UNRESOLVED` |
| `subprocess.Popen(..., close_fds=True)` verified | `UNRESOLVED` |

PRE-01 can be closed only by a target-host execution record containing the
above facts and command/test evidence. Until then, no offline capability claim
is permissible.

## PRE-02 — signing mechanism

Decision: **HMAC-SHA256**.

Rationale:

- It uses the Python standard library and therefore minimizes the air-gapped
  wheel closure while PRE-01 remains open.
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
| COCO JSON | In scope | Runtime availability remains conditional on pycocotools target-host closure (PRE-01). |
| YOLO_DETECTION | In scope | All-box structural validation required. |
| YOLO_SEG | In scope | Polygon structural validation only; no semantic correctness claim. |
| YOLO_POSE | Not in MVP | Must produce `UNSUPPORTED`, never a positive finding. |
| YOLO_OBB | Not in MVP | Must produce `UNSUPPORTED`, never a positive finding. |
| PyTorch `.pt/.pth` | In scope | Runtime availability remains conditional on PRE-01 and `torch >= 2.10.0`; `weights_only=True` only, with no fallback. |
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

PRE-04 is complete, so TASK-002 may begin. This decision does not release:

- target-dependent offline, pycocotools, ONNX-wheel, or torch-wheel claims
  (PRE-01 remains unresolved);
- operational signing (PRE-08 key storage path/provisioning remains unresolved);
- TASK-027 offline validation.
