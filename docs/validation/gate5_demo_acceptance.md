# GATE-5 — Final MVP/demo acceptance

**Decision: PASS (ALL-OF), 2026-10-03 IST.** Starting HEAD
`17d200f2a6c449102d70247838881f2796c16f09`, clean `feature/vertical-slice`,
fast-forward-only synchronization already current. Approved CPython 3.13.12 /
pytest 9.1.1 in the adjacent `.venv-torch-test` environment; no package installed.
UTC artifact timestamps on 2026-10-02 precede the local IST decision date.

## Seven authoritative criteria

| Criterion | Evidence source | Observed result | Verdict | Limitations |
|---|---|---|---|---|
| 1. Automated offline demo | `scripts/demo.py`; real CLI run and G5-DEMO-001..008 | Exit 0 without input; approved generator at seed 26228, two genuine assessments, reads, export and dashboard cleanup | PASS | Stdlib orchestration; approved local project dependencies required. Only loopback HTTP; no new network-isolation/zero-egress experiment |
| 2. Dashboard starts; evidence / UNAVAILABLE visible | Real CLI dashboard `/` and `/api/dashboard`; `test_dashboard.py` 27 cases | HTTP 200; both run assets, B UNAVAILABLE, explicit coverage, chain status; repeated data snapshots/audit identical; child reaped | PASS | HTTP/API and existing rendering/static-CSS tests, not browser GUI inspection. Signing notice visible; no invented provenance when none stored |
| 3. Valid export ZIP | Real `export-bundle` for B; zipfile CRC/JSON checks; exporter regression 27 | Exactly six documents, unchanged unavailable finding/coverage, synthetic labels in findings/evidence | PASS | Empty provenance array is valid for missing-model C4_BINDING_UNAVAILABLE; export is not signing or asset validation |
| 4. CHAIN_CORRUPT in CLI | `test_cli.py::test_int_cli_004_audit_corruption_is_printed_before_events` and `::test_aud_read_004_cli_corrupt_chain_does_not_write` | Literal CHAIN_CORRUPT before history; events/state unchanged, all writes forbidden | PASS | Corruption created only in isolated test stores; deployed/demo chain untouched |
| 5. All applicable DEFERRED_IN_SCOPE visible | Real `list-deferred`, G5-DEMO-005 and export/API comparisons | All 15 registry entries for B visible with exact production statuses/reasons; 13 DEFERRED_IN_SCOPE, one REFERENCE_UNAVAILABLE, one COMPLETENESS_UNAVAILABLE | PASS | Expected set derived from production COMP-CAP registry, not invented. T05d remains permanent non-claim |
| 6. Frozen host tuple recorded | `docs/p1_decisions.md` PRE-01, PROJECT_STATE.md; approved interpreter preflight | Owner-recorded Windows 10 Pro version 2009 / build 22631 / AMD64 / CPython 3.13.12 / 16 GB | PASS | Owner decision retained; no substitution from Python's Windows branding; not portability validation |
| 7. Claims bounded to demonstrated evidence | README, PROJECT_STATUS, CHANGELOG, DEMO_GUIDE and maintained MVP review; output-field scans | No affirmative malware/safety/every-attack/full-integrity/signing claim; PF-002, T05d, unavailability, deferrals and unsigned state retained | PASS | Research history untouched; finite synthetic observations are not operational detection guarantees |

**GATE-5 PASS. SIH26228 MVP / Demo Gate complete.** Exactly these seven criteria
were applied; neither signing provisioning, historical HOST-CAP procedural
re-entry nor browser GUI automation was introduced as an additional gate.

## Actual demonstration observations

Explicit real run:
`build/demo/20261002T184101Z-118e799e824c45638f87765b98c95b40/`.
All CLI subprocesses used the approved `sys.executable` from repository root.

- A: `demo-coco-20261002T184101Z-118e799e824c45638f87765b98c95b40`.
  Four C2 evidence records, one synthetic finding; M01 COMPLETED with zero
  fixture violations. C5 COMPLETED_STATISTICS_ONLY / STATISTICS_REPORTED /
  ACCEPT_WITH_CONTEXT, not a fabricated clean result.
- B: `demo-unavailable-20261002T184101Z-118e799e824c45638f87765b98c95b40`.
  Contained `missing.pt` was never created. C3A/C3B ARTIFACT_UNIT_AMBIGUOUS,
  C3D ASSESSMENT_ERROR; C5 UNAVAILABLE / UNAVAILABLE_NO_DECISION. All three
  evidence records and the finding retain is_synthetic=1 and non-empty
  limitations/non-claims. C4_BINDING_UNAVAILABLE is retained.
