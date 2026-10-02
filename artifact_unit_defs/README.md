# artifact_unit_defs/

This directory contains the approved SP-002 artifact-unit definitions for MVP
PyTorch and ONNX model identity.

| Format | Definition | Decision record |
|---|---|---|
| PyTorch | `pytorch-single-file-v1` | [PyTorch specification](pytorch_artifact_unit_spec.md), PRE-03 resolved 2026-09-27 |
| ONNX | `onnx-main-referenced-external-data-v1` | [ONNX specification](onnx_artifact_unit_spec.md), owner decision dated 2026-10-05; E-2 resolved by real acceptance executed 2026-10-02 |

## Why this directory exists

COMP-W-C3A (artifact-unit resolver) requires a formal definition of what
constitutes one assessable artifact unit for each supported model format.

The two definitions above provide the trusted format-specific membership rules.
Submitted manifests cannot select arbitrary definition IDs.

## Resolution

PRE-03 was resolved on 2026-09-27. The MVP PyTorch unit is one contained
regular `.pt` or `.pth` file. If the active definition cannot be loaded,
COMP-W-C3A still fails closed with `ARTIFACT_UNIT_AMBIGUOUS`.

The ONNX unit is one regular contained `.onnx` file plus every unique referenced
contained regular external tensor-data file. Recursive discovery is preserved;
complete external files are hashed, while unreferenced neighbours are excluded.
Incomplete units fail closed without a digest. This freezes Architecture AC-03
and Technical Specification §3.7/§3.8 under the separate ONNX ID.

See: `docs/TECHNICAL_SPECIFICATION.md` §1.4 (PRE-03)
     `docs/ARCHITECTURE_SPECIFICATION.md` §22 (open conditions)
