# TASK-026 — Formal Gate-4 evaluation

Date: 2026-10-02. Starting HEAD:
`8ce7569da5a4e88ccc575ff11593245f9af7a3c2`, `feature/vertical-slice`, clean
and synchronized before changes. Authority: MVP §14 Gate-4 / TASK-026 / TASK-022,
Technical §§17–18, Architecture §20, and the approved final reconciliation packet.

## Read-only inventory and gap classification

Before changing files, the criterion-to-evidence inventory established:

| Criteria | Existing evidence at starting HEAD | Latest recorded observation | Sufficient? / fresh action |
|---|---|---|---|
| VS-001, VS-002, VS-004, VS-005, VS-006, VS-007 | test_vertical_slice.py | 7 VS tests passed; baseline non-offline 530 passed / 11 skipped | Re-run; supplement explicit synthetic/export and intact audit assertions |
| VS-003 | Real hostile-pickle VS test | LOAD_BLOCKED / no fallback | Add same-pipeline later COCO continuation assertion |
| §18.1 | VS-002 and C2A geometry units | FIX-008 exact nine; YOLO manifest maps in units | Real persisted/exported observations for FIX-008/009 and maintained observed-result rows missing |
| §18.2 | VS-003, C3D units, accepted C3D record | Hostile blocked / benign load succeeds | Record paired real persisted/exported observations; do not reopen SEC-002/003 |
| §18.3 | Genuine C3A/C3C FIX-004/005/006 units | All containment cases passed at E-2 checkpoint | Record real supervisor/storage observations and synthetic propagation |
| §18.4 | UT-AUD-002/004 and SEC-010 | Modification detected; original events retained; no reset | Existing exact coverage sufficient; re-run and record |
| §18.5 | VS-004 and unavailable negative suite | Four required points remain UNAVAILABLE | Existing exact coverage sufficient; re-run and record |
| Synthetic propagation | Real ONNX storage and exporter preservation tests | Partial explicit coverage | Add all ten fixture cases through pipeline, finding and existing export |
| REPRO-001 | C2A single-run units | No exact repeated violations-list assertion | Add repeated same-input COCO/detection/segmentation assertions |
| REPRO-002 | C2B REPRO-002 and C2D deterministic test | Exact repeated digests passed | Reuse and re-run |
| REPRO-003 | C3B REPRO-003 and real ONNX repeated hash test | Exact combined digest passed | Reuse and re-run; distinguish test-only hash contract from genuine frozen ONNX identity |
| REPRO-004 | C5 rule/schema units | No exact repeated semantic-finding assertion | Add five rule branches, excluding only finding_id / created_at |
| REPRO-005 | Canonicalization expected-bytes unit | No explicit repeated-call assertion | Add same nested/unicode dictionary twice |
| REPRO-006 | Fixture generator REPRO-006 | Same-seed complete COCO file trees match | Reuse and re-run |
| INT-001 | Separate valid COCO / ONNX supervisor runs | Both individually passed | Add one real combined submission |
| INT-002 | Hostile model plus prior resource-fault continuation | LOAD_BLOCKED separately passed | Add hostile model then COCO in one real submission |
| INT-003 | C3 unavailable negative rule tests | C5 UNAVAILABLE | Supplement with schema-gated real supervisor collection-boundary injection |
| INT-004 | Orchestrator schema-rejection test | Rejection audited; no write | Reuse and re-run exact acceptance boundary |
| INT-005 | VS-005 complete persisted deferred set | 15 required coverage-gap records | Reuse and re-run; preserve frozen unavailable states rather than promote them |
| OFF-001 | Accepted target-host stdout / result.json | Install/import PASS, exit 0 offline | Sufficient; review/hash only |
| OFF-002 | TASK-027-S accepted capture and reconciliation | Acceptance 0 packets / 0 bytes, exit 0 | Sufficient; never rerun; preserve recovery-marker FAIL separately |
| OFF-003 | Accepted target-host stdout / result.json | Imports OK, exit 0 offline | Sufficient; review/hash only |
| OFF-004 | Accepted assess/show-finding outputs / result.json | Both exit 0, stored finding returned | Sufficient; review/hash only |

