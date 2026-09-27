# artifact_unit_defs/

This directory is reserved for SP-002 artifact-unit definitions for PyTorch models.

**Status: EMPTY — BLOCKED on PRE-03 (SP-002 not yet produced).**

## Why this directory exists

COMP-W-C3A (artifact-unit resolver) requires a formal definition of what
constitutes a single assessable artifact unit for PyTorch models (e.g., a
`.pt` file, a `.pth` checkpoint, a model directory with associated config).

This definition is captured in SP-002 and placed here for use by the worker.

## Blocking condition

PRE-03: SP-002 (artifact-unit definitions) has not yet been produced.

Until PRE-03 is resolved:
- COMP-W-C3A will emit ARTIFACT_UNIT_AMBIGUOUS for all PyTorch assets.
- ONNX artifact-unit definition (single `.onnx` file) is already established
  and does not require SP-002.

See: 10_TECHNICAL_SPECIFICATION_SIH26228.md §1.4 (PRE-03)
     09_ARCHITECTURE_SPECIFICATION_SIH26228.md §22 (open conditions)
