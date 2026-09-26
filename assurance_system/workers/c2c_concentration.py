"""Source-concentration statistics worker."""

from __future__ import annotations

import math
from typing import Any

from assurance_system.constants import AssessmentStatus, IdentityQuality
from assurance_system.workers.base import build_worker_output, main as worker_main


WORKER_ID = "COMP-W-C2C"
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")

C2C_LIMITATIONS = [
    "Contributor identity is self-asserted (path/metadata-derived) unless external authenticated identity is provided via TRUSTED identity_quality.",
    "SYBIL_UNRELIABLE=True means fragmentation cannot be attributed to Sybil attack vs. legitimate multi-source distribution.",
    "High HHI indicates concentration; it does not establish attack type or intent.",
    "No external identity authentication mechanism is currently established.",
]
C2C_NON_CLAIMS = [
    "Source concentration statistics do not prove data poisoning.",
    "High HHI does not imply malicious intent.",
    "SYBIL_UNRELIABLE=True does not mean a Sybil attack is occurring.",
    "No aggregate risk score is produced by this method.",
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


def _error_output(
    detail: str,
    *,
    limitations: list[str],
    non_claims: list[str],
) -> dict[str, Any]:
    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=AssessmentStatus.ASSESSMENT_ERROR,
        error_detail=detail,
        raw_signal=None,
        limitations=limitations,
        non_claims=non_claims,
    )


def run_assessment(task: dict[str, Any]) -> dict[str, Any]:
    """Compute HHI, Shannon entropy, and per-source shares."""

    if _contains_prohibited_input(task):
        return _error_output(
            "Prohibited input field detected",
            limitations=["Worker input contained a prohibited field."],
            non_claims=["No statistics can be reported for rejected input."],
        )

    contributor_metadata = task.get("contributor_metadata", [])
    identity_quality = task.get("identity_quality", IdentityQuality.UNTRUSTED)

    if not contributor_metadata:
        return _error_output(
            "No contributor metadata available",
            limitations=["No contributor metadata supplied."],
            non_claims=["No statistics can be reported without metadata."],
        )

    source_counts: dict[Any, int] = {}
    for record in contributor_metadata:
        source = (
            record.get("contributor_id")
            or record.get("source_batch")
            or "UNKNOWN"
        )
        source_counts[source] = source_counts.get(source, 0) + 1

    total = sum(source_counts.values())
    shares = {source: count / total for source, count in source_counts.items()}
    hhi = sum(share**2 for share in shares.values())
    entropy = -sum(
        share * math.log2(share) for share in shares.values() if share > 0
    )
    sybil_unreliable = identity_quality != IdentityQuality.TRUSTED

    return build_worker_output(
        worker_id=WORKER_ID,
        assessment_status=AssessmentStatus.COMPLETED,
        raw_signal={
            "hhi": hhi,
            "shannon_entropy_bits": entropy,
            "per_source_shares": shares,
            "per_source_counts": source_counts,
            "total_items": total,
            "unique_sources": len(source_counts),
            "identity_quality": identity_quality,
            "sybil_unreliable": sybil_unreliable,
        },
        limitations=C2C_LIMITATIONS,
        non_claims=C2C_NON_CLAIMS,
    )


def main() -> None:
    worker_main(run_assessment)


if __name__ == "__main__":
    main()
