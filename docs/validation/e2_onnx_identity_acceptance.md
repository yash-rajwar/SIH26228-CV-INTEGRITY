# E-2 / SP-002-ONNX — Real Identity Acceptance and Gate-3

## Checkpoint and authority

- Starting HEAD: `1a7c21919475cdc0bc4ce2432910852709937819`.
- Branch: `feature/vertical-slice`; clean worktree verified before modification.
  `git pull --ff-only origin feature/vertical-slice` reported already up to date.
- Owner decision date: **2026-10-05**, exactly as required by the execution packet.
  Actual validation execution date: **2026-10-02**. These are distinct; no future
  execution is claimed.
- Authority: Architecture §6 COMP-W-C3A and AC-03; Technical §§3.7/3.8/3.9;
  MVP TASK-014/015 and §14 Gate-3; approved owner SP-002-ONNX closure packet.
- Decision record: `artifact_unit_defs/onnx_artifact_unit_spec.md`, with the
  smallest freezing entry in `docs/ARCHITECTURE_CHANGE_LOG.md`. This resolves
  an existing pending definition, not an architecture/trust-boundary change.
- Frozen ID: `onnx-main-referenced-external-data-v1`.

One unit is exactly one contained existing regular main `.onnx`, plus every
unique contained existing regular external tensor-data file referenced through
the complete existing recursive protobuf TensorProto traversal. Paths are
canonical, sorted and deduplicated. Every external member is a whole file byte
object; offsets/lengths do not restrict hashing. Unreferenced neighbours and
directory scanning/globbing do not establish membership.

Absolute/rooted/drive/UNC/traversal/canonical/symlink escapes retain
ONNX_PATH_CONTAINMENT_VIOLATION, before outside content is opened. Contained
missing, non-regular or inconsistent members remain ARTIFACT_UNIT_AMBIGUOUS,
without any identity digest. PF-002, limitations and non-claims are unchanged.

## Minimal implementation and genuine defect

Changed files (17):

- Production: `assurance_system/workers/c3a_artifact_unit.py`,
  `assurance_system/supervisor/orchestrator.py`.
- Tests: `tests/unit/test_c3a_artifact_unit.py`,
  `tests/unit/test_artifact_unit_definitions.py`,
  `tests/integration/test_onnx_identity.py`,
  `tests/integration/test_onnx_supervisor.py`.
- Decisions/specifications: `artifact_unit_defs/README.md`,
  `artifact_unit_defs/onnx_artifact_unit_spec.md`,
  `docs/ARCHITECTURE_CHANGE_LOG.md`, `docs/ARCHITECTURE_SPECIFICATION.md`,
  `docs/TECHNICAL_SPECIFICATION.md`, `docs/MVP_IMPLEMENTATION_PLAN.md`.
- State/public evidence: `PROJECT_STATE.md`, `PROJECT_STATUS.md`, `README.md`,
  `CHANGELOG.md`, `docs/validation/e2_onnx_identity_acceptance.md`.

C3A replaces its intentionally unresolved ID with the approved ID and removes
only the obsolete E-2 limitation. A complete unit now returns COMPLETED,
BLACK_BOX and the frozen artifact_unit_id. Main suffix enforcement occurs after
containment/regular-file checks, before header parsing. Recursive traversal and
external-reference containment algorithms are not rewritten or narrowed.

The supervisor selects the approved ONNX ID; PyTorch remains
`pytorch-single-file-v1`. A supplied mismatching ID fails ingestion closed.

A real missing-external-file supervisor test demonstrated a genuine defect:
C3A returned ARTIFACT_UNIT_AMBIGUOUS with diagnostic partial membership, but the
supervisor forwarded that membership to C3B. Once the definition was frozen,
C3B produced a COMPLETED main-only digest. Previously, the UNAVAILABLE ID masked
this defect. The smallest contract-preserving repair forwards membership only
after COMPLETED C3A resolution. The same real test now proves C3B ambiguity,
no per-file/combined digest, and `artifact_unit=None` at the dispatch boundary.

