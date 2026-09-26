"""Pure-Python schema gate for supervisor-owned persistence paths."""

from dataclasses import dataclass
import datetime
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str | None = None


class EvidenceSchemaValidator:
    REQUIRED_WORKER_OUTPUT_FIELDS = [
        "schema_version",
        "worker_id",
        "assessment_status",
        "raw_signal",
        "access_mode",
        "artifact_unit_id",
        "coverage_gap_clean_label",
        "limitations",
        "non_claims",
        "dependency_declaration",
        "assessment_timestamp",
        "error_detail",
    ]

    PROHIBITED_FIELDS = {
        "_".join(parts)
        for parts in (
            ("risk", "score"),
            ("aggregate", "assurance"),
            ("compromise", "probability"),
            ("overall", "score"),
            ("threat", "score"),
            ("malicious", "probability"),
            ("confidence", "score"),
            ("trust", "score"),
            ("safety", "score"),
        )
    }

    VALID_ASSESSMENT_STATUS_VALUES = {
        "COMPLETED",
        "ASSESSMENT_ERROR",
        "UNAVAILABLE",
        "UNSUPPORTED",
        "DEFERRED_IN_SCOPE",
        "ARTIFACT_UNIT_AMBIGUOUS",
        "LOAD_BLOCKED",
        "LOAD_SUCCESS",
        "LOAD_ERROR",
        "ONNX_PATH_CONTAINMENT_VIOLATION",
        "STRUCTURAL_VALID",
        "STRUCTURAL_INVALID",
        "REFERENCE_UNAVAILABLE",
    }

    C3_WORKER_IDS = {"COMP-W-C3A", "COMP-W-C3B", "COMP-W-C3C", "COMP-W-C3D"}
    C2_WORKER_IDS = {"COMP-W-C2A", "COMP-W-C2B", "COMP-W-C2C", "COMP-W-C2D"}

    _ACTIVE_WORKER_SCHEMA_VERSION = "worker-output-v1"
    _MAX_FUTURE_CLOCK_SKEW = datetime.timedelta(minutes=5)

    _REQUIRED_FINDING_FIELDS = (
        "finding_id",
        "detection_status",
        "interpretation_status",
        "applicability_status",
        "reference_health",
        "coverage_gap_clean_label",
        "anomaly_not_malicious_non_claim",
        "global_backdoor_absence_not_established",
        "pf_002_non_claim",
        "analyst_disposition_prompt",
    )
    _PROHIBITED_DETECTION_STATUSES = {
        "CONFIRMED_MALICIOUS",
        "CLEAN",
        "SAFE",
        "PROVEN_ATTACK",
    }
    _REQUIRED_PROVENANCE_FIELDS = (
        "provenance_id",
        "artifact_unit_digest",
        "evidence_record_digests",
        "signing_key_id",
        "signature",
        "signature_algorithm",
        "canonicalization_algorithm",
        "sequence_number",
        "replay_nonce",
        "pf_002_non_claim",
        "signing_status",
        "timestamp",
    )

    def validate_worker_output(self, raw: dict, task_type: str) -> ValidationResult:
        del task_type  # Worker class is determined by the signed worker_id contract.
        try:
            if not isinstance(raw, dict):
                return ValidationResult(False, "worker output must be a dict")

            for field_name in self.REQUIRED_WORKER_OUTPUT_FIELDS:
                if field_name not in raw:
                    return ValidationResult(
                        False, f"missing required field: {field_name}"
                    )

            prohibited = self._recursive_prohibited_scan(raw)
            if prohibited:
                return ValidationResult(
                    False, "prohibited field(s): " + ", ".join(prohibited)
                )

            if raw["assessment_status"] not in self.VALID_ASSESSMENT_STATUS_VALUES:
                return ValidationResult(False, "invalid assessment_status")

            worker_id = raw["worker_id"]
            if worker_id in self.C2_WORKER_IDS | self.C3_WORKER_IDS:
                if raw["coverage_gap_clean_label"] is not True:
                    return ValidationResult(
                        False, "coverage_gap_clean_label must be exactly True"
                    )

            if worker_id in self.C3_WORKER_IDS:
                access_mode = raw["access_mode"]
                if not isinstance(access_mode, str) or not access_mode.strip():
                    return ValidationResult(
                        False, "access_mode must be a non-empty string for C3"
                    )

            invalid_list = self._validate_nonempty_string_list(
                raw["limitations"], "limitations"
            )
            if invalid_list is not None:
                return invalid_list

            invalid_list = self._validate_nonempty_string_list(
                raw["non_claims"], "non_claims"
            )
            if invalid_list is not None:
                return invalid_list

            timestamp_result = self._validate_assessment_timestamp(
                raw["assessment_timestamp"]
            )
            if timestamp_result is not None:
                return timestamp_result

            if raw["schema_version"] != self._ACTIVE_WORKER_SCHEMA_VERSION:
                return ValidationResult(False, "schema_version is not active")

            return ValidationResult(True)
        except Exception as exc:
            return ValidationResult(False, "INTERNAL_VALIDATOR_ERROR: " + str(exc))

    @staticmethod
    def _validate_nonempty_string_list(
        value: Any, field_name: str
    ) -> ValidationResult | None:
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            return ValidationResult(
                False, f"{field_name} must contain non-empty strings"
            )
        return None

    def _validate_assessment_timestamp(
        self, value: Any
    ) -> ValidationResult | None:
        if not isinstance(value, str) or not value.strip():
            return ValidationResult(False, "assessment_timestamp must be ISO 8601 UTC")
        try:
            parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return ValidationResult(False, "assessment_timestamp must be ISO 8601 UTC")
        if parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0):
            return ValidationResult(False, "assessment_timestamp must be ISO 8601 UTC")
        now = datetime.datetime.now(datetime.timezone.utc)
        if parsed > now + self._MAX_FUTURE_CLOCK_SKEW:
            return ValidationResult(False, "assessment_timestamp is too far in the future")
        return None

    def _recursive_prohibited_scan(self, obj, path="") -> list[str]:
        violations: list[str] = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_path = f"{path}.{key}"
                if key in self.PROHIBITED_FIELDS:
                    violations.append(key_path)
                violations.extend(self._recursive_prohibited_scan(value, key_path))
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                violations.extend(
                    self._recursive_prohibited_scan(value, f"{path}[{index}]")
                )
        return violations

    def validate_finding(self, finding: dict) -> ValidationResult:
        try:
            if not isinstance(finding, dict):
                return ValidationResult(False, "finding must be a dict")
            for field_name in self._REQUIRED_FINDING_FIELDS:
                if field_name not in finding:
                    return ValidationResult(
                        False, f"missing required finding field: {field_name}"
                    )
            prohibited = self._recursive_prohibited_scan(finding)
            if prohibited:
                return ValidationResult(
                    False, "prohibited field(s): " + ", ".join(prohibited)
                )
            clean_label = finding["coverage_gap_clean_label"]
            if not (clean_label is True or type(clean_label) is int and clean_label == 1):
                return ValidationResult(
                    False, "coverage_gap_clean_label must be True or integer 1"
                )
            if finding["detection_status"] in self._PROHIBITED_DETECTION_STATUSES:
                return ValidationResult(False, "prohibited detection_status")
            return ValidationResult(True)
        except Exception as exc:
            return ValidationResult(False, "INTERNAL_VALIDATOR_ERROR: " + str(exc))

    def validate_provenance_record(self, record: dict) -> ValidationResult:
        try:
            if not isinstance(record, dict):
                return ValidationResult(False, "provenance record must be a dict")
            for field_name in self._REQUIRED_PROVENANCE_FIELDS:
                if field_name not in record:
                    return ValidationResult(
                        False, f"missing required provenance field: {field_name}"
                    )
            prohibited = self._recursive_prohibited_scan(record)
            if prohibited:
                return ValidationResult(
                    False, "prohibited field(s): " + ", ".join(prohibited)
                )
            non_claim = record["pf_002_non_claim"]
            if not isinstance(non_claim, str) or not non_claim.strip():
                return ValidationResult(False, "pf_002_non_claim must be non-empty")
            if record["signing_status"] not in {"SIGNED", "SIGNING_UNAVAILABLE"}:
                return ValidationResult(False, "invalid signing_status")
            nonce = record["replay_nonce"]
            if not isinstance(nonce, str) or not nonce.strip():
                return ValidationResult(False, "replay_nonce must be non-empty")
            return ValidationResult(True)
        except Exception as exc:
            return ValidationResult(False, "INTERNAL_VALIDATOR_ERROR: " + str(exc))
