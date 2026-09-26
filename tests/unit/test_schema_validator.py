"""UT-SCHEMA-001 through UT-SCHEMA-008."""

import copy
import datetime

from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator


def _valid_worker_output(worker_id="COMP-W-C2A", status="COMPLETED"):
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "schema_version": "worker-output-v1",
        "worker_id": worker_id,
        "assessment_status": status,
        "raw_signal": {"count": 1},
        "access_mode": "BLACK_BOX",
        "artifact_unit_id": "UNAVAILABLE",
        "coverage_gap_clean_label": True,
        "limitations": ["test limitation"],
        "non_claims": ["test non-claim"],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "assessment_timestamp": timestamp,
        "error_detail": None,
    }


def test_ut_schema_001_valid_c2_output_passes():
    result = EvidenceSchemaValidator().validate_worker_output(
        _valid_worker_output(), "C2A_STRUCTURAL"
    )
    assert result.valid is True
    assert result.reason is None


def test_ut_schema_002_missing_required_field_fails():
    record = _valid_worker_output()
    del record["artifact_unit_id"]
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is False
    assert "artifact_unit_id" in result.reason


def test_ut_schema_003_prohibited_aggregate_field_fails():
    record = _valid_worker_output()
    record["risk_score"] = 0.9
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is False
    assert "risk_score" in result.reason


def test_ut_schema_004_false_clean_label_fails():
    record = _valid_worker_output()
    record["coverage_gap_clean_label"] = False
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is False
    assert "coverage_gap_clean_label" in result.reason


def test_ut_schema_005_null_c3_access_mode_fails():
    record = _valid_worker_output(worker_id="COMP-W-C3A")
    record["access_mode"] = None
    result = EvidenceSchemaValidator().validate_worker_output(record, "C3A_ARTIFACT_UNIT")
    assert result.valid is False
    assert "access_mode" in result.reason


def test_ut_schema_006_invalid_assessment_status_fails():
    record = _valid_worker_output(status="INVALID_MADE_UP_VALUE")
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is False
    assert "assessment_status" in result.reason


def test_ut_schema_007_unavailable_status_is_valid():
    record = _valid_worker_output(status="UNAVAILABLE")
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is True


def test_ut_schema_008_complete_valid_output_passes():
    record = copy.deepcopy(_valid_worker_output())
    result = EvidenceSchemaValidator().validate_worker_output(record, "C2A_STRUCTURAL")
    assert result.valid is True
