# assurance_system/supervisor/audit_chain.py
#
# Hash-chain audit trail writer.
# Conceptual design informed by R01 (VIKASHL25/SIH-26228) TamperEvidentAuditChain (REUSE-013).
# Code is a full re-implementation: fail-open corrupt reset replaced by fail-closed quarantine;
# supervisor-only write authority enforced; COMPLETENESS_UNAVAILABLE emitted for tail completeness.
# R01 code is NOT copied (license unresolved). See AGENTS.md §REUSE-013.

"""Fail-closed, supervisor-owned hash-chain audit writer."""

from dataclasses import dataclass, field
import datetime
import hashlib
import json

from assurance_system.constants import AuditEventType
from assurance_system.exceptions import AuditWriteError
from assurance_system.supervisor.evidence_store import EvidenceStore


_SUPERVISOR_VERSION = "0.1.0-mvp"


@dataclass
class ChainVerificationResult:
    intact: bool
    violations: list[dict] = field(default_factory=list)


class AuditChainWriter:
    """Append and verify audit events without any reset or repair path."""

    GENESIS_HASH = "GENESIS"

    def __init__(self, store: EvidenceStore):
        self._store = store

    @staticmethod
    def _canonical_bytes(value: dict) -> bytes:
        return json.dumps(value, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    @classmethod
    def _event_hash(cls, event_record: dict) -> str:
        return hashlib.sha256(cls._canonical_bytes(event_record)).hexdigest()

    @staticmethod
    def _timestamp() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    def _read_chain_state(self) -> dict:
        try:
            row = self._store._conn.execute(
                """SELECT last_event_id, last_chain_link_hash,
                          last_sequence_number
                   FROM chain_state WHERE id = ?""",
                (1,),
            ).fetchone()
        except Exception as exc:
            raise AuditWriteError("Failed to read audit chain state") from exc
        if row is None:
            raise AuditWriteError("Audit chain state is missing")
        state = dict(row)
        if (
            state["last_event_id"] == 0
            and state["last_sequence_number"] == 0
            and state["last_chain_link_hash"] == self.GENESIS_HASH
        ):
            return state
        if (
            state["last_event_id"] < 1
            or state["last_sequence_number"] < 1
            or not state["last_chain_link_hash"]
        ):
            raise AuditWriteError("Audit chain state is inconsistent")
        return state

    def append_event(self, event_type: str, payload: dict) -> str:
        canonical_payload = self._canonical_bytes(payload)
        payload_digest = hashlib.sha256(canonical_payload).hexdigest()
        state = self._read_chain_state()
        sequence_number = state["last_sequence_number"] + 1
        event_record = {
            "event_type": event_type,
            "payload_digest": payload_digest,
            "previous_event_digest": state["last_chain_link_hash"],
            "timestamp": self._timestamp(),
            "supervisor_version_id": _SUPERVISOR_VERSION,
            "sequence_number": sequence_number,
        }
        event_record["chain_link_hash"] = self._event_hash(event_record)
        return self._store.write_audit_event(event_type, event_record)

    @staticmethod
    def _persisted_event_record(event: dict) -> dict:
        return {
            "event_type": event["event_type"],
            "payload_digest": event["payload_digest"],
            "previous_event_digest": event["previous_event_digest"],
            "timestamp": event["timestamp"],
            "supervisor_version_id": event["supervisor_version_id"],
            # The authoritative DDL uses event_id as the persisted event sequence.
            "sequence_number": event["event_id"],
        }

    @staticmethod
    def _violation(
        event_id: int, violation_type: str, expected: object, found: object
    ) -> dict:
        return {
            "event_id": event_id,
            "violation_type": violation_type,
            "expected_hash": str(expected),
            "found_hash": str(found),
        }

    def verify_chain_integrity(self) -> ChainVerificationResult:
        events = self._store.query_audit_trail()
        violations: list[dict] = []
        sequence_gap = False
        expected_event_id = 1
        expected_predecessor = self.GENESIS_HASH

        for event in events:
            event_id = event["event_id"]
            if event_id != expected_event_id:
                sequence_gap = True
                violations.append(
                    self._violation(
                        event_id, "SEQUENCE_GAP", expected_event_id, event_id
                    )
                )
            if event["previous_event_digest"] != expected_predecessor:
                violations.append(
                    self._violation(
                        event_id,
                        "PREVIOUS_EVENT_DIGEST_MISMATCH",
                        expected_predecessor,
                        event["previous_event_digest"],
                    )
                )
            recomputed = self._event_hash(self._persisted_event_record(event))
            if event["chain_link_hash"] != recomputed:
                violations.append(
                    self._violation(
                        event_id,
                        "CHAIN_LINK_HASH_MISMATCH",
                        recomputed,
                        event["chain_link_hash"],
                    )
                )
            expected_predecessor = event["chain_link_hash"]
            expected_event_id = event_id + 1

        state = self._read_chain_state()
        expected_last_id = events[-1]["event_id"] if events else 0
        expected_last_hash = events[-1]["chain_link_hash"] if events else self.GENESIS_HASH
        if (
            state["last_event_id"] != expected_last_id
            or state["last_sequence_number"] != expected_last_id
        ):
            sequence_gap = True
            violations.append(
                self._violation(
                    expected_last_id,
                    "CHAIN_STATE_SEQUENCE_MISMATCH",
                    expected_last_id,
                    state["last_sequence_number"],
                )
            )
        if state["last_chain_link_hash"] != expected_last_hash:
            violations.append(
                self._violation(
                    expected_last_id,
                    "CHAIN_STATE_HASH_MISMATCH",
                    expected_last_hash,
                    state["last_chain_link_hash"],
                )
            )

        if violations:
            if sequence_gap:
                self.append_event(
                    AuditEventType.SEQUENCE_GAP_DETECTED,
                    {"violations_count": len(violations)},
                )
            self.append_event(
                AuditEventType.CHAIN_CORRUPT,
                {"violations_count": len(violations)},
            )
            return ChainVerificationResult(intact=False, violations=violations)
        return ChainVerificationResult(intact=True, violations=[])
