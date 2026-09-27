"""Negative tests for fail-closed UNAVAILABLE propagation through COMP-C5."""

from __future__ import annotations

import pytest

from assurance_system.fixtures.hostile.unavailable_injector import (
    inject_unavailable_at_c2_output,
    inject_unavailable_at_c3_output,
)
from assurance_system.supervisor.interpretation import C5InterpretationEngine


def _anomaly_record() -> dict:
    return {
        "worker_id": "COMP-W-C2A",
        "assessment_status": "COMPLETED",
        "raw_signal": {"violation_count": 4},
        "limitations": ["Synthetic anomaly evidence."],
        "non_claims": ["Synthetic evidence does not establish intent."],
        "is_synthetic": True,
    }


@pytest.mark.parametrize(
    "unavailable_record",
    [inject_unavailable_at_c2_output(), inject_unavailable_at_c3_output()],
    ids=["c2-unavailable", "c3-unavailable"],
)
def test_fix_013_unavailable_overrides_anomaly(
    unavailable_record: dict,
) -> None:
    finding = C5InterpretationEngine().produce_finding(
        asset_id="fix-013",
        method_id="FIX-013",
        evidence_records=[_anomaly_record(), unavailable_record],
        c4_binding=None,
        reference_health="UNAVAILABLE",
        access_mode="UNAVAILABLE",
    )

    assert finding["detection_status"] == "UNAVAILABLE"
    assert finding["interpretation_status"] == "UNAVAILABLE"
    assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
    assert finding["coverage_gap_clean_label"] == 1
    assert finding["is_synthetic"] is True


@pytest.mark.parametrize(
    "failure_status",
    [
        "ASSESSMENT_ERROR",
        "UNAVAILABLE",
        "ARTIFACT_UNIT_AMBIGUOUS",
        "LOAD_ERROR",
        "REFERENCE_UNAVAILABLE",
    ],
)
def test_every_fail_state_has_priority_over_lower_rules(
    failure_status: str,
) -> None:
    failing_record = {
        "worker_id": "COMP-W-C3B",
        "assessment_status": failure_status,
        "raw_signal": {"comparison_result": "DIFFERENT"},
        "limitations": ["Synthetic upstream failure."],
        "non_claims": ["No positive interpretation is available."],
        "is_synthetic": True,
    }
    finding = C5InterpretationEngine().produce_finding(
        asset_id="fix-013-failure",
        method_id="FIX-013",
        evidence_records=[failing_record, _anomaly_record()],
        c4_binding=None,
        reference_health="UNAVAILABLE",
        access_mode="UNAVAILABLE",
    )

    assert finding["detection_status"] == "UNAVAILABLE"
    assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
    assert finding["anomaly_not_malicious_non_claim"] == 0
