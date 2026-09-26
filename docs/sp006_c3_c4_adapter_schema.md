# SP-006 C3→C4 Adapter Schema

Decision date: 2026-09-27
Resolves: PRE-09

## Boundary rule

C4 never consumes a raw worker result. The supervisor first validates the
worker output through COMP-SCHEMA, adds supervisor-owned fields, persists it
through the sole evidence-store write path, and computes `record_digest`.
Only those validated values enter the adapter.

## Exact field mapping

| C4 provenance field | Validated source | Mapping rule |
|---|---|---|
| `artifact_unit_digest` | C3B evidence record `raw_signal.combined_artifact_unit_digest` | Copy only after the C3B record has `assessment_status = COMPLETED` and the value is exactly 64 lowercase hex characters. No external input may supply or override it. |
| `evidence_record_digests` | Supervisor-owned `record_digest` on persisted C2/C3 evidence records | Build an array from every evidence record selected for this provenance binding, sorted lexicographically by `record_id` before extracting its digest. Each digest must be 64 lowercase hex characters. |

No other worker field is copied into a top-level provenance field.
`artifact_unit_definition_id`, `per_file_digests`, `sorted_path_order_used`,
`comparison_result`, C3A resolution details, C3C structural results, and C3D
safe-load results remain in their evidence records. They are bound indirectly
because those evidence records' supervisor-computed digests are included in
`evidence_record_digests`.

## C4-generated fields

These fields are generated or supplied inside the trusted supervisor and are
not mapped from C3 worker output:

| Provenance field | Trusted source |
|---|---|
| `provenance_id` | Supervisor UUID4 generator |
| `signing_key_id` | Supervisor signing configuration/key registry; never key material |
| `signature` | HMAC-SHA256 over canonical unsigned record, hex encoded; otherwise null |
| `signature_algorithm` | `HMAC-SHA256` on success; otherwise null |
| `canonicalization_algorithm` | Frozen SP-003 value `json-canonical-utf8-sort-keys-v1` |
| `sequence_number` | Durable supervisor sequence state |
| `replay_nonce` | Supervisor UUID4 hex generator |
| `pf_002_non_claim` | Mandatory constant from the Technical Specification; never worker-supplied |
| `signing_status` | `SIGNED` or `SIGNING_UNAVAILABLE` from supervisor signing outcome |
| `timestamp` | Supervisor local system clock with AF-003 caveat |

## Adapter failure behavior

- Missing or non-completed C3B evidence, a malformed artifact digest, missing
  persisted evidence, or malformed record digests prevents construction of a
  signed binding. The adapter does not substitute `UNAVAILABLE` for a required
  digest and does not report success.
- `ARTIFACT_UNIT_AMBIGUOUS`, `ASSESSMENT_ERROR`, `UNAVAILABLE`, and containment
  violations remain visible in their evidence and findings; C4 does not convert
  them into a positive state.
- A signing failure follows SP-004 and produces an unsigned provenance record
  explicitly marked `SIGNING_UNAVAILABLE`; it is never represented as signed.