C3B production code is unchanged. It validates every member's containment before
the first read, SHA-256 hashes complete file bytes, sorts canonical paths
lexicographically, concatenates the lowercase per-file hex digests in that order,
and SHA-256 hashes the ASCII sequence. Even a single-file unit retains the outer
digest. Reference comparison remains MATCH / DIFFERENT / UNAVAILABLE.

Initial integration-test failures were classified separately as test defects:
PF-002 worker fields are checked on the actual rich validated C5 input, not as
nonexistent evidence-table columns. A missing identity has no C4 binding, so its
finding legitimately retains `C4_BINDING_UNAVAILABLE`. No DDL/schema or production
non-claim handling was changed to accommodate those assertions.

## Real acceptance cases

`tests/integration/test_onnx_identity.py` contains ten real cases. Existing
deterministic ONNX writers are used; no production fixture is modified.

| Case | Actual observation |
|---|---|
| Valid no-external ONNX | C3A COMPLETED/BLACK_BOX/frozen ID, external_files []; C3B COMPLETED with independently recomputed outer digest; repeat deterministic; MATCH/DIFFERENT/UNAVAILABLE comparisons retained |
| Valid contained external data | ONNX checker validates the model; C3A includes canonical weights.bin; C3B hashes main plus the complete external file, matching an independent byte computation |
| Tail tamper outside declared tensor length | Main bytes and main digest unchanged; external digest and combined digest change, proving whole-file hashing rather than offset/length-only slices |
| Unreferenced neighbour control | Changing unrelated.bin and unreferenced.onnx.data changes neither membership nor combined digest |
| Duplicate canonical references | weights.bin and ./weights.bin resolve to one canonical member, hashed once |
| Missing referenced member | C3A/C3B ARTIFACT_UNIT_AMBIGUOUS; no digest |
| Referenced directory | C3A/C3B ARTIFACT_UNIT_AMBIGUOUS; no digest |
| Duplicate/inconsistent location metadata | C3A/C3B ARTIFACT_UNIT_AMBIGUOUS; no digest |
| Non-.onnx main with real ONNX header | ARTIFACT_UNIT_AMBIGUOUS; no digest |
| Complete recursive protobuf scope | Eight referenced files from initializer, sparse initializer, tensor attribute, repeated tensor attributes, graph/graphs substructures and function discovered and hashed; custom synthetic nodes prove membership traversal, not operator validity or model execution |

SEC-004/005/006 execute genuine FIX-004 absolute-reference, FIX-005 traversal
and FIX-006 symlink-escape models through both C3A and C3C: six selected tests
pass. Existing missing-runtime, outside-main, mixed-separator, rooted/drive/UNC,
before-stat/read containment, malformed protobuf and checker tests also pass.

## Actual restricted Windows supervisor pipeline

`tests/integration/test_onnx_supervisor.py` executes two real runs: seed-26228
benign no-external ONNX and missing external data. Neither worker outputs nor
hashes are mocked. Observers wrap, then invoke, the real production seams.

For the valid run: normalized manifest gets the frozen ID; C3A and C3B are
COMPLETED; C3C is STRUCTURAL_VALID. Three workers exit 0, three schema-gated
synthetic records persist, C5 receives all three rich records with exact PF-002
and boolean non-claims, one schema-valid finding and unsigned provenance persist,
15 explicit missing-coverage records remain visible, no schema rejection occurs,
and the audit chain is intact. Missing reference comparison remains UNAVAILABLE.

Observed single-file inner SHA-256:
`69020278010c8918798f7ca517dc81ff571fcd3f87bea07720d66df0fd77aefe`.
Independently recomputed combined digest:
`3bea394d1082240f0964085484e5dcfd3cff3da475e7bc1e73ecefe414afc537`.
These are distinct: the raw main digest was not substituted for the combined one.

For the incomplete run: C3A/C3B retain ARTIFACT_UNIT_AMBIGUOUS; C3C remains
structural-validation-only; no identity digest/provenance binding is fabricated.
Finding PF-002 binding status is explicitly C4_BINDING_UNAVAILABLE.

Both runs use `RestrictedWindowsProcess`, the production deny-only privileged
groups and configured Windows Jobs. Three jobs per run are assigned/resumed/
closed; native/token/process/thread/station/desktop/pipe handles are closed and
temporary worker directories removed. No unrestricted launch fallback is used.

