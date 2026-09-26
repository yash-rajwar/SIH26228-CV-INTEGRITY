# artifact_unit_defs/

This directory is reserved for SP-002 artifact-unit definitions for PyTorch models.

**Status: PRE-03 RESOLVED — `pytorch_artifact_unit_spec.md` is the active MVP definition.**

## Why this directory exists

COMP-W-C3A (artifact-unit resolver) requires a formal definition of what
constitutes a single assessable artifact unit for PyTorch models (e.g., a
`.pt` file, a `.pth` checkpoint, a model directory with associated config).

This definition is captured in `pytorch_artifact_unit_spec.md` for use by the
worker.

## Resolution

PRE-03 was resolved on 2026-09-27. The MVP PyTorch unit is one contained
regular `.pt` or `.pth` file. If the active definition cannot be loaded,
COMP-W-C3A still fails closed with `ARTIFACT_UNIT_AMBIGUOUS`.

The ONNX artifact-unit definition remains governed by the Technical
Specification and does not use this PyTorch definition.

See: `docs/TECHNICAL_SPECIFICATION.md` §1.4 (PRE-03)
     `docs/ARCHITECTURE_SPECIFICATION.md` §22 (open conditions)
