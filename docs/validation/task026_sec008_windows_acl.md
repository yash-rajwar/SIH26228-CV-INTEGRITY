# TASK-026 — Windows evidence-store ACL isolation / SEC-008

Date: 2026-10-02. Starting HEAD:
`1da72cd15e5d24e99d384c4ea9dac05e4c0917e5`, clean, on `feature/vertical-slice`;
fast-forward synchronization confirmed the same origin HEAD before changes.
Target: Windows build 22631 / AMD64 / NTFS / CPython 3.13.12 / pytest 9.1.1.
Approved interpreter: the existing `SIH26228-CV-INTEGRITY.venv-torch-test` environment.

Disposition: **SEC-008 PASS; GATE-3 NOT PASSED; GATE-4 NOT PASSED.**
Gate-2 PASS is preserved, not rerun or re-adjudicated. No OFF/network test ran.

## Authority and approved change

- Technical Specification §17.3 SEC-008: a non-supervisor process cannot write
  the evidence-store path (OS ACL test).
- Architecture B2/B3 and §11.4: untrusted workers, supervisor-only evidence
  persistence, target-specific OS enforcement.
- MVP TASK-022 repeats SEC-008; MVP §14 GATE-3 requires SEC-001 through SEC-012
  and the all-C3-complete trigger.
- ACC-2026-10-02-02 was recorded in the architecture/build documents before
  implementation, under the current project-owner packet. It clarifies the
  supported Windows restricted-primary-token launch, without credentials,
  unrestricted fallback, schema changes or Unix changes.

The initial elevated identity was `SDG100\master`, user SID
`S-1-5-21-2629837429-4180215226-2665119787-500`. The owner-supplied verified
precondition remains historical evidence: ordinary inherited-token Python child
identity was the same; its evidence-directory marker write was **ALLOWED**.
This insecure BEFORE result was not rerun, overwritten or relabelled.

## Exact original and final ACLs

Configured path: `/var/assurance/evidence-store/evidence.db`; resolved on this
host to `C:\var\assurance\evidence-store\evidence.db`.
The following are full security descriptors, including owner/group and DACL.
`BA` = Administrators, `SY` = SYSTEM, `BU` = Users, `AU` = Authenticated Users;
`FA` = FullControl; `0x1301bf` = Modify; `0x1200a9` = ReadAndExecute.

Original directory:

```text
O:BAG:S-1-5-21-2629837429-4180215226-2665119787-513D:(A;OICIID;FA;;;BA)(A;OICIID;FA;;;SY)(A;OICIID;0x1200a9;;;BU)(A;ID;0x1301bf;;;AU)(A;OICIIOID;SDGXGWGR;;;AU)
```

Original database:

```text
O:BAG:S-1-5-21-2629837429-4180215226-2665119787-513D:(A;ID;FA;;;BA)(A;ID;FA;;;SY)(A;ID;0x1200a9;;;BU)(A;ID;0x1301bf;;;AU)
```

Final directory:

```text
O:SYG:S-1-5-21-2629837429-4180215226-2665119787-513D:PAI(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)
```

Final database:

```text
O:SYG:S-1-5-21-2629837429-4180215226-2665119787-513D:PAI(A;;FA;;;SY)(A;;FA;;;BA)
```

Both existing objects are SYSTEM-owned, avoiding a shared user owner's implicit
WRITE_DAC authority. The protected directory has only explicit SYSTEM and
Administrators grants, inheritable by future files and directories. Newly
created SQLite sidecars inherit those two grants; an elevated supervisor's
Administrators default owner is permitted, because BA is deny-only in workers.
The shared user SID is not a permitted store/sidecar owner or write grant.
The parent `C:\var\assurance` was inspected without modification; its AU Modify
grant cannot provide the restricted worker a parent delete/write bypass.

### Explicit deployment and rollback

`scripts/windows/provision_sec008_evidence_acl.ps1` targets only the exact
evidence directory, rejects reparse points/scope escapes, exports original
per-object SDDL and ownership, provisions SID-based ACLs, verifies inheritance,
and supplies deterministic rollback. It is never invoked by application startup.
Apply was performed in the already elevated shell; Verify passed afterward.
Rollback was not executed: the accepted boundary remains deployed.

Original snapshot: `build/task026-sec008/acl-before.json`, captured
`2026-10-02T14:54:38.4834377Z`. SHA-256:
`2ee2befc20f6eb6df3f9ea08d22e15e61e1d2c254739deae10d95197e425dbf8`.

Authorized deployment recovery command (not executed):

```powershell
powershell.exe -NoProfile -File scripts\windows\provision_sec008_evidence_acl.ps1 -Mode Rollback -SnapshotPath "C:\Users\master\Desktop\SIH26228-CV-INTEGRITY\build\task026-sec008\acl-before.json"
```

## Production token/process contract