## Ordered validation and evidence hashes

Approved interpreter: `C:\Users\master\Desktop\SIH26228-CV-INTEGRITY.venv-torch-test\Scripts\python.exe`.
Python 3.13.12 / AMD64; ONNX 1.23.0; protobuf 7.36.2; pytest 9.1.1. No package
installation/download or dependency version change.

Reports below are preserved locally in ignored `build/e2-onnx/`. Each command
uses `-m pytest -q --tb=short --junitxml=build/e2-onnx/<report>`; selectors below
specify exactly the executed scopes. All commands exit 0.

| Order / selector | Result | Report / SHA-256 |
|---|---|---|
| 1: unit/test_artifact_unit_definitions.py + unit/test_config_loader.py | 18 passed | 01-definitions.xml / `e4e0422a68978d65707b4ba7e1a3820806fac7ab9f8401eeaee631e58d9832c6` |
| 2: unit/test_c3a_artifact_unit.py | 30 passed | 02-c3a.xml / `e25488378115570354fb8c5a61c927e9b955d3affe9374f65ead84ac0b5984e2` |
| 3: unit/test_c3b_model_hash.py | 18 passed | 03-c3b.xml / `c0f29a449e4bc437b8fe5389e1643ebf052c776266e302de275fc15d991dbc4a` |
| 4: unit/test_c3c_onnx_structural.py | 18 passed | 04-c3c.xml / `1588c30037b52012c4b26032dc786ecd7dd887d58a231b15cb9303339606a26f` |
| 5: integration/test_onnx_identity.py | 10 passed | 05-real-identity.xml / `c961bdba7ea59dcaab62b5512a269c81255bc8191ef2cc29abf52966c05e9140` |
| 6: integration/test_onnx_supervisor.py | 2 passed | 06-real-supervisor.xml / `da9b7fd7d7eac8f72110b5af3eaf95d2719ec38e3de322e036ae79f32301a674` |
| 7: C3A/C3C units -k 'fix_004 or fix_005 or fix_006 or sec_006' | 6 passed, 42 deselected | 07-sec004-006.xml / `e65753305c6a5be57b22a449f977bacf7363627da36a96b00359720174c26d89` |
| 8: security/test_c3d_security.py -k sec_002 | 1 passed, 11 deselected | 08-sec002.xml / `95eb1c01cf0ed7fb373ca70b93cdd5249b44265144b4a7a1af11019c05761d33` |
| 9: security/test_c3d_security.py -k sec_003 | 1 passed, 11 deselected | 09-sec003.xml / `c25d5a18660ee4b8b1b1fdaad4539b815a6e03784587f389f16e84c8e91ab00f` |
| 10: security/test_windows_evidence_acl.py | 2 passed | 10-sec008.xml / `f60a924bfd351f1e82101f8487388e0568bc33adb541fbaac63c6509df3d3fd0` |
| 11: tests/security/ | 92 passed, 4 skipped | 11-security.xml / `9144cb19154069b7bebb97ec1115d8e35fbb17590255a6c6d70ffbce680dbc3e` |
| 12: tests/integration/ + tests/negative/ | 57 passed, 4 skipped | 12-integration.xml / `96ac5d22ebf8915f6021f3b16e700d3a538ca58ded14453195c99b6d1b48385e` |
| 13: tests/ --ignore=tests/offline | 530 passed, 11 skipped, 0 failed | 13-non-offline.xml / `e483d6a739dde0799fb8c5c5e81aa02f253def6d152a8b4893fef9ab08b48ae4` |

Final supervisor observations (also exercised during regression):

- supervisor-valid.json: `372535412f2cde6965d24cbaa0ee2d1a69a037493f6bd67eb52281018bc5279f`.
- supervisor-missing.json: `6e1ba26208bcf3004773de58d6e33584fdf7a4682cc261a1ad6de9147b2b2842`.

Skips remain distinct from passes: four historical security stubs, two historical
integration stubs, two historical negative stubs, historical UT-CAP-003 CLI
placeholder, PRE-08-gated HMAC and non-selected Ed25519. Their functional
counterparts execute where implemented. No test was deleted or newly skipped.

