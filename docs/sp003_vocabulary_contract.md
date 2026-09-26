# SP-003 Vocabulary Contract and Schema Version Freeze

Decision date: 2026-09-27  
Resolves: PRE-04

## Frozen identifiers

| Item | Frozen value |
|---|---|
| Project schema version | `v1.0` |
| Active worker input schema ID | `worker-input-v1` |
| Active worker output schema ID | `worker-output-v1` |
| Canonicalization algorithm ID | `json-canonical-utf8-sort-keys-v1` |

Canonicalization is confirmed exactly as Technical Specification §8.1:

```python
json.dumps(
    record_dict,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=True,
).encode("utf-8")
```

NaN, infinity, non-string object keys, and other values outside the declared
schemas are rejected before canonicalization. The algorithm identifier is
included in each provenance record.

## Worker `assessment_status` vocabulary

The exact allowed set is confirmed from Technical Specification §3.2:

```text
COMPLETED
ASSESSMENT_ERROR
UNAVAILABLE
UNSUPPORTED
DEFERRED_IN_SCOPE
ARTIFACT_UNIT_AMBIGUOUS
LOAD_BLOCKED
LOAD_SUCCESS
LOAD_ERROR
ONNX_PATH_CONTAINMENT_VIOLATION
STRUCTURAL_VALID
STRUCTURAL_INVALID
REFERENCE_UNAVAILABLE
```

No other value is valid in the `assessment_status` field of a worker output.
In particular:

- `SCHEMA_VIOLATION` is a supervisor validation/audit outcome. A rejected
  worker object is not persisted as a valid worker evidence record.
- `SIGNING_UNAVAILABLE` is a provenance `signing_status`, not a worker
  `assessment_status`.
- `APPLICABLE` and related values belong to `applicability_status`.
- No positive assurance term such as `CLEAN`, `SAFE`, or `HEALTHY` is allowed.

## Additional frozen state vocabularies

These are separate typed fields; they do not extend `assessment_status`.

| Field | Allowed values |
|---|---|
| `access_mode` | `BLACK_BOX`, `GREY_BOX`, `WHITE_BOX`, `INTERNAL_ACTIVATION`, `UNAVAILABLE` |
| `detection_status` | `UNAVAILABLE`, `ANOMALY_DETECTED`, `IDENTITY_MATCH`, `IDENTITY_DIFFERENT`, `NO_ANOMALY_DETECTED`, `COMPLETED_STATISTICS_ONLY`, `DEFERRED_IN_SCOPE` |
| `interpretation_status` | `UNAVAILABLE`, `REQUIRES_INVESTIGATION`, `CONSISTENT_WITH_EXPECTED`, `IDENTITY_DEVIATION_DETECTED`, `STATISTICS_REPORTED`, `NO_ANOMALY_DETECTED`, `DEFERRED` |
| `applicability_status` | `APPLICABLE`, `NOT_APPLICABLE`, `UNSUPPORTED`, `DEFERRED_IN_SCOPE`, `REFERENCE_UNAVAILABLE` |
| `analyst_disposition_prompt` | `ACCEPT`, `ACCEPT_WITH_CONTEXT`, `ESCALATE`, `CONTAIN_HOLD`, `OVERRIDE`, `UNAVAILABLE_NO_DECISION` |
| `identity_quality` | `TRUSTED`, `UNTRUSTED`, `UNAVAILABLE` |
| `reference_health` | `UNAVAILABLE`, `HEALTH_UNVERIFIED`, `FORMAT_ASSET`, `HEALTH_VERIFIED`, `CONTAMINATION_SUSPECTED`, `STALE_SUSPECTED` |
| `signing_status` | `SIGNED`, `SIGNING_UNAVAILABLE` |
| `signature_algorithm` | `HMAC-SHA256`, or `null` exactly when `signing_status` is `SIGNING_UNAVAILABLE` |

The vocabulary is otherwise as specified in Technical Specification §3.2 and
§4. This contract does not introduce an aggregate score or any safety verdict.

## Versioning rule

Any addition, removal, or semantic reinterpretation of a frozen value requires
a new schema ID and an approved change record. Aliasing an unknown value to a
known value is prohibited. An unknown or version-mismatched record is rejected
as a schema violation and cannot be interpreted as a positive result.

