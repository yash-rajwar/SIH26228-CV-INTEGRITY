"""Containment-first model artifact-unit resolver."""

# REUSE-008: the artifact hashing concept is hardened and reimplemented here.
# No R01 source code is copied; this worker resolves files but never hashes or loads code.

from __future__ import annotations

import os
import pathlib
from collections.abc import Iterator
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


WORKER_ID = "COMP-W-C3A"
PYTORCH_ARTIFACT_UNIT_DEFINITION_ID = "pytorch-single-file-v1"
ONNX_ARTIFACT_UNIT_DEFINITION_ID: str | None = None

_WORKER_INPUT_SCHEMA = "worker-input-v1"
_PYTORCH_SUFFIXES = frozenset({".pt", ".pth"})
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")
_MAX_ERROR_DETAIL_CHARS = 512

_PF_002_FIELDS = {
    FIELD_PF_002_NON_CLAIM: PF_002_NON_CLAIM,
    "hash_match_not_safe": True,
    "hash_match_not_semantically_equivalent": True,
    "hash_match_not_causal_execution_proof": True,
}

_BASE_NON_CLAIMS = [
    "Artifact-unit resolution does not establish model safety or absence of backdoors.",
    "A later digest match would establish byte identity only, not semantic equivalence or causal execution proof.",
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


def _output(
    assessment_status: str,
    *,
    raw_signal: dict[str, Any] | None,
    access_mode: str,
    artifact_unit_id: str = "UNAVAILABLE",
    limitations: list[str],
    non_claims: list[str] | None = None,
    error_detail: str | None = None,
    **extra_fields: Any,
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        access_mode=access_mode,
        artifact_unit_id=artifact_unit_id,
        limitations=limitations,
        non_claims=list(non_claims or _BASE_NON_CLAIMS),
        error_detail=(
            error_detail[:_MAX_ERROR_DETAIL_CHARS]
            if isinstance(error_detail, str)
            else error_detail
        ),
        **_PF_002_FIELDS,
        **extra_fields,
    )


def _assessment_error(detail: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=None,
        access_mode=AccessMode.UNAVAILABLE,
        limitations=["Artifact-unit resolution did not complete."],
        non_claims=[
            *_BASE_NON_CLAIMS,
            "No artifact-unit identity is available from this failed assessment.",
        ],
        error_detail=detail,
    )


def _ambiguous_output(
    reason: str,
    *,
    artifact_unit: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
    access_mode: str = AccessMode.UNAVAILABLE,
) -> dict[str, Any]:
    raw_signal: dict[str, Any] = {"reason": reason}
    if artifact_unit is not None:
        raw_signal["artifact_unit"] = artifact_unit
    return _output(
        AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS,
        raw_signal=raw_signal,
        access_mode=access_mode,
        limitations=limitations
        or ["The complete artifact unit could not be frozen deterministically."],
        non_claims=[
            *_BASE_NON_CLAIMS,
            "ARTIFACT_UNIT_AMBIGUOUS means hash-dependent methods are UNAVAILABLE.",
        ],
    )


def _onnx_path_violation(
    model_path: str, *, ref: str, reason: str
) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION,
        raw_signal={
            "model_path": model_path,
            "violations": [{"ref": ref, "reason": reason}],
        },
        access_mode=AccessMode.UNAVAILABLE,
        limitations=[
            "Path containment violation detected; the model pipeline is blocked."
        ],
        non_claims=[
            *_BASE_NON_CLAIMS,
            "ONNX_PATH_CONTAINMENT_VIOLATION does not prove malicious intent.",
        ],
    )


def _load_onnx_module():
    import onnx

    return onnx


def _iter_tensor_protos(message: Any) -> Iterator[Any]:
    """Yield every TensorProto reachable through protobuf message fields."""

    descriptor = getattr(message, "DESCRIPTOR", None)
    if descriptor is None:
        return
    if getattr(descriptor, "full_name", None) == "onnx.TensorProto":
        yield message
        return

    for field, value in message.ListFields():
        if field.type != field.TYPE_MESSAGE:
            continue
        if field.label == field.LABEL_REPEATED:
            for item in value:
                yield from _iter_tensor_protos(item)
        else:
            yield from _iter_tensor_protos(value)


def _external_references(model_proto: Any, onnx_module: Any) -> tuple[list[str], list[str]]:
    references: list[str] = []
    inconsistencies: list[str] = []
    external_value = onnx_module.TensorProto.EXTERNAL

    for tensor in _iter_tensor_protos(model_proto):
        if tensor.data_location != external_value:
            continue
        locations = [
            item.value
            for item in tensor.external_data
            if item.key == "location" and isinstance(item.value, str)
        ]
        if len(locations) != 1 or not locations[0].strip():
            tensor_name = tensor.name or "UNNAMED_TENSOR"
            inconsistencies.append(f"EXTERNAL_DATA_LOCATION_INVALID:{tensor_name}")
            continue
        references.append(locations[0])

    return references, inconsistencies


