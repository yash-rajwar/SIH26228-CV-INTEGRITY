"""Shared worker-side IPC, output, and path-containment contract."""

import argparse
import datetime
import json
import os
import pathlib
import sys
from collections.abc import Callable
from typing import Any

from assurance_system.constants import AccessMode, AssessmentStatus


_WORKER_INPUT_SCHEMA = "worker-input-v1"
_WORKER_OUTPUT_SCHEMA = "worker-output-v1"
_PROHIBITED_OUTPUT_FIELDS = frozenset(
    "_".join(parts)
    for parts in (
        ("risk", "score"),
        ("aggregate", "assurance"),
        ("compromise", "probability"),
        ("overall", "score"),
        ("threat", "score"),
        ("malicious", "probability"),
        ("confidence", "score"),
        ("trust", "score"),
        ("safety", "score"),
    )
)
_PROHIBITED_INPUT_FIELDS = frozenset(
    {"_".join(("key", "path")), "_".join(("db", "path"))}
)
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")


def is_within_directory(path_str: str, base_dir_str: str) -> bool:
    """Return whether a canonical path is contained by a canonical directory."""

    try:
        real_base = os.path.realpath(base_dir_str)
        real_path = os.path.realpath(path_str)
        return real_path == real_base or real_path.startswith(real_base + os.sep)
    except OSError:
        return False


def _validate_nonempty_strings(value: Any, field_name: str) -> None:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError(f"{field_name} must be non-empty")


def _find_prohibited_output_field(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in _PROHIBITED_OUTPUT_FIELDS:
                return key
            found = _find_prohibited_output_field(nested)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for nested in value:
            found = _find_prohibited_output_field(nested)
            if found is not None:
                return found
    return None


def build_worker_output(
    worker_id,
    assessment_status,
    raw_signal,
    limitations,
    non_claims,
    access_mode=AccessMode.UNAVAILABLE,
    artifact_unit_id="UNAVAILABLE",
    dependency_declaration=None,
    error_detail=None,
    **extra_fields,
) -> dict:
    """Construct a complete worker output while enforcing security invariants."""

    _validate_nonempty_strings(limitations, "limitations")
    _validate_nonempty_strings(non_claims, "non_claims")
    if dependency_declaration is None:
        dependency_declaration = {
            "co_firing_detectors": [],
            "independence_established": False,
        }

    candidate = {
        "raw_signal": raw_signal,
        "dependency_declaration": dependency_declaration,
        **extra_fields,
    }
    if _find_prohibited_output_field(candidate) is not None:
        raise ValueError("prohibited aggregate output field")

    output = dict(extra_fields)
    output.update(
        {
            "schema_version": _WORKER_OUTPUT_SCHEMA,
            "worker_id": worker_id,
            "assessment_status": assessment_status,
            "raw_signal": raw_signal,
            "access_mode": access_mode,
            "artifact_unit_id": artifact_unit_id,
            "coverage_gap_clean_label": True,
            "limitations": list(limitations),
            "non_claims": list(non_claims),
            "dependency_declaration": dependency_declaration,
            "assessment_timestamp": (
                datetime.datetime.now(datetime.timezone.utc)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            ),
            "error_detail": error_detail,
        }
    )
    return output


def _find_prohibited_input_field(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold()
            if normalized in _PROHIBITED_INPUT_FIELDS or any(
                fragment in normalized for fragment in _PROHIBITED_INPUT_FRAGMENTS
            ):
                return str(key)
            found = _find_prohibited_input_field(nested)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for nested in value:
            found = _find_prohibited_input_field(nested)
            if found is not None:
                return found
    return None


def _assessment_error(task: dict[str, Any], detail: str) -> dict:
    worker_id = str(task.get("task", "COMP-W-UNKNOWN"))
    return build_worker_output(
        worker_id=worker_id,
        assessment_status=AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=None,
        limitations=["Worker assessment did not complete."],
        non_claims=["No positive assurance conclusion is available."],
        error_detail=detail,
    )


def main(run_assessment_fn: Callable[[dict], dict]) -> None:
    """Run one worker task and write exactly one named-file JSON result."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--result-file", required=True)
    args = parser.parse_args()

    task: dict[str, Any] = {}
    result: dict[str, Any] | None = None
    exit_code = 0
    result_path = pathlib.Path(args.result_file)

    try:
        task_data = pathlib.Path(args.task_file).read_text(encoding="utf-8")
        loaded_task = json.loads(task_data)
        if not isinstance(loaded_task, dict):
            raise ValueError("task input must be a JSON object")
        task = loaded_task
        if task.get("schema_version") != _WORKER_INPUT_SCHEMA:
            raise ValueError("unrecognized worker input schema_version")
        prohibited = _find_prohibited_input_field(task)
        if prohibited is not None:
            raise ValueError("task input contains a prohibited field")

        result = run_assessment_fn(task)
        if not isinstance(result, dict):
            raise ValueError("worker assessment must return a dict")
        if _find_prohibited_output_field(result) is not None:
            raise ValueError("worker assessment returned a prohibited field")
    except Exception as exc:
        exit_code = 1
        result = _assessment_error(task, f"{type(exc).__name__}: {exc}")
        print("Worker assessment failed; details written to result file.", file=sys.stderr)
    finally:
        if result is None:
            result = _assessment_error(task, "Worker produced no result")
            exit_code = 1
        try:
            serialized_result = json.dumps(
                result, sort_keys=True, separators=(",", ":")
            )
        except Exception as exc:
            result = _assessment_error(
                task, f"ResultSerializationError: {type(exc).__name__}: {exc}"
            )
            serialized_result = json.dumps(
                result, sort_keys=True, separators=(",", ":")
            )
            exit_code = 1
        try:
            result_path.write_text(
                serialized_result,
                encoding="utf-8",
            )
        except Exception as exc:
            print(f"Unable to write worker result file: {exc}", file=sys.stderr)
            exit_code = 1

    if exit_code:
        raise SystemExit(exit_code)
