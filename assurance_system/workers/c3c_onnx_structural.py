"""Containment-first ONNX protobuf structural validator."""

# REUSE-009: the R01 loader approach is replaced entirely. This worker uses
# approved ONNX protobuf/checker APIs and never executes a model or imports ORT.

from __future__ import annotations

import os
from typing import Any

from assurance_system.constants import (
    AccessMode,
    AssessmentStatus,
    FIELD_PF_002_NON_CLAIM,
    PF_002_NON_CLAIM,
)
from assurance_system.workers.base import (
    build_worker_output,
    is_within_directory,
    main as worker_main,
)
from assurance_system.workers.c3a_artifact_unit import (
    _external_references as extract_external_references,
    _resolve_external_files as resolve_external_files,
)


WORKER_ID = "COMP-W-C3C"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_MAX_ERROR_DETAIL_CHARS = 512
_PROHIBITED_INPUT_FIELDS = frozenset(
    {"_".join(("key", "path")), "_".join(("db", "path"))}
)
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")

EF_004_NON_CLAIM = (
    "structural_validity_does_not_establish_semantic_equivalence"
)
_PF_002_FIELDS = {
    FIELD_PF_002_NON_CLAIM: PF_002_NON_CLAIM,
    "hash_match_not_safe": True,
    "hash_match_not_semantically_equivalent": True,
    "hash_match_not_causal_execution_proof": True,
}

C3C_LIMITATIONS = [
    "Structural validity is checked via onnx.checker; no model execution occurs.",
    "EF-004: structural validity does not establish semantic equivalence with source model.",
    "Runtime compatibility with a specific inference engine is not tested here.",
]
C3C_NON_CLAIMS = [
    "STRUCTURAL_VALID ≠ semantically equivalent to source model (EF-004).",
    "STRUCTURAL_VALID ≠ safe to execute.",
    "STRUCTURAL_VALID ≠ behavioral battery passed (behavioral battery is DEFERRED_IN_SCOPE).",
    "ONNX_PATH_CONTAINMENT_VIOLATION does not prove malicious intent.",
]


def _contains_prohibited_input(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).casefold()
            if normalized in _PROHIBITED_INPUT_FIELDS or any(
                fragment in normalized for fragment in _PROHIBITED_INPUT_FRAGMENTS
            ):
                return True
            if _contains_prohibited_input(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_prohibited_input(item) for item in value)
    return False


def _raw_signal(
    structural_status: str,
    *,
    opset_version: int | None = None,
    graph_node_count: int | None = None,
    graph_input_names: list[str] | None = None,
    graph_output_names: list[str] | None = None,
    violation_detail: str | None = None,
    violations: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    signal: dict[str, Any] = {
        "structural_status": structural_status,
        "opset_version": opset_version,
        "graph_node_count": graph_node_count,
        "graph_input_names": list(graph_input_names or []),
        "graph_output_names": list(graph_output_names or []),
        "violation_detail": violation_detail,
        "ef_004_non_claim": EF_004_NON_CLAIM,
    }
    if violations is not None:
        signal["violations"] = violations
    return signal


def _output(
    assessment_status: str,
    *,
    raw_signal: dict[str, Any],
    access_mode: str,
    error_detail: str | None = None,
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        access_mode=access_mode,
        artifact_unit_id="UNAVAILABLE",
        limitations=C3C_LIMITATIONS,
        non_claims=C3C_NON_CLAIMS,
        error_detail=(
            error_detail[:_MAX_ERROR_DETAIL_CHARS]
            if isinstance(error_detail, str)
            else error_detail
        ),
        ef_004_non_claim=EF_004_NON_CLAIM,
        **_PF_002_FIELDS,
    )


def _assessment_error(detail: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=_raw_signal("UNAVAILABLE", violation_detail=detail),
        access_mode=AccessMode.UNAVAILABLE,
        error_detail=detail,
    )


def _structural_invalid(detail: str) -> dict[str, Any]:
    bounded_detail = detail[:_MAX_ERROR_DETAIL_CHARS]
    return _output(
        AssessmentStatus.STRUCTURAL_INVALID,
        raw_signal=_raw_signal(
            AssessmentStatus.STRUCTURAL_INVALID,
            violation_detail=bounded_detail,
        ),
        access_mode=AccessMode.BLACK_BOX,
        error_detail=bounded_detail,
    )


def _path_containment_violation(
    model_path: str,
    violations: list[dict[str, str]],
    *,
    parsing_occurred: bool,
) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION,
        raw_signal={
            **_raw_signal(
                "UNAVAILABLE",
                violation_detail="ONNX_PATH_CONTAINMENT_VIOLATION",
                violations=violations,
            ),
            "model_path": model_path,
        },
        access_mode=(
            AccessMode.BLACK_BOX if parsing_occurred else AccessMode.UNAVAILABLE
        ),
    )