def _is_absolute_reference(reference: str) -> bool:
    normalized = reference.replace("\\", "/")
    windows_path = pathlib.PureWindowsPath(reference)
    return (
        os.path.isabs(reference)
        or pathlib.PurePosixPath(normalized).is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
    )


def _resolve_external_files(
    references: list[str], model_path: str, asset_directory: str
) -> tuple[list[str], list[dict[str, str]], list[str]]:
    resolved_paths: list[str] = []
    violations: list[dict[str, str]] = []
    inconsistencies: list[str] = []
    model_directory = os.path.dirname(model_path)

    for reference in references:
        normalized = reference.replace("\\", "/")
        if _is_absolute_reference(reference):
            violations.append({"ref": reference, "reason": "ABSOLUTE_PATH"})
            continue
        if ".." in normalized.split("/"):
            violations.append({"ref": reference, "reason": "TRAVERSAL_PATTERN"})
            continue

        unresolved_path = os.path.join(model_directory, reference)
        if not is_within_directory(unresolved_path, asset_directory):
            violations.append({"ref": reference, "reason": "SYMLINK_ESCAPE"})
            continue
        candidate_real = os.path.realpath(unresolved_path)
        if not is_within_directory(candidate_real, asset_directory):
            violations.append({"ref": reference, "reason": "SYMLINK_ESCAPE"})
            continue
        if not os.path.isfile(candidate_real):
            inconsistencies.append(f"EXTERNAL_FILE_MISSING:{reference}")
            continue
        resolved_paths.append(candidate_real)

    return sorted(set(resolved_paths)), violations, inconsistencies


def resolve_onnx_artifact_unit(
    model_path: str, asset_directory: str
) -> dict[str, Any]:
    """Resolve an ONNX file manifest without loading any external tensor bytes."""

    if not is_within_directory(model_path, asset_directory):
        return _onnx_path_violation(
            model_path,
            ref=model_path,
            reason="MODEL_FILE_OUTSIDE_ASSET_DIR",
        )

    model_real = os.path.realpath(model_path)
    if not is_within_directory(model_real, asset_directory):
        return _onnx_path_violation(
            model_path,
            ref=model_path,
            reason="MODEL_FILE_OUTSIDE_ASSET_DIR",
        )
    if not os.path.isfile(model_real):
        return _assessment_error("MODEL_FILE_NOT_REGULAR_OR_MISSING")

    try:
        onnx_module = _load_onnx_module()
    except ImportError:
        return _assessment_error("ONNX_UNAVAILABLE: HOST-CAP-003")
    except Exception as exc:
        return _assessment_error(f"ONNX_IMPORT_FAILED: {type(exc).__name__}")

    try:
        model_proto = onnx_module.load(model_real, load_external_data=False)
    except Exception as exc:
        return _assessment_error(f"ONNX_LOAD_HEADER_FAILED: {type(exc).__name__}")

    references, manifest_inconsistencies = _external_references(
        model_proto, onnx_module
    )
    external_files, violations, file_inconsistencies = _resolve_external_files(
        references, model_real, asset_directory
    )
    if violations:
        return _output(
            AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION,
            raw_signal={"model_path": model_real, "violations": violations},
            access_mode=AccessMode.UNAVAILABLE,
            limitations=[
                "Path containment violation detected; the model pipeline is blocked."
            ],
            non_claims=[
                *_BASE_NON_CLAIMS,
                "ONNX_PATH_CONTAINMENT_VIOLATION does not prove malicious intent.",
            ],
        )

    artifact_unit = {
        "main_file": model_real,
        "external_files": external_files,
        "artifact_unit_definition_id": (
            ONNX_ARTIFACT_UNIT_DEFINITION_ID or "UNAVAILABLE"
        ),
    }
    inconsistencies = [*manifest_inconsistencies, *file_inconsistencies]
    if inconsistencies:
        return _ambiguous_output(
            ";".join(inconsistencies),
            artifact_unit=artifact_unit,
            access_mode=AccessMode.BLACK_BOX,
            limitations=[
                "The ONNX external-data manifest is incomplete or inconsistent."
            ],
        )

    if ONNX_ARTIFACT_UNIT_DEFINITION_ID is None:
        return _ambiguous_output(
            "ONNX_ARTIFACT_UNIT_DEFINITION_ID_UNAVAILABLE",
            artifact_unit=artifact_unit,
            access_mode=AccessMode.BLACK_BOX,
            limitations=[
                "Artifact-unit definition ID is UNAVAILABLE pending SP-002."
            ],
        )

    return _output(
        AssessmentStatus.COMPLETED,
        raw_signal={"artifact_unit": artifact_unit},
        access_mode=AccessMode.BLACK_BOX,
        artifact_unit_id=ONNX_ARTIFACT_UNIT_DEFINITION_ID,
        limitations=[
            "Artifact-unit resolution checks file membership and containment only."
        ],
    )


