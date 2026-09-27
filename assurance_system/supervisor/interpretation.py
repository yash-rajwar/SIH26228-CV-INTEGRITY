"""COMP-C5 deterministic assurance interpretation rule engine.

The engine converts already-schema-validated C2/C3 evidence into a structured
finding. It does not parse submitted artifacts, persist findings, or emit audit
events; those remain supervisor-orchestrator responsibilities.
"""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any


_SCHEMA_VERSION = "v1.0"  # Frozen by the approved SP-003 vocabulary contract.

T05D_NON_CLAIM_TEXT = (
    "T05d (clean-label poisoning) is NOT detectable under the current assessment "
    "scope; no detection claim is made for this attack class."
)
_ANOMALY_NON_CLAIM_TEXT = (
    "An observed anomaly does not establish malicious intent or prove an attack."
)
_GLOBAL_BACKDOOR_NON_CLAIM_TEXT = (
    "Finite model assessment does not establish global backdoor absence."
)
_DEFAULT_LIMITATION = (
    "Interpretation is limited to the supplied evidence records and their declared "
    "coverage."
)

_FAIL_STATES = frozenset(
    {
        "ASSESSMENT_ERROR",
        "UNAVAILABLE",
        "ARTIFACT_UNIT_AMBIGUOUS",
        "LOAD_ERROR",
        "REFERENCE_UNAVAILABLE",
    }
)
_COMPLETED_STATES = frozenset(
    {"COMPLETED", "STRUCTURAL_VALID", "LOAD_SUCCESS"}
)
_C3_WORKER_IDS = frozenset(
    {"COMP-W-C3A", "COMP-W-C3B", "COMP-W-C3C", "COMP-W-C3D"}
)

_INTERPRETATION_MAP = {
    "UNAVAILABLE": "UNAVAILABLE",
    "ANOMALY_DETECTED": "REQUIRES_INVESTIGATION",
    "IDENTITY_MATCH": "CONSISTENT_WITH_EXPECTED",
    "IDENTITY_DIFFERENT": "IDENTITY_DEVIATION_DETECTED",
    "COMPLETED_STATISTICS_ONLY": "STATISTICS_REPORTED",
    "NO_ANOMALY_DETECTED": "NO_ANOMALY_DETECTED",
}

_DISPOSITION_MAP = {
    "UNAVAILABLE": "UNAVAILABLE_NO_DECISION",
    "ANOMALY_DETECTED": "ESCALATE",
    "IDENTITY_DIFFERENT": "ESCALATE",
    "IDENTITY_MATCH": "ACCEPT",
    "NO_ANOMALY_DETECTED": "ACCEPT",
    "COMPLETED_STATISTICS_ONLY": "ACCEPT_WITH_CONTEXT",
}