Missing explicit coverage was classified as validation/evidence gaps, not
production defects. Only one new test file was added; no existing test was
deleted, weakened, renamed or newly skipped. Production, fixtures, schemas,
constants, dependency contracts and protected research content are unchanged.

## Criterion-to-observation adjudication

Abbreviations: **VS** = tests/integration/test_vertical_slice.py;
**G4** = tests/integration/test_gate4_validation.py;
**ORCH** = tests/integration/test_orchestrator.py.
Experiment details are in [the observations record](task026_gate4_experiment_observations.md).

| Criterion | Executed / accepted evidence | Observed result | Verdict | Claim boundary |
|---|---|---|---|---|
| VS-001 | VS::test_vs_001_valid_coco_submission_completes_vertical_slice; G4 benign COCO export case | COMPLETED M01, zero violations, four records, finding and audit lifecycle; chain intact | PASS | C2C finding is statistics-only, not stale positive-assurance alias |
| VS-002 | VS::test_vs_002_fix_008_preserves_all_geometry_violations | Nine exact violations/types; 10 annotations checked; anomaly/ESCALATE | PASS | Injected geometry only; intent not established |
| VS-003 | VS::test_vs_003_fix_001_hostile_pickle_is_blocked_without_fallback; G4 combined hostile-pickle case | LOAD_BLOCKED, fallback=false, subsequent COCO C2 completes | PASS | No malicious-intent or behavioral-safety inference |
| VS-004 | VS::test_vs_004_unavailable_propagates_at_every_declared_layer | Ingestion/C2/C3/C4 (plus C5) UNAVAILABLE / UNAVAILABLE_NO_DECISION | PASS | Tested injection points only |
| VS-005 | VS::test_vs_005_capability_declaration_persists_every_deferred_record | Complete 15-record method set persisted with exact disclosures/states | PASS | Nine DEFERRED_IN_SCOPE; reference/tail/identity unavailable and permanent T05d non-claim retained |
| VS-006 | VS::test_vs_006_cli_list_deferred_displays_complete_records | Complete stored records displayed | PASS | Deferred is not successful assessment |
| VS-007 | VS::test_vs_007_cli_export_preserves_unavailable_and_deferred_records | Required six-document ZIP; unavailable findings and coverage records preserved | PASS | No suppression or positive substitution |
| §18.1 | G4::test_experiment_and_synthetic_export[FIX-008/FIX-009-D/FIX-009-S] | Exact manifest maps/counts: 9/6/6; all-box counts 10/7/7 | PASS | Synthetic injected types, not semantic poisoning/T05d |
| §18.2 | G4::test_experiment_and_synthetic_export[FIX-001/FIX-015]; SEC-007 guards | LOAD_BLOCKED / LOAD_SUCCESS; both fallback=false; unsafe-load zero matches | PASS | Successful load is not safety; rejected load is not proven attack |
| §18.3 | G4::test_experiment_and_synthetic_export[FIX-004/FIX-005/FIX-006] | All three ONNX_PATH_CONTAINMENT_VIOLATION; C3 chain stops | PASS | Three genuine injected escape classes, not every traversal variant |
| §18.4 | unit/test_audit_chain.py::test_ut_aud_002_corruption_is_flagged_without_deletion / test_ut_aud_004_no_destructive_recovery_methods; security/test_audit_security.py::test_sec_010_modified_event_detected_without_reset | Modification detected, CHAIN_CORRUPT emitted, original IDs retained, no reset | PASS | Body integrity only; COMPLETENESS_UNAVAILABLE tail remains |
| §18.5 | VS-004 and negative/test_unavailable_propagation.py | Four required injection layers yield UNAVAILABLE / UNAVAILABLE_NO_DECISION | PASS | Mechanism-tested propagation, not all possible failures |
| Synthetic evidence propagation | All G4 experiment + combined/injected runs | 45/45 evidence records and 15/15 findings labelled; exports preserve labels | PASS | Origin set by production submission/pipeline; no post-hoc injection; C3 unavailable injection explicitly marked test-only |
| REPRO-001 | G4::test_repro_001_same_annotations_same_violations, three cases | Exact violations lists match on repeated identical inputs | PASS | COCO/YOLO detection/segmentation fixture scope |
| REPRO-002 | unit/test_c2b_exact_hash.py::test_repro_002_same_file_has_same_digest; unit/test_c2d_image_hash.py::test_ut_c2d_001_deterministic_sha256 | Same bytes, same 64-character SHA-256 | PASS | Byte identity, not decoded image semantics |
| REPRO-003 | unit/test_c3b_model_hash.py::test_repro_003_same_unit_and_moved_copy_have_same_combined_digest; integration/test_onnx_identity.py::test_real_onnx_without_external_data_has_the_independent_combined_digest | Repeated combined digest identical; real frozen-definition ONNX calculation agrees | PASS | Ordered whole-member identity; PF-002 retained |
| REPRO-004 | G4::test_repro_004_same_semantic_finding, five rule branches | Every field identical after ONLY finding_id/created_at exclusion; source evidence unchanged | PASS | No UUID/clock rewrite or broader portability claim |
| REPRO-005 | G4::test_repro_005_identical_canonical_bytes | Repeated nested/unicode dictionary canonical bytes identical and equal frozen JSON encoding | PASS | Same approved Python version |
| REPRO-006 | unit/test_fixture_generator.py::test_repro_006_coco_generation_is_byte_identical | Complete generated COCO file trees byte-identical at seed 42 | PASS | Existing deterministic fixture members, not runtime path metadata |
| INT-001 | G4::test_int_001_002_combined_assets_complete[onnx] | Two assets, seven worker/evidence records, two findings, zero schema rejections, intact terminal audit | PASS | Benign model's absent identity reference remains UNAVAILABLE |
| INT-002 | G4::test_int_001_002_combined_assets_complete[hostile-pickle] | Model first: LOAD_BLOCKED/no fallback; later COCO zero-violation C2 completes; seven records/two findings | PASS | Data-integrity continuation, no unsafe retry |
| INT-003 | G4::test_int_003_c3_unavailable_through_supervisor | Injected C3B UNAVAILABLE passes schema gate to persisted C5 UNAVAILABLE/NO_DECISION | PASS | Named test-only injection after genuine worker collection |
| INT-004 | ORCH::test_invalid_result_is_rejected_without_evidence_write | SchemaViolationError; WORKER_RESULT_REJECTED_SCHEMA_VIOLATION; no invalid evidence | PASS | Actual supervisor acceptance boundary, not fabricated worker runtime |
| INT-005 | VS-005 and G4 exports | Entire frozen coverage-gap set persists before findings and exports | PASS | Architecture-specific unavailable values remain unavailable |
| OFF-001 | Accepted O run off001.stdout.txt + result.json | INSTALL STATUS PASS; declared imports PASS; offline exit 0 | PASS | Frozen target/staged binaries only; no fresh install |
| OFF-002 | Accepted S run acceptance-traffic.json / capture + committed reconciliation | 0 non-loopback physical-NIC Tx packets / bytes, assess exit 0 in accepted window | PASS | No transition traffic included; original recovery marker FAIL is separate |
| OFF-003 | Accepted O run off003.stdout.txt + result.json | Native ONNX/Torch/pycocotools imports OK, offline exit 0 | PASS | Same accepted target tuple; no rerun |
| OFF-004 | Accepted O run off004-assess/show-finding stdout + result.json | Assess and SQLite-backed finding read exit 0; actual asset off-002-valid-coco | PASS | Accepted local read/write evidence, not portable offline guarantee |