`windows_token.RestrictedWindowsProcess` uses stdlib ctypes and documented
Win32 APIs: OpenProcessToken → CreateRestrictedToken(DISABLE_MAX_PRIVILEGE) →
CreateProcessAsUserW(CREATE_SUSPENDED) → existing Windows Job assignment → resume.
Only designated NUL stdin/stdout and stderr-pipe handles are inherited via
STARTUPINFOEX HANDLE_LIST. The same executable, arguments, clean environment,
cwd, named-file IPC and bytes-mode collection semantics remain. No key/database
environment paths, shell, secondary account, password or unrestricted fallback.

Actual child token:

| Item | Observed state |
|---|---|
| User SID | Same `...-500` user; token reduction, not a second account |
| `S-1-5-32-544` Administrators | Attributes 16, DENY_ONLY; ENABLED bit absent |
| `S-1-5-11` Authenticated Users | Attributes 16, DENY_ONLY; ENABLED bit absent |
| `S-1-5-114` local account/admin | Attributes 16, DENY_ONLY; ENABLED bit absent |
| Privileges | Only SeChangeNotifyPrivilege, attributes 3 |
| Restricting SID list | Empty; no additional WRITE_RESTRICTED SID claimed |
| Integrity label | High (`S-1-16-12288`); no low-integrity claim |

Derived-token default owner/DACL and a private window station/desktop are needed
on this elevated built-in Administrator host: retaining BA-dependent startup
defaults after making BA deny-only caused DLL initialization failure. Only the
derived token is adjusted, and the trusted process station is restored before
launch; shared RDP desktop ACLs are untouched. A tested additional write-restricting
SID was not viable and is not part of the approved minimum implementation.

The worker IPC directory receives explicit user access only after the supervisor
creates it. Submitted asset ACLs are not changed by production. Tests grant only
READ/EXECUTE on fresh pytest asset roots, because Python 3.13's Administrator
mode-0700 temporary directories otherwise depend on BA/OWNER_RIGHTS. This does
not give workers test-asset write permission or grant access to the deployed DB.

Success/failure/timeout tests verify restricted identity before resume, Job
ordering, no code execution on setup failure, no unrelated inherited handle,
and token/process/thread/pipe/window-station/desktop/Job cleanup. Assigned-Job
failed-start cleanup waits for KILL_ON_JOB_CLOSE termination instead of racing a
redundant TerminateProcess. Existing memory/timeout semantics are unchanged.

## Actual SEC-008 acceptance

`tests/security/test_windows_evidence_acl.py` verifies the deployed ACL (without
provisioning it), then exercises both directions using the production launcher.
No AccessDenied acceptance is mocked.

Trusted supervisor: approved seed-26228 local COCO fixture → all four restricted
C2 workers spawned/collected → every raw output schema-validated → four bounded
synthetic evidence records plus one valid finding persisted → intact audit.
All worker exits are 0, SQLite WAL/SHM exist, and IPC/native handles are cleaned.
Final regression asset: `sec008-synthetic-609978a3b5dd4750bac28e5eea3d918d`.

Restricted probe: real file-open/native-write/SQLite attempts on the configured
deployed path. The controlled supervisor write precedes the frozen DB baseline.

| Operation | Actual result |
|---|---|
| Create marker / open DB r+b (Python CRT) | Denied, errno 13; CRT WinError field absent |
| Native marker creation / DB GENERIC_WRITE | Denied, WinError 5 (ERROR_ACCESS_DENIED) |
| DB WRITE_DAC | Denied, WinError 5; no DACL mutation attempted |
| Live WAL/SHM GENERIC_WRITE and WRITE_DAC | All denied, WinError 5 |
| SQLite mode=rw + transactional write attempt | Denied, SQLITE_CANTOPEN 14: unable to open database file |
| Open supervisor PROCESS_DUP_HANDLE | Denied, WinError 5 |
| Own named result IPC | Succeeds; child exits 0 |

No worker marker/probe table exists. Database integrity_check is `ok`; audit
remains intact. Database SHA-256 is identical before/after the denial probe:
`02a8ef631838c9bfef0ed2d4bb6020ff6007ac8ed480a44e2cfde28fead1e8a7`.
Live sidecar hashes also remain unchanged:

- WAL: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- SHM: `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb`

Each repeated acceptance adds only its explicitly controlled synthetic
supervisor records; hashes freeze after that write, not before it. The denied
worker never changes DB bytes. This proves an OS boundary, not an application
conditional or a whole-host filesystem/GUI sandbox. Other user-owned paths and
trusted elevated administrators remain outside this acceptance claim.

## Validation order and raw report hashes

All runs used the approved interpreter; no package installation. Reports are
preserved locally in ignored `build/task026-sec008/` and summarized here.

