import inspect

from assurance_system import constants
from assurance_system.constants import AssessmentStatus, AuditEventType


def _public_string_values(group):
    return [
        value
        for name, value in vars(group).items()
        if not name.startswith("_") and isinstance(value, str)
    ]


def test_no_duplicate_assessment_status_values():
    values = _public_string_values(AssessmentStatus)
    assert len(values) == len(set(values)), "Duplicate assessment status values"


def test_assessment_status_matches_pre04_contract():
    expected = {
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
    assert set(_public_string_values(AssessmentStatus)) == expected


def test_prohibited_positive_state_literals_absent():
    source = inspect.getsource(constants)
    for name in ("CLEAN", "SAFE", "HEALTHY"):
        assert f'= "{name}"' not in source
        assert f"= '{name}'" not in source


def test_unavailable_exists_as_constant():
    assert AssessmentStatus.UNAVAILABLE == "UNAVAILABLE"


def test_pf_002_non_claim_is_exact_and_untruncated():
    expected = (
        "Cryptographic signature establishes that this record was produced and not modified "
        "after signing under accepted-key assumptions. It does NOT establish: "
        "(a) that the named model executed the assessed inferences (PF-002); "
        "(b) that the assessment was accurate; "
        "(c) that the signing key was not compromised; or "
        "(d) that the system producing this record was not itself compromised."
    )
    assert constants.PF_002_NON_CLAIM == expected
    assert len(constants.PF_002_NON_CLAIM) > 200


def test_audit_event_types_complete():
    required = {
        "PIPELINE_RUN_START",
        "PIPELINE_RUN_COMPLETE",
        "PIPELINE_RUN_ERROR",
        "WORKER_DISPATCHED",
        "WORKER_RESULT_ACCEPTED",
        "WORKER_RESULT_REJECTED_SCHEMA_VIOLATION",
        "EVIDENCE_RECORD_WRITTEN",
        "FINDING_WRITTEN",
        "PROVENANCE_RECORD_WRITTEN",
        "DEFERRED_IN_SCOPE_EMITTED",
        "REFERENCE_HEALTH_TRANSITION",
        "SIGNING_UNAVAILABLE",
        "SEQUENCE_GAP_DETECTED",
        "CHAIN_CORRUPT",
        "ANALYST_DISPOSITION",
        "CAPABILITY_DECLARATION_EMITTED",
        "UNAVAILABLE_PROPAGATED",
        "REPLAY_ATTEMPT_DETECTED",
    }
    assert set(_public_string_values(AuditEventType)) == required


def test_prohibited_aggregate_field_name_absent():
    parts = ("risk", "score")
    assert "_".join(parts) not in inspect.getsource(constants)