INT-001..005 names come from MVP TASK-022. Historical Technical IT-001 positive
finding aliases do not override the frozen C5 vocabulary/priority rules:
statistics-only and missing reference comparison are disclosed, not promoted.
Worker secret removal and temporary cleanup remain covered by
ORCH::test_dispatch_uses_controlled_subprocess_environment_and_cleans_up,
security/test_supervisor_security.py, real ONNX supervisor tests, and G4 runs.
No new output field/state or aggregate assurance is introduced.

## Offline evidence identity and separate recovery facts

**O run:** `C:\ProgramData\SIH26228-Off002\evidence\task027-run-20260928-215709`.
**S run:** `C:\ProgramData\SIH26228-Off002\evidence\task027s-run-20260928-224909`.
Read-only review reuses PROJECT_STATE's TASK-027 current-evidence reconciliation
and `docs/task027s_off002_reconciliation.md`; no OFF test or network command ran.

| Raw artifact | SHA-256 verified during review |
|---|---|
| O/result.json | `1b7b2b5dcde6953f563eb85132a77ea6eb8cc126d204d0b4be61f39b85792df4` |
| O/off001.stdout.txt | `06a5805024f3f41425e798328e1e140e30492b2197811c04bc2c861daf15f55d` |
| O/off003.stdout.txt | `c7a1ba7a18c0ba7c5d1c47c9251171ea565cb782f1e4f607e5cd80b0875f67c5` |
| O/off004-assess.stdout.txt | `de9acc5c0ffc7ede6833aa3d8a15d45da3d117e5cc02f4611a6a7f43ff27552b` |
| O/off004-show-finding.stdout.txt | `37b02f4487ed381702b5f7a4137676dfe5a7b703b96ebd1c96b2d35bd562e2f4` |
| S/TASK-027-Q-final-result.json | `a7d69a670244a2e06355bfa0eecad1f5ad66a3b89760f1d5c754b3a61a24c461` |
| S/acceptance-traffic.json | `a466d36fc4a9816148bdffb894e89191eb11120a1f54a43828a8928647ef20e6` |
| S/acceptance1.etl | `9b33301e176cf60afc0f6b1d43efcd9976782833d79faedab8cd7841c7fe6573` |

