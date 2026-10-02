"""
test_security_invariants.py
Authority: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md §14 GATE-1, GATE-3
           10_TECHNICAL_SPECIFICATION_SIH26228.md §17

STUB — tests will be implemented as implementation progresses.
All security tests require TASK-009 (hostile fixture suite) to be complete first.
"""
import pytest
import pathlib


REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def _source_matches(pattern: str) -> list[str]:
    """Return deterministic Python-source matches without a shell dependency."""

    matches = []
    for path in sorted((REPO_ROOT / "assurance_system").rglob("*.py")):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if pattern in line:
                matches.append(f"{path.relative_to(REPO_ROOT)}:{line_number}:{line}")
    return matches


def test_no_weights_only_false_in_codebase():
    """
    SEC-007: weights_only=False must never appear in any code path.
    This test must pass from Day 1 and must never be disabled.
    Authority: 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md MB-25; D-MVP-005
    """
    matches = _source_matches("weights_only=False")
    assert not matches, (
        "SECURITY VIOLATION: weights_only=False found in codebase.\n"
        "Matches:\n" + "\n".join(matches) +
        "\nThis is an absolute prohibition. See: RC-013 REJECTED; §09 §1.4"
    )


def test_no_risk_score_field_in_codebase():
    """
    Aggregate risk score / compromise probability is absolutely prohibited.
    Authority: §09 §1.4 NB-02; G-07
    """
    for pattern in ["risk_score", "compromise_probability", "overall_assurance_score"]:
        # Only fail if the pattern appears as a field being SET or emitted — not in prohibition comments
        # Simple check: no match at all is cleanest
        matches = [
            line for line in _source_matches(pattern)
            if not line.strip().startswith("#") and pattern in line
        ]
        assert not matches, (
            f"PROHIBITED FIELD found: '{pattern}'\n"
            "Matches:\n" + "\n".join(matches) +
            "\nThis field is absolutely prohibited. See: §09 §1.4 NB-02"
        )


@pytest.mark.skip(reason="TASK-009 hostile fixtures not yet built")
def test_hostile_pickle_blocked():
    """SEC-001: Hostile pickle payload must be blocked by c3d_safe_load worker."""
    pass


@pytest.mark.skip(reason="TASK-009 hostile fixtures not yet built")
def test_onnx_path_traversal_blocked():
    """SEC-002: Path-traversal ONNX must be rejected by c3c_onnx_structural worker."""
    pass


@pytest.mark.skip(reason="TASK-009 hostile fixtures not yet built")
def test_unavailable_does_not_become_clean():
    """SEC/FIX-013: UNAVAILABLE must propagate; must never be compressed to CLEAN."""
    pass


@pytest.mark.skip(reason="TASK-006 audit chain not yet implemented")
def test_audit_chain_corrupt_on_modification():
    """SEC-010: Modifying an audit record must cause CHAIN_CORRUPT to be reported."""
    pass
