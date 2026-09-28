"""Target-host offline validation contracts for TASK-027.

Part A authors the contracts only.  The execution bodies remain deliberately
blocked until a separately authorized target-host validation session.

The skip text below is retained verbatim from the TASK-027-A packet.  The live
project record already marks PRE-01 resolved; PROJECT_STATE.md records that
this legacy packet wording does not reopen PRE-01.
"""

import pytest


PRE_01_SKIP_REASON = (
    "BLOCKED: PRE-01 — target host not confirmed. Execute these tests manually "
    "on the actual target host after PRE-01 is resolved. Do not run on development "
    "machine and claim offline capability."
)


@pytest.mark.skip(reason=PRE_01_SKIP_REASON)
def test_off_001_wheelhouse_installation_validation():
    """OFF-001: Install every required package from the local wheelhouse only."""


@pytest.mark.skip(reason=PRE_01_SKIP_REASON)
def test_off_002_zero_network_egress_validation():
    """OFF-002: Run the full pipeline under target-host network monitoring."""


@pytest.mark.skip(reason=PRE_01_SKIP_REASON)
def test_off_003_offline_import_verification():
    """OFF-003: Import onnx, torch, and pycocotools in the offline runtime."""


@pytest.mark.skip(reason=PRE_01_SKIP_REASON)
def test_off_004_sqlite_evidence_store_offline_validation():
    """OFF-004: Exercise evidence-store read/write with zero network access."""
