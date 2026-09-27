"""
test_negative_stubs.py
Authority: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md §10 §17
Negative tests: system must fail correctly on invalid inputs, hostile assets, bad schemas.
"""
import pytest


@pytest.mark.skip(reason="TASK-008 schema validator not yet implemented")
def test_schema_rejects_risk_score_field():
    """Schema validator must reject any record containing risk_score."""
    pass


@pytest.mark.skip(reason="TASK-008 schema validator not yet implemented")
def test_schema_rejects_coverage_gap_false():
    """Schema validator must reject C2/C3 records where coverage_gap_clean_label=0."""
    pass
