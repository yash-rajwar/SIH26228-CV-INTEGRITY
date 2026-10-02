# Architecture Change-Control Log

This log records approved changes under Architecture Specification §23. It does
not replace the architecture or technical specification; approved entries are
also incorporated into those authoritative documents before implementation.

## ACC-2026-10-02-03 — Read-only audit-chain inspection for COMP-IFACE

**Status:** APPROVED by the project-owner TASK-024 continuation packet.
**Scope:** Audit inspection, read-only analyst CLI and TASK-024 dashboard.
Recorded before implementation; resolves TASK-024-AUDIT-READONLY.

`inspect_chain_integrity()` reads audit events and durable chain state, performs
the complete existing integrity checks and returns `ChainVerificationResult`
without writing, resetting or repairing anything. Dashboard and read-only
`show-audit-trail` use this operation. `verify_chain_integrity()` uses that same
inspection implementation and preserves trusted supervisor diagnostics:
`SEQUENCE_GAP_DETECTED` where applicable and `CHAIN_CORRUPT` on violations.
AuditWriteError remains fail-closed and is never swallowed.

No hash-chain algorithm, corruption semantics, stored record, assessment
vocabulary or trust boundary changes. SEC-010 still exercises the trusted
verification path, persists corruption diagnostics and retains historical
events. Historical SEC-010 evidence is not rewritten. Narrow SELECT-only store
queries expose chain state, evidence and provenance to the analyst interface;
no generic SQL access or analyst persistence authority is introduced.

**Acceptance (2026-10-02):** audit unit 12 passed, existing SEC-010 1 passed,
CLI 9 passed and dashboard 27 passed. Full non-offline regression 588 passed /
11 unchanged skips, zero failures. Historical discovery is retained in
PROJECT_STATE.md. Browser visual acceptance is static-only (input access denied).

## SP-002-ONNX / E-2 — Freeze the existing ONNX artifact-unit contract

**Decision date:** 2026-10-05, as specified by the project-owner execution packet.
**Status:** APPROVED / RESOLVED by real ONNX acceptance executed 2026-10-02.
**Record:** `artifact_unit_defs/onnx_artifact_unit_spec.md`.
**Validation:** `docs/validation/e2_onnx_identity_acceptance.md`. The owner-specified
decision date and actual execution date are intentionally recorded separately.

The frozen ID is `onnx-main-referenced-external-data-v1`: exactly one contained
regular main `.onnx` plus unique canonical referenced external tensor-data files
discovered by the complete existing recursive TensorProto traversal. Members
are complete byte objects; unreferenced neighbours and offset/length-only slices
do not define membership. Containment and ambiguous-unit failure behavior,
C3B's ordered inner/outer SHA-256 algorithm, schemas, trust boundaries, supported
formats and PF-002 are unchanged. Supervisor ingestion rejects mismatching IDs
and authorizes a C3B unit only from COMPLETED C3A resolution.

This entry freezes the already specified Architecture AC-03 / §6 COMP-W-C3A
contract; it is a pending-decision resolution, not an architecture amendment.
Historical E-2 OPEN statements in earlier dated entries remain historical.

## ACC-2026-10-02-02 — Windows worker token isolation for SEC-008

**Status:** APPROVED by the project owner's current SEC-008 execution packet.
**Scope:** Windows COMP-SUP worker launch and explicit evidence-store deployment
ACL provisioning only. Recorded before production implementation.

Architecture §§5 B2/B3 and 11.3 permit target-specific OS isolation. This entry
clarifies their Windows implementation and the older Popen-only build wording:
the elevated trusted supervisor creates a restricted derivative of its primary
token using supported Win32 APIs, without secondary accounts or credentials.
Administrators, Authenticated Users and Local-account-administrator SIDs become
deny-only; DISABLE_MAX_PRIVILEGE removes privileges other than change-notify.
A worker-specific default owner/DACL on the derived token replaces the elevated
account's Administrators-dependent startup defaults, without changing the
supervisor token. A private Win32 window station/desktop avoids exposing the
interactive/RDP desktop; handles are retained until cleanup. This follows
Microsoft's restricted-application desktop guidance. Filesystem permissions
remain DACL-enforced. This decision does not claim whole-host filesystem/GUI
confinement: the narrowly authorized deployment operation covers the evidence
directory only, not all user-owned paths, audit, references or signing keys.

