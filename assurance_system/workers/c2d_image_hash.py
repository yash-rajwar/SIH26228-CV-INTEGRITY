"""Image-level SHA-256 identity-floor worker."""

# SHA-256 streaming is independently reimplemented with stdlib per REUSE-005.
# No R01 or COMP-W-C2B implementation code is imported.

from __future__ import annotations

import hashlib
from typing import Any

from assurance_system.constants import AssessmentStatus
from assurance_system.workers.base import (
    build_worker_output,
    is_within_directory,
    main as worker_main,
)


WORKER_ID = "COMP-W-C2D"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_HASH_CHUNK_BYTES = 65536
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")

C2D_LIMITATIONS = [
    "SHA-256 hash equality establishes byte-level identity only.",
    "PDQ near-duplicate detection is DEFERRED_IN_SCOPE; visually similar images with different bytes are not detected by this method.",
]
C2D_NON_CLAIMS = [
    "Hash equality does not establish visual or semantic near-duplicate relationship.",
    "PDQ near-duplicate detection (M03-PDQ) is DEFERRED_IN_SCOPE.",
    "Clean-label poisoning (T05d) is NOT detectable by image hashing; this is a permanent coverage gap.",
    "T05d (clean-label poisoning) is NOT covered by any method in this assessment.",
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
    *,
    per_image_digests: dict[str, str] | None = None,
    duplicate_groups: dict[str, list[str]] | None = None,
    read_errors: list[dict[str, str]] | None = None,
    total_images_processed: int = 0,
) -> dict[str, Any]:
    per_image_digests = per_image_digests or {}
    duplicate_groups = duplicate_groups or {}
    read_errors = read_errors or []
    return {
        "per_image_digests": per_image_digests,
        "duplicate_groups": duplicate_groups,
        "duplicate_image_count": sum(
            len(paths) for paths in duplicate_groups.values()
        ),
        "total_images_processed": total_images_processed,
        "read_errors": read_errors,
        "pdq_status": AssessmentStatus.DEFERRED_IN_SCOPE,
    }


def _output(
    assessment_status: str,
    *,
    raw_signal: dict[str, Any],
    error_detail: str | None = None,
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=assessment_status,
        raw_signal=raw_signal,
        limitations=C2D_LIMITATIONS,
        non_claims=C2D_NON_CLAIMS,
        error_detail=error_detail,
    )


def _error_output(detail: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=_raw_signal(),
        error_detail=detail,
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Hash contained image files without decoding their contents."""

    if not isinstance(task, dict) or task.get("schema_version") != _WORKER_INPUT_SCHEMA:
        return _error_output("UNRECOGNISED_SCHEMA_VERSION")
    if _contains_prohibited_input(task):
        return _error_output("PROHIBITED_INPUT_FIELD")

    asset_paths = task.get("asset_paths")
    asset_directory = task.get("asset_directory")
    if (
        not isinstance(asset_paths, list)
        or not isinstance(asset_directory, str)
        or not asset_directory
    ):
        return _error_output("INVALID_TASK_INPUT")

    digest_map: dict[str, list[str]] = {}
    error_files: list[dict[str, str]] = []

    for path_str in asset_paths:
        if not isinstance(path_str, str) or not is_within_directory(
            path_str, asset_directory
        ):
            error_files.append(
                {"path": str(path_str), "error": "PATH_CONTAINMENT_VIOLATION"}
            )
            continue
        try:
            hasher = hashlib.sha256()
            with open(path_str, "rb") as image_file:
                for chunk in iter(
                    lambda: image_file.read(_HASH_CHUNK_BYTES), b""
                ):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
            digest_map.setdefault(digest, []).append(path_str)
        except (IOError, OSError) as exc:
            error_files.append({"path": path_str, "error": str(exc)})

    per_image_digests = {
        path: digest for digest, paths in digest_map.items() for path in paths
    }
    duplicate_groups = {
        digest: paths for digest, paths in digest_map.items() if len(paths) > 1
    }
    all_failed = len(error_files) == len(asset_paths)
    status = (
        AssessmentStatus.ASSESSMENT_ERROR
        if all_failed
        else AssessmentStatus.COMPLETED
    )

    return _output(
        status,
        raw_signal=_raw_signal(
            per_image_digests=per_image_digests,
            duplicate_groups=duplicate_groups,
            read_errors=error_files,
            total_images_processed=len(asset_paths) - len(error_files),
        ),
        error_detail="ALL_FILES_FAILED" if all_failed else None,
    )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
