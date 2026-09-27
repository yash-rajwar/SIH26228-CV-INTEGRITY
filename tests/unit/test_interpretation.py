"""TASK-021 COMP-C5 interpretation rule and finding-contract tests."""

from __future__ import annotations

import datetime
import json
import pathlib
import uuid

import pytest

from assurance_system.supervisor.interpretation import (
    C5InterpretationEngine,
    T05D_NON_CLAIM_TEXT,
)
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator


def _record(
    worker_id: str = "COMP-W-C2A",
    assessment_status: str = "COMPLETED",
    raw_signal=None,
    *,
    is_synthetic: bool = False,
) -> dict:
    return {
        "worker_id": worker_id,
        "assessment_status": assessment_status,
        "raw_signal": {} if raw_signal is None else raw_signal,
        "limitations": ["Fixture evidence has bounded coverage."],
        "non_claims": ["Fixture evidence does not establish intent."],
        "is_synthetic": is_synthetic,
    }


def _finding(evidence_records: list[dict], **overrides) -> dict:
    arguments = {
        "asset_id": "asset-021",
        "method_id": "M01",
        "evidence_records": evidence_records,
        "c4_binding": None,
        "reference_health": "UNAVAILABLE",
        "access_mode": "UNAVAILABLE",
    }
    arguments.update(overrides)
    return C5InterpretationEngine().produce_finding(**arguments)


def test_ut_c5_001_unavailable_overrides_all_lower_rules() -> None:
    finding = _finding(
        [
            _record(assessment_status="UNAVAILABLE"),
            _record(
                worker_id="COMP-W-C2A",
                assessment_status="COMPLETED",
                raw_signal={"violation_count": 9},
            ),
            _record(worker_id="COMP-W-C3D", assessment_status="LOAD_BLOCKED"),
        ]
    )

    assert finding["detection_status"] == "UNAVAILABLE"
    assert finding["interpretation_status"] == "UNAVAILABLE"
    assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
    assert finding["anomaly_not_malicious_non_claim"] == 0


def test_ut_c5_002_load_blocked_maps_to_anomaly() -> None:
    finding = _finding(
        [_record(worker_id="COMP-W-C3D", assessment_status="LOAD_BLOCKED")],
        method_id="C3D",
        access_mode="BLACK_BOX",
    )

    assert finding["detection_status"] == "ANOMALY_DETECTED"
    assert finding["interpretation_status"] == "REQUIRES_INVESTIGATION"
    assert finding["analyst_disposition_prompt"] == "ESCALATE"
    assert finding["anomaly_not_malicious_non_claim"] == 1


def test_ut_c5_003_structural_invalid_maps_to_anomaly() -> None:
    finding = _finding(
        [_record(worker_id="COMP-W-C3C", assessment_status="STRUCTURAL_INVALID")],
        method_id="C3C",
        access_mode="BLACK_BOX",
    )

    assert finding["detection_status"] == "ANOMALY_DETECTED"
    assert finding["interpretation_status"] == "REQUIRES_INVESTIGATION"
    assert finding["analyst_disposition_prompt"] == "ESCALATE"


@pytest.mark.parametrize(
    ("comparison_result", "expected_detection", "expected_interpretation"),
    [
        ("MATCH", "IDENTITY_MATCH", "CONSISTENT_WITH_EXPECTED"),
        ("DIFFERENT", "IDENTITY_DIFFERENT", "IDENTITY_DEVIATION_DETECTED"),
        ("UNAVAILABLE", "UNAVAILABLE", "UNAVAILABLE"),
    ],
)
def test_ut_c5_004_c3b_identity_mapping(
    comparison_result: str,
    expected_detection: str,
    expected_interpretation: str,
) -> None:
    finding = _finding(
        [
            _record(
                worker_id="COMP-W-C3B",
                assessment_status="COMPLETED",
                raw_signal={"comparison_result": comparison_result},
            )
        ],
        method_id="C3B",
        access_mode="BLACK_BOX",
    )

    assert finding["detection_status"] == expected_detection
    assert finding["interpretation_status"] == expected_interpretation


def test_ut_c5_005_c2c_completed_is_statistics_only() -> None:
    finding = _finding(
        [
            _record(
                worker_id="COMP-W-C2C",
                assessment_status="COMPLETED",
                raw_signal={"hhi": 0.5, "shannon_entropy_bits": 1.0},
            )
        ],
        method_id="M06",
    )

    assert finding["detection_status"] == "COMPLETED_STATISTICS_ONLY"
    assert finding["interpretation_status"] == "STATISTICS_REPORTED"
    assert finding["analyst_disposition_prompt"] == "ACCEPT_WITH_CONTEXT"