CreateProcessAsUserW creates the child suspended under that token, inheriting
only the three designated standard-I/O handles via an explicit handle list.
The configured Windows Job is assigned before resume. There is no unrestricted
Windows fallback. Token/process/thread/pipe/Job handles close on all paths.
The evidence-store DACL remains the authoritative write boundary, provisioned
explicitly outside application startup, with SYSTEM-owned directory/database
and only SYSTEM/elevated Administrators write grants. New sidecars may retain
the supervisor's Administrators default owner, never the shared user SID.
Original ACLs are exported for exact
rollback. Audit, references and keys are not provisioned by this task.

Unix/Linux behavior, schemas, persistence APIs, non-claims, vocabulary, C5,
timeout and committed-memory semantics remain unchanged. E-2 remains OPEN;
PRE-08 remains PARTIAL. No OFF/network procedure is changed or executed.

Win32 authority: [CreateRestrictedToken](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-createrestrictedtoken),
[CreateProcessAsUserW](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw),
[restricted tokens](https://learn.microsoft.com/en-us/windows/win32/secauthz/restricted-tokens).

## ACC-2026-10-02-01 — Windows worker committed-memory containment

**Status:** APPROVED by project owner.
**Scope:** TASK-022 worker dispatch / TASK-026 SEC-002 on the frozen Windows
AMD64, CPython 3.13.12 target.
**Supersedes:** the earlier HOST-CAP-002 statement that no authorized Windows
replacement for Unix resource limits existed. Historical probe records remain
valid for the time at which they were recorded.

### Decision

On Windows, the trusted supervisor enforces the existing per-worker
`ResourceLimits.memory_limit_mb` contract with a Windows Job Object:

1. configure `JOB_OBJECT_LIMIT_PROCESS_MEMORY` and
   `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`;
2. create the worker process suspended;
3. assign it to the configured Job before any untrusted worker code executes;
4. resume the initial thread only after assignment succeeds;
5. retain the Job handle through collection and close all Job/thread/process
   resources on every completion or failure path.

The supervisor monitors the Job completion port. A process-memory-limit
notification terminates the Job so the violating worker cannot continue; the
kill-on-close flag remains the cleanup backstop.

Setup/configuration/assignment/resume failure is fail-closed: the suspended
worker must never run outside the selected boundary. Unix/Linux RLIMIT behavior
is unchanged. The Windows limit is a per-process **committed-memory ceiling**;
it is not Unix `RLIMIT_AS`, an exact RSS measurement, or a portable resource
claim. B2, IPC, schemas, evidence-store ownership, assessment vocabulary,
timeout semantics and C3D restricted-load semantics are unchanged.

### Approved host-capability evidence

A bounded target-host probe configured a 128 MiB process-memory ceiling plus
kill-on-close, created a child suspended, assigned it before resume, and observed:

- `MEMORY_ERROR` at the enforced boundary;
- child exit code 42;
- peak committed process memory 127.05 MiB;
- Job Object capability result: PASS.

This probe establishes availability of the containment primitive; it is not by
itself SEC-002 acceptance. SEC-002 still requires real FIX-002 execution through
the supervisor, schema/store/audit/C5 evidence, cleanup, and continuation.

### Implementation and acceptance result

Implemented and validated on 2026-10-02. Real seed-42 FIX-002 ran through
COMP-SUP with a bounded 768 MiB ceiling. The Job emitted its process-memory-limit
notification, the supervisor terminated the violating worker, persisted
`ASSESSMENT_ERROR/MEMORY_LIMIT_EXCEEDED`, produced C5
`UNAVAILABLE/UNAVAILABLE_NO_DECISION`, preserved an intact audit chain, cleaned
all worker/Job resources, and completed the following FIX-015 benign asset.
SEC-002 is PASS for the frozen Windows mechanism and target. The detailed
observation and local evidence hashes are recorded in
`docs/validation/task026_c3d_dispatch_acceptance.md`.

### Unchanged constraints

No network or OFF-002 behavior changes. No unsafe load fallback is permitted.
No additional evidence-store write path, assessment state, score, positive
assurance language, or broader host/platform capability is introduced.
