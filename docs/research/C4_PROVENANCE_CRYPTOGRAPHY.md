# C4 — Provenance & Cryptography Research

> **Public Research Edition — SIH 2026 PS 26228**  
> **Problem Statement:** Trustworthy Computer Vision Integrity Assurance for Data, Models and Inference Outputs in Multi-Contributor Pipelines  
> **Cell:** C4 — Provenance / Cryptography  
> **Deliverable:** C4-V2-001  
> **Audit supplement:** C4-V2-AUD-001  
> **Revision:** 2  
> **Research status:** **CONDITIONAL GO TO IMPLEMENTATION TARGET; NO PROJECT-VERIFIED PROMOTION**

---

## Document Metadata

| Field | Value |
|---|---|
| Deliverable ID | `C4-V2-001` |
| Audit supplement ID | `C4-V2-AUD-001` |
| Revision | 2 |
| Domain | Provenance and Cryptography |
| Stage | V2 |
| Research objective | Specify defensible offline inference-record binding, freshness, trust anchors, and claim boundaries |
| Current implementation disposition | **CONDITIONAL — implementation target only** |
| Project-verified | **false** |
| Final architecture claimed | **false** |
| Offline installation | **UNVERIFIED** |
| Target-format coverage | **UNVERIFIED** for COCO, YOLO, ONNX, PyTorch, and TorchScript |
| Trusted wall-clock time | **UNSUPPORTED** |
| Rollback-resistant state | **UNSUPPORTED** |
| Tail completeness without trusted checkpoint/witness | **UNSUPPORTED** |
| Multi-writer operation | **UNSUPPORTED** |
| Baseline retraining | **OUT OF SCOPE** |
| Semantic correctness | **OUT OF SCOPE** |

The V2 dossier supports proceeding to a **current implementation target** built around RFC 8785/JCS canonicalized records, exact-byte SHA-256 artifact digests, Ed25519 signatures, a single-writer hash chain, persisted verifier state, and an independently retained signed checkpoint. That is a research/design recommendation, not evidence that the complete mechanism has been implemented or validated on the project target.

A separate project-control inconsistency also remains: the research task is scoped as V2, while a control workbook inspected by the source dossier still recorded C4 as `DISCOVERY` with V2 `NOT_STARTED`. This public edition preserves the inconsistency as an unresolved control-state issue rather than silently rewriting it.

### Public-safety note

One inspected source packet contained credential-bearing, time-limited presigned-URL metadata in OOXML relationships. That metadata was treated as untrusted sensitive input, was not dereferenced, and is intentionally excluded from this public document. Its presence is a provenance-hygiene finding, not implementation evidence.

---

## 1. Research Objective

C4 owns the problem of **cryptographic binding and audit provenance** around an inference event. Its core question is:

> How can an offline or air-gapped verifier establish a defensible relationship between the exact bytes of an inference input, the model identity or digest, preprocessing and runtime configuration, inference output, provenance metadata, and stream state so that specified post-hoc modification becomes detectable under explicitly stated assumptions?

The narrow proposition supported by this research is:

> A verifier can establish that presented bytes match committed digests and that a canonical record verifies under an accepted public trust anchor, subject to the declared serialization, key, state, storage, checkpoint, and freshness assumptions.

That proposition is deliberately narrower than a generic statement that the system, model, data, or inference is “secure.”

C4 therefore separates four questions that are often conflated:

1. **Byte binding:** do presented bytes match signed digest commitments?
2. **Record integrity and origin under a key:** does the configured signature verification algorithm accept the canonical signed payload under an accepted trust anchor?
3. **Logical continuity:** does the record satisfy stream, sequence, predecessor, local state, and applicable checkpoint rules?
4. **Semantic assurance:** are the data clean, the model safe, the inference correct, or the event malicious?

C4 addresses the first three only within its declared boundary. Semantic assurance belongs to the other cells.

---

## 2. C4 Scope and Boundaries

### In scope

C4 covers:

- exact-byte artifact hashing;
- SHA-256 digest commitments;
- deterministic serialization and canonicalization;
- digital signatures;
- signed inference records;
- public trust-anchor verification;
- stream and epoch identifiers;
- sequence-based logical freshness;
- replay handling relative to intact verifier state;
- previous-record hash linkage;
- persisted verifier state;
- independently retained signed checkpoints;
- detection of specified deletion and reordering cases under stated preconditions;
- explicit verification result classes;
- audit-record integrity;
- offline verification design;
- trust-anchor handling and key-lifecycle questions;
- crash/state/recovery evaluation requirements;
- evidence packaging and reproducibility requirements.

### Out of scope

C4 does **not** own:

| Area | Owning cell / treatment |
|---|---|
| Data cleanliness, poisoning assessment, dataset semantics | C2 |
| Model behavior, backdoor assessment, model-identity semantics | C3 |
| Assurance interpretation and analyst-facing semantics | C5 |
| Overall engineering/build validation and target runtime integration | C6 |
| Mission and operational context | C1 |
| Baseline retraining or model repair | Out of scope for C4 |

C4 must not be read as a generic security architecture. It binds and verifies specific evidence under conditions; it does not independently establish that the protected evidence is truthful or safe.

---

## 3. PS Requirements Relevant to Provenance

| ID | Status | Requirement and boundary |
|---|---|---|
| `C4-REQ-01` | FACT | Operate offline or air-gapped after installation. Verification must not require a network timestamp, public transparency service, online identity provider, or online revocation service. |
| `C4-REQ-02` | FACT | Remain model-agnostic. COCO/YOLO and ONNX/PyTorch/TorchScript are target representations, but no coverage claim is permitted until explicit fixtures are executed. |
| `C4-REQ-03` | FACT | No baseline retraining. C4 consumes C2/C3 outputs and does not retrain or repair the model. |
| `C4-REQ-04` | FACT | Preserve unavailable/unsupported states. A mismatch does not prove attack, and an unavailable assessment must never be translated to `CLEAN`. |
| `C4-REQ-05` | FACT | Fit an approximately five-implementation-day envelope using public or team assets and reproducible tests. |
| `C4-REQ-06` | RECOMMENDATION | Use deterministic serialization, signed records, logical freshness controls, protected trust anchors, explicit failure classes, and conservative claim language. Do not publish a final-architecture claim before project evidence exists. |

### Assumptions and required access

| Area | Current C4 position |
|---|---|
| Read access | The signer must receive exact input, output, configuration, and C3 model-reference bytes or authoritative digests. A path alone or a mutable buffer is insufficient for a strong binding claim. |
| Write access | The implementation target needs append-only record output and crash-safe local state. Checkpoints should be retained independently of the record directory where feasible. |
| Keys | Record and checkpoint private keys are signer-only; verifiers receive authenticated public anchors. Key compromise, anchor substitution, and rollback remain deployment risks. |
| Concurrency | One logical writer per stream. Multi-writer ordering is unsupported until a coordination rule and race tests exist. |
| Artifact unit | The five-day target is single-file exact-byte hashing. Directories, symlinks, sparse files, archives, mutable memory, and remote objects are unsupported. |
| Formats | No COCO, YOLO, ONNX, PyTorch, or TorchScript project fixture results were supplied. |
| Time | Host time is descriptive unless a trusted-time profile is separately introduced and verified. |

---

## 4. Provenance and Trust Model

### 4.1 Protected relationship

The current C4 target binds the following categories into one signed payload:

```text
INPUT BYTES / INPUT DIGEST
          +
MODEL IDENTITY / CONDITIONAL WEIGHT DIGEST
          +
PREPROCESSING + RUNTIME CONFIGURATION
          +
INFERENCE OUTPUT BYTES / OUTPUT DIGEST
          +
PROVENANCE + C2/C3 STATUS
          +
STREAM + EPOCH + SEQUENCE + PREVIOUS RECORD HASH
          +
ALGORITHM + KEY REFERENCES
          ↓
VERSIONED CANONICAL PAYLOAD
          ↓
SHA-256 RECORD HASH + ED25519 SIGNATURE
          ↓
VERIFIABLE RECORD
```

This diagram is a **conceptual/current implementation target**, not proof of a deployed architecture.

### 4.2 Threat model and interpretation

| Threat / condition | Cryptographic effect | Required interpretation |
|---|---|---|
| Record-key compromise | An attacker controlling the private key can create records that verify under that key. | A valid signature is not evidence that the key was uncompromised. |
| Replay | A previously valid signed record remains cryptographically valid. | Replay handling requires sequence/state rules; signature validation alone is insufficient. |
| Interior deletion | A missing middle record can produce a sequence gap or predecessor mismatch when adjacent evidence/state exists. | Detection is conditional on available neighboring evidence and intact state. |
| Suffix/tail deletion | A shorter valid prefix may still verify internally. | Stronger tail-completeness evidence requires a later trusted checkpoint or witness. |
| Reordering | Strict sequence and predecessor-hash checks are intended to expose changed order within one stream/epoch. | Claim only after tests and only within the single-writer state model. |
| Canonicalization ambiguity | Semantically equivalent JSON can have different byte encodings. | Freeze the canonicalization and rejection profile before signing. |
| Trust-anchor replacement | Replacing the accepted public key can make attacker-signed records appear accepted locally. | Trust provisioning, fingerprint comparison, replacement control, versioning, and rollback behavior are security-critical. |
| Verifier-state rollback | Restoring an old last-seen sequence/head can admit replayed prefixes. | Logical freshness is conditional on intact non-volatile state. |
| TOCTOU | Bytes can change between hashing and execution. | Hashing a snapshot is not automatically proof of causal execution with that snapshot. |
| Semantic conflation | Authentic signed content can still be wrong, poisoned, backdoored, or malicious. | Report cryptographic binding separately from C2/C3/C5 assurance. |

### 4.3 Trust-root boundary

A `signer_key_id` is only useful when it resolves to a key already accepted by a trusted provisioning process. A key identifier embedded in an untrusted record must never authorize a new key by itself.

The current source does **not** provide a complete project ceremony for:

- initial anchor provisioning;
- two-channel fingerprint comparison;
- protected trust-store installation;
- anchor replacement;
- offline rotation;
- offline revocation;
- compromise recovery;
- historical validation after rotation;
- rollback-resistant anchor metadata.

