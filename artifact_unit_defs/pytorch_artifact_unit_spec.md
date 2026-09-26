# PyTorch Artifact Unit Specification

Specification ID: `pytorch-single-file-v1`  
Decision date: 2026-09-27  
Resolves: PRE-03 / SP-002 for the MVP PyTorch path

## Unit definition

For MVP, one PyTorch artifact unit is exactly one submitted regular file whose
case-insensitive extension is `.pt` or `.pth`.

- The file is the `main_file`.
- `external_files` is always an empty list.
- Companion YAML/JSON configuration, source code, class definitions,
  optimizer state in separate files, and arbitrary neighbouring files are not
  members of the artifact unit.
- TorchScript remains `DEFERRED_IN_SCOPE` and is not reclassified by this
  definition.
- The unit definition enables byte-identity hashing and the C3D safe-loading
  gate only. It does not claim that a state dict is sufficient to reconstruct
  or execute a model.

## COMP-W-C3A resolution procedure

Given `model_path` and `asset_directory`, C3A performs these checks in order:

1. Resolve both paths to canonical real paths.
2. Require `model_path` to remain within `asset_directory` after symlink and
   junction resolution. A prefix string comparison without a path-boundary
   check is insufficient.
3. Require an existing regular file; reject directories, devices, pipes, and
   missing paths.
4. Require a case-insensitive `.pt` or `.pth` suffix. Other suffixes are
   `UNSUPPORTED` for this definition.
5. Do not search for, infer, or automatically include companion files.
6. Return the resolved unit below. C3A does not import `torch` or deserialize
   the file while resolving the unit.

```json
{
  "main_file": "<canonical contained path>",
  "external_files": [],
  "artifact_unit_definition_id": "pytorch-single-file-v1"
}
```

If containment or regular-file checks fail, the resolver returns a non-positive
failure record; it never hashes or loads an out-of-scope path. If the definition
cannot be loaded, the existing `ARTIFACT_UNIT_AMBIGUOUS` behavior remains.

## C3B hashing contract

C3B hashes the complete `main_file` bytes with SHA-256. The combined artifact
digest uses the Technical Specification §3.8 algorithm over the resolved file
list. With one file, it is still the outer SHA-256 of the inner file digest's
ASCII hex representation; it is not silently replaced by the raw per-file
digest.

## Non-claims

- A digest match establishes byte identity only.
- `LOAD_SUCCESS` under `weights_only=True` does not establish model safety,
  semantic equivalence, or absence of backdoors.
- Excluding companion configuration means the digest does not identify a full
  executable inference environment.