OFF-002 acceptance: **PASS**, start `2026-09-28T17:19:58.2002931Z`, end
`2026-09-28T17:19:59.5909248Z`, 0 packets / 0 bytes, assess exit 0.
Original recovery marker: **FAIL**, transient ms_netbios/ms_netbt query errors.
Independent restored host state: **PASS**, adapter Up, zero snapshot binding
mismatches, temporary rule and recovery task absent, PktMon stopped.
The raw overall FAIL/recovery_exit=1 is retained and is not renamed PASS.
Earlier O-run OFF-002 transition failure is historical, not the S acceptance.

## Ordered final regression and gate decision

All eight ordered runs exited 0. Reports are local ignored artifacts in
`build/task026-gate4/`; no skipped test counts as acceptance.

| Order / scope (effective selector) | Observed result | JUnit / SHA-256 |
|---|---|---|
| 1: complete VS file | 7 passed | vs.xml / `654ea6e7e9d3cb5b44b397e683c221b6c7e2f3ae75d3c60c1fcd06f84849b7ed` |
| 2: G4, audit units/security and VS; -k 'experiment or aud or modified or vs_004' | 17 passed, 18 deselected | experiments.xml / `7c34e23cc776528b0ec8e45673b8ea0052b67fe0ed2f762527b50d22715272bc` |
| 3: G4, C2B/C2D/C3B units, fixture generator and real ONNX identity; -k 'repro or deterministic_sha256 or real_onnx_without_external_data' | 15 passed, 64 deselected | repro.xml / `3a5f5c756556919066207e67ea73fa3c3ad67817f94a914b0fe920281c51fe0a` |
| 4: G4, ORCH, VS; -k 'test_int_ or invalid_result_is_rejected_without_evidence_write or vs_005 or controlled_subprocess_environment' | 6 passed, 39 deselected | int.xml / `54704eaba9224665919f33bc6350b1af78ecf92480102dcfab88e5d72954f788` |
| 5: G4 and exporter integration; -k 'experiment_and_synthetic_export or exporter' | 17 passed, 12 deselected | synthetic-export.xml / `9f86c7af94563415ab30f63af5b279fa97db63a318fe29114d70753f7ddf52ef` |
| 6: tests/security | 92 passed, 4 skipped | security.xml / `2408b51b6a4b28c39d1215f3c708681c4188866bd02d0df6f3b2708d70591a4f` |
| 7: tests/integration + tests/negative | 79 passed, 4 skipped | integration-negative.xml / `6799237f030efe55557c98e11ac1e963d151f5b92f0c54044bc670924c003594` |
| 8: tests --ignore=tests/offline | 552 passed, 11 skipped, 0 failed | non-offline.xml / `e880a2820ed9dfbe12cde046f3d466ecbff0f720f322587dd33e7cec2172afa0` |