Those remain implementation and operational gaps.

---

## 5. Cryptographic Integrity Foundations

### 5.1 Hashing

The current C4 target uses SHA-256 to commit to exact artifact bytes.

Conceptually:

```text
artifact_digest = SHA256(presented_exact_bytes)
artifact_match  = artifact_digest == digest_inside_signed_payload
```

A digest commitment establishes a byte-level relationship: if the exact presented bytes produce the same digest as the digest protected inside the signed record, the verifier has evidence that those presented bytes match the committed byte sequence, subject to the hash and trust assumptions.

A digest match does **not** establish that:

- the content is safe;
- the content was authentic before hashing;
- the model is clean;
- the input was unpoisoned;
- the output is correct;
- the bytes were actually used in the inference;
- the key or host was uncompromised.

A digest mismatch means the presented bytes do not match the signed commitment. It does **not** by itself identify the cause. Mutation, replacement, corruption, incorrect selection, storage error, transport error, or malicious action can all produce a mismatch.

Therefore:

> **HASH MATCH ≠ SAFE**  
> **HASH MISMATCH ≠ PROVEN ATTACK**

#### Artifact-unit scope

The selected five-day profile is deliberately narrow: one exact immutable file at a time. Broader artifact types require additional semantics that are not yet frozen.

| Artifact form | Current C4 status |
|---|---|
| Ordinary single file | Implementation target |
| Model weights in a single exact file | Conditional on C3 scope definition |
| External model-data files | Unresolved / must be explicitly included in scope |
| Multiple-file model package | Unsupported in current target |
| Directory tree | Unsupported |
| Symlink | Unsupported |
| Sparse file | Unsupported |
| Archive with internal members | Unsupported as a semantic container; exact archive bytes may be hashable but do not define member semantics |
| Mutable in-memory object | Unsupported |
| Remote object/path-only reference | Unsupported |
| Memory-mapped mutable file | Unsupported until stable-byte behavior is tested |

### 5.2 Canonicalization

Digital signatures operate on bytes. JSON objects are not inherently a unique byte representation: whitespace, property order, numeric rendering, escaping, and implementation behavior can change the serialization.

RFC 8785 defines the JSON Canonicalization Scheme (JCS), which provides a deterministic JSON serialization within its accepted profile. C4 uses canonicalization as a prerequisite to deterministic signing, not as an authentication mechanism.

The source research preserves the following JCS-related boundaries:

- object properties are deterministically sorted;
- array order is preserved;
- insignificant whitespace is absent;
- strings are preserved rather than silently Unicode-normalized;
- invalid Unicode input is rejected;
- `NaN` and infinities are rejected;
- duplicate JSON member names are rejected by the C4 profile before canonicalization;
- verified RFC 8785 Erratum 7920 is applied to reject negative zero rather than silently collapsing `-0` to `0`;
- out-of-profile numeric intent or precision must be rejected rather than silently coerced.

The source does **not** support the statement “JCS guarantees integrity.” JCS only makes the byte representation deterministic enough for cryptographic operations when implementations agree on the frozen accepted profile.

The exact parser flags, library version, numeric bounds, profile identifier, and interimplementation tests are still part of the Day 0 freeze.

### 5.3 Digital Signatures

The current implementation target uses Ed25519, with RFC 8032 test vectors as mechanism-level conformance material.

Conceptually:

```text
payload_bytes = JCS_RFC8785_C4_PROFILE(payload)
signature     = Ed25519.Sign(record_private_key, payload_bytes)

verification  = Ed25519.Verify(
                  accepted_public_key,
                  payload_bytes,
                  signature
                )
```

Asymmetric signing fits the offline-verifier model because the verifier can hold an authenticated **public** trust anchor without also receiving the private signing capability.

Within C4, a valid signature means:

> The configured verification algorithm accepted the exact canonical payload bytes under an authenticated accepted public key.

It does **not** independently establish:

- who physically controlled the signer;
- that a human or organization was authorized;
- that the private key was uncompromised;
- that the record was truthful before signing;
- that the model was safe;
- that the inference was correct;
- that the host clock was trustworthy;
- that the stream is complete.

The source dossier contains the sentence:

> “A valid signature on an inference record proves the record content was not modified after signing. It does not prove the inference was semantically correct.”

For the public research edition, that statement must be read with its source-audit qualification: the claim assumes the verifier is checking the exact canonical signed bytes against an accepted authentic key. It is not a claim about uncompromised key custody, signer authorization, or pre-signing truth.

### 5.4 HMAC and Trust Models

HMAC is not treated as “bad.” It represents a different trust model.

HMAC uses a shared secret. Any verifier holding that secret can also generate valid authentication tags. That can be appropriate when all participating verifiers are intentionally trusted as tag generators, but it does not provide the same verifier-origin separation as public-key signatures.

For C4:

- HMAC is **DEFERRED** unless a shared-secret operational requirement is established;
- it is not used as a drop-in replacement for asymmetric record signing;
- the public-verifier model favors a public trust anchor and signer-only private key;
- broad “nonrepudiation” claims are not adopted for the project because key ownership, signer identity, authorization, and compromise handling are not established.

---

## 6. Inference-Record Binding Model

### 6.1 Current V2 binding matrix

The following matrix is the selected **V2 recommendation**, not an approved final architecture.

`MANDATORY IF AVAILABLE` means the status field must be present and the digest becomes mandatory only when the supplying dependency reports `AVAILABLE`. Otherwise the record must preserve `UNAVAILABLE` or `NOT_ASSESSED`.

| Binding element | Proposed field/control | Requirement | Meaning and boundary |
|---|---|---|---|
| Schema and record type | `schema_version`, `record_type` | MANDATORY | Selects the verification profile. Unknown schema versions/types are rejected. |
| Input hash | `input.status`, `input.digest`, `input.representation` | MANDATORY IF AVAILABLE | Binds exact input bytes using SHA-256. Does not prove authenticity before hashing. |
| Model identity | `model.status`, `model.identity_digest`, `model.scope_id`, `model.format` | MANDATORY IF AVAILABLE | Binds the identity statement supplied by C3; C4 does not redefine its semantics. |
| Weight hash | `model.weight_digest`, `model.weight_scope_id` | CONDITIONALLY MANDATORY | Required when the C3 identity digest does not commit to the exact executed weights. |
| Pre/post-processing and configuration | `config.status`, `config.digest`, `config.scope_id` | MANDATORY IF AVAILABLE | Binds deterministic bytes only to the extent C2/C3 define a representation. |
| Output hash | `output.status`, `output.digest`, `output.representation` | MANDATORY IF AVAILABLE | Binds exact serialized inference-output bytes; does not prove correctness. |
| Stream / epoch | `stream_id`, `epoch_id` | MANDATORY | Separates ordered streams and reset/key epochs. Epoch-transition authorization remains unresolved. |
| Sequence | `sequence_no` | MANDATORY | Genesis is sequence 0; later records increment by one in current profile. Integer bounds remain to be frozen. |
| Nonce | `nonce` | OPTIONAL | Can provide uniqueness but is not accepted as replay protection. |
| Previous record hash | `prev_record_hash` | MANDATORY EXCEPT GENESIS | `null` at sequence 0; otherwise SHA-256 of prior canonical payload bytes under current V2 rule. |
| Host timestamp | `host_timestamp` | OPTIONAL / DESCRIPTIVE | Format may be RFC 3339 UTC after freeze; does not drive acceptance and is not trusted time. |
| Trusted time evidence | `trusted_time` | OPTIONAL / DEFERRED | Only if a separately verified trusted-time profile exists. None is available in the MVP. |
| Signer key reference | `signer_key_id`, `signer_key_fingerprint` | MANDATORY | Resolves an already trusted anchor. `key_id` is a lookup hint, not identity proof. |
| Contributor identity | `contributor_id`, `contributor_authority` | OPTIONAL | A signed name is not authenticated identity without an external identity/authorization policy. |
| Algorithms | `hash_alg`, `signature_alg` | MANDATORY | Fixed/allowlisted values (`sha256`, `ed25519`) in current target; reject unrecognized record-selected algorithms. |
| Canonicalization | `canonicalization`, `canonicalization_profile` | MANDATORY | Identifies RFC 8785 plus the local rejection profile. Exact package/profile ID remains to be frozen. |
| Availability/assessment | `availability`, `c2_status`, `c3_status`, `execution_binding` | MANDATORY | Preserves `AVAILABLE`, `UNAVAILABLE`, `NOT_ASSESSED`; never translates to `CLEAN`. |
| Signature | `envelope.signature` | MANDATORY | Ed25519 over exact JCS payload bytes. Outer-envelope and encoding rules remain open. |
| Record storage | `logs/<stream_id>.jsonl` | MANDATORY OPERATION | Candidate append-only local storage for single-writer profile. Locking/append durability are not frozen. |
| Verifier state | `state/<stream_id>.state.json` | MANDATORY FOR FRESHNESS | Stores last accepted epoch, sequence, record hash, checkpoint version, and key reference. |
| Checkpoint | `checkpoints/<stream_id>.checkpoint.json` | MANDATORY FOR COMPLETENESS | Independently retained signed head commitment. Separate-key choice remains unresolved. |
| Verification result | Structured result object | MANDATORY | Reports component statuses and non-proven properties; no single `ATTACK_DETECTED` boolean. |

### 6.2 Binding reconstruction rule

```text
validate_schema(payload)

payload_bytes    = JCS_RFC8785_C4_PROFILE(payload)
signature        = Ed25519.Sign(record_private_key, payload_bytes)
record_hash      = SHA256(payload_bytes)

verify_signature = Ed25519.Verify(
                     accepted_public_key,
                     payload_bytes,
                     signature
                   )

verify_artifact  = SHA256(presented_exact_bytes) == signed_digest

verify_chain     = (
                     sequence_no == last_sequence + 1
                     and prev_record_hash == last_record_hash
                   )
```

This rule remains incomplete until at least the following are frozen: outer-envelope format, signature encoding, digest text encoding, parser behavior, canonicalization package/version, numeric bounds, record schema, key serialization, fingerprint derivation, and state-commit protocol.

---

## 7. Sequence, Replay and Freshness

### 7.1 Logical freshness versus wall-clock time

