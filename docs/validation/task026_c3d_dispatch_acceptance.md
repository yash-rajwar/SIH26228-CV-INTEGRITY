# TASK-026 — C3D supervisor resource/timeout acceptance

Validation: 2026-09-29; documentation finalized: 2026-10-02.
Starting checkpoint: `d850f43` on `feature/vertical-slice`.
Target: approved Windows AMD64 / CPython 3.13.12 environment, pytest 9.1.1,
Torch 2.10.0+cpu. Gate-2 remains PASS; this is not a Gate-2 re-run.

**Current disposition (2026-10-02): SEC-002 PASS; SEC-003 PASS.** The original
SEC-002 OPEN record below is preserved as historical evidence and is superseded
for the validated Windows target by ACC-2026-10-02-01 and the observed result
recorded in the final section of this document.

## Authoritative contract

- Technical Specification §17.3, SEC-002: FIX-002 OOM trigger → worker
  killed; ASSESSMENT_ERROR emitted; supervisor continues.
- Technical Specification §17.3, SEC-003: FIX-003 hang trigger →
  ASSESSMENT_ERROR after timeout_seconds; supervisor not hung.
- Architecture §11.7: timeout/OOM evidence → C5 UNAVAILABLE/NO_DECISION.
- Architecture §21 security validation requires memory resource-limit
  enforcement. Technical §11.2 permits truthful platform-limit disclosure;
  that disclosure does not establish enforcement or satisfy SEC-002.
- MVP TASK-017 repeats these security criteria; GATE-3 requires all
  SEC-001–SEC-012. GATE-4 also requires the §18 observed-result records.

## Existing boundary and minimal correction

TASK-022 `_start_worker()` validates the approved task/module and positive
resource contract, strips key/database environment paths, and launches a real
Popen child using named-file IPC. `_collect_worker()` enforces the configured
timeout and classifies unsuccessful exits. `_process_results()` / the schema
gate precede supervisor-owned SQLite writes and audit events; C5 preserves
unavailability. No dispatcher or worker was replaced.

Repeated real timeout runs exposed a cleanup defect: the killed child's empty
working directory survived final removal with `PermissionError(13, 'The process
cannot access the file because it is being used by another process')`. The old
path called kill/wait without completing the existing communication reader.
The only production correction is kill followed by
`communicate(timeout=configured_timeout)` before temporary-directory cleanup.
This drains/reaps the child within the existing resource contract. The same
directory/pipe assertions then pass without sleep, retry, or private handle
manipulation. Earlier failed JUnit files remain preserved locally.

## SEC-003 — PASS (controlled supervisor-dispatch integration)

Input: seed-42 FIX-003's existing infinite-sleep trigger. Test-only child
startup instrumentation imports real Torch and calls unchanged C3D main().
At the restricted load boundary it checks weights_only=True / map_location=cpu,
signals readiness, then executes the generated FIX-003 script. The parent waits
for readiness before handing the real process to ordinary supervisor collection.
No supervisor result, schema, store, audit, C5, or follow-on worker is mocked.
This proves dispatch behavior, not that a particular checkpoint naturally hangs
Torch's deserializer.

The named C3D timeout is overridden to 1 second for this test only; production
configuration is unchanged. A separate test safety watchdog bounds an accidental
dispatcher regression. Acceptance fails if that watchdog, rather than the
supervisor, terminates the child.

Observed reference run (relevant regression):

- Child PID 5612; exit code 1; collector elapsed 1.0210326 seconds.
- No watchdog intervention; child terminated/reaped, stderr closed, all worker
  temporary directories removed before the test's own safety cleanup.
- Persisted C3D record `96e69c91-3a0f-4ec6-9c76-88ce6adf20ec`, digest
  `a7cd4a67cc161ce86ca2807fb6a6f767e2a66e428e5944c5d2d4f05123d47e01`:
  ASSESSMENT_ERROR, raw_signal.failure_reason=TIMEOUT, access_mode=UNAVAILABLE.
- Coverage gap true, nonempty limitations/non-claims, synthetic label and
  independence_established=False retained.
- C5: UNAVAILABLE / UNAVAILABLE_NO_DECISION; T05d and global-backdoor
  non-claims retained. No positive assurance is substituted.
- A second benign YOLO asset executes normally in the same pipeline: 2 assets,
  7 real workers, 7 persisted evidence records, 2 findings, 1 unsigned provenance
  record, 0 schema rejections. Audit chain intact; PIPELINE_RUN_COMPLETE present.

Expected and actual observable timeout behavior agree. SEC-003 is PASS for this
controlled integration on the validated target tuple; no process-tree or portable
memory-containment claim is made.

