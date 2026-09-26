# SP-004 Crypto Profile

Decision date: 2026-09-27  
Related decisions: PRE-02 resolved to HMAC-SHA256; PRE-08 path provisioning remains conditional on PRE-01

## Algorithm and key

| Property | Value |
|---|---|
| Algorithm | `HMAC-SHA256` |
| Implementation | Python standard library `hmac` with `hashlib.sha256` |
| Key material | At least 32 cryptographically random bytes; 32 bytes is the MVP generation size |
| Key encoding on disk | Raw bytes, not hex, Base64, text, or a Python literal |
| Signature bytes | 32 bytes |
| Stored signature encoding | Lowercase hex, exactly 64 hexadecimal characters |
| Verification | `hmac.compare_digest` |

## Storage and access

The configuration key is `signing.key_path`. The Technical Specification's
Linux deployment value is `/var/assurance/keys/hmac_key.bin`. Because PRE-01
does not identify the target OS, that absolute path is not claimed to be valid
on the actual target yet. PRE-08 operational provisioning closes only when the
target-specific absolute path is recorded and verified.

Required invariants regardless of OS:

- The key is generated and provisioned outside the repository and submission
  pipeline; it is never committed.
- Only the supervisor service identity may read it; workers and analyst
  interfaces cannot read or write it.
- The supervisor strips the key path and all key material from worker task
  objects and subprocess environments.
- Absence, unreadability, invalid length, or signing failure produces
  `signing_status = SIGNING_UNAVAILABLE`, `signature = null`, and
  `signature_algorithm = null`; it never falls back to another algorithm.
- When signing succeeds, `signature_algorithm = HMAC-SHA256`.

## Security property and non-claim

HMAC authenticates records only to parties holding the shared secret. It does
not provide public verification or asymmetric non-repudiation. All provenance
records retain the complete PF-002 non-claim required by the specifications.