- 59 new audit events; pre-existing prefix unchanged. Read-only audit display,
  export and two dashboard snapshots preserve history. Server returned 200 at
  `127.0.0.1:5372`, exposed both assets and was stopped/reaped in finally.
- No provenance rows existed in that deployed store. The unsigned-signing
  notice is visible; `stored_signing_statuses=[]` is recorded, not invented
  SIGNING_UNAVAILABLE rows. Existing controlled dashboard tests separately
  prove actual stored unsigned provenance is displayed with signature=null.
- ZIP: manifest.json, findings.json, evidence_records.json, provenance.json,
  audit_trail.json, capabilities.json. All parse; CRC check passes. Empty C4
  array is consistent with the incomplete artifact-unit contract.
- Normal supervisor writes append to the configured
  `C:\var\assurance\evidence-store\evidence.db`. CLI has no deployment-path
  override: none was invented. Working artifacts/logs/ZIP remain only under
  ignored `build/demo/`; stores/history are not cleared or relocated.

| Explicit run artifact | SHA-256 |
|---|---|
| result.json | `91085717be65f7b4095ec8339172f6dc8bb6308c41500f5999c306212f894707` |
| unavailable-evidence.zip | `964101d3c9ee2c6b05c2611a2a993599a34cc896207c3e25ae60c86b00abc228` |
| benign-coco/valid_coco.json | `3ce4740447c1b11bbe27343a621f44c8b99b04e5ae6572de9ed951207446e586` |

Per-command exit-code/argv records, complete stdout/stderr, HTML/API snapshots
and per-artifact SHA-256 values are retained beside result.json. Unique run IDs
and asset IDs permit repeat execution without overwrite/reset. No runtime
artifact is tracked. The first development attempt exited nonzero due to a
new demo assertion incorrectly demanding a nonempty C4 array. Inspection proved
the existing completed-C3B requirement; only the demo assertion was repaired.
No production semantics, required test, or non-claim was weakened.

## Ordered validation

All final runs below exit 0. JUnit reports are in `build/demo/validation/`.
An initial exporter command used an incorrect test filename and collected zero
tests (exit 4); the correct existing `test_exporter_security.py` was then run
in its prescribed position. No failing application test was suppressed.

| Order | Effective scope | Actual result |
|---|---|---|
| 1 | tests/integration/test_gate5_demo.py | 8 passed |
| 2 | real `python scripts/demo.py` | PASS, exit 0 |
| 3 | tests/integration/test_dashboard.py | 27 passed |
| 4 | tests/integration/test_cli.py | 9 passed |
| 5 | tests/integration/test_exporter.py + tests/security/test_exporter_security.py | 27 passed |
| 6 | tests/unit/test_audit_chain.py | 12 passed |
| 7 | tests/security/test_audit_security.py::test_sec_010_modified_event_detected_without_reset | 1 passed |
| 8 | tests/security | 92 passed, 4 unchanged skips |
| 9 | tests/integration + tests/negative | 115 passed, 4 unchanged skips |
| 10 | tests --ignore=tests/offline | 596 passed, 11 unchanged skips, 0 failed |

The baseline was 588 passed/11 skips; the only additional cases are eight
G5-DEMO tests. Repeated real demo execution also passes in the combined/full
regressions. Skips are not accepted as passes. SEC-010 still exercises trusted
diagnostic writes/no-reset, unlike read-only inspection. Dashboard controlled
corruption (`test_int_dash_005_corruption_visible_history_unchanged`) and
all-writes-forbidden refresh (`test_int_dash_007_render_refresh_zero_mutations`)
pass without damage to the deployed chain.

| JUnit artifact in build/demo/validation | SHA-256 |
|---|---|
| focused.xml | `3e17a8592b9cfb3a16c9df33dc415e8a116ae353db3ec729a0102f43634356e9` |
| dashboard.xml | `4822d38fe9742681628397a397e390ad59651ba4b729f486e97c8f02eaf13732` |
| cli.xml | `e923e18283b343654a7b62a992d2f90e5016e7b5e1a32edc04c5437981e7bd27` |
| exporter.xml | `14860a4574444ca240d62470682b528f88a30c0ca3058dfd10962761a43740fc` |
| audit.xml | `2d31a02d0da06af9265b5f39cffd371c4a591c7ec80d8f28340e59a130102b1c` |
| sec010.xml | `711749646b31255cc8aee78670911e4e77529641ac0c4473ab617eedc3377383` |
| security.xml | `33fe07b7c177f277c56b345f3cec7332b92af1cf0c1f3d7099e4598b2dbd013b` |
| integration-negative.xml | `5f77aa6068ac22b76f3370661b5178a464fa0d2f40f6a2587c3e8669c4080bba` |
| non-offline.xml | `724c58d8ac64e7b6d1b6d9d665908f3761d7ff16f5091982aedf8ebc8bb7c916` |

