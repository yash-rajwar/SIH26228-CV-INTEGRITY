"""
test_integration_stubs.py
Authority: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md TASK-026; §10 §17
All integration tests require GATE-1 (foundation gate) to pass first.
"""
import pytest


@pytest.mark.skip(reason="TASK-026 requires GATE-1 to pass first")
def test_vertical_slice_coco_onnx():
    """VS-001 through VS-007: End-to-end vertical slice with COCO + ONNX assets."""
    pass


@pytest.mark.skip(reason="TASK-026 requires GATE-1 to pass first")
def test_unavailable_propagation_all_injection_points():
    """FIX-013: UNAVAILABLE must propagate at all 4 injection points."""
    pass