The 11 unchanged skips comprise four historical security placeholders, two
historical integration placeholders, two historical negative placeholders,
historical UT-CAP-003, PRE-08-gated HMAC and non-selected Ed25519. None is a
missing Gate-4 acceptance case: the criterion matrix maps executable coverage,
not the skipped stubs. All 22 new validation cases execute and pass.

Final observation JSON hashes (same directory's `observations/`, after regression):

| Report | SHA-256 |
|---|---|
| FIX-001.json | `03c51bdfb0f0270fb52130cd63c0e3e33bd0b69f86c2f3f44990b493e57516d4` |
| FIX-004.json | `f814c4e4f9fbeb4d35cb4da1d20ced303db7186a10f7f765c9ebca36ead3605e` |
| FIX-005.json | `24c014a889899bfb608898a2c45e1f5bcbbac72f5cf4e66a51264f7a29380503` |
| FIX-006.json | `068c125c36937abd494cc97391c49bf0e4a8c91cee4fa21f7f4ec258877fbd79` |
| FIX-008-CONTROL.json | `a19871b8ce9e13c25f0e4a1735a99b906fea83ad6dec6ac17eb922fbfce1ba13` |
| FIX-008.json | `19b662fe420e56cacbf3cf9a1af69db87fe920a7e6a6d539400c849f2ce87566` |
| FIX-009-D.json | `c3f3681cb375d8a62fb8452c9ebd6e724c8d065d553d6538d5b5caa5b49c64d2` |
| FIX-009-S.json | `eca1b4db5166322ffc4990383feeb0a78faaf55ecca9af469c5e50a2e19965d5` |
| FIX-015.json | `2ac08b417cc44143dcf19046061a05349b5c0ffb8a02091338b2d0fcd722c3bb` |
| FIX-016.json | `f6a22da70bd75ca635fd46b636384d4ad9ecb6870de86a828a38f2eb550090a7` |
| INT-hostile-pickle.json | `8a8836a626f48d04fe5a53a763d28991d3e35663d295cbaf4f45e9da4b307662` |
| INT-onnx.json | `72e980806a21a466d8c336067e87bfe593d2b7eddd9e211296e7cd3ba0a795eb` |
| INT-unavailable.json | `563ed0f7dbc3c9a7f6986ffbff9b334d3a484ea1a535d60447670f5806257bbd` |

Prior locally overwritten E-2 supervisor / SEC-008 observation reports were
copied unchanged into `build/task026-gate4/prior-observations/` before their
existing regression tests wrote fresh observations. Historical committed
validation records and report hashes remain unchanged.

Universal production guards: zero matches for unsafe loading, risk_score,
aggregate_assurance, compromise_probability, overall_assurance_score,
shell=True, Fabric/HyperLedger, and quoted positive CLEAN/SAFE/HEALTHY constants.
No production defect was found or repaired. `git diff --check` passes;
`docs/research/**` and production source have no diff from the starting HEAD.

**ALL-OF decision: GATE-4 PASS. TASK-026 TESTED.** Every authoritative criterion
has actual passing evidence; no extra procedural or operational-signing gate
was invented. This establishes only the fixture-bounded observations above.

## Carried boundaries

GATE-2 and GATE-3 PASS are retained, E-2 remains RESOLVED and all C3 workers
remain TESTED. PRE-08 stays PARTIAL; unsigned SIGNING_UNAVAILABLE is the approved
MVP shell, not signing completion. HOST-CAP-003 factual ONNX runtime capability
is PASS; its separately recorded historical TASK-027-C full procedural re-entry
remains pending. The approved packet permits accepted OFF evidence for Gate-4:
that historical procedural note is not an invented additional Gate-4 criterion.
Neither historical source nor prior validation record is rewritten.

GATE-5 is NOT PASSED, TASK-024 is NOT STARTED. With Gate-4 PASS, the next logical
candidate is TASK-024 dashboard / analyst visual interface preparation for
Gate-5 under its own execution packet. No dashboard, demo, signing or new task
starts here.