Universal guards: zero production matches for weights_only=False, risk_score,
aggregate_assurance, compromise_probability, overall_assurance_score, shell=True
and quoted positive CLEAN/SAFE/HEALTHY constants. Diff check is clean. No C3B,
C3C, C3D, schema, constants, production fixtures, network controls or protected
docs/research modification. No ONNX Runtime or model execution introduced.

## Complete Gate-3 adjudication

| MVP §14 trigger / criterion | Observed evidence / result |
|---|---|
| All C2 workers complete | Existing Stage-5 acceptance in ancestor 21b0600 (E-1 CLEAR), preserved C2 implementations; current units C2A/B/C/D 12/8/8/6 pass, including UT-C2A-004; C2B's historical IMPLEMENTED summary label is not a missing implementation or acceptance requirement |
| All C3 workers complete | C3A/C3B now TESTED after real frozen-definition acceptance; C3C/C3D TESTED retained; targeted and full regression units 30/18/18/29 pass |
| C4 shell, C5, REF, CAP complete | Existing TESTED component/shell acceptance and current unit/security regression pass; PRE-08 operational signing is not substituted for or required by the permitted shell |
| All C2 worker units | PASS, including every-annotation coverage; real COCO/FIX-008 vertical slice also passes |
| All C3 worker units | PASS; real ONNX identity evidence replaces the historical test-only-definition limitation |
| SEC-001..012 | Functional PASS: actual hostile restricted load; Job OOM ceiling; controlled timeout; genuine ONNX absolute/traversal/symlink containment; unsafe-load guards; actual deployed DACL worker denial; replay; corruption; nested schema rejection and boolean coverage enforcement. Skipped historical placeholders are not acceptance evidence |
| FIX-013 all four injection points | PASS: VS-004 includes ingestion, C2, C3, C4 and additional C5; negative propagation 7 passed; failure states and disclosures retained |
| C5 priority 1 / no score / T05d / PF-002 | PASS: interpretation 13 units, negative cases, schema guards and real C3-to-C5 propagation; absence of C4 binding is explicitly unavailable, not fabricated assurance |
| SEC-010 audit corruption | PASS: tests/security/test_audit_security.py detects modified payload, emits CHAIN_CORRUPT and retains original events without reset |
| SEC-009 replay | PASS: tests/security/test_provenance_security.py rejects duplicate nonce, preserves one record and emits REPLAY_ATTEMPT_DETECTED |
| Unsafe-load zero-match guard | PASS, exact production literal scan and dedicated SEC-007 tests |

**Gate-3: PASS.** Every authoritative trigger/criterion has observed evidence.
Earlier NOT PASSED decisions in SEC-008/C3D records remain historical; their
only latest remaining trigger, E-2, is now resolved. Gate-2 PASS is preserved.

## HOST-CAP-003 and carried boundaries

Factual capability now passes: approved target runtime executes real C3A/C3B/C3C
with complete traversal, containment, structural checks and persisted pipeline
evidence. ONNX is not described as absent or runtime-blocked.

Formal HOST-CAP-003 remains **PROCEDURAL-PENDING**. The exact recorded requirement
is `docs/task027c_gate2_validation.md`, **Required Next Action**: after the PyYAML
and descriptor prerequisites, TASK-027-C must be rerun from the beginning with
approved zero-egress evidence. `docs/task027e_dependency_contract_closure.md`
§19 likewise calls for formal host-capability revalidation. This packet forbids
OFF-002/network execution and does not authorize that distinct action. This
procedural remainder does not undo E-2 or passing C3 component/Gate-3 acceptance.

Gate-4 NOT PASSED and not adjudicated; TASK-026 IN PROGRESS pending separate §18
observed-result/full-validation reconciliation. PRE-08 PARTIAL; operational
signing remains deferred. TASK-024 NOT STARTED. OFF-002 acceptance PASS, original
recovery-marker FAIL and independent restored-state PASS remain separate
historical facts. No OFF/network test is rerun. No next task is authorized;
obtain a separate execution packet before Gate-4 or any new implementation.