C4 distinguishes two different concepts:

**Wall-clock time** answers “what time did the host claim it was?”  
**Logical freshness** answers “is this record consistent with the last accepted stream/epoch/sequence state?”

The current design does not treat host time as a trust source. RFC 3161 is relevant because a proper time-stamping authority requires a trustworthy time source; an ordinary offline host clock does not gain that property simply because its value is signed.

C4 therefore uses:

- `stream_id`;
- `epoch_id`;
- strict sequence progression;
- previous-record linkage;
- persisted verifier state;
- optional signed checkpoints;

as logical consistency controls.

### 7.2 Replay handling

A valid signature does not make an old record “new.” Replay handling is conditional on intact local state.

For a single stream/epoch, the verifier is intended to reject:

- an already accepted sequence;
- an older sequence;
- a duplicate;
- a sequence gap;
- a predecessor mismatch;
- an unexpected stream/epoch transition.

However, restoring old verifier state can re-enable a previously accepted prefix. Therefore:

> Sequence/state can provide conditional rejection relative to the last accepted local state. It is not generic real-time freshness and it is not rollback-resistant by itself.

### 7.3 State-commit boundary

The target requires verifier state to be committed atomically before acceptance is acknowledged. If state cannot be loaded or committed safely, the verifier must fail closed as `STATE_UNAVAILABLE`.

The exact commit order is not yet specified. The audit requires a target-filesystem protocol covering temporary files, file `fsync`, rename or append semantics, directory `fsync`, record/state/checkpoint ordering, acknowledgement, and deterministic recovery.

---

## 8. Hash Chains and Completeness

### 8.1 Single-writer chain

The selected stateful target is:

```text
RECORD n-1
    ↓
SHA256(canonical payload n-1)
    ↓
prev_record_hash + sequence n
    ↓
RECORD n
```

Genesis uses:

```text
sequence_no      = 0
prev_record_hash = null
```

Each later record increments the sequence by one and carries the hash of the prior canonical payload bytes.

A hash chain can make certain changes **tamper-evident under the state model**, but it is not “tamper-proof.”

### 8.2 What the chain is intended to expose

Within one persisted single-writer stream/epoch, tests are expected to show that the verifier can detect or classify:

- adjacent predecessor mismatch;
- sequence gaps;
- duplicates;
- replay relative to intact state;
- reordering;
- interior deletion;
- some fork/continuation inconsistencies.

These are project targets, not executed project results.

### 8.3 What the chain does not provide automatically

A hash chain does not automatically provide:

- trusted real-time freshness;
- tail completeness;
- rollback resistance;
- multi-writer safety;
- cross-verifier anti-equivocation;
- trusted anchor provisioning;
- key-compromise recovery.

A valid shorter prefix can remain internally valid after suffix deletion. That is the central reason checkpoints are treated as a separate control.

---

## 9. Checkpoints and Trust Anchors

### 9.1 Checkpoint purpose

A valid prefix does not prove that later records have not been removed.

The current target therefore proposes a signed checkpoint containing:

- `stream_id`;
- `epoch_id`;
- `highest_sequence`;
- `head_hash`;
- `checkpoint_version`;
- `prior_checkpoint_hash`.

The checkpoint is intended to be retained separately from the main log. If a verifier later sees a shorter head than a trusted later checkpoint, it can return `CHECKPOINT_MISMATCH`.

Without a trusted checkpoint or witness:

> tail completeness is **UNAVAILABLE**, not verified.

### 9.2 Checkpoint-key decision

The source deliberately leaves the same-key versus separate-key decision open.

A separate checkpoint key can provide compromise separation only if:

- the checkpoint private key is independently protected;
- its trust anchor is provisioned independently or with equivalent assurance;
- checkpoint storage remains independently trusted;
- replacement and rollback of the checkpoint/anchor are controlled.

If the same record key signs both records and checkpoints, compromise of that key can permit forged records and forged checkpoints. If a separate checkpoint key is used, the project must accept the additional provisioning, rotation, storage, and recovery complexity.

Current status: **MISSING DECISION / UNVERIFIED**.

### 9.3 Trust-anchor replacement

A verifier cannot derive trust from the record itself. The accepted public key must already be authenticated.

The audit therefore requires:

- a defined offline provisioning medium;
- a key manifest;
- fingerprint derivation over exact public-key bytes;
- independent fingerprint comparison;
- installer authorization;
- protected store path and permissions;
- replacement policy;
- rotation/revocation policy;
- audit trail;
- rollback behavior.

No tested project mechanism currently exists for those requirements.

---

## 10. Safe Artifact-Binding Scope

### 10.1 Exact-byte rule

C4 binds **bytes**, not filenames or informal object names.

The recommended rule is:

> Hash exact immutable byte snapshots. Wherever possible, the signer and inference runner should consume the same opened descriptor or a verified immutable copy.

A path is only a locator. If the path can be changed between hashing and execution, it is not sufficient evidence of causal execution.

### 10.2 External sidecar target

The current V2 target prefers an external JSONL/audit sidecar rather than modifying ONNX, PyTorch, or TorchScript model containers.

Embedding provenance inside model formats remains conditional on C3-defined format semantics and explicit tests. This keeps C4 from claiming container semantics it does not own.

### 10.3 Target, tested, and project-verified coverage

The following distinction is mandatory:

```text
TARGET FORMAT
      ≠
TESTED FORMAT
      ≠
PROJECT-VERIFIED FORMAT
```

COCO, YOLO, ONNX, PyTorch, and TorchScript are named target representations. The inspected project evidence contains no completed binding fixture/results for any of them. They therefore remain **UNVERIFIED target formats**.

---

## 11. TOCTOU and Causal-Binding Limitations

Hashing a file at time `t1` and running inference later at time `t2` does not prove that the inference consumed the exact bytes hashed at `t1`.

This is a time-of-check/time-of-use problem.

C4 distinguishes:

### Snapshot-level binding

The verifier can show:

- the record was signed over a canonical payload;
- the payload committed to a digest;
- the bytes presented at verification match that digest.

This is valuable, but it does not establish what bytes the runtime actually executed.

### Execution-level / causal binding

Stronger causal binding requires the execution path to enforce or demonstrate that the inference runner consumes the exact immutable byte stream committed by the signed record.

Candidate controls include:

- same opened file descriptor for hashing and execution;
- verified immutable copy;
- immutable staging object whose digest is checked before execution;
- a controlled handoff where mutation/replacement tests fail as expected.

The source does not contain project evidence that this causal handoff has been implemented. Therefore the current claim remains:

> **SNAPSHOT_BINDING_ONLY** unless the exact-byte execution handoff is enforced and tested.

---

## 12. Candidate Methods

| Method | What it provides | Main limitation | Offline fit | Current C4 status |
|---|---|---|---|---|
| Hash only | Detects mismatch against an already authentic reference digest | No signer authentication; authentic-reference problem remains | High | **REJECT as sole control**; retain SHA-256 inside signed records |
| HMAC chain | Shared-secret authentication and possible chaining | Any verifier holding the secret can also generate valid tags | High | **DEFER** unless shared-key operations are explicitly required |
| JCS + Ed25519 | Deterministic JSON bytes plus public-key signature verification | Requires frozen canonicalization profile, trust anchors, key lifecycle, and executed tests | High | **SELECT — implementation target** |
| Hash chain + persisted state | Ordered linkage and conditional logical freshness within a stream | State rollback, completeness, forks, and multi-writer semantics remain unresolved | High | **SELECT CONDITIONALLY** |
| Signed checkpoint | Commits to an independently retained stream head | Key separation, storage independence, rollback, and checkpoint selection are unresolved | High | **SELECT CONDITIONALLY** |
| DSSE | Standard domain-separated envelope and pre-authentication encoding | Adds interoperability/profile choices not required for five-day core target | High | **DEFER** to post-MVP interoperability |
| COSE_Sign1 | Compact CBOR single-signer structure | Introduces a second serialization stack without a verified PS need | High | **DEFER** |
| Hardware monotonic state | Could reduce software rollback risk on compatible hardware | Target hardware/access profile is unknown | Potentially high | **DEFER** |
| Transparency / blockchain | Replication, consensus, and cross-observer properties when actually deployed | No verified requirement for mutually distrustful writers or distributed consensus; offline synchronization model absent | Conditional | **DEFER / REJECT FOR MVP** |
| Standard public keyless Sigstore workflow | OIDC-linked short-lived certs, Fulcio/Rekor transparency workflow | Standard public flow assumes online identity/transparency/root distribution behavior incompatible with a strict isolated runtime | Low for strict air gap | **DEFER**; a separately operated local profile would be a different design |
| SLSA build provenance | Build-output provenance through source/build process | Describes build provenance, not individual inference execution records | Can be packaged offline, but scope mismatch | **DEFER as runtime-record mechanism** |

### Blockchain research position

Blockchain was investigated as a candidate because it can provide distributed ledger and consensus properties in deployments designed around those requirements. The verified C4 problem inputs do not establish a need for distributed consensus, mutually distrustful writers, or cross-observer consistency for the five-day local verifier.

Therefore C4 does **not** select blockchain for the MVP.

This is not a universal statement that blockchain is useless or that a local signed log is equivalent to every blockchain deployment. If the system later requires independent observers, mutually distrustful writers, cross-site anti-equivocation, or a specified offline synchronization/consensus failure model, distributed-ledger candidates may need to be re-evaluated.

---

## 13. Current C4 Implementation Target

> **This is the current implementation target described by C4 V2, not a project-verified final deployment architecture.**

The target is:

```text
JCS-canonicalized payload
        +
SHA-256 artifact digests
        +
Ed25519 record signing
        +
single-writer sequence/hash chain
        +
persisted verifier state
        +
signed checkpoint retained separately
```

### 13.1 Record creation target

1. Obtain exact immutable input/output/config/model-reference bytes or authoritative dependency digests.
2. Preserve C2/C3 availability/status without reinterpretation.
3. Build a versioned payload containing all security-relevant fields.
4. Validate the payload against a frozen strict schema.
5. Canonicalize with the frozen RFC 8785/C4 profile.
6. Compute SHA-256 over canonical payload bytes for `record_hash`.
7. Sign the exact canonical payload bytes with Ed25519.
8. Append according to the crash-consistent single-writer protocol.
9. Update local state only at the frozen commit boundary.
10. Produce a checkpoint at the selected cadence if completeness evidence is required.