Production scans: zero unsafe-load, risk_score, aggregate_assurance,
compromise_probability, overall_assurance_score, shell=True, Fabric/HyperLedger
matches and zero quoted positive CLEAN/SAFE/HEALTHY constants. Demo HTTP/bind
destinations are exclusively IPv4 loopback; dashboard has no external URL/CDN.
No packages, signing, firewall/NIC/PktMon controls or OFF tests were executed.

## Mandatory MVP/release inventory

Reviewed against maintained MVP §3 MB-01..29, task acceptance, actual modules,
PROJECT_STATE's committed task evidence and current passing regression:

| Mandatory IDs | Current implementation / accepted evidence | Result |
|---|---|---|
| MB-01, MB-27 | Constants/exceptions/config loader and three YAML files; TASK-003/004 tests | COMPLETE / TESTED |
| MB-02, MB-03 | EvidenceStore and AuditChainWriter; TASK-005/006 tests, actual ACL/SEC-008 acceptance, audit and SEC-010 regressions | COMPLETE / TESTED |
| MB-04, MB-05, MB-26 | Schema validator, six schema files, worker IPC/output/containment base; TASK-007/008 tests | COMPLETE / TESTED |
| MB-06 | Seed-pinned hostile/benign generator suite and mandatory in-scope fixture evidence, TASK-009 | COMPLETE / TESTED |
| MB-07..10 | C2A/B/C/D modules; required fixture, non-claim and reproducibility tests | COMPLETE / TESTED |
| MB-11..14 | C3A/B/C/D modules; frozen E-2, real ONNX identity/structure, restricted loading and supervisor security acceptance | COMPLETE / TESTED |
| MB-15 | TASK-019 Part A provenance/replay/sequence shell; SIGNING_UNAVAILABLE and PF-002 tests | COMPLETE for approved unsigned MVP shell; Part B DEFERRED, PRE-08 PARTIAL |
| MB-16..19 | Reference manager, capability declaration, C5 interpretation, supervisor; respective task tests and real pipeline integration | COMPLETE / TESTED |
| MB-20..22 | Seven accepted CLI entry points, actual `export/exporter.py` six-document contract and read-only dashboard | COMPLETE / TESTED |
| MB-23..25 | Vertical slice, FIX-013 negative propagation, automated unsafe-loading/security guards | COMPLETE / TESTED |
| MB-28, MB-29 | Repository/package/wheelhouse/definition layout and all test infrastructure; accepted frozen-target offline evidence | COMPLETE in approved target scope |

C2B reconciliation is evidential, not cosmetic: UT-C2B-001..006, REPRO-002,
empty-input boundary and SEC-C2B-001..002 (10 cases total) already had committed
passing evidence; all run in the current non-offline regression. Source uses
stdlib hashlib streaming, mandatory PDQ deferral and the exact-duplicate
non-claim. TASK-011 is therefore TESTED. No worker was edited.

R17 EvidenceStore attribution identifies MIT/R17, REUSE-018 and original project
schema/security work. R27 C2A header identifies pycocotools/R27 BSD-style reuse
and its original geometry layer. These satisfy the existing approved source
attribution requirement; NOTICES.md's stale PENDING R27 entry is reconciled.
Historical singular NOTICE references mean NOTICES.md, without source edits or
a new license assertion. REPRO-001..006 release rows use the existing
[Gate-4 evaluation](task026_gate4_evaluation.md), not new experiments for cosmetic
status updates. SEC/synthetic/offline release rows retain that accepted evidence.

Public/demo-facing claims were reviewed without rewriting protected research
history. Completed approved MVP deliverables do **not** mean every capability
is implemented. Operational signing, PDQ/behavioral/drift/OOD/reference-relative
methods, TorchScript/SafeTensors, external tail witnesses, authenticated identity
and other explicitly deferred research remain outside accepted implementation.
T05d is a permanent non-claim. No R01 benchmark is reported as a project result.

## Carried boundaries / stop point

GATE-2/3/4 PASS, TASK-024/026/027 TESTED, SEC-001..012 functional acceptance,
E-2 RESOLVED and ACC-2026-10-02-03 remain unchanged. PRE-08 is PARTIAL;
operational signing remains SIGNING_UNAVAILABLE/Part B DEFERRED. HOST-CAP-003
actual ONNX runtime capability is PASS, while historical TASK-027-C procedural
re-entry remains pending separately. Accepted OFF-002 acceptance PASS / original
recovery-marker FAIL / independent restored-state PASS are not conflated.
No OFF-002 rerun, new architecture decision or post-MVP task is authorized.
