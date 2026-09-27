"""PyTorch restricted safe-loading gate for untrusted model artifacts."""

from __future__ import annotations

import os
import pickle
from typing import Any

from assurance_system.constants import (
    AccessMode,
    AssessmentStatus,
    FIELD_PF_002_NON_CLAIM,
    IdentityQuality,
    PF_002_NON_CLAIM,
)
from assurance_system.workers.base import (
    build_worker_output,
    is_within_directory,
    main as base_main,
)


WORKER_ID = "COMP-W-C3D"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_TASK_NAME = "C3D_SAFE_LOAD"
_PYTORCH_FORMAT = "PYTORCH"
_PYTORCH_ARTIFACT_UNIT_DEFINITION_ID = "pytorch-single-file-v1"
_PYTORCH_SUFFIXES = frozenset({".pt", ".pth"})
_RESOURCE_LIMIT_KEYS = frozenset({"timeout_s", "memory_mb", "max_fds"})
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")
_MAX_ERROR_DETAIL_CHARS = 512
_BYTES_PER_MEBIBYTE = 1024 * 1024

_PF_002_FIELDS = {
    FIELD_PF_002_NON_CLAIM: PF_002_NON_CLAIM,
    "hash_match_not_safe": True,
    "hash_match_not_semantically_equivalent": True,
    "hash_match_not_causal_execution_proof": True,
}

C3D_LIMITATIONS = [
    "Restricted weights-only loading is one security control and is not a complete model-security boundary.",
    "LOAD_SUCCESS does not establish behavioral safety or absence of backdoors.",
    "Legitimate models using unsupported Python classes may be blocked by restricted loading.",
    "The behavioral consistency battery remains DEFERRED_IN_SCOPE.",
]
C3D_NON_CLAIMS = [
    "LOAD_BLOCKED does not prove malicious intent or a proven attack.",
    "LOAD_SUCCESS does not establish behavioral safety, semantic equivalence, or global backdoor absence.",
    "T05d clean-label poisoning is not covered by this method.",
    "Model loading does not establish causal execution proof (PF-002).",
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


def _bounded_detail(detail: str) -> str:
    return detail[:_MAX_ERROR_DETAIL_CHARS]


def _limitations(resource_limits_applied: bool, load_attempted: bool) -> list[str]:
    limitations = list(C3D_LIMITATIONS)
    if not resource_limits_applied:
        if load_attempted:
            limitations.append(
                "OS memory and file-descriptor limits were unavailable on this platform."
            )
        else:
            limitations.append(
                "OS resource limits were not applied because artifact loading was not attempted."
            )
    return limitations


def _output(
    assessment_status: str,
    *,
    raw_signal: dict[str, Any],
    access_mode: str,
    resource_limits_applied: bool,
    load_attempted: bool,
    artifact_unit_id: str = "UNAVAILABLE",
    error_detail: str | None = None,
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        access_mode=access_mode,
        artifact_unit_id=artifact_unit_id,
        limitations=_limitations(resource_limits_applied, load_attempted),
        non_claims=C3D_NON_CLAIMS,
        error_detail=(
            _bounded_detail(error_detail)
            if isinstance(error_detail, str)
            else error_detail
        ),
        **_PF_002_FIELDS,
    )


def _early_signal(
    resource_limits: dict[str, int] | None,
    *,
    resource_limits_applied: bool = False,
    torch_available: bool | str = "NOT_CHECKED",
) -> dict[str, Any]:
    return {
        "fallback_attempted": False,
        "pytorch_version": "UNAVAILABLE",
        "torch_available": torch_available,
        "resource_limits_applied": resource_limits_applied,
        "resource_limits": resource_limits or "UNAVAILABLE",
    }


def _assessment_error(
    detail: str,
    *,
    resource_limits: dict[str, int] | None = None,
    resource_limits_applied: bool = False,
    torch_available: bool | str = "NOT_CHECKED",
) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=_early_signal(
            resource_limits,
            resource_limits_applied=resource_limits_applied,
            torch_available=torch_available,
        ),
        access_mode=AccessMode.UNAVAILABLE,
        resource_limits_applied=resource_limits_applied,
        load_attempted=False,
        error_detail=detail,
    )


def _validated_resource_limits(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict) or set(value) != _RESOURCE_LIMIT_KEYS:
        return None
    validated: dict[str, int] = {}
    for key in _RESOURCE_LIMIT_KEYS:
        limit = value[key]
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            return None
        validated[key] = limit
    return validated


