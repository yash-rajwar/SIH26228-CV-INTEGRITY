"""Deterministic SHA-256 identity hashing for resolved model artifact units."""

# REUSE-008: the model-hashing concept is hardened and reimplemented here.
# No R01 source code is copied; only the frozen C3A artifact-unit contract is consumed.

from __future__ import annotations

import hashlib
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


WORKER_ID = "COMP-W-C3B"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_HASH_CHUNK_BYTES = 65536
_MAX_ERROR_DETAIL_CHARS = 512
_PROHIBITED_INPUT_FIELDS = frozenset(
    {"_".join(("key", "path")), "_".join(("db", "path"))}
)
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")

_PF_002_FIELDS = {
    FIELD_PF_002_NON_CLAIM: PF_002_NON_CLAIM,
    "hash_match_not_safe": True,
    "hash_match_not_semantically_equivalent": True,
    "hash_match_not_causal_execution_proof": True,
}

C3B_LIMITATIONS = [
    "SHA-256 digest match establishes byte-level identity only (PF-002).",
    "MATCH does not imply the model is free of backdoors or adversarial modifications.",
    "DIFFERENT does not establish malicious modification; legitimate updates also produce DIFFERENT.",
]
C3B_NON_CLAIMS = [
    "Hash match ≠ safe; hash match ≠ semantically equivalent; hash match ≠ causal execution proof (PF-002).",
    "MATCH does not establish global backdoor absence.",
    "DIFFERENT does not prove malicious intent.",
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
    error_detail: str | None = None,
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        access_mode=access_mode,
        artifact_unit_id=artifact_unit_id,
        limitations=C3B_LIMITATIONS,
        non_claims=C3B_NON_CLAIMS,
        error_detail=(
            error_detail[:_MAX_ERROR_DETAIL_CHARS]
            if isinstance(error_detail, str)
            else error_detail
        ),
        **_PF_002_FIELDS,
    )


def _ambiguous_output(reason: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS,
        raw_signal={"reason": reason},
        access_mode=AccessMode.UNAVAILABLE,
    )


def _assessment_error(detail: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal={"reason": detail},
        access_mode=AccessMode.UNAVAILABLE,
        error_detail=detail,
    )


def _containment_violation(path: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION,
        raw_signal={"reason": "ARTIFACT_MEMBER_OUTSIDE_ASSET_DIRECTORY", "path": path},
        access_mode=AccessMode.UNAVAILABLE,
    )


def _artifact_unit_files(artifact_unit: Any) -> tuple[list[str], str] | None:
    if not isinstance(artifact_unit, dict):
        return None

    main_file = artifact_unit.get("main_file")
    external_files = artifact_unit.get("external_files")
    definition_id = artifact_unit.get("artifact_unit_definition_id")
    if (
        not isinstance(main_file, str)
        or not main_file.strip()
        or not isinstance(external_files, list)
        or any(
            not isinstance(path, str) or not path.strip()
            for path in external_files
        )
        or not isinstance(definition_id, str)
        or not definition_id.strip()
        or definition_id == "UNAVAILABLE"
    ):
        return None
    return [main_file, *external_files], definition_id


def _hash_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as artifact_file:
        for chunk in iter(lambda: artifact_file.read(_HASH_CHUNK_BYTES), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(task, dict) or task.get("schema_version") != _WORKER_INPUT_SCHEMA:
        return _assessment_error("UNRECOGNISED_SCHEMA_VERSION")
    if _contains_prohibited_input(task):
        return _assessment_error("PROHIBITED_INPUT_FIELD")

    resolved_unit = _artifact_unit_files(task.get("artifact_unit"))
    if resolved_unit is None:
        return _ambiguous_output("ARTIFACT_UNIT_UNDEFINED_OR_AMBIGUOUS")

    all_files, definition_id = resolved_unit
    asset_directory = task.get("asset_directory")
    if not isinstance(asset_directory, str) or not asset_directory.strip():
        return _assessment_error("ASSET_DIRECTORY_UNAVAILABLE")

    # Validate the complete unit before opening its first member. This prevents a
    # later violating path from causing a partial read or partial identity result.
    for path in all_files:
        if not is_within_directory(path, asset_directory):
            return _containment_violation(path)

    per_file_digests: dict[str, str] = {}
    try:
        for path in all_files:
            per_file_digests[path] = _hash_file(path)
    except (OSError, IOError) as exc:
        return _assessment_error(
            f"ARTIFACT_MEMBER_READ_FAILED: {type(exc).__name__}"
        )

    sorted_paths = sorted(per_file_digests)
    combined_input = "".join(per_file_digests[path] for path in sorted_paths)
    combined_digest = hashlib.sha256(combined_input.encode("ascii")).hexdigest()

    reference_digest = task.get("reference_digest")
    comparison_result = "UNAVAILABLE"
    if reference_digest is not None:
        comparison_result = (
            "MATCH" if combined_digest == reference_digest else "DIFFERENT"
        )

    return _output(
        AssessmentStatus.COMPLETED,
        raw_signal={
            "combined_artifact_unit_digest": combined_digest,
            "per_file_digests": per_file_digests,
            "sorted_path_order_used": sorted_paths,
            "artifact_unit_definition_id": definition_id,
            "reference_digest_provided": reference_digest is not None,
            "comparison_result": comparison_result,
        },
        access_mode=AccessMode.BLACK_BOX,
        artifact_unit_id=definition_id,
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Hash one already-resolved artifact unit without parsing model contents."""

    try:
        return _run_assessment(task)
    except Exception as exc:
        return _assessment_error(f"UNEXPECTED_HASH_ERROR: {type(exc).__name__}")


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