### 13.2 Verification outcomes

| Outcome | Meaning |
|---|---|
| `VERIFIED_BINDING` | Signature, canonical payload, presented artifact digests, chain, sequence, state, and applicable checkpoint checks passed. **This is not `CLEAN`.** |
| `SIGNATURE_INVALID` | Signature or accepted-key verification failed; cause and attacker identity are not established. |
| `ARTIFACT_MISMATCH` | Presented bytes do not match a signed digest; this does not prove attack. |
| `CHAIN_BROKEN` | `prev_record_hash` does not match the verified predecessor. |
| `SEQUENCE_REPLAY_OR_GAP` | Sequence violates persisted stream rules; replay, deletion, loss, corruption, or state error remain alternatives. |
| `CHECKPOINT_MISMATCH` | Observed stream head or version conflicts with the accepted checkpoint. |
| `TRUST_UNAVAILABLE` | No authenticated current trust anchor is available. |
| `STATE_UNAVAILABLE` | Verifier state cannot be safely loaded or committed. |
| `COMPLETENESS_UNAVAILABLE` | No trusted checkpoint or witness supports a tail-completeness claim. |
| `NOT_ASSESSED` | Required evidence or adapter output is unavailable. It must never be mapped to `CLEAN`. |

### 13.3 Design readiness categories

| Category | Current content |
|---|---|
| **BUILD READY** | Single-file SHA-256 hashing; Ed25519 primitive; mandatory claim-boundary text; component failure taxonomy; RFC 8032/RFC 8785 vector-harness skeleton |
| **PROTOTYPE** | Strict JSON/JCS wrapper; minimal signed envelope; JSONL single-writer chain; local sequence state; session-end checkpoint; structured C2/C3 placeholder adapters; crash-injection harness |
| **DEFERRED** | Key rotation/revocation; rollback-resistant state; hardware monotonic counters; trusted time; multi-writer coordination; directory/multi-file hashing; embedded model metadata; DSSE/COSE interoperability; transparency log; local Sigstore infrastructure; contributor-identity authority |
| **REJECTED FOR MVP** | Blockchain; hash-only protection; HMAC as a drop-in replacement for asymmetric signing; public online keyless services; semantic correctness claims; attack attribution; clean-from-unavailable; baseline retraining |

“BUILD READY” means the behavior is sufficiently bounded to begin coding after Day 0 prerequisites are available. It does **not** mean implemented, tested, or production-ready.

---

## 14. Project Implementation Evidence

### 14.1 Evidence hierarchy

C4 distinguishes evidence types that must not be collapsed:

1. **External normative/mechanism evidence** — standards/specifications explaining cryptographic properties.
2. **Project control/request evidence** — problem requirements and project status.
3. **Curated research packets** — prior research and red-team/reverification material.
4. **Secondary synthesis** — consolidation material that cannot independently promote a claim.
5. **Project implementation/execution evidence** — code, target runs, fixtures, logs, package hashes, tests.
6. **Negative evidence** — an expected artifact was not found in the enumerated inspected inputs.

Standards can support statements about how a mechanism is specified. They do not become proof that this project implemented that mechanism correctly.

### 14.2 Inspected project evidence

| Evidence item | Finding |
|---|---|
| Team-owned reference implementation | **NEGATIVE EVIDENCE:** no signer/verifier source bundle was supplied in the inspected inputs |
| E01–E24 execution logs | **NEGATIVE EVIDENCE:** no target-machine experiment results, command logs, or failure artifacts were supplied |
| Offline dependency bundle | **NEGATIVE EVIDENCE:** no lockfile, hashed wheelhouse, package hashes, or successful no-index installation log was supplied |
| Format fixtures | **NEGATIVE EVIDENCE:** no COCO, YOLO, ONNX, PyTorch, or TorchScript binding fixtures/results were supplied |
| Key/state operations | **NEGATIVE EVIDENCE:** no provisioning, rotation, checkpoint-key, atomic-state, crash, or rollback test evidence was supplied |
| Standards evidence | **AVAILABLE:** supports mechanism-level statements only |
| Red-team / reverification packet review | **AVAILABLE:** retains implementation promotion as conditional/unverified |

“Negative evidence” means the artifact was not found in the enumerated source set. It does not prove the artifact does not exist elsewhere.

### 14.3 Candidate dependency details are not project evidence

The audit packet contains candidate implementation choices including:

- `cryptography==50.0.1` with Ed25519 APIs;
- `rfc8785==0.1.4` with `rfc8785.dumps(payload)`.

These are **candidate-only** details in the source packet. The project has not supplied target wheels, hashes, ABI compatibility evidence, no-index install logs, frozen parser behavior, or conformance results. They must not be presented as selected/verified dependencies until Day 0 evidence exists.

### 14.4 Current public status snapshot

```text
checkpoint_2:
  CONDITIONAL_GO_TO_IMPLEMENTATION_TARGET_NO_PROJECT_VERIFIED_PROMOTION

claim_status:
  PARTIALLY_SUPPORTED

project_status:
  IMPLEMENTATION_TARGET_CONDITIONAL

project_verified:
  false

final_architecture_claimed:
  false

offline_install:
  UNVERIFIED

trusted_time:
  UNSUPPORTED

rollback_resistance:
  UNSUPPORTED

multi_writer:
  UNSUPPORTED

implementation_evidence:
  NONE_SUPPLIED
```

---

## 15. Evaluation and Experiment Plan

The evaluation plan is a design artifact. Its acceptance targets are **evaluation criteria**, not achieved results.

### 15.1 Ground truth

- **Cryptographic ground truth:** RFC 8032 §7 Ed25519 vectors plus independently generated invalid-signature mutations.
- **Canonicalization ground truth:** RFC 8785 examples/Appendix B, strict rejection fixtures, and verified Erratum 7920 for negative zero.
- **Artifact ground truth:** immutable fixture bytes with independently recorded SHA-256 values plus controlled one-bit/truncation mutations.
- **Sequence ground truth:** generated streams with declared duplicate, old-sequence, gap, deletion, reorder, suffix-deletion, fork, state-rollback, and checkpoint-rollback operations.

### 15.2 E01–E24 experiment tracks

The source defines E01–E24 as grouped experiment ranges rather than an individual per-number specification. This public edition preserves those grouped IDs rather than inventing a finer mapping.

| Experiment range | Property tested | Ground truth | Expected observation / target | Current project status |
|---|---|---|---|---|
| `E01–E04` / `TRK-CANON` | Canonical valid/invalid cases, Unicode, numeric edge cases | RFC 8785 examples + C4 rejection fixtures + Erratum 7920 | 100% vector conformance; same canonical bytes across two clean runs; 0 invalid-profile acceptance | **PLANNED / UNEXECUTED** |
| `E05–E09` / `TRK-BINDING` | Sign/verify, payload mutation, artifact mutation, key mutation, causal-binding handoff | RFC 8032 vectors + immutable fixture digests | 100% unmodified acceptance and enumerated mutation rejection; correct outcome class | **PLANNED / UNEXECUTED** |
| `E10–E15` / `TRK-FRESHNESS` | Duplicate, replay, gap, deletion, reorder, suffix deletion | Generated declared stream mutations | Expected logical violations detected when state/checkpoint preconditions hold; tail deletion without checkpoint returns unavailable completeness | **PLANNED / UNEXECUTED** |
| `E16–E18` / `TRK-TRUST` | Key rotation, anchor replacement, checkpoint-key compromise | Frozen trust/epoch transition fixtures | Expected transitions pass; substituted anchors fail only when anchor protection exists | **PLANNED / UNEXECUTED** |
| `E19–E22` / `TRK-OPS` | Crash points, state loss/rollback, disk full, corrupt record | Deterministic failure injection | No false `VERIFIED_BINDING`; recovery matches the frozen state machine | **PLANNED / UNEXECUTED** |
| `E23` / `TRK-FORMAT` | Exact-byte fixture coverage for each available target format | Clean + controlled mutated fixtures | At least one reproducible clean and mutated fixture per claimed format; otherwise format remains `UNVERIFIED` | **PLANNED / UNEXECUTED** |
| `E24` / `TRK-PERF` | Offline performance/storage benchmark | Fixed target machine + fixtures | Report p50/p95 creation/verification latency, throughput, record size, artifact hashing time; no threshold before measurement | **PLANNED / UNEXECUTED** |

Every run should capture:

- random seeds where applicable;
- fixture hashes;
- tool versions;
- dependency hashes;
- exact commands;
- stdout/stderr;
- exit codes;
- target OS/runtime/ABI;
- filesystem;
- failure artifacts;
- schema/profile version;
- key/trust-store fixture identifiers without private material.

### 15.3 Minimum concrete test catalog