## SEC-002 — OPEN (HOST-CAP-002)

Windows cannot import Unix `resource`, so unchanged C3D
`_apply_resource_limits()` returns False. The dispatcher supplies the configured
4096 MiB contract but does not independently enforce a Windows memory cap.
Loading default FIX-002 (>4096 MiB declared storage) here would risk uncontrolled
host exhaustion and would not establish the required containment primitive.
The exact acceptance test therefore remains a named HOST-CAP-002 skip, not PASS.

Supplemental bounded experiment: a test-only restricted-load hook raises
MemoryError without allocating large memory. Real C3D returns LOAD_ERROR (exit 0),
resource_limits_applied=False, fallback_attempted=False. The supervisor persists
that evidence, C5 stays UNAVAILABLE, and the next asset completes. Reference
record `96314d7c-366f-4677-be5f-7505375d1178`, digest
`54f2ef445170aff984e0b514dd4874036ea5c327458776e7b422493177d65647`.

This is mechanism-tested fault handling only. It is not a kernel OOM, cap breach,
or killed-worker experiment and does not satisfy SEC-002. Approved resource
enforcement and a safe validated test host remain necessary before closure.

## Validation and evidence retention

Execution order: targeted SEC-002 (1 named skip), targeted SEC-003 (1 passed),
relevant TASK-022/C3D/base regression (70 passed, 1 skipped), then security suite
(89 passed, 5 skipped), then non-offline regression
(485 passed, 12 skipped, 0 failed; `pytest tests --ignore=tests/offline`).
The prior full 483-passed/20-skipped checkpoint remains historical, not re-run.
Production scans have zero unsafe-load, score-field, and
prohibited positive-assurance constant matches. One initial security run failed
two legacy guards because grep was not on PATH; rerunning with the existing
Git-bundled grep in the test-shell PATH passes. No package was installed and no
test was weakened.

Local raw evidence is retained under ignored `build/task026-c3d-dispatch/`:
JUnit files, preserved test SQLite stores, and `dispatch-observed.json` containing
process timing, record/finding data, summary and audit-chain records. Reference
reports under `final-relevant-temp/` have SHA-256:

- SEC-003 report: `e8c4ca057fdc476a4636b7ed1431c6e5699a22ea72936fce2e988e334177ef34`.
- Bounded MemoryError report: `c55bf24e99ae18d9324637d6d4674192c5926dbba57727dd969ec58783e15aef`.
- Non-offline regression JUnit (`regression.xml`):
  `99e382cb644bb53311fc480465572a18ec2289c566e2132828380c95da32116a`.

These raw artifacts are local evidence, not claimed to be tracked or remotely
archived. This committed record preserves the observation and its evidence hashes.
Offline tests, OFF-002, FIX-008 rework, network isolation, PktMon and dashboard
work were not executed. Protected `docs/research/**` content is unchanged.

SEC-002 remains OPEN; GATE-3 and GATE-4 remain NOT PASSED. PRE-08, E-2,
HOST-CAP-002 and HOST-CAP-003 are not closed by this task. Historical OFF-002
acceptance PASS, recovery-marker FAIL and independent restored-state PASS remain
distinct and untouched. No subsequent implementation task is authorized here.

## SEC-002 — PASS (Windows Job Object supervisor containment, 2026-10-02)

ACC-2026-10-02-01 supersedes the historical lack of an approved Windows memory
mechanism. COMP-SUP now creates each Windows worker suspended, configures and
assigns it to a Job Object carrying `JOB_OBJECT_LIMIT_PROCESS_MEMORY` and
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and resumes the worker only after successful
assignment. The ceiling is the existing `ResourceLimits.memory_limit_mb` value.
A completion-port monitor treats the process-memory-limit notification as a
supervisor resource failure and terminates the Job. This is committed-process
memory enforcement, not a Unix `RLIMIT_AS` or exact RSS claim. Unix behavior is
unchanged.

The target capability probe remains separate from acceptance: its 128 MiB Job
reported a 127.05 MiB peak and a child `MemoryError`/exit 42. The acceptance run
used the real seed-42 FIX-002, real COMP-SUP dispatch, and a bounded test-only
768 MiB C3D ceiling. FIX-002 declares 805,306,372 bytes of storage, exceeding the
805,306,368-byte ceiling. Windows reported the process-memory-limit event with a
peak committed-process-memory observation of 247,291,904 bytes (235.84 MiB): the
large pending allocation was rejected before the process could commit through
the ceiling. The supervisor then terminated the Job with exit code 3,758,096,385
(`0xE0000001`).

