"""Supervisor-owned reference health state management."""

from __future__ import annotations

import datetime
import json
import sqlite3
from typing import Any

from assurance_system.constants import AuditEventType, ReferenceHealth
from assurance_system.exceptions import AuditWriteError, StorageWriteError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


REFERENCE_CATEGORY_VIOLATION = "REFERENCE_CATEGORY_VIOLATION"
_REQUIRED_GATES = tuple(f"R{index}" for index in range(8))


class ReferenceManager:
    """Manage reference health without inferring trust from registration alone."""

    HEALTH_STATES = frozenset(
        {
            ReferenceHealth.UNAVAILABLE,
            ReferenceHealth.HEALTH_UNVERIFIED,
            ReferenceHealth.FORMAT_ASSET,
            ReferenceHealth.HEALTH_VERIFIED,
            ReferenceHealth.CONTAMINATION_SUSPECTED,
            ReferenceHealth.STALE_SUSPECTED,
        }
    )

    def __init__(
        self, evidence_store: EvidenceStore, audit_chain: AuditChainWriter
    ) -> None:
        self._store = evidence_store
        self._audit = audit_chain

    @staticmethod
    def _required_text(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _timestamp() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    def get_reference_health(self, reference_id: str) -> str:
        """Return the persisted health state or the fail-closed MVP default."""

        self._required_text(reference_id, "reference_id")
        row = self._store.query_reference_health(reference_id)
        if row is None:
            return ReferenceHealth.UNAVAILABLE
        state = row["health_state"]
        if state not in self.HEALTH_STATES:
            return ReferenceHealth.UNAVAILABLE
        return state

    def _write_transition(
        self,
        *,
        reference_id: str,
        previous_state: str,
        new_state: str,
        reason: str,
        reference_name: str,
        format_category: str,
        gate_completion_record: dict[str, Any] | None = None,
        last_verified_timestamp: str | None = None,
    ) -> str:
        if new_state not in self.HEALTH_STATES:
            raise ValueError("new_state is not in the approved reference vocabulary")

        payload = {
            "reference_id": reference_id,
            "previous_state": previous_state,
            "new_state": new_state,
            "reason": reason,
        }
        encoded_gates = (
            json.dumps(
                gate_completion_record,
                sort_keys=True,
                separators=(",", ":"),
            )
            if gate_completion_record is not None
            else None
        )

        try:
            with self._store._conn:
                self._store._conn.execute(
                    """INSERT INTO reference_health
                       (reference_id, reference_name, health_state,
                        format_category, gate_completion_record,
                        last_verified_timestamp)
                       VALUES (?,?,?,?,?,?)
                       ON CONFLICT(reference_id) DO UPDATE SET
                         reference_name = excluded.reference_name,
                         health_state = excluded.health_state,
                         format_category = excluded.format_category,
                         gate_completion_record = excluded.gate_completion_record,
                         last_verified_timestamp = excluded.last_verified_timestamp,
                         updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')""",
                    (
                        reference_id,
                        reference_name,
                        new_state,
                        format_category,
                        encoded_gates,
                        last_verified_timestamp,
                    ),
                )
                self._audit.append_event(
                    AuditEventType.REFERENCE_HEALTH_TRANSITION,
                    payload,
                )
        except AuditWriteError:
            raise
        except sqlite3.Error as exc:
            raise StorageWriteError(
                "Failed to persist reference health transition"
            ) from exc
        return new_state

    def register_reference(
        self,
        reference_id: str,
        format_category: str,
        reference_name: str | None = None,
    ) -> str:
        """Register a reference without granting verified health."""

        reference_id = self._required_text(reference_id, "reference_id")
        format_category = self._required_text(format_category, "format_category")
        reference_name = self._required_text(
            reference_name if reference_name is not None else reference_id,
            "reference_name",
        )

        existing = self._store.query_reference_health(reference_id)
        if existing is not None:
            if (
                existing["reference_name"] != reference_name
                or existing["format_category"] != format_category
            ):
                raise ValueError("reference_id is already registered")
            return self.get_reference_health(reference_id)

        initial_state = (
            ReferenceHealth.FORMAT_ASSET
            if format_category == ReferenceHealth.FORMAT_ASSET
            else ReferenceHealth.HEALTH_UNVERIFIED
        )
        return self._write_transition(
            reference_id=reference_id,
            previous_state=ReferenceHealth.UNAVAILABLE,
            new_state=initial_state,
            reason="REFERENCE_REGISTERED",
            reference_name=reference_name,
            format_category=format_category,
        )

    @staticmethod
    def _approved_gates_pass(
        reference_id: str, gate_records: dict[str, Any]
    ) -> bool:
        if not isinstance(gate_records, dict) or set(gate_records) != set(
            _REQUIRED_GATES
        ):
            return False

        artifact_digest: str | None = None
        for gate_name in _REQUIRED_GATES:
            record = gate_records[gate_name]
            if not isinstance(record, dict):
                return False
            if record.get("reference_id") != reference_id:
                return False
            if record.get("passed") is not True:
                return False
            record_digest = record.get("artifact_digest")
            if not isinstance(record_digest, str) or not record_digest:
                return False
            if artifact_digest is None:
                artifact_digest = record_digest
            elif record_digest != artifact_digest:
                return False
        return True

    def attempt_health_promotion(
        self, reference_id: str, gate_records: dict[str, Any]
    ) -> str:
        """Apply the approved all-of R0–R7 promotion rule."""

        reference_id = self._required_text(reference_id, "reference_id")
        row = self._store.query_reference_health(reference_id)
        if row is None:
            return ReferenceHealth.UNAVAILABLE

        previous_state = row["health_state"]
        if previous_state == ReferenceHealth.FORMAT_ASSET:
            self._audit.append_event(
                REFERENCE_CATEGORY_VIOLATION,
                {
                    "reference_id": reference_id,
                    "previous_state": previous_state,
                    "new_state": previous_state,
                    "reason": "FORMAT_ASSET_CANNOT_BE_HEALTH_VERIFIED",
                },
            )
            return ReferenceHealth.FORMAT_ASSET

        new_state = (
            ReferenceHealth.HEALTH_VERIFIED
            if self._approved_gates_pass(reference_id, gate_records)
            else ReferenceHealth.HEALTH_UNVERIFIED
        )
        if new_state == previous_state:
            return new_state

        return self._write_transition(
            reference_id=reference_id,
            previous_state=previous_state,
            new_state=new_state,
            reason=(
                "R0_R7_GATES_VERIFIED"
                if new_state == ReferenceHealth.HEALTH_VERIFIED
                else "R0_R7_GATES_INCOMPLETE_OR_FAILED"
            ),
            reference_name=row["reference_name"],
            format_category=row["format_category"],
            gate_completion_record=(
                gate_records
                if new_state == ReferenceHealth.HEALTH_VERIFIED
                else row.get("gate_completion_record")
            ),
            last_verified_timestamp=(
                self._timestamp()
                if new_state == ReferenceHealth.HEALTH_VERIFIED
                else row.get("last_verified_timestamp")
            ),
        )

    def register_staleness_event(self, reference_id: str, reason: str) -> str:
        """Downgrade an existing reference to ``STALE_SUSPECTED``."""

        reference_id = self._required_text(reference_id, "reference_id")
        reason = self._required_text(reason, "reason")
        row = self._store.query_reference_health(reference_id)
        if row is None:
            raise ValueError("reference_id is not registered")
        previous_state = row["health_state"]
        if previous_state == ReferenceHealth.STALE_SUSPECTED:
            return previous_state

        return self._write_transition(
            reference_id=reference_id,
            previous_state=previous_state,
            new_state=ReferenceHealth.STALE_SUSPECTED,
            reason=reason,
            reference_name=row["reference_name"],
            format_category=row["format_category"],
            gate_completion_record=row.get("gate_completion_record"),
            last_verified_timestamp=row.get("last_verified_timestamp"),
        )
