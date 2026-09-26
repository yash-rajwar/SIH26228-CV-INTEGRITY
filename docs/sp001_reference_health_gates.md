# SP-001 Reference-Health Gate Procedure

Decision date: 2026-09-27  
Resolves: PRE-06

## Default and authority

Every reference starts as `UNAVAILABLE`. Registering a file, successfully
parsing it, or labelling it a format example does not make it
`HEALTH_VERIFIED`. Only the supervisor reference manager may change health
state, and each transition is written to the fail-closed audit chain.

COCO val2017 and similar public format examples are `FORMAT_ASSET`, never
`HEALTH_VERIFIED` under this procedure.

## Gates R0–R7

| Gate | Required check | Pass evidence |
|---|---|---|
| R0 — Registration and scope | A unique `reference_id`, reference name, intended format/category, assessment scope, and accountable owner are recorded. The category is not `FORMAT_ASSET`. | Supervisor-created registration record with all fields present. |
| R1 — Source authorization | The owner records the acquisition/source, licensing or authorization basis, acquisition time, and expected artifact-unit definition. Unknown or unapproved provenance fails the gate. | Owner-approved source record. |
| R2 — Artifact-unit resolution | The applicable C3A/C2 resolver deterministically resolves the complete unit; no ambiguity, missing file, containment violation, or unsupported format exists. | Validated resolver evidence with a non-`UNAVAILABLE` definition ID. |
| R3 — Immutable identity | SHA-256 digests exist for every unit member and the deterministic combined digest; the digest set is stored by the supervisor. | Validated hash evidence and stored digest set. |
| R4 — Structural assessment | All mandatory structural/format assessments for the declared category complete. Any `ASSESSMENT_ERROR`, `UNAVAILABLE`, `UNSUPPORTED`, `ARTIFACT_UNIT_AMBIGUOUS`, `LOAD_BLOCKED`, `LOAD_ERROR`, `ONNX_PATH_CONTAINMENT_VIOLATION`, or `STRUCTURAL_INVALID` fails the gate. | Schema-valid evidence records for every mandatory method. |
| R5 — Baseline review | The accountable owner reviews R0–R4 evidence and records that no unresolved integrity anomaly or contamination indicator is present. An anomaly is not auto-waived. | Dated owner disposition referencing evidence record digests. |
| R6 — Independence and contamination control | The reference is not derived from the submission being assessed and its storage is outside contributor-writable submission paths. Access-control evidence and separation rationale are recorded. | Supervisor-verified storage/ACL and independence record. |
| R7 — Freshness and final authorization | No staleness/invalidating event is open; the verification time and review interval are recorded; an authorized owner approves promotion for the declared scope and time. | Final approval referencing R0–R6 and an expiry/review timestamp. |

## Promotion algorithm

`HEALTH_VERIFIED` is emitted only if all eight records exist, refer to the same
`reference_id` and artifact digest, have `passed: true`, and have no later
invalidating event. Missing, malformed, failed, mismatched, or expired gate
evidence leaves the state `HEALTH_UNVERIFIED`. A missing reference remains
`UNAVAILABLE`. A `FORMAT_ASSET` is never promoted.

The check is all-of, not a score. Gates cannot compensate for one another and
there is no aggregate confidence or risk value.

## Failure and downgrade behavior

- Evidence suggesting contamination sets `CONTAMINATION_SUSPECTED` and emits a
  transition audit event.
- An expired review, artifact modification, key access/ACL change, source
  revocation, or other recorded invalidating event sets `STALE_SUSPECTED`.
- Re-verification requires a new R0–R7 set bound to the current artifact digest;
  old gate records are immutable and are not overwritten.
- Reference-relative methods receive `REFERENCE_UNAVAILABLE` unless the current
  state is exactly `HEALTH_VERIFIED` for the requested scope and time.

## MVP state

No reference has completed these gates. All references therefore remain
`UNAVAILABLE`, and reference-relative methods remain unavailable at MVP start.