def test_ut_c5_006_completed_without_violation_uses_default_path() -> None:
    finding = _finding(
        [
            _record(
                worker_id="COMP-W-C2A",
                raw_signal={"violation_count": 0},
            )
        ]
    )

    assert finding["detection_status"] == "NO_ANOMALY_DETECTED"
    assert finding["interpretation_status"] == "NO_ANOMALY_DETECTED"
    assert finding["analyst_disposition_prompt"] == "ACCEPT"


@pytest.mark.parametrize(
    ("worker_id", "signal"),
    [
        ("COMP-W-C2A", {"violation_count": 1}),
        ("COMP-W-C2B", {"duplicate_group_count": 1}),
    ],
)
def test_c2_positive_signal_maps_to_anomaly(worker_id: str, signal: dict) -> None:
    finding = _finding([_record(worker_id=worker_id, raw_signal=signal)])

    assert finding["detection_status"] == "ANOMALY_DETECTED"


def test_ut_c5_007_prohibited_fields_and_states_are_absent() -> None:
    finding = _finding([_record()])
    prohibited_fields = {
        "risk_score",
        "aggregate_assurance",
        "confidence_score",
        "malicious_probability",
        "threat_score",
    }
    prohibited_states = {
        "CLEAN",
        "SAFE",
        "HEALTHY",
        "CONFIRMED_MALICIOUS",
        "PROVEN_ATTACK",
    }

    assert prohibited_fields.isdisjoint(finding)
    assert finding["detection_status"] not in prohibited_states
    assert finding["interpretation_status"] not in prohibited_states
    assert finding["analyst_disposition_prompt"] not in prohibited_states


def test_non_claims_dependencies_and_c3_marker_are_mandatory() -> None:
    finding = _finding(
        [
            _record(worker_id="COMP-W-C2A"),
            _record(worker_id="COMP-W-C3D", assessment_status="LOAD_SUCCESS"),
        ],
        method_id="C3D",
        c4_binding={"pf_002_non_claim": "BOUND_PF_002_NON_CLAIM"},
        access_mode="BLACK_BOX",
    )

    assert finding["coverage_gap_clean_label"] == 1
    assert T05D_NON_CLAIM_TEXT in finding["non_claims"]
    assert finding["dependency_declaration"] == {
        "co_firing_detectors": ["COMP-W-C2A", "COMP-W-C3D"],
        "independence_established": False,
    }
    assert finding["global_backdoor_absence_not_established"] == 1
    assert finding["pf_002_non_claim"] == "BOUND_PF_002_NON_CLAIM"


def test_produced_finding_matches_finding_v1_contract() -> None:
    schema_path = pathlib.Path(__file__).parents[2] / (
        "assurance_system/schema/finding_v1.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = EvidenceSchemaValidator()
    finding = C5InterpretationEngine(validator).produce_finding(
        asset_id="asset-schema",
        method_id="M01",
        evidence_records=[_record(is_synthetic=True)],
        c4_binding=None,
        reference_health="UNAVAILABLE",
        access_mode="UNAVAILABLE",
    )
    task_required_fields = {
        "finding_id",
        "schema_version",
        "asset_id",
        "method_id",
        "detection_status",
        "interpretation_status",
        "applicability_status",
        "raw_signal",
        "reference_health",
        "access_mode",
        "limitations",
        "non_claims",
        "dependency_declaration",
        "coverage_gap_clean_label",
        "anomaly_not_malicious_non_claim",
        "global_backdoor_absence_not_established",
        "pf_002_non_claim",
        "analyst_disposition_prompt",
        "is_synthetic",
        "created_at",
    }

    assert set(schema["required"]).issubset(finding)
    assert task_required_fields.issubset(finding)
    assert finding["schema_version"] == schema["schema_version"] == "v1.0"
    assert uuid.UUID(finding["finding_id"]).version == 4
    created_at = datetime.datetime.fromisoformat(
        finding["created_at"].replace("Z", "+00:00")
    )
    assert created_at.utcoffset() == datetime.timedelta(0)
    assert finding["limitations"] and finding["non_claims"]
    assert finding["is_synthetic"] is True
    assert validator.validate_finding(finding).valid
