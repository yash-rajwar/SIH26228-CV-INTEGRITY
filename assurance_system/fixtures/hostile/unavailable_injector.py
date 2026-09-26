"""Synthetic UNAVAILABLE propagation helpers (FIX-013)."""

import copy
import json
import pathlib
import random

from assurance_system.constants import AccessMode, AssessmentStatus, SigningStatus
from assurance_system.workers.base import build_worker_output


def inject_unavailable_at_ingestion(task_spec: dict) -> dict:
    modified = copy.deepcopy(task_spec)
    modified["is_synthetic"] = True
    modified["injected_assessment_status"] = AssessmentStatus.UNAVAILABLE
    modified["injected_failure_point"] = "INGESTION"
    return modified


def _unavailable_worker_output(worker_id: str, access_mode: str) -> dict:
    output = build_worker_output(
        worker_id=worker_id,
        assessment_status=AssessmentStatus.UNAVAILABLE,
        raw_signal=None,
        limitations=["Synthetic dependency unavailability was injected."],
        non_claims=["No positive assurance conclusion is available."],
        access_mode=access_mode,
        is_synthetic=True,
    )
    output["assessment_timestamp"] = "2026-01-01T00:00:00.000000Z"
    return output


def inject_unavailable_at_c2_output() -> dict:
    return _unavailable_worker_output("COMP-W-C2-SYNTHETIC", AccessMode.UNAVAILABLE)


def inject_unavailable_at_c3_output() -> dict:
    return _unavailable_worker_output("COMP-W-C3-SYNTHETIC", AccessMode.UNAVAILABLE)


def inject_unavailable_at_c4_output() -> dict:
    return {
        "schema_version": "v1.0",
        "signing_status": SigningStatus.SIGNING_UNAVAILABLE,
        "signature": None,
        "is_synthetic": True,
        "limitations": ["Synthetic signing unavailability was injected."],
        "non_claims": ["No signed provenance assertion is available."],
    }


def generate(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = {
        "ingestion.json": inject_unavailable_at_ingestion(
            {"schema_version": "worker-input-v1", "task": "SYNTHETIC"}
        ),
        "c2_output.json": inject_unavailable_at_c2_output(),
        "c3_output.json": inject_unavailable_at_c3_output(),
        "c4_output.json": inject_unavailable_at_c4_output(),
    }
    for filename, record in records.items():
        (output / filename).write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return {
        "fixture_id": "FIX-013",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "assessment_status": AssessmentStatus.UNAVAILABLE,
            "signing_status": SigningStatus.SIGNING_UNAVAILABLE,
            "injection_points": ["INGESTION", "C2", "C3", "C4"],
        },
    }