def resolve_pytorch_artifact_unit(
    model_path: str, asset_directory: str
) -> dict[str, Any]:
    """Apply the frozen PRE-03 single-file definition without importing Torch."""

    if not is_within_directory(model_path, asset_directory):
        return _ambiguous_output(
            "MODEL_FILE_OUTSIDE_ASSET_DIR",
            limitations=["The PyTorch model path is outside the submitted asset directory."],
        )

    model_real = os.path.realpath(model_path)
    if not is_within_directory(model_real, asset_directory):
        return _ambiguous_output(
            "MODEL_FILE_OUTSIDE_ASSET_DIR",
            limitations=["The PyTorch model path is outside the submitted asset directory."],
        )
    if not os.path.isfile(model_real):
        return _ambiguous_output(
            "MODEL_FILE_NOT_REGULAR_OR_MISSING",
            limitations=["The PyTorch artifact must be one existing regular file."],
        )
    if pathlib.Path(model_real).suffix.casefold() not in _PYTORCH_SUFFIXES:
        return _output(
            AssessmentStatus.UNSUPPORTED,
            raw_signal={
                "reason": "PYTORCH_SUFFIX_NOT_SUPPORTED_BY_DEFINITION",
                "artifact_unit_definition_id": PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
            },
            access_mode=AccessMode.UNAVAILABLE,
            artifact_unit_id=PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
            limitations=[
                "pytorch-single-file-v1 applies only to regular .pt or .pth files."
            ],
        )

    artifact_unit = {
        "main_file": model_real,
        "external_files": [],
        "artifact_unit_definition_id": PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
    }
    return _output(
        AssessmentStatus.COMPLETED,
        raw_signal={"artifact_unit": artifact_unit},
        access_mode=AccessMode.BLACK_BOX,
        artifact_unit_id=PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
        limitations=[
            "pytorch-single-file-v1 excludes companion configuration, source, and separately stored optimizer state."
        ],
        non_claims=[
            *_BASE_NON_CLAIMS,
            "Resolving one .pt or .pth file does not establish that it is sufficient to reconstruct or execute a model.",
        ],
    )


def resolve_torchscript_artifact_unit(model_path: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.DEFERRED_IN_SCOPE,
        raw_signal={"model_path": model_path, "format": "TORCHSCRIPT"},
        access_mode=AccessMode.UNAVAILABLE,
        limitations=["TorchScript format is DEFERRED_IN_SCOPE at MVP."],
        non_claims=[
            *_BASE_NON_CLAIMS,
            "DEFERRED_IN_SCOPE does not mean TorchScript was assessed and found acceptable.",
        ],
        deferral_reason=(
            "TorchScript loading: isolated worker not demonstrated on target host"
        ),
    )


def _run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Resolve exactly one submitted model artifact according to its declared format."""

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
        or not asset_paths[0]
        or not isinstance(asset_directory, str)
        or not asset_directory
        or not isinstance(format_name, str)
        or not format_name.strip()
    ):
        return _assessment_error("INVALID_TASK_INPUT")
    if not os.path.isdir(asset_directory):
        return _assessment_error("ASSET_DIRECTORY_NOT_DIRECTORY")

    model_path = asset_paths[0]
    normalized_format = format_name.strip().upper()
    if normalized_format == "ONNX":
        return resolve_onnx_artifact_unit(model_path, asset_directory)
    if normalized_format == "PYTORCH":
        return resolve_pytorch_artifact_unit(model_path, asset_directory)
    if normalized_format == "TORCHSCRIPT":
        return resolve_torchscript_artifact_unit(model_path)

    return _output(
        AssessmentStatus.UNSUPPORTED,
        raw_signal={"format": normalized_format},
        access_mode=AccessMode.UNAVAILABLE,
        limitations=[f"Model format {normalized_format} is not supported by COMP-W-C3A."],
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Return a C3A-contract result for every resolver outcome."""

    try:
        return _run_assessment(task)
    except Exception as exc:
        return _assessment_error(
            f"UNEXPECTED_RESOLUTION_ERROR: {type(exc).__name__}"
        )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
