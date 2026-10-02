# Architecture Change-Control Log

This log records approved changes under Architecture Specification §23. It does
not replace the architecture or technical specification; approved entries are
also incorporated into those authoritative documents before implementation.

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