def _apply_resource_limits(resource_limits: dict[str, int]) -> bool:
    """Apply supported worker-side limits; timeout remains supervisor-owned."""

    try:
        import resource
    except ImportError:
        return False

    try:
        memory_bytes = resource_limits["memory_mb"] * _BYTES_PER_MEBIBYTE
        resource.setrlimit(
            resource.RLIMIT_AS,
            (memory_bytes, resource.RLIM_INFINITY),
        )
        file_descriptor_limit = resource_limits["max_fds"]
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (file_descriptor_limit, file_descriptor_limit),
        )
    except (AttributeError, OSError, ValueError):
        return False
    return True


def _run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    if task.get("schema_version") != _WORKER_INPUT_SCHEMA:
        return _assessment_error("SCHEMA_VERSION_UNSUPPORTED")

    if _contains_prohibited_input(task):
        return _assessment_error(
            "PROHIBITED_INPUT_FIELD: Task input contains a prohibited field; rejected without processing."
        )

    resource_limits = _validated_resource_limits(task.get("resource_limits"))
    identity_quality = task.get("identity_quality")
    permitted_identity_quality = {
        IdentityQuality.TRUSTED,
        IdentityQuality.UNTRUSTED,
        IdentityQuality.UNAVAILABLE,
    }
    asset_paths = task.get("asset_paths")
    asset_directory = task.get("asset_directory")

    if (
        task.get("task") != _TASK_NAME
        or task.get("format") != _PYTORCH_FORMAT
        or task.get("artifact_unit_definition_id")
        != _PYTORCH_ARTIFACT_UNIT_DEFINITION_ID
        or identity_quality not in permitted_identity_quality
        or not isinstance(asset_paths, list)
        or len(asset_paths) != 1
        or not isinstance(asset_directory, str)
        or not asset_directory.strip()
        or resource_limits is None
    ):
        return _assessment_error(
            "INVALID_TASK_INPUT",
            resource_limits=resource_limits,
        )

    model_path = asset_paths[0]
    if (
        not isinstance(model_path, str)
        or not model_path.strip()
        or os.path.splitext(model_path)[1].casefold() not in _PYTORCH_SUFFIXES
    ):
        return _assessment_error(
            "INVALID_PYTORCH_ARTIFACT_UNIT",
            resource_limits=resource_limits,
        )

    if not is_within_directory(model_path, asset_directory):
        return _assessment_error(
            "PATH_CONTAINMENT_VIOLATION",
            resource_limits=resource_limits,
        )

    if not os.path.isfile(model_path):
        return _assessment_error(
            "MODEL_FILE_UNAVAILABLE",
            resource_limits=resource_limits,
        )

    resource_limits_applied = _apply_resource_limits(resource_limits)

    try:
        import torch
    except ImportError:
        return _assessment_error(
            "torch is not importable in the current worker environment; safe-loading assessment unavailable.",
            resource_limits=resource_limits,
            resource_limits_applied=resource_limits_applied,
            torch_available=False,
        )

    load_result: str
    load_detail: str | None
    try:
        loaded_artifact = torch.load(
            model_path,
            weights_only=True,
            map_location="cpu",
        )
        del loaded_artifact
        load_result = AssessmentStatus.LOAD_SUCCESS
        load_detail = None
    except (RuntimeError, pickle.UnpicklingError) as exc:
        load_result = AssessmentStatus.LOAD_BLOCKED
        load_detail = _bounded_detail(f"SAFE_LOAD_BLOCKED: {type(exc).__name__}")
    except Exception as exc:
        load_result = AssessmentStatus.LOAD_ERROR
        load_detail = _bounded_detail(f"SAFE_LOAD_ERROR: {type(exc).__name__}")

    raw_signal = {
        "weights_only_flag_used": True,
        "map_location": "cpu",
        "fallback_attempted": False,
        "pytorch_version": str(torch.__version__),
        "torch_available": True,
        "load_result": load_result,
        "load_detail": load_detail,
        "resource_limits_applied": resource_limits_applied,
        "resource_limits": resource_limits,
    }
    return _output(
        load_result,
        raw_signal=raw_signal,
        access_mode=AccessMode.BLACK_BOX,
        resource_limits_applied=resource_limits_applied,
        load_attempted=True,
        artifact_unit_id=_PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
    )


def run_assessment(task: dict) -> dict:
    """Assess one contained PyTorch artifact through the sole restricted load path."""

    if not isinstance(task, dict):
        return _assessment_error("INVALID_TASK_INPUT")
    try:
        return _run_assessment(task)
    except Exception as exc:
        return _assessment_error(
            f"UNEXPECTED_ASSESSMENT_ERROR: {type(exc).__name__}"
        )


def main() -> None:
    base_main(run_assessment)


if __name__ == "__main__":
    main()