Observed acceptance behavior:

- schema-valid C3D evidence persisted through the normal supervisor path as
  `ASSESSMENT_ERROR`, `failure_reason=MEMORY_LIMIT_EXCEEDED`,
  `access_mode=UNAVAILABLE`, with configured/peak Job accounting and mandatory
  limitations/non-claims;
- C5 emitted `UNAVAILABLE` / `UNAVAILABLE_NO_DECISION`, retaining T05d and global
  backdoor-absence non-claims;
- the audit chain remained intact and ended in `PIPELINE_RUN_COMPLETE`;
- worker pipes, processes, Job handles, and temporary directories were cleaned;
- the following seed-42 FIX-015 benign PyTorch asset completed `LOAD_SUCCESS`
  under the same 768 MiB limit with restricted loading and no fallback;
- the two-asset run persisted 6/6 dispatched worker results, 2 findings, and 2
  unsigned provenance records with zero schema rejections.

Validation order and results: Job Object unit/capability 6 passed; targeted
SEC-002 1 passed; existing SEC-003 1 passed; relevant COMP-SUP/C3D regression
51 passed; security suite 90 passed / 4 historical skips; non-offline regression
492 passed / 11 historical or conditional skips, zero failures. Offline tests,
OFF-002, network controls, and TASK-024 were not run. The production scans have
zero Python matches for `weights_only=False`, `risk_score`,
`compromise_probability`, and `overall_assurance_score`.

Local ignored evidence is under `build/task027-sec002/`:

- `sec002-observed.json`:
  `89cafa175f20bf15ce829bce8f5b799e5ff589b9f8bd8c27bedcb10a98a84acb`
  (under `complete-sec002-temp/`);
- `complete-sec002.xml`:
  `e24a641bce95026514bc8b28e8336cce3b1ecda1aff0e57667917cb5f718541c`;
- `complete-security.xml`:
  `bb54b8114b6b0de4023cbc5653edada3fcc0c7a84d36f66150e063c04ea93c11`;
- `complete-nonoffline.xml`:
  `5b691df451021734945b9b49add7e699005156872f40c91b7441b80476a91ba6`.

SEC-002 is PASS and HOST-CAP-002 is resolved for this frozen Windows mechanism
and target. SEC-003 remains PASS and was not re-adjudicated. GATE-3 remains NOT
PASSED because the authoritative checklist still records SEC-008 (OS ACL denial
for a non-supervisor process) as pending. E-2 still blocks final C3A/C3B ONNX
identity acceptance; those component statuses are not promoted. GATE-4 remains NOT PASSED pending its
separate full validation/Section 18 reconciliation. Gate-2 and all historical
OFF-002 distinctions are unchanged.

### GATE-3 security criterion review

The following maps Technical Specification §17.3 and MVP GATE-3 to actual tests
executed in the current non-offline regression. Historical skipped stub names
are not substituted for executable acceptance coverage.

| Criterion | Result | Executed evidence |
|---|---|---|
| SEC-001 | PASS | `test_sec_001_hostile_pickle_boundary`; VS-003 real supervisor hostile-pickle path |
| SEC-002 | PASS | Real FIX-002 / Windows Job / supervisor acceptance above |
| SEC-003 | PASS retained | Existing controlled FIX-003 supervisor timeout acceptance |
| SEC-004 | PASS | Genuine FIX-004 C3A/C3C tests, including containment before outside file access |
| SEC-005 | PASS | Genuine FIX-005 C3A/C3C traversal tests |
| SEC-006 | PASS | Genuine FIX-006 symlink escape and shared C3A/C3C containment tests |
| SEC-007 | PASS | Exact and broad unsafe-load scans and platform-neutral production source scan |
| SEC-008 | PENDING | No accepted target-host OS ACL test denying writes by a non-supervisor process; source/import ownership checks alone do not meet it |
| SEC-009 | PASS | Duplicate replay nonce rejected with required audit event |
| SEC-010 | PASS | Modified audit event detected; no reset path |
| SEC-011 | PASS | Nested prohibited field rejected before store write |
| SEC-012 | PASS | Non-boolean/false coverage label rejected before store write |

All current C2/C3 worker unit tests pass, including all-box coverage. VS-004
confirms every declared FIX-013 injection layer; C5 priority-one, T05d/PF-002
non-claims, and score-field absence pass. The unresolved SEC-008 requirement
prevents GATE-3 acceptance. E-2, PRE-08, HOST-CAP-003 procedural reconciliation,
and Section 18/GATE-4 remain carried independently.