| Test ID | Case | Required oracle |
|---|---|---|
| `Q5-T01` | Offline clean install | Disconnected target installs only from the hashed local dependency set and imports all selected packages |
| `Q5-T02` | Ed25519 vectors | RFC 8032 §7 vectors and local positive sign/verify pass |
| `Q5-T03` | Signature mutations | One-bit payload/signature changes, wrong key, truncated and noncanonical signature encodings fail |
| `Q5-T04` | Key round trip | Chosen private/public serialization reloads and verifies; malformed lengths/files fail closed |
| `Q5-T05` | JCS positive vectors | RFC 8785 examples, property order, arrays, escapes, Unicode keys, supported numbers produce fixed bytes |
| `Q5-T06` | JCS rejection | Duplicate keys, invalid UTF-8, lone surrogates, non-finite values, negative zero, excessive precision, unknown critical fields reject |
| `Q5-T07` | Artifact mutations | Input, output, config, model identity, and conditional weight changes produce the correct component mismatch |
| `Q5-T08` | Availability composition | `UNAVAILABLE` and `NOT_ASSESSED` remain distinct and never yield `CLEAN` |
| `Q5-T09` | TOCTOU | Mutation/replacement between hash and inference handoff reveals only the property actually enforced |
| `Q5-T10` | Genesis | Only sequence 0 with null predecessor starts an empty stream; forged continuation fails |
| `Q5-T11` | Replay / duplicate | Previously accepted and duplicate records reject against intact state |
| `Q5-T12` | Gap / reorder | Sequence gap and swapped records return the specified sequence/chain status |
| `Q5-T13` | Interior deletion | Removing a middle record produces the specified gap or predecessor mismatch |
| `Q5-T14` | Tail deletion without checkpoint | Valid shorter prefix returns `COMPLETENESS_UNAVAILABLE`, not verified completeness |
| `Q5-T15` | Tail deletion with checkpoint | Trusted later checkpoint conflicts with shorter head and returns `CHECKPOINT_MISMATCH` |
| `Q5-T16` | State rollback | Restoring old state demonstrates replay acceptance or a detectable mismatch and records the unsupported condition |
| `Q5-T17` | Trust-anchor replacement | Replacement demonstrates why signatures under the substituted key may verify; no false protection claim is emitted |
| `Q5-T18` | Record-key compromise | Forged records can verify under the compromised key; separate trusted checkpoint only limits checkpoint-inconsistent history if independently protected |
| `Q5-T19` | Checkpoint-key compromise | Forged checkpoint demonstrates loss of independent-head assurance |
| `Q5-T20` | Concurrency | Two writers cannot both commit a successor, or the profile deterministically reports unsupported conflict |
| `Q5-T21` | Crash injection | Crashes around record/state/rename/directory-fsync/checkpoint steps never yield silently accepted inconsistent state |
| `Q5-T22` | Format fixtures | Every claimed COCO/YOLO/ONNX/PyTorch/TorchScript representation has clean and mutated reproducible fixtures or remains `UNVERIFIED` |
| `Q5-T23` | Performance | Report p50/p95 create/verify latency, throughput, record size, hashing time; do not invent a threshold before measurement |

---

## 16. Five-Day Feasibility

> **Status: PLANNING HYPOTHESIS, NOT MEASURED PROJECT EVIDENCE**

A five-day prototype may be feasible only if the project adopts a narrow single-writer, single-file profile and already has the required target runtime access.

| Day | Objective | Exit condition / cut line |
|---|---|---|
| **Day 0** | Freeze schema, RFC 8785 profile, encodings, key roles, state/checkpoint semantics, C2/C3 adapters, target runtime/filesystem, package set | Clean offline/no-index dependency install and smoke test pass. **If this fails, stop.** |
| **Day 1** | Strict parser/JCS wrapper, SHA-256 artifact hashing, Ed25519 sign/verify, encoding rules | RFC 8785 and RFC 8032 vectors pass |
| **Day 2** | Record creation/verification, artifact comparison, structured outcomes, mutation tests | Signed-record path and mutation outcomes behave per frozen profile |
| **Day 3** | Single-writer chain and persisted state; replay/gap/deletion/reorder tests | State transition tests pass or unsupported behaviors are explicitly removed from claims |
| **Day 4** | Session-end checkpoint and crash/recovery protocol on target filesystem; C2/C3 integration and available format fixtures | Drop completeness claims if checkpoint/crash tests fail |
| **Day 5** | Clean-room offline rerun, available format fixtures, evidence packaging, performance measurement, claim matrix | Only passing rows may be promoted toward project verification; separate final audit still required |

If schedule pressure occurs, the source recommends retaining the **stateless signed-record binding and claim boundaries** rather than claiming untested stateful properties. Checkpoint completeness, rollback resistance, rotation, and multi-format coverage should be dropped from claims before tests are dropped.

---

## 17. Limitations and Security Boundaries

| Limitation | Current boundary |
|---|---|
| Signing-key compromise | A compromised record key can produce records that verify. Signature validity cannot distinguish legitimate use from attacker use of the same key. |
| Signer compromise | A compromised signer can sign false or malicious content. Cryptography cannot make false input true. |
| Trust-anchor replacement | A substituted accepted public key can cause attacker signatures to verify. No tested replacement/rollback protection is supplied. |
| Verifier-state rollback | Can defeat local replay checks by restoring old last-seen state. |
| Checkpoint rollback | A stale or substituted checkpoint can defeat tail-completeness comparison. No rollback-resistant checkpoint store is selected. |
| No trusted time | Host timestamps are descriptive only. They are not independently verified time. |
| Revocation | No offline revocation distribution, compromise recovery, or historical-verification policy is frozen. |
| Key rotation | No signed rotation manifest or authoritative epoch-transition procedure is frozen. |
| Multi-writer | Unsupported. No coordination, lock, conflict-resolution, or race-tested ordering rule exists. |
| Tail completeness | Unavailable without a later independently trusted checkpoint/witness. |
| Cross-verifier equivocation | Undetectable without an external witness or reconciliation design. |
| TOCTOU / causal execution | Snapshot-level only unless execution consumes the exact immutable bytes committed by the record. |
| Semantic correctness | Out of scope. Correctly signed content can still be incorrect. |
| Model cleanliness | Out of scope for C4. A backdoored model can be faithfully hashed and signed. |
| Input authenticity before hashing | Not established by C4. |
| Model identity semantics | Owned by C3; C4 binds the statement it receives. |
| External-data scope | Unresolved unless exact external bytes/manifests are explicitly committed. |
| Complex artifact types | Directories, symlinks, sparse files, archives as semantic packages, remote objects, and mutable memory are unsupported. |
| Format/version coverage | COCO/YOLO/ONNX/PyTorch/TorchScript remain target-only until reproducible fixtures pass. |
| Offline deployment | Designed for offline verification, but clean offline installation/runtime have not been demonstrated. |
| Crash consistency | Required but exact commit/recovery protocol is not yet frozen or executed. |
| Resource exhaustion | Maximum record/JSON/field/artifact sizes, timeouts, streaming limits, and memory bounds remain to be specified. |
| Contributor identity | A signed contributor string is not authenticated human/organizational identity without an external authority. |
| Performance/storage | No p50/p95 or bytes-per-record project measurements have been produced. |

### Offline status language

The following statements are not interchangeable:

```text
DESIGNED FOR OFFLINE OPERATION
        ≠
OFFLINE INSTALLATION VERIFIED
        ≠
OFFLINE RUNTIME VALIDATED
```

Current C4 status is **designed for offline verification**, with installation and runtime validation still **UNVERIFIED**.

---

## 18. Cryptographic Non-Claims

## What Cryptographic Binding Does NOT Prove

- A valid signature does not prove semantic correctness.
- A valid signature does not prove model cleanliness.
- A valid signature does not prove the private key was uncompromised.
- A valid signature does not prove who physically controlled the signer.
- A valid signature does not prove the signer was authorized.
- A hash match does not prove safety.
- A hash mismatch does not prove malicious intent.
- A valid prefix does not prove log completeness without a trusted later checkpoint or witness.
- A host timestamp does not prove trusted time.
- A signed record does not prove the inference used the exact hashed bytes unless causal handoff is enforced and tested.
- A signed model digest does not prove the model is not backdoored.
- A cryptographic record does not prove the underlying inference is correct.
- A cryptographic mismatch does not identify an attacker.
- `VERIFIED_BINDING` does not mean `CLEAN`.
- `UNAVAILABLE` does not mean `CLEAN`.
- `NOT_ASSESSED` does not mean `CLEAN`.

---

## 19. Contradictions, Corrections and Research Evolution

### 19.1 Research lineage

```text
V1
 ↓
Red-Team Review
 ↓
Reverification
 ↓
V2
```

Later stages were used to challenge earlier assumptions, narrow claims, and preserve unresolved questions rather than presenting research evolution as a linear increase in confidence.

### 19.2 Major corrections and unresolved alternatives

| Topic | Earlier position / risk | Later finding | Current C4 treatment |
|---|---|---|---|
| HMAC vs asymmetric signing | HMAC could appear to satisfy “authentication” generically | Every verifier holding a shared HMAC secret can also create valid tags | HMAC remains a valid shared-secret model but is **DEFERRED** for the public-verifier profile |
| Blockchain vs local signed ledger | Distributed ledger was considered as a provenance option | No verified PS requirement establishes distributed consensus or mutually distrustful writers | **DEFER/REJECT FOR MVP**; re-open only if cross-observer/consensus requirements emerge |
| Host timestamps vs trusted time | A signed timestamp might be mistaken for trusted time | RFC 3161 requires trustworthy time at the TSA; offline host clock is only host-supplied data | Timestamp is optional/descriptive and must not drive acceptance |
| Signature vs freshness | Valid signature could be conflated with recency | Previously valid signed data remains valid | Sequence/state/checkpoint are separate controls |
| Hash chain vs completeness | Linked history may look “complete” | Suffix deletion can leave a valid prefix | Completeness requires a later trusted checkpoint/witness |
| Same vs separate checkpoint key | Separate key suggested for compromise isolation | Separation only helps if second key/anchor/storage remain independently trusted | **UNRESOLVED**; freeze at Day 0 |
| JCS naming/profile | Packet wording alternated between “JCS 1.0” and RFC 8785/JCS | Canonical reference is RFC 8785 plus verified errata and a local accepted profile | Freeze RFC 8785/C4 profile; no generic library-conformance claim |
| BUILD vs project-verified | Earlier packet used BUILD language without execution evidence | Red-team/reverification found no project execution evidence | Use **IMPLEMENTATION TARGET**, **PROTOTYPE**, **UNVERIFIED**; no promotion |
| Control state | Current research task is V2 while project workbook recorded discovery/not-started | Source inspection confirms inconsistency | Retain as a reconciliation issue; do not silently normalize |
| C3 model hash | C4 could appear to treat “model digest” as complete weight identity | C3 scope semantics are unresolved | C4 binds C3 `identity_digest/scope_id`; separate weight digest becomes mandatory if C3 does not cover exact weights |

### 19.3 Claims requiring explicit narrowing

The V2 audit identified the following claims as requiring narrow wording or adjacent qualification:

- `C4-V2-004` — state-based “freshness” must mean rejection relative to last accepted local state, not generic freshness.
- `C4-V2-005` — chain deletion/reorder detection is intended/unverified until project tests run.
- `C4-V2-013` — signature integrity statement requires accepted-key and exact-byte qualifications.
- `C4-V2-015` — five-day feasibility is a planning hypothesis, not measured evidence.
- `C4-V2-016` — checkpoint-key separation helps only if the second trust domain remains independently protected.