class C5InterpretationEngine:
    """Produce bounded findings from supplied evidence without persistence."""

    def __init__(self, schema_validator=None):
        self._schema_validator = schema_validator

    @staticmethod
    def _raw_signal(record: dict[str, Any]) -> dict[str, Any]:
        raw_signal = record.get("raw_signal")
        if isinstance(raw_signal, dict):
            return raw_signal
        if isinstance(raw_signal, str):
            try:
                decoded = json.loads(raw_signal)
            except (TypeError, ValueError, json.JSONDecodeError):
                return {}
            if isinstance(decoded, dict):
                return decoded
        return {}

    @staticmethod
    def _positive_count(raw_signal: dict[str, Any], field_name: str) -> bool:
        value = raw_signal.get(field_name, 0)
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value > 0
        )

    def _derive_detection_status(
        self, evidence_records: list[dict[str, Any]]
    ) -> str:
        statuses = {record.get("assessment_status") for record in evidence_records}

        # Priority 1: upstream failure always overrides every lower rule.
        if statuses & _FAIL_STATES:
            return "UNAVAILABLE"

        # Priorities 2 through 4: explicit structural or loading signals.
        if "ONNX_PATH_CONTAINMENT_VIOLATION" in statuses:
            return "ANOMALY_DETECTED"
        if "LOAD_BLOCKED" in statuses:
            return "ANOMALY_DETECTED"
        if "STRUCTURAL_INVALID" in statuses:
            return "ANOMALY_DETECTED"

        # Priority 5: C2A geometry/structure violations.
        for record in evidence_records:
            if record.get("worker_id") == "COMP-W-C2A" and self._positive_count(
                self._raw_signal(record), "violation_count"
            ):
                return "ANOMALY_DETECTED"

        # Priority 6: C2B exact duplicate groups.
        for record in evidence_records:
            if record.get("worker_id") == "COMP-W-C2B" and self._positive_count(
                self._raw_signal(record), "duplicate_group_count"
            ):
                return "ANOMALY_DETECTED"

        # Priority 7: C3B identity comparison.
        for record in evidence_records:
            if record.get("worker_id") != "COMP-W-C3B":
                continue
            comparison = self._raw_signal(record).get(
                "comparison_result", "UNAVAILABLE"
            )
            if comparison == "DIFFERENT":
                return "IDENTITY_DIFFERENT"
            if comparison == "MATCH":
                return "IDENTITY_MATCH"
            return "UNAVAILABLE"

        # Priority 8: C2C output reports statistics without an anomaly claim.
        for record in evidence_records:
            if (
                record.get("worker_id") == "COMP-W-C2C"
                and record.get("assessment_status") == "COMPLETED"
            ):
                return "COMPLETED_STATISTICS_ONLY"

        # The technical contract permits the default only for completed evidence.
        if evidence_records and all(
            record.get("assessment_status") in _COMPLETED_STATES
            for record in evidence_records
        ):
            return "NO_ANOMALY_DETECTED"
        return "UNAVAILABLE"

    @staticmethod
    def _derive_applicability_status(
        evidence_records: list[dict[str, Any]],
    ) -> str:
        statuses = {record.get("assessment_status") for record in evidence_records}
        if "UNSUPPORTED" in statuses:
            return "UNSUPPORTED"
        if "DEFERRED_IN_SCOPE" in statuses:
            return "DEFERRED_IN_SCOPE"
        if "REFERENCE_UNAVAILABLE" in statuses:
            return "REFERENCE_UNAVAILABLE"
        return "APPLICABLE"

    @staticmethod
    def _collect_text_values(
        evidence_records: list[dict[str, Any]], field_name: str
    ) -> list[str]:
        collected: list[str] = []
        for record in evidence_records:
            values = record.get(field_name)
            if not isinstance(values, list):
                continue
            for value in values:
                if (
                    isinstance(value, str)
                    and value.strip()
                    and value not in collected
                ):
                    collected.append(value)
        return collected

    @staticmethod
    def _created_at() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _validate_inputs(
        asset_id: str,
        method_id: str,
        evidence_records: list[dict[str, Any]],
        c4_binding: dict[str, Any] | None,
        reference_health: str,
        access_mode: str,
    ) -> None:
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ValueError("asset_id must be a non-empty string")
        if not isinstance(method_id, str) or not method_id.strip():
            raise ValueError("method_id must be a non-empty string")
        if not isinstance(evidence_records, list) or any(
            not isinstance(record, dict) for record in evidence_records
        ):
            raise ValueError("evidence_records must be a list of dictionaries")
        if c4_binding is not None and not isinstance(c4_binding, dict):
            raise ValueError("c4_binding must be a dictionary or None")
        if not isinstance(reference_health, str) or not reference_health.strip():
            raise ValueError("reference_health must be a non-empty string")
        if not isinstance(access_mode, str) or not access_mode.strip():
            raise ValueError("access_mode must be a non-empty string")

    def produce_finding(
        self,
        asset_id: str,
        method_id: str,
        evidence_records: list[dict],
        c4_binding: dict | None,
        reference_health: str,
        access_mode: str,
    ) -> dict:
        """Apply the frozen C5 priority rules and return a validated finding."""

        self._validate_inputs(
            asset_id,
            method_id,
            evidence_records,
            c4_binding,
            reference_health,
            access_mode,
        )

        detection_status = self._derive_detection_status(evidence_records)
        worker_ids = sorted(
            {
                record["worker_id"]
                for record in evidence_records
                if isinstance(record.get("worker_id"), str)
                and record["worker_id"].strip()
            }
        )
        contains_c3_evidence = any(
            worker_id in _C3_WORKER_IDS for worker_id in worker_ids
        )

        limitations = self._collect_text_values(evidence_records, "limitations")
        if not limitations:
            limitations.append(_DEFAULT_LIMITATION)

        non_claims = self._collect_text_values(evidence_records, "non_claims")
        if T05D_NON_CLAIM_TEXT not in non_claims:
            non_claims.append(T05D_NON_CLAIM_TEXT)
        if (
            detection_status == "ANOMALY_DETECTED"
            and _ANOMALY_NON_CLAIM_TEXT not in non_claims
        ):
            non_claims.append(_ANOMALY_NON_CLAIM_TEXT)
        if (
            contains_c3_evidence
            and _GLOBAL_BACKDOOR_NON_CLAIM_TEXT not in non_claims
        ):
            non_claims.append(_GLOBAL_BACKDOOR_NON_CLAIM_TEXT)

        pf_002_non_claim = "C4_BINDING_UNAVAILABLE"
        if c4_binding is not None:
            supplied_non_claim = c4_binding.get("pf_002_non_claim")
            if isinstance(supplied_non_claim, str) and supplied_non_claim.strip():
                pf_002_non_claim = supplied_non_claim

        finding = {
            "finding_id": str(uuid.uuid4()),
            "schema_version": _SCHEMA_VERSION,
            "asset_id": asset_id,
            "method_id": method_id,
            "detection_status": detection_status,
            "interpretation_status": _INTERPRETATION_MAP[detection_status],
            "applicability_status": self._derive_applicability_status(
                evidence_records
            ),
            "raw_signal": {
                "evidence_records": [
                    {
                        "worker_id": record.get("worker_id"),
                        "assessment_status": record.get("assessment_status"),
                        "raw_signal": record.get("raw_signal"),
                    }
                    for record in evidence_records
                ]
            },
            "reference_health": reference_health,
            "access_mode": access_mode,
            "limitations": limitations,
            "non_claims": non_claims,
            "dependency_declaration": {
                "co_firing_detectors": worker_ids,
                "independence_established": False,
            },
            "coverage_gap_clean_label": 1,
            "anomaly_not_malicious_non_claim": int(
                detection_status == "ANOMALY_DETECTED"
            ),
            "global_backdoor_absence_not_established": int(
                contains_c3_evidence
            ),
            "pf_002_non_claim": pf_002_non_claim,
            "analyst_disposition_prompt": _DISPOSITION_MAP[detection_status],
            "is_synthetic": any(
                bool(record.get("is_synthetic")) for record in evidence_records
            )
            or bool(c4_binding and c4_binding.get("is_synthetic")),
            "created_at": self._created_at(),
        }

        if self._schema_validator is not None:
            result = self._schema_validator.validate_finding(finding)
            if not getattr(result, "valid", result is True):
                reason = getattr(result, "reason", "finding rejected")
                raise ValueError(f"finding schema validation failed: {reason}")

        return finding
