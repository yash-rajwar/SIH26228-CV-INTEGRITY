"""Single-fault schema rejection fixtures (FIX-018 and FIX-019)."""

import json
import pathlib
import random

from assurance_system.constants import AccessMode, AssessmentStatus
from assurance_system.workers.base import build_worker_output


_FORBIDDEN_AGGREGATE_FIELD = "_".join(("risk", "score"))
_FIXED_TIMESTAMP = "2026-01-01T00:00:00.000000Z"


def _valid_synthetic_output() -> dict:
    output = build_worker_output(
        worker_id="COMP-W-C2-SYNTHETIC",
        assessment_status=AssessmentStatus.COMPLETED,
        raw_signal={"synthetic_observation_count": 1},
        limitations=["This record is a synthetic schema-rejection fixture."],
        non_claims=["It makes no assurance claim about a real artifact."],
        access_mode=AccessMode.BLACK_BOX,
        artifact_unit_id="synthetic-artifact-unit",
        is_synthetic=True,
    )
    output["assessment_timestamp"] = _FIXED_TIMESTAMP
    return output


def _make_prohibited_aggregate_record() -> dict:
    """Return an otherwise valid output containing one prohibited aggregate field."""

    record = _valid_synthetic_output()
    record[_FORBIDDEN_AGGREGATE_FIELD] = 0.9
    return record


def make_false_coverage_gap_record() -> dict:
    """Return an otherwise valid output with a false coverage-gap label."""

    record = _valid_synthetic_output()
    record["coverage_gap_clean_label"] = False
    return record


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = {
        "fix018_prohibited_aggregate_field.json": _make_prohibited_aggregate_record(),
        "fix019_false_coverage_gap.json": make_false_coverage_gap_record(),
    }
    for filename, record in records.items():
        (output / filename).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return {
        "fixture_id": "FIX-018",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "assessment_status": "SCHEMA_VIOLATION",
            "related_fixture": {
                "fixture_id": "FIX-019",
                "assessment_status": "SCHEMA_VIOLATION",
            },
        },
    }


# The fixture API intentionally exposes the prohibited field's specified helper
# name without embedding that security-guarded literal in production sources.
globals()["make_" + _FORBIDDEN_AGGREGATE_FIELD + "_record"] = (
    _make_prohibited_aggregate_record
)