---

## 20. Open Questions

| ID | Question | Dependency | Current status |
|---|---|---|---|
| `C4-OQ-001` | Who provisions, authenticates, rotates, revokes, and restores record/checkpoint trust anchors in the air-gapped deployment? | C1/C6/operations | **OPEN** |
| `C4-OQ-002` | Must record and checkpoint keys be separate, and what compromise domain is each meant to isolate? | Trust model | **OPEN** |
| `C4-OQ-003` | What prevents or detects verifier-state and trust-anchor rollback on the target? | C6/platform | **OPEN** |
| `C4-OQ-004` | What exact bytes and `scope_id` does C3 define for ONNX, PyTorch, and TorchScript model identity? | C3 | **OPEN** |
| `C4-OQ-005` | What exact digest/status contract does C2 expose for COCO/YOLO inputs and annotations? | C2 | **OPEN** |
| `C4-OQ-006` | Is tail completeness required between checkpoints, and where is the independently trusted checkpoint stored? | C1/C6/operations | **OPEN** |
| `C4-OQ-007` | Is there ever more than one writer per stream or more than one verifier whose views must be reconciled? | C1/deployment topology | **OPEN** |
| `C4-OQ-008` | What target OS, filesystem, runtime, key store, and offline package process are available? | C6 | **OPEN** |
| `C4-OQ-009` | Which target formats have redistributable public/team fixtures for the evidence bundle? | C2/C3/C6 | **OPEN** |
| `C4-OQ-010` | Who owns the canonical evidence-class registry and the missing input-packet schema? | Project governance / audit | **OPEN** |

Additional audit-level open decisions include outer-envelope format, signature encoding, digest encoding, key serialization, key fingerprint algorithm, storage layout, locking, exact atomic commit order, checkpoint cadence, stale/missing checkpoint behavior, contributor identity authority, resource bounds, and overall result composition.

---

## 21. Cross-Cell Dependencies

C4 depends on other cells through explicit contracts. “Dependency” and “handoff” do not imply that integration has already been demonstrated.

| Dependency ID | Provider | Required handoff / contract | Failure handling |
|---|---|---|---|
| `C4-DEP-C1-001` | C1 — mission/threat context | Actor model, storage threat, freshness/completeness expectations, deployment topology | Keep disputed controls conditional |
| `C4-DEP-C2-001` | C2 — data integrity | Authoritative input/data digest, digest scope, representation, `AVAILABLE/UNAVAILABLE/NOT_ASSESSED` | Bind status; never reinterpret as `CLEAN` |
| `C4-DEP-C3-001` | C3 — model identity | Model identity digest, scope ID, format/version, identity status, adapter contract, exact-weight coverage | Bind C3 output; if exact weights are not covered, require a separate weight digest |
| `C4-DEP-C5-001` | C5 — assurance | Consume C4 verification outcomes and limitations separately from anomaly/model findings | Never map mismatch/unavailability to attack or clean |
| `C4-DEP-C6-001` | C6 — engineering | Target OS/runtime/ABI, offline dependency bundle, fixture inventory, filesystem semantics, key/storage access, crash/state tests | Fail closed where required access/evidence is unavailable |

### C4 → C5 handoff

C4 should provide structured results such as `VERIFIED_BINDING`, `ARTIFACT_MISMATCH`, `TRUST_UNAVAILABLE`, and explicit non-proven properties. C5 must interpret those as evidence states, not semantic verdicts.

### C4 → C6 handoff

C4 supplies the security-sensitive implementation profile and test obligations. C6 must turn those into target-host packaging, dependency, storage, crash/recovery, and format-fixture evidence before any project-verification promotion.

---

## 22. Reproducibility and Evidence Requirements

### 22.1 Evidence classes

The source dossier uses the following classes:

| Class | Meaning |
|---|---|
| `EC1` | PRIMARY_NORMATIVE / external technical specification |
| `EC2` | PROJECT_CONTROL / user or project-control source |
| `EC3` | CURATED_PACKET / prior research packet |
| `EC4` | SYNTHESIS_SECONDARY |
| `EC5` | EXECUTION_ARTIFACT |
| `EC6` | NEGATIVE_EVIDENCE |

`EC5` is empty in the inspected V2 evidence set.

### 22.2 Project packet provenance recorded by the source audit

| Input | Class | SHA-256 recorded in C4 V2 |
|---|---|---|
| `S7OC4 V1.docx` (`PKT-01`) | EC3 | `A0ED7C516185705A684F937FC13C23B36C4862A86F3D8D1D76D835F678EDF544` |
| `S8OC4.docx` (`PKT-02`) | EC3 | `FBC8C492C0733A8D0D328D759CD4AF2336EFEEBE6332C7F06FE28C7D6AF1E997` |
| `S9OC4.docx` (`PKT-03`) | EC3 | `97F73DCDE9767A9DBFD9866FFEA78523588FB8C1575F8410063AD005076DDC28` |
| `Pasted text.txt` (`SYN-01`) | EC4 | `7BEF8A3C83D7A3F7F448BB508C73AD4F04A31B0107143E7DD33251DC8931952C` |
| `RESEARCH_STATUS.xlsx` (`CTL-01`) | EC2 | `4C3D4CC0E24DE1337E33FB28C31A9190DB22EF62EE997AFFE77208A0BD1514EA` |

The public edition does not reproduce the credential-bearing presigned metadata identified inside `PKT-03`.

### 22.3 Required verification flow

The audit requires the final implementation profile to freeze a verification order at least as strict as:

1. Read bounded record bytes without mutating trusted state.
2. Parse strict UTF-8 JSON; reject duplicate keys, invalid syntax, unknown critical fields, and resource-limit violations.
3. Validate the versioned envelope and payload schema.
4. Resolve `signer_key_id` only in the installed trust store and compare the configured public-key fingerprint.
5. Reconstruct exact RFC 8785 canonical payload bytes with the frozen C4 profile.
6. Decode the signature canonically and verify Ed25519 **before** using untrusted payload fields to mutate state.
7. Recompute every `AVAILABLE` artifact digest from exact presented bytes and compare against signed commitments.
8. Check stream, epoch, genesis, sequence, predecessor hash, and current persisted state.
9. If completeness is requested, select and verify the expected checkpoint, key, version, sequence, and head hash.
10. Compose component outcomes and explicit non-proven properties. Never emit `CLEAN` or `ATTACK_DETECTED` from C4 alone.
11. Commit record/state using the frozen crash-consistent protocol only after all required checks pass.
12. Emit structured result, tool versions, schema/profile versions, and evidence identifiers without secrets.

### 22.4 Implementation gaps that must be frozen before independent MVP implementation

| Gap | Status | Required decision/evidence |
|---|---|---|
| Runtime target | MISSING | OS, CPU, Python/runtime ABI, filesystem, `fsync`/rename semantics |
| Cryptographic library | CANDIDATE ONLY | Pin selected version + offline wheel/hash + target compatibility |
| JCS library | CANDIDATE ONLY | Pin selected version, parser behavior, negative-zero handling, conformance results |
| JSON parser | PARTIAL | Exact decoder flags, duplicate-key behavior, non-finite handling, size bounds, errors |
| Record schema | MISSING | Versioned JSON Schema, required fields, types, enums, ranges, nullability, unknown-field policy |
| Outer envelope | MISSING | Embedded/detached payload representation, signature field, exact signed-byte reconstruction |
| Signature encoding | MISSING | Base64url padding rule, canonical decoding, raw Ed25519 signature length |
| Digest encoding | MISSING | Lowercase hex or other frozen representation; signed algorithm field |
| Key serialization | MISSING | Raw vs PKCS8/PEM, encoding, permissions, backup/zeroization expectations |
| Key identifier | MISSING | Exact fingerprint algorithm and uniqueness rules |
| Trust-anchor setup | MISSING | Provisioning medium, fingerprint ceremony, manifest, authorization, storage, replacement audit |
| Checkpoint key | MISSING DECISION | Same vs separate key and complete second-key trust ceremony if separate |
| Genesis/record hash | PARTIAL | Integer bounds, empty-stream state, epoch resets, forks, textual encoding |
| Sequence-state policy | PARTIAL | Gap/duplicate/wrong-stream behavior and state-advance boundary |
| Concurrency | MISSING | Process ownership, lock mechanism, timeout/stale lock behavior |
| Storage layout | CANDIDATE ONLY | Permissions, durability, record-size limit, rotation, archive, disk-full behavior |
| Atomic commit | MISSING | Temp/write/fsync/rename/dir-fsync/state/checkpoint/ack/recovery order |
| Checkpoint protocol | MISSING | Cadence, versioning, selection, independence, replacement, stale/missing behavior |
| Key rotation/revocation | MISSING | Rotation manifest, epoch transition, revocation distribution, compromise recovery |
| C2 adapter | MISSING | Digest/status schema, errors, version compatibility |
| C3 adapter | MISSING | Identity/weight scope, status, exact bytes/manifest contract |
| Verification flow | PARTIAL | Failure precedence, fail-closed points, state mutation boundary, result schema |
| Timestamp profile | MISSING | RFC 3339 UTC form, precision, absence, rollback reporting; must not drive acceptance |
| Contributor identity | OPTIONAL / UNDEFINED | External identity authority or omit field |
| Resource bounds | MISSING | Max JSON/record/field/artifact sizes, streaming, timeouts, memory |
| Offline packaging | MISSING EVIDENCE | Hashed dependency set, no-index install, disconnected smoke tests |

### 22.5 Quality gates

| Gate | V2 status | Basis |
|---|---|---|
| Scope | **PASS** | Binding-versus-assessment boundary is explicit |
| Evidence | **CONDITIONAL** | Normative/packet sources are traceable; EC5 execution evidence is empty |
| Verification | **CONDITIONAL** | Normative claims checked; project behavior not executed |
| Implementation | **FAIL — NOT READY** | No independent signer/verifier bundle, clean offline install log, or executed suite |
| Limitations | **PASS** | Key, time, rollback, completeness, TOCTOU, format, semantic and availability boundaries explicit |
| Red-team handling | **PASS** | Key/checkpoint, rollback, canonicalization, and claim corrections retained |
| Feasibility | **CONDITIONAL** | Five-day plan depends on Day 0 |
| Evaluation | **PASS — DESIGN ONLY** | Ground truth, tests, metrics and targets specified; no results claimed |
| Uncertainty | **PASS** | Control conflict and unresolved decisions are preserved |
| Cross-domain dependencies | **CONDITIONAL** | Interfaces named but not frozen/demonstrated |