| Ordered check | Result | Report | SHA-256 |
|---|---|---|---|
| Restricted token | 14 passed | token.xml | `0beea2a0e5992caa0b2435d274823ccb75310d082ce21cb970c9991bf452ce87` |
| Deployed ACL verification then real SEC-008 | 2 passed | sec008.xml | `be3f611a386669379fb91577d70ffa83b8bc1712f904f0cae79499533e5054f2` |
| SEC-002 real FIX-002 / 768 MiB Job | 1 passed | sec002.xml | `a471f3ed51515c86a9b81441801a7cb55961a5bb54475749fb31185f9168c3fc` |
| SEC-003 ready FIX-003 / 1-second timeout | 1 passed | sec003.xml | `00aeb0a9e295a9ee02533cf54436969aa668961c0477e6494212b516aac39114` |
| Token/Job/orchestrator/C3D/security relevant | 71 passed | relevant.xml | `8cb04882d4dd5bba75ca34367658ac1eefd50c486ffaa8abeec24d969a00b59a` |
| Complete security suite | 92 passed, 4 skipped | security.xml | `72c890057a339916ee88958e1b0fe0b035d378f70201b349dc0489e64ad5c978` |
| Non-offline regression | 508 passed, 11 skipped | non-offline.xml | `204f6c3ec35328dc9e16e7f2b100820bde122978a272242ea8de9fdc8820004f` |

Final `sec008-observed.json` SHA-256:
`3589416e712988027184b3041299da2c0deaa5f1567ee9bb02617becf8fe1725`.
Zero failures. Existing security test seams capture the new production launcher;
their assertions are retained, not weakened. Four security skips are historical
stubs, not accepted tests. Eleven non-offline skips comprise those four, two
historical integration stubs, two historical negative stubs, the historical
UT-CAP-003 CLI placeholder, PRE-08-gated HMAC and unselected Ed25519. Functional
counterparts execute where implemented; none of the skipped items count as PASS.

Universal production guards: zero matches for unsafe loading, risk_score,
compromise_probability, overall_assurance_score, shell=True, and quoted positive
CLEAN/SAFE/HEALTHY constants. `git diff --check` clean. No protected research,
worker, schema, constant, fixture, E-2 or OFF/network change.

## Complete Gate-3 adjudication

MVP §14 trigger and each criterion are evaluated separately; security-suite
success is not substituted for component completion.

| Trigger / criterion | Result and current evidence |
|---|---|
| All C2 workers complete | Existing Stage-5 exit acceptance; C2A/B/C/D units 12/8/8/6 pass. Historical C2B summary label is IMPLEMENTED with recorded completed acceptance; this task does not promote unrelated task rows. |
| All C3 workers complete | **NOT MET:** C3A/C3B remain IMPLEMENTED WITH BLOCKER. E-2 has no frozen ONNX definition ID; real final identity paths remain ambiguous/unavailable. Test-only IDs do not satisfy this trigger. C3C/C3D TESTED. |
| C4 shell, C5, REF, CAP complete | Existing TESTED shell/component acceptance retained; PRE-08 blocks operational signing only, not the permitted C4 shell. |
| All C2 units including UT-C2A-004 | PASS in non-offline regression; all-box traversal assertions retained. |
| All C3 units | PASS: C3A 30, C3B 18, C3C 18, C3D 29. C3B injected IDs prove contract/hash logic, not a frozen ONNX identity definition. |
| SEC-001..012 | Functional PASS: hostile-pickle boundary; real Job memory/timeout; genuine C3A/C3C absolute/traversal/symlink containment; unsafe-load guards; real SEC-008; replay; corruption; nested schema rejection; boolean coverage enforcement. Historical skipped stubs do not establish these passes. |
| All four FIX-013 UNAVAILABLE injection points | PASS: negative propagation tests and VS-004 all declared layers; no positive conversion. |
| C5 rule 1, no score field, T05d/PF-002 | PASS: interpretation units/negative cases/schema/security guards, C3 field propagation and VS-004. |
| SEC-010 audit mutation | PASS: dedicated modified-event detection without reset. |
| SEC-009 replay nonce | PASS: duplicate rejected with required audit event. |
| Unsafe-load zero-match guard | PASS. |

**Gate-3 decision: NOT PASSED**, because its all-C3-complete trigger is unmet
under E-2. SEC-008 is resolved independently. Gate-4 remains NOT PASSED pending
separate §18/full validation reconciliation; TASK-026 remains IN PROGRESS.

Carried unchanged: E-2 OPEN; PRE-08 PARTIAL; HOST-CAP-003 formal reconciliation
pending; HOST-CAP-002 resolved for the approved Windows Job mechanism; TASK-024
NOT STARTED. OFF-002 acceptance PASS, original recovery marker FAIL and
independent restored-state PASS remain separate historical facts. OFF-002 was
not rerun. No later task is authorized; next work requires a separate packet.
