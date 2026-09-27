"""Supervisor-owned COMP-C4 provenance record construction.

TASK-019 Part A deliberately implements the unsigned provenance shell only.
Operational signing remains unavailable until PRE-08 key-path provisioning and
supervisor-only ACL verification are complete.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import sqlite3
import uuid
from typing import Any

from assurance_system.constants import (
    AuditEventType,
    CANONICALIZATION_ALGORITHM_ID,
    PF_002_NON_CLAIM,
    SigningStatus,
)
from assurance_system.exceptions import ReplayAttemptError, StorageWriteError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


_SCHEMA_VERSION = "v1.0"
_SIGNING_KEY_UNAVAILABLE = "UNAVAILABLE"
_SIGNING_BLOCKER = "PRE-08_KEY_PATH_AND_ACL_UNRESOLVED"


@dataclasses.dataclass
class SequenceState:
    """Mutable next-sequence state for one provenance-building session."""

    sequence_number: int = 1
    last_record_digest: str = ""


class ProvenanceBuilder:
    """Build, persist, and audit provenance records in the supervisor process."""

    def __init__(self, store: EvidenceStore, audit: AuditChainWriter):
        self._store = store
        self._audit = audit

    @staticmethod
    def canonicalize(record: dict[str, Any]) -> bytes:
        """Return canonical UTF-8 JSON under the frozen SP-003 algorithm."""

        return json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    @staticmethod
    def generate_replay_nonce() -> str:
        """Generate a fresh UUID4 replay nonce in the specified hex form."""

        return uuid.uuid4().hex

    @staticmethod
    def _timestamp() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    def _last_sequence_number(self) -> int:
        row = self._store._conn.execute(
            "SELECT MAX(sequence_number) FROM provenance_records"
        ).fetchone()
        if row is None or row[0] is None:
            return 0
        return int(row[0])

    def _nonce_exists(self, replay_nonce: str) -> bool:
        row = self._store._conn.execute(
            "SELECT 1 FROM provenance_records WHERE replay_nonce = ? LIMIT 1",
            (replay_nonce,),
        ).fetchone()
        return row is not None

    def _audit_replay(self, replay_nonce: str) -> None:
        self._audit.append_event(
            AuditEventType.REPLAY_ATTEMPT_DETECTED,
            {"replay_nonce": replay_nonce, "action": "REJECTED"},
        )

    def _check_replay_nonce(self, replay_nonce: str) -> None:
        if self._nonce_exists(replay_nonce):
            self._audit_replay(replay_nonce)
            raise ReplayAttemptError("Duplicate provenance replay nonce")

    def _check_sequence(self, sequence_number: int, last_sequence: int) -> int:
        expected = last_sequence + 1
        if sequence_number == expected:
            return sequence_number
        self._audit.append_event(
            AuditEventType.SEQUENCE_GAP_DETECTED,
            {
                "expected": expected,
                "received": sequence_number,
                "gap_size": sequence_number - expected,
            },
        )
        return expected

    @staticmethod
    def _sign(_record_bytes: bytes) -> tuple[None, None, str]:
        """Part A signing stub: no key is read and no signature is produced."""

        return None, None, SigningStatus.SIGNING_UNAVAILABLE

    def _default_sequence_state(self) -> SequenceState:
        return SequenceState(sequence_number=self._last_sequence_number() + 1)

    @staticmethod
    def _validate_digests(
        artifact_unit_digest: str, evidence_record_digests: list[str]
    ) -> None:
        if not isinstance(artifact_unit_digest, str) or not artifact_unit_digest:
            raise ValueError("artifact_unit_digest must be a non-empty string")
        if not isinstance(evidence_record_digests, list) or not all(
            isinstance(digest, str) and digest
            for digest in evidence_record_digests
        ):
            raise ValueError(
                "evidence_record_digests must be a list of non-empty strings"
            )

    def build_and_sign(
        self,
        artifact_unit_digest: str,
        evidence_record_digests: list[str],
        sequence_state: SequenceState | None = None,
        timestamp: str | None = None,
        replay_nonce: str | None = None,
    ) -> dict[str, Any]:
        """Build the Part A record, persist it, and emit mandatory audit events.

        A caller-supplied ``sequence_state`` supports deterministic recovery and
        gap tests. When omitted, the next value is recovered durably from the
        supervisor-owned provenance table. A detected gap is audited and the
        sequence resumes from the store-derived expected value, matching the
        COMP-C4 recovery contract.
        """

        self._validate_digests(artifact_unit_digest, evidence_record_digests)
        state = sequence_state or self._default_sequence_state()
        if (
            not isinstance(state.sequence_number, int)
            or state.sequence_number < 1
        ):
            raise ValueError("sequence_number must be a positive integer")

        nonce = replay_nonce or self.generate_replay_nonce()
        if not isinstance(nonce, str) or not nonce:
            raise ValueError("replay_nonce must be a non-empty string")
        self._check_replay_nonce(nonce)

        last_sequence = self._last_sequence_number()
        sequence_number = self._check_sequence(
            state.sequence_number, last_sequence
        )

        provenance_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "provenance_id": provenance_id,
            "schema_version": _SCHEMA_VERSION,
            "artifact_unit_digest": artifact_unit_digest,
            "evidence_record_digests": list(evidence_record_digests),
            "signing_key_id": _SIGNING_KEY_UNAVAILABLE,
            "signature": None,
            "signature_algorithm": None,
            "canonicalization_algorithm": CANONICALIZATION_ALGORITHM_ID,
            "sequence_number": sequence_number,
            "replay_nonce": nonce,
            "pf_002_non_claim": PF_002_NON_CLAIM,
            "signing_status": SigningStatus.SIGNING_UNAVAILABLE,
            "timestamp": timestamp or self._timestamp(),
        }

        signature, algorithm, signing_status = self._sign(
            self.canonicalize(record)
        )
        record["signature"] = signature
        record["signature_algorithm"] = algorithm
        record["signing_status"] = signing_status

        try:
            self._store.write_provenance_record(record)
        except StorageWriteError as exc:
            if (
                isinstance(exc.__cause__, sqlite3.IntegrityError)
                and self._nonce_exists(nonce)
            ):
                self._audit_replay(nonce)
                raise ReplayAttemptError(
                    "Duplicate provenance replay nonce"
                ) from exc
            raise

        state.last_record_digest = hashlib.sha256(
            self.canonicalize(record)
        ).hexdigest()
        state.sequence_number = sequence_number + 1

        self._audit.append_event(
            AuditEventType.SIGNING_UNAVAILABLE,
            {
                "provenance_id": provenance_id,
                "reason": _SIGNING_BLOCKER,
            },
        )
        self._audit.append_event(
            AuditEventType.PROVENANCE_RECORD_WRITTEN,
            {
                "provenance_id": provenance_id,
                "artifact_unit_digest": artifact_unit_digest,
                "sequence_number": record["sequence_number"],
                "signing_status": record["signing_status"],
            },
        )
        return record