**Overall V2 quality-gate disposition: CONDITIONAL / NO PROMOTION.**

### 22.6 Audit supplement disposition

| Audit question | Disposition |
|---|---|
| Q1 — V2 completeness | **CONDITIONAL:** boundary coverage is strong; protocol and operations remain incomplete |
| Q2 — claim audit | **FIVE CLAIMS REQUIRE NARROWING:** qualifications are retained in this public edition |
| Q3 — binding matrix | **DEFINED AS V2 RECOMMENDATION:** fields remain conditional on C2/C3 and profile freeze |
| Q4 — attack coverage | **PARTIAL:** tampering/local consistency conditional; key/trust-anchor compromise and robust rollback uncovered |
| Q5 — implementation readiness | **NOT READY FOR INDEPENDENT MVP IMPLEMENTATION:** core prototype only |
| Q6 — five-day reality | **CORE BUILD + STATEFUL PROTOTYPE:** drop unsupported claims before dropping tests |
| Q7 — evaluator readiness | **BOUNDARIES ANSWERABLE:** several operational questions correctly remain unanswered |

### 22.7 Evaluator challenge ledger

| Evaluator question | Evidence-backed C4 answer | Status |
|---|---|---|
| What exactly does a valid record prove? | Accepted-key signature verification of canonical bytes plus digest agreement for presented bytes, with conditional state/checkpoint rules. It does not prove semantic correctness, clean inputs/model, causal execution, uncompromised keys, or attack. | ANSWERED |
| How is the public key trusted? | Only through out-of-band provisioning and fingerprint verification. The project ceremony/store protection are not defined or tested. | PARTIAL |
| What if the signing key is compromised? | Forged records can verify. A separately protected checkpoint key can limit only some record-key-only head forgery if independently trusted. | ANSWERED LIMIT |
| Can replay succeed after state rollback? | Yes. Local replay rejection depends on intact state. | ANSWERED LIMIT |
| How is tail deletion detected? | Only against a later independently trusted checkpoint/witness. | ANSWERED |
| Why not blockchain? | No verified requirement establishes distributed consensus or mutually distrustful writers for the MVP. | SCOPED RECOMMENDATION |
| What exact bytes are signed? | Intended bytes are RFC 8785 canonical payload bytes; outer envelope/encoding are not yet frozen. | INCOMPLETE |
| What does `prev_record_hash` cover? | V2 selects SHA-256 of prior canonical payload bytes; text encoding/context/interoperability remain to be frozen. | PARTIAL |
| How are difficult JSON values handled? | Intended profile rejects duplicates, invalid UTF-8/lone surrogates, non-finite values, negative zero, and out-of-profile precision; implementation tests absent. | PARTIAL |
| Does the model digest cover executed weights? | C4 cannot answer until C3 defines `scope_id` and exact-weight coverage. | OPEN DEPENDENCY |
| How do you prove inference used the hashed model/input? | V2 does not yet. Current claim is snapshot-level unless exact-byte handoff is enforced and tested. | ANSWERED LIMIT |
| Who is the contributor named in a record? | No authenticated contributor-identity profile exists. A signer key ID is not necessarily a person. | OPEN |
| How is checkpoint storage independent? | V2 says separate storage, but no independent device/admin/replacement/rollback model is frozen. | OPEN |
| Same record/checkpoint key or separate? | Unresolved. Both choices carry different compromise and provisioning consequences. | OPEN |
| What happens on crash between log and state writes? | Fail-closed crash consistency is required, but commit/recovery ordering is not frozen. | OPEN |
| Can two processes write the same successor? | Single-writer profile is declared; no lock protocol exists. Multi-process safety is unverified. | INCOMPLETE |
| How are keys rotated/revoked offline? | No complete procedure exists. | OPEN |
| Why believe offline operation works? | It is not yet demonstrated: no hashed wheelhouse/no-index target install/disconnected run was supplied. | UNVERIFIED |
| Which target formats are demonstrated? | None in the supplied project evidence. | UNVERIFIED |
| What does the timestamp prove? | Only that the signer included a host-supplied value. | ANSWERED |
| Does HMAC provide the same trust property? | No. Shared-secret verifiers can also generate tags; it is a different trust profile. | ANSWERED |
| What if C2/C3 evidence is unavailable? | Preserve `UNAVAILABLE`/`NOT_ASSESSED`; never emit `CLEAN` from absence. | ANSWERED CONCEPTUALLY |
| Performance/storage cost? | No measured project result yet; E24/Q5-T23 must report it. | NO RESULT |
| Is this final-architecture ready? | No. It is a conditional implementation target requiring project evidence and final audit. | ANSWERED |

---

## 23. Claim / Source Index

The claim index preserves separate **claim status** and **project status**. Mechanism support does not imply project validation.

| Claim ID | Claim | Claim status | Project status | Primary source(s) | Exact location / boundary |
|---|---|---|---|---|---|
| `C4-V2-001` | A valid signature binds canonical record bytes under an accepted key; it does not establish semantic correctness. | SUPPORTED | UNVERIFIED | R02, R03, R05 | RFC 8032 §5.1.7; FIPS 186-5 scope; SP 800-57 key-compromise context |
| `C4-V2-002` | Exact presented bytes can be compared with a signed SHA-256 digest commitment. | SUPPORTED | UNVERIFIED | R04 | FIPS 180-4 / SHA-256 |
| `C4-V2-003` | RFC 8785 provides deterministic JSON serialization only inside the frozen accepted profile. | SUPPORTED | UNVERIFIED | R01, R01E | RFC 8785 §§3.1–3.2.3; Erratum 7920 |
| `C4-V2-004` | Strict sequence checks against intact local state can reject records inconsistent with the last accepted local state; state rollback defeats that property. | PARTIALLY_SUPPORTED | CONDITIONAL | R06, R09, PKT-02 | RFC 5848 §8.4; TUF state analogy; not generic freshness |
| `C4-V2-005` | The proposed single-writer chain is intended to expose tested interior deletion/reorder operations when adjacent evidence/state are available. | PARTIALLY_SUPPORTED | UNVERIFIED | R06, PKT-02 | Project behavior unexecuted |
| `C4-V2-006` | Tail deletion is detectable only against a trusted external checkpoint or witness. | PARTIALLY_SUPPORTED | CONDITIONAL | PKT-01, PKT-02 | Requires checkpoint key/storage trust |
| `C4-V2-007` | Host timestamps without a trusted time source are not independently verifiable. | SUPPORTED | UNSUPPORTED | R07, R14 | RFC 3161 §2.1; RFC 3339 format does not create trust |
| `C4-V2-008` | Signature validity does not establish that the private key was uncompromised. | SUPPORTED | UNSUPPORTED | R05 | Key-compromise implications |
| `C4-V2-009` | Without atomic exact-byte handoff, C4 provides snapshot-level rather than execution-level binding. | PARTIALLY_SUPPORTED | CONDITIONAL | PKT-02 | TOCTOU boundary |
| `C4-V2-010` | Blockchain is not selected because no verified consensus/cross-observer requirement or necessity argument was supplied; no universal equivalence is claimed. | SUPPORTED as scoped recommendation | DEFERRED | R08, project requirements, PKT-02 | NISTIR 8202 distributed-ledger/consensus context |
| `C4-V2-011` | Offline dependency installation has not been demonstrated on the target. | UNVERIFIABLE from standards; supported negative evidence | UNVERIFIED | PKT-02; EC5 absent | No target wheelhouse/no-index install evidence |
| `C4-V2-012` | COCO, YOLO, ONNX, PyTorch, and TorchScript coverage is not yet tested; retraining is out of scope. | UNVERIFIABLE as project coverage | UNVERIFIED | Project requirements; EC5 absent | Target format ≠ tested format |
| `C4-V2-013` | A valid signature on an inference record protects the signed canonical record against undetected post-signing byte changes under the accepted-key/exact-byte assumptions; it does not prove semantic correctness. | SUPPORTED WITH QUALIFIER | UNVERIFIED | R02, R03 | Must retain accepted-key/exact-byte qualification |
| `C4-V2-014` | The selected construct can report successful signed-payload verification, artifact digest matching, and implemented linkage checks under trust/state/checkpoint assumptions. | PARTIALLY_SUPPORTED | UNVERIFIED | R01–R07 + local protocol design | Verifier output, not real-world truth |
| `C4-V2-015` | A five-day prototype may be feasible only with a frozen profile and pre-existing runtime access. | HYPOTHESIS | CONDITIONAL | PKT-01, PKT-02 | Planning hypothesis; not measured evidence |
| `C4-V2-016` | A distinct checkpoint key may provide compromise separation only when its key, anchor, and storage remain independently trusted. | SUPPORTED as recommendation | UNVERIFIED | PKT-01, PKT-02 | Same/separate-key decision unresolved |
| `C4-V2-017` | Standard public keyless Sigstore is deferred for a strict air gap. | SUPPORTED for standard public workflow | DEFERRED | R15 | OIDC/Fulcio/Rekor/root-update assumptions; local profile may differ |
| `C4-V2-018` | No implementation bundle, target-machine run log, wheelhouse, or executed E01–E24 result was supplied in the inspected evidence set. | SUPPORTED negative evidence | UNVERIFIED | PKT-01, PKT-02, PKT-03; EC5 absent | Scoped only to inspected inputs |

---

## 24. References

Authoritative public URLs below were rechecked on **2026-09-29**. The research conclusions remain based on the source state captured by C4 V2; current-source verification is used only to provide real public URLs and to identify source-version changes.

### [R01] RFC 8785 — JSON Canonicalization Scheme (JCS)

