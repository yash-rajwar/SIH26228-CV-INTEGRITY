"""SEC-011 and SEC-012 schema-gate security tests."""

import datetime
from unittest.mock import Mock

from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator


def _valid_c2_record():
    return {
        "schema_version": "worker-output-v1",
        "worker_id": "COMP-W-C2A",
        "assessment_status": "COMPLETED",
        "raw_signal": {"violations": []},
        "access_mode": "BLACK_BOX",
        "artifact_unit_id": "UNAVAILABLE",
        "coverage_gap_clean_label": True,
        "limitations": ["test limitation"],
        "non_claims": ["test non-claim"],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "assessment_timestamp": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "error_detail": None,
    }


def _write_only_if_valid(validator, store, record):
    result = validator.validate_worker_output(record, "C2A_STRUCTURAL")
    if result.valid:
        store.write_evidence_record(record)
    return result


def test_sec_011_nested_prohibited_field_never_reaches_store():
    validator = EvidenceSchemaValidator()
    store = Mock()
    record = _valid_c2_record()
    record["raw_signal"]["analysis"] = {"risk_score": 0.5}

    paths = validator._recursive_prohibited_scan(record)
    result = _write_only_if_valid(validator, store, record)

    assert any("risk_score" in path for path in paths)
    assert result.valid is False
    store.write_evidence_record.assert_not_called()


def test_sec_012_non_boolean_clean_label_never_reaches_store():
    validator = EvidenceSchemaValidator()
    store = Mock()
    record = _valid_c2_record()
    record["coverage_gap_clean_label"] = 0

    result = _write_only_if_valid(validator, store, record)

    assert result.valid is False
    store.write_evidence_record.assert_not_called()
