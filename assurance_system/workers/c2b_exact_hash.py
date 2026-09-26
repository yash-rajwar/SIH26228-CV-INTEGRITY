"""Deterministic SHA-256 exact-duplicate detector worker."""

# SHA-256 streaming hash pattern — algorithm is stdlib; see REUSE-002a.
# R01 code is NOT used here (no repository-wide license established).

from __future__ import annotations

import hashlib
from typing import Any

from assurance_system.constants import AssessmentStatus
from assurance_system.workers.base import (
    build_worker_output,
    is_within_directory,
    main as worker_main,
)


WORKER_ID = "COMP-W-C2B"
_WORKER_INPUT_SCHEMA = "worker-input-v1"
_HASH_CHUNK_BYTES = 65536
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")

C2B_LIMITATIONS = [
    "Detects byte-level exact duplicates only; near-duplicate detection (PDQ) is DEFERRED_IN_SCOPE.",
    "Read errors for individual files exclude those files; remaining files are assessed.",
    "Does not attribute duplicate pairs to any specific attack category.",
    "Large corpora are subject to the configured wall-clock timeout.",
]
C2B_NON_CLAIMS = [
    "Exact duplicate presence does not imply flooding attack or malicious intent.",
    "Non-duplicate files may still be adversarially manipulated.",
    "Near-duplicate detection (PDQ) is DEFERRED_IN_SCOPE and is not covered here.",
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
    file_digest_map: dict[str, str] | None = None,
    duplicate_groups: dict[str, list[str]] | None = None,
    read_errors: list[dict[str, str]] | None = None,
    total_files_processed: int = 0,
) -> dict[str, Any]:
    file_digest_map = file_digest_map or {}
    duplicate_groups = duplicate_groups or {}
    read_errors = read_errors or []
    return {
        "file_digest_map": file_digest_map,
        "duplicate_groups": duplicate_groups,
        "duplicate_group_count": len(duplicate_groups),
        "total_duplicated_files": sum(
            len(paths) for paths in duplicate_groups.values()
        ),
        "read_errors": read_errors,
        "total_files_processed": total_files_processed,
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
        limitations=C2B_LIMITATIONS,
        non_claims=C2B_NON_CLAIMS,
        error_detail=error_detail,
    )


def _error_output(detail: str) -> dict[str, Any]:
    return _output(
        AssessmentStatus.ASSESSMENT_ERROR,
        raw_signal=_raw_signal(),
        error_detail=detail,
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Hash every contained readable file and report exact duplicate groups."""

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

    for path in asset_paths:
        if not isinstance(path, str) or not is_within_directory(path, asset_directory):
            error_files.append(
                {"path": str(path), "error": "PATH_CONTAINMENT_VIOLATION"}
            )
            continue
        try:
            hasher = hashlib.sha256()
            with open(path, "rb") as asset_file:
                for chunk in iter(lambda: asset_file.read(_HASH_CHUNK_BYTES), b""):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
            digest_map.setdefault(digest, []).append(path)
        except (IOError, OSError) as exc:
            error_files.append({"path": path, "error": str(exc)})

    file_digest_map = {
        path: digest for digest, paths in digest_map.items() for path in paths
    }
    duplicate_groups = {
        digest: paths for digest, paths in digest_map.items() if len(paths) > 1
    }

    all_failed = len(error_files) == len(asset_paths) and len(asset_paths) > 0
    status = (
        AssessmentStatus.ASSESSMENT_ERROR
        if all_failed
        else AssessmentStatus.COMPLETED
    )
    return _output(
        status,
        raw_signal=_raw_signal(
            file_digest_map=file_digest_map,
            duplicate_groups=duplicate_groups,
            read_errors=error_files,
            total_files_processed=len(asset_paths) - len(error_files),
        ),
        error_detail="ALL_FILES_FAILED" if all_failed else None,
    )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