- **Authors:** A. Rundgren, B. Jordan, S. Erdtman
- **Type:** RFC / Informational
- **Published:** June 2020
- **Relevant locations:** §§3.1, 3.2.1, 3.2.2, 3.2.3; Appendix B
- **URL:** https://www.rfc-editor.org/rfc/rfc8785.html
- **Use in C4:** deterministic JSON serialization, Unicode/number constraints, property ordering
- **Accessed:** 2026-09-29

### [R01E] RFC 8785 Verified Erratum 7920

- **Organization:** RFC Editor
- **Type:** Verified technical erratum
- **Verified:** May 2024
- **Relevant location:** Erratum 7920, negative-zero handling
- **URL:** https://www.rfc-editor.org/errata/eid7920
- **Use in C4:** reject negative zero in the accepted profile
- **Accessed:** 2026-09-29

### [R02] RFC 8032 — Edwards-Curve Digital Signature Algorithm (EdDSA)

- **Authors:** S. Josefsson, I. Liusvaara
- **Type:** RFC / Informational
- **Published:** January 2017
- **Relevant locations:** §5.1.7 verification; §7 test vectors
- **URL:** https://www.rfc-editor.org/rfc/rfc8032.html
- **Use in C4:** Ed25519 signing/verification and conformance vectors
- **Accessed:** 2026-09-29

### [R03] NIST FIPS 186-5 — Digital Signature Standard (DSS)

- **Organization:** National Institute of Standards and Technology
- **Type:** Federal Information Processing Standard
- **Published:** February 2023
- **Relevant location:** abstract and digital-signature scope
- **URL:** https://csrc.nist.gov/pubs/fips/186-5/final
- **Use in C4:** mechanism-level signature integrity/authentication context
- **Accessed:** 2026-09-29

C4 does not promote the standard’s general discussion of signatory authentication/nonrepudiation into a project claim because the project has not established human identity, authorization, uncompromised key custody, or a complete PKI/operational policy.

### [R04] NIST FIPS 180-4 — Secure Hash Standard (SHS)

- **Organization:** National Institute of Standards and Technology
- **Type:** Federal Information Processing Standard
- **Published/updated:** August 2015
- **Relevant location:** abstract and SHA-256 specification
- **URL:** https://csrc.nist.gov/pubs/fips/180-4/upd1/final
- **Use in C4:** SHA-256 digest commitments
- **Accessed:** 2026-09-29

### [R05] NIST SP 800-57 Part 1 Rev. 5 — Recommendation for Key Management: Part 1 — General

- **Author:** Elaine Barker / NIST
- **Type:** NIST Special Publication
- **Published:** May 2020
- **Relevant location in source dossier:** §5.5 key-compromise implications
- **URL:** https://csrc.nist.gov/pubs/sp/800/57/pt1/r5/final
- **Use in C4:** key lifecycle and compromise boundaries
- **Accessed:** 2026-09-29

### [R06] RFC 5848 — Signed Syslog Messages

- **Authors:** J. Kelsey, J. Callas, A. Clemm
- **Type:** RFC / Standards Track
- **Published:** May 2010
- **Relevant locations:** abstract, §1, §8.4
- **URL:** https://www.rfc-editor.org/rfc/rfc5848.html
- **Use in C4:** replay resistance, message sequencing, missing-message concepts
- **Accessed:** 2026-09-29

### [R07] RFC 3161 — Internet X.509 Public Key Infrastructure Time-Stamp Protocol (TSP)

- **Authors:** C. Adams, P. Cain, D. Pinkas, R. Zuccherato
- **Type:** RFC / Standards Track
- **Published:** August 2001
- **Relevant location:** §2.1 trustworthy-time-source requirement
- **URL:** https://www.rfc-editor.org/rfc/rfc3161.html
- **Use in C4:** distinction between host timestamp and independently trusted time
- **Accessed:** 2026-09-29

### [R08] NISTIR 8202 — Blockchain Technology Overview

- **Authors:** Dylan Yaga, Peter Mell, Nik Roby, Karen Scarfone
- **Organization:** NIST
- **Type:** NIST Interagency/Internal Report
- **Published:** October 2018
- **Relevant locations:** abstract; §4 consensus; §8.1 considerations
- **URL:** https://csrc.nist.gov/pubs/ir/8202/final
- **Use in C4:** distributed ledger/consensus characteristics and scoped blockchain decision
- **Accessed:** 2026-09-29

### [R09] The Update Framework (TUF) Specification v1.0.35

- **Organization:** The Update Framework / CNCF community
- **Type:** Open specification
- **Source version used by C4 V2:** v1.0.35, released 15 July 2026
- **Relevant locations in source dossier:** §2.1.4; §5.4 steps 3–5
- **Version URL:** https://github.com/theupdateframework/specification/releases/tag/v1.0.35
- **Project specification site:** https://theupdateframework.github.io/specification/
- **Use in C4:** analogy for persisted trusted-version state and rollback checks; C4 does **not** claim TUF conformance
- **Current verification note:** upstream now lists v1.0.36 as newer; C4 retains v1.0.35 because that is the version cited by the original dossier
- **Accessed:** 2026-09-29

### [R10] DSSE — Dead Simple Signing Envelope

- **Organization:** Secure Systems Lab / DSSE Working Group
- **Type:** Open specification / repository
- **Source version cited by C4 V2:** v1.0.2
- **Relevant locations:** `protocol.md` Signing/Verification; `envelope.md` schema
- **URL:** https://github.com/secure-systems-lab/dsse
- **Use in C4:** domain-separated pre-authentication encoding and candidate envelope design
- **Accessed:** 2026-09-29

### [R11] RFC 9052 — CBOR Object Signing and Encryption (COSE): Structures and Process

- **Author:** J. Schaad
- **Type:** RFC / Internet Standard
- **Published:** August 2022
- **Relevant locations:** §2; §4.2 `COSE_Sign1`
- **URL:** https://www.rfc-editor.org/rfc/rfc9052.html
- **Use in C4:** compact CBOR signed-envelope candidate
- **Accessed:** 2026-09-29

### [R12] SLSA Specification v1.2

- **Organization:** SLSA community
- **Type:** Open software supply-chain specification
- **Version:** 1.2
- **Relevant locations:** Provenance; Build Track Basics
- **URLs:**  
  - https://slsa.dev/spec/v1.2/provenance  
  - https://slsa.dev/spec/v1.2/build-track-basics
- **Use in C4:** distinguishes build provenance from per-inference runtime records
- **Accessed:** 2026-09-29

### [R13] NIST FIPS 198-1 — The Keyed-Hash Message Authentication Code (HMAC)

- **Organization:** National Institute of Standards and Technology
- **Type:** Federal Information Processing Standard
- **Published:** July 2008
- **Relevant location:** abstract / shared-secret-key construction
- **URL:** https://csrc.nist.gov/pubs/fips/198-1/final
- **Use in C4:** HMAC shared-secret trust model
- **Accessed:** 2026-09-29

### [R14] RFC 3339 — Date and Time on the Internet: Timestamps

- **Authors:** G. Klyne, C. Newman
- **Type:** RFC / Standards Track
- **Published:** July 2002
- **Relevant location:** §5.6 format
- **URL:** https://www.rfc-editor.org/rfc/rfc3339.html
- **Use in C4:** timestamp syntax/profile only; does not create a trusted time source
- **Accessed:** 2026-09-29

### [R15] Sigstore — Keyless Signing Overview

- **Organization:** Sigstore
- **Type:** Project documentation
- **Relevant locations:** Root of Trust; Identity Tokens; Fulcio/Rekor workflow
- **URL:** https://docs.sigstore.dev/cosign/signing/overview/
- **Use in C4:** supports deferring the standard public keyless workflow for a strict air-gapped runtime while leaving open the possibility of a separately designed local infrastructure
- **Accessed:** 2026-09-29

### Internal packet/control locators retained for audit traceability

These are not public standards and are not substituted for primary references:

- `PKT-01` — `S7OC4 V1.docx`: P0016–P0019; P0216–P0249; T004; P0252; P0556; P1585–P1586; plus later implementation candidate locations cited by the audit.
- `PKT-02` — `S8OC4.docx`: P0012–P0060; P0097–P0116; P0126–P0133; P0141–P0160; P0168–P0182; P0188–P0199; P0222–P0225; P1726–P1747.
- `PKT-03` — `S9OC4.docx`: T001; T002; P0013–P0018; T009; P0077; P0106–P0112.
- `SYN-01` — secondary pasted synthesis; treated as consolidation only.
- `CTL-01` — project-control workbook used to identify the stale/inconsistent stage state.
- `USR-01` — problem-statement/cell requirements and required quality gates.

---

## 25. C4 Research Conclusion

C4 V2 supports a narrow and defensible cryptographic proposition: a verifier can check that presented artifact bytes match signed digest commitments and that a versioned canonical record verifies under an accepted public trust anchor. SHA-256 and digital signatures are complementary: the digest binds exact artifact bytes, while the signature authenticates the canonical record under the accepted key. RFC 8785-style deterministic serialization is necessary so the producer and verifier can reconstruct the same signed byte sequence.

Freshness and completeness are separate concerns. A signature alone does not reject replay, detect every deletion, protect against state rollback, or prove log completeness. Sequence, previous-record linkage, persisted verifier state, and independently retained checkpoints are separate controls with separate trust assumptions.

The unresolved trust assumptions are material: key compromise, trust-anchor replacement, state rollback, checkpoint rollback, offline revocation/rotation, crash consistency, multi-writer behavior, exact C2/C3 contracts, complex artifact scope, format fixtures, and causal execution binding remain incomplete or unverified. Host timestamps are descriptive because no trusted-time profile has been established.

The current target — JCS-canonicalized payloads, SHA-256 artifact digests, Ed25519 signatures, a single-writer chain, persisted state, and a signed checkpoint — is an **implementation target**, not a final architecture and not a project-verified deployment.

C4 hands C5 structured cryptographic evidence and explicit non-claims, including the distinction between `VERIFIED_BINDING` and `CLEAN`. It hands C6 the implementation profile, offline packaging gate, state/crash requirements, format-fixture obligations, and reproducibility tests required before any project-verification promotion.

**Final C4 V2 disposition: CONDITIONAL GO TO IMPLEMENTATION TARGET; NO PROJECT-VERIFIED PROMOTION.**
