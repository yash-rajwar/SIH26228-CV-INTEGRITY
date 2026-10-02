# ONNX Artifact Unit Specification

Specification ID: `onnx-main-referenced-external-data-v1`
Decision date: 2026-10-05
Resolves: E-2 / SP-002-ONNX

Acceptance: real C3A/C3B identity and restricted Windows supervisor C3A/C3B/C3C
tests passed on 2026-10-02; see `docs/validation/e2_onnx_identity_acceptance.md`.
The decision date above is the date explicitly specified by the owner packet,
not a claim that validation executed on that future date.

This project-owner decision freezes the existing Architecture Specification
AC-03 contract: main `.onnx` plus all referenced external tensor data files.
It does not change artifact semantics, trust boundaries or the hashing algorithm.

## Unit definition

For MVP, one ONNX artifact unit consists of exactly one submitted, contained,
existing regular main `.onnx` file plus every unique contained existing regular
external tensor-data file referenced by its protobuf `external_data` `location`
metadata. The `.onnx` suffix is checked case-insensitively.

- `main_file` is the canonical real path of the main file.
- `external_files` contains canonical real paths, deduplicated and sorted in the
  existing deterministic order. It is `[]` when no external data is referenced.
- Several tensors referencing the same canonical external file include it once.
- Each external member is the complete file byte object, including bytes outside
  declared tensor offset/length slices. Slices do not define artifact membership.
- Unreferenced neighbouring `.bin` or `.onnx.data` files, YAML/JSON/configuration,
  source, directories and files found by globbing or scanning are excluded.

## Recursive reference discovery

C3A retains its complete recursive traversal through populated protobuf message
fields, discovering every reachable external TensorProto supported by the
installed ONNX schema: graph initializers, sparse initializers, tensor-valued and
repeated tensor attributes, nested/subgraph structures and model functions.
Discovery is not restricted to `graph.initializer`.

## COMP-W-C3A resolution procedure

1. Require one submitted main file and resolve canonical paths. Check containment
   before opening/parsing the main model; require a regular `.onnx` file.
2. Parse only the ONNX protobuf header with `load_external_data=False`.
3. Recursively discover external-data locations. Each external tensor must have
   exactly one non-empty location; inconsistent metadata makes the unit ambiguous.
4. Resolve each location relative to the main file's directory. Reject absolute,
   rooted, drive-qualified, UNC and traversal paths, canonical escapes and symlink
   escapes as `ONNX_PATH_CONTAINMENT_VIOLATION` before outside content is opened.
5. A contained missing or non-regular external file or inconsistent manifest
   produces `ARTIFACT_UNIT_AMBIGUOUS`. No hash is authorized for an incomplete unit.
6. Deduplicate and sort the contained regular external members. Return COMPLETED,
   BLACK_BOX and the frozen ID only for a complete unit. Missing ONNX capability
   retains the existing `ASSESSMENT_ERROR` behavior.

```json
{
  "main_file": "<canonical contained .onnx path>",
  "external_files": ["<sorted unique canonical contained referenced file>"],
  "artifact_unit_definition_id": "onnx-main-referenced-external-data-v1"
}
```

The unit above is `raw_signal.artifact_unit` on a successful C3A output, with
`artifact_unit_id` equal to the frozen ID. Diagnostic partial membership in an
ambiguous output is not a resolved unit: the supervisor forwards a unit to C3B
only after a COMPLETED C3A result. Manifest ingestion supplies this approved ID
for ONNX and rejects any caller-supplied mismatching ID.

## C3B hashing contract

C3B validates containment of all members before reading its first member, then
SHA-256 hashes the complete bytes of each member. It sorts canonical member
paths lexicographically, concatenates their lowercase SHA-256 hex digests in
that order, and SHA-256 hashes the ASCII digest sequence. This existing outer
digest remains mandatory for a single-file unit too; a raw main-file digest is
not substituted. Ambiguous/incomplete units emit no identity digest.

Reference comparison retains MATCH / DIFFERENT / UNAVAILABLE semantics. This
decision changes membership authorization only; it adds no reference health or
provenance trust claim.

## Non-claims

- Artifact membership and digest comparison establish byte identity only.
- They do not establish model safety, semantic or behavioral equivalence,
  causal execution, absence of backdoors or trusted provenance.
- PF-002 and the existing limitations/non-claims remain mandatory and unchanged.
- No ONNX model execution or ONNX Runtime is introduced.
