import json
import math

from assurance_system.constants import AssessmentStatus, IdentityQuality
from assurance_system.fixtures.hostile import sybil_corpus
from assurance_system.workers import c2c_concentration


def _records(source_counts: dict[str, int]) -> list[dict[str, str]]:
    return [
        {"item_id": f"{source}-{index}", "contributor_id": source}
        for source, count in source_counts.items()
        for index in range(count)
    ]


def _task(
    contributor_metadata: list[dict[str, str]],
    identity_quality: str = IdentityQuality.UNTRUSTED,
) -> dict:
    return {
        "schema_version": "worker-input-v1",
        "task": "C2C_CONCENTRATION",
        "contributor_metadata": contributor_metadata,
        "identity_quality": identity_quality,
    }


def _keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _keys(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _keys(nested)


def test_ut_c2c_001_two_equal_share_sources():
    result = c2c_concentration.run_assessment(_task(_records({"A": 5, "B": 5})))
    signal = result["raw_signal"]

    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert math.isclose(signal["hhi"], 0.5, rel_tol=1e-9)
    assert math.isclose(signal["shannon_entropy_bits"], 1.0, rel_tol=1e-9)
    assert signal["sybil_unreliable"] is True


def test_ut_c2c_002_single_source():
    result = c2c_concentration.run_assessment(_task(_records({"A": 10})))
    signal = result["raw_signal"]

    assert signal["hhi"] == 1.0
    assert signal["shannon_entropy_bits"] == 0.0
    assert signal["sybil_unreliable"] is True


def test_ut_c2c_003_missing_contributor_metadata_is_assessment_error():
    result = c2c_concentration.run_assessment(_task([]))

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["assessment_status"] != AssessmentStatus.COMPLETED
    assert result["raw_signal"] is None
    assert result["error_detail"] == "No contributor metadata available"


def test_ut_c2c_004_trusted_identity_disables_sybil_unreliable():
    result = c2c_concentration.run_assessment(
        _task(_records({"A": 10}), IdentityQuality.TRUSTED)
    )

    assert result["raw_signal"]["sybil_unreliable"] is False


def test_ut_c2c_005_untrusted_identity_keeps_sybil_unreliable():
    result = c2c_concentration.run_assessment(
        _task(_records({"A": 10}), IdentityQuality.UNTRUSTED)
    )

    assert result["raw_signal"]["sybil_unreliable"] is True


def test_ut_c2c_006_prohibited_scoring_fields_are_absent():
    result = c2c_concentration.run_assessment(_task(_records({"A": 5, "B": 5})))
    prohibited = {
        "risk_score",
        "aggregate_assurance",
        "compromise_probability",
        "threat_score",
        "malicious_probability",
        "confidence_score",
        "trust_score",
        "safety_score",
    }

    assert prohibited.isdisjoint(set(_keys(result)))
    assert result["coverage_gap_clean_label"] is True
    assert result["limitations"] == c2c_concentration.C2C_LIMITATIONS
    assert result["non_claims"] == c2c_concentration.C2C_NON_CLAIMS


def test_fix_012_manifest_and_corpus_match_worker_output(tmp_path):
    manifest = sybil_corpus.generate(str(tmp_path), seed=42)
    metadata = json.loads((tmp_path / "single_source.json").read_text(encoding="utf-8"))

    result = c2c_concentration.run_assessment(_task(metadata))
    expected = manifest["expected_result"]

    assert result["raw_signal"]["sybil_unreliable"] is expected[
        "expected_sybil_unreliable"
    ]
    assert math.isclose(
        result["raw_signal"]["hhi"], expected["expected_hhi"], rel_tol=1e-9
    )
    assert math.isclose(
        result["raw_signal"]["shannon_entropy_bits"],
        expected["expected_entropy"],
        rel_tol=1e-9,
    )


def test_prohibited_input_is_rejected_recursively():
    task = _task(_records({"A": 1}))
    task["nested"] = {"api_secret": "not-a-real-secret"}

    result = c2c_concentration.run_assessment(task)

    assert result["assessment_status"] == AssessmentStatus.ASSESSMENT_ERROR
    assert result["raw_signal"] is None
    assert result["error_detail"] == "Prohibited input field detected"