def _load_onnx_module():
    import onnx

    return onnx


def _metadata(model: Any) -> tuple[int | None, int | None, list[str], list[str]]:
    try:
        opset = model.opset_import[0].version if model.opset_import else None
        node_count = len(model.graph.node)
        input_names = [item.name for item in model.graph.input]
        output_names = [item.name for item in model.graph.output]
        return opset, node_count, input_names, output_names
    except Exception:
        return None, None, [], []


def _run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(task, dict) or task.get("schema_version") != _WORKER_INPUT_SCHEMA:
        return _assessment_error("UNRECOGNISED_SCHEMA_VERSION")
    if _contains_prohibited_input(task):
        return _assessment_error("PROHIBITED_INPUT_FIELD")

    asset_paths = task.get("asset_paths")
    asset_directory = task.get("asset_directory")
    format_name = task.get("format")
    if (
        not isinstance(asset_paths, list)
        or len(asset_paths) != 1
        or not isinstance(asset_paths[0], str)
        or not asset_paths[0].strip()
        or not isinstance(asset_directory, str)
        or not asset_directory.strip()
        or not isinstance(format_name, str)
        or format_name.strip().upper() != "ONNX"
    ):
        return _assessment_error("INVALID_TASK_INPUT")
    if not os.path.isdir(asset_directory):
        return _assessment_error("ASSET_DIRECTORY_NOT_DIRECTORY")

    model_path = asset_paths[0]
    if not is_within_directory(model_path, asset_directory):
        return _path_containment_violation(
            model_path,
            [{"ref": model_path, "reason": "MODEL_FILE_OUTSIDE_ASSET_DIR"}],
            parsing_occurred=False,
        )

    try:
        onnx_module = _load_onnx_module()
    except ImportError:
        return _assessment_error("ONNX_UNAVAILABLE: HOST-CAP-003")
    except Exception as exc:
        return _assessment_error(f"ONNX_IMPORT_FAILED: {type(exc).__name__}")

    try:
        model = onnx_module.load(model_path, load_external_data=False)
    except Exception as exc:
        return _structural_invalid(f"LOAD_FAILED: {type(exc).__name__}")

    try:
        references, manifest_inconsistencies = extract_external_references(
            model, onnx_module
        )
        _, violations, file_inconsistencies = resolve_external_files(
            references, model_path, asset_directory
        )
    except Exception as exc:
        return _structural_invalid(
            f"EXTERNAL_REFERENCE_SCAN_FAILED: {type(exc).__name__}"
        )

    if violations:
        return _path_containment_violation(
            model_path,
            violations,
            parsing_occurred=True,
        )

    inconsistencies = [*manifest_inconsistencies, *file_inconsistencies]
    if inconsistencies:
        return _structural_invalid(
            f"EXTERNAL_DATA_MANIFEST_INVALID: {len(inconsistencies)} issue(s)"
        )

    try:
        onnx_module.checker.check_model(model)
    except Exception as exc:
        return _structural_invalid(f"CHECKER_FAILED: {type(exc).__name__}")

    opset, node_count, input_names, output_names = _metadata(model)
    return _output(
        AssessmentStatus.STRUCTURAL_VALID,
        raw_signal=_raw_signal(
            AssessmentStatus.STRUCTURAL_VALID,
            opset_version=opset,
            graph_node_count=node_count,
            graph_input_names=input_names,
            graph_output_names=output_names,
        ),
        access_mode=AccessMode.BLACK_BOX,
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Validate ONNX protobuf structure without loading data or executing a graph."""

    try:
        return _run_assessment(task)
    except Exception as exc:
        return _assessment_error(
            f"UNEXPECTED_STRUCTURAL_ERROR: {type(exc).__name__}"
        )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
