"""TASK-023 integration tests for the read-only analyst CLI."""

from __future__ import annotations

import datetime
import io
import json
import pathlib

import pytest

from assurance_system.interfaces.cli import AssuranceCLI
from assurance_system.supervisor.audit_chain import ChainVerificationResult
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import PipelineRunSummary


def _timestamp() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class _TestConfigLoader:
    def load(self) -> dict:
        return {"system": {"evidence_store": {"path": "test-evidence.db"}}}


def _finding(asset_id: str = "asset-cli-001") -> dict:
    return {
        "schema_version": "finding-v1",
        "asset_id": asset_id,
        "method_id": "COMP-C5",
        "detection_status": "UNAVAILABLE",
        "interpretation_status": "UNAVAILABLE",
        "applicability_status": "NOT_ASSESSED",
        "raw_signal": {"source": "integration-test"},
        "reference_health": "UNAVAILABLE",
        "limitations": ["The named assessment path did not yield a result."],
        "non_claims": ["No malicious-intent conclusion is established."],
        "dependency_declaration": {
            "co_firing_detectors": ["COMP-W-C2B"],
            "independence_established": False,
        },
        "coverage_gap_clean_label": True,
        "anomaly_not_malicious_non_claim": True,
        "global_backdoor_absence_not_established": True,
        "pf_002_non_claim": "C4_BINDING_UNAVAILABLE",
        "analyst_disposition_prompt": "UNAVAILABLE_NO_DECISION",
        "is_synthetic": False,
    }


def _evidence(asset_id: str = "asset-cli-001") -> dict:
    return {
        "schema_version": "worker-output-v1",
        "asset_id": asset_id,
        "method_id": "M02",
        "assessment_status": "COMPLETED",
        "raw_signal": {"duplicate_group_count": 0},
        "access_mode": "UNAVAILABLE",
        "artifact_unit_id": "UNAVAILABLE",
        "coverage_gap_clean_label": True,
        "limitations": ["Only exact byte duplicates are represented."],
        "non_claims": ["No semantic duplicate conclusion is established."],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "assessment_timestamp": _timestamp(),
        "worker_id": "COMP-W-C2B",
        "is_synthetic": False,
    }


@pytest.fixture
def store() -> EvidenceStore:
    evidence_store = EvidenceStore(":memory:")
    try:
        yield evidence_store
    finally:
        evidence_store._conn.close()


def _cli(
    store: object,
    output: io.StringIO,
    *,
    audit_chain_factory=None,
    orchestrator_factory=None,
) -> AssuranceCLI:
    return AssuranceCLI(
        config_loader=_TestConfigLoader(),
        evidence_store_factory=lambda _path: store,
        audit_chain_factory=audit_chain_factory,
        orchestrator_factory=orchestrator_factory,
        stdout=output,
        stderr=output,
    )


def test_int_cli_001_valid_assessment_generates_evidence_and_summary(
    store: EvidenceStore,
) -> None:
    class FakeOrchestrator:
        def __init__(self, evidence_store, _audit_chain, *, config_loader) -> None:
            self.store = evidence_store
            assert config_loader is not None

        def run_pipeline(self, manifest_path: str) -> PipelineRunSummary:
            assert manifest_path == "submission.json"
            self.store.write_evidence_record(_evidence())
            self.store.write_finding(_finding())
            now = _timestamp()
            return PipelineRunSummary(
                run_id="run-cli-001",
                assets_processed=1,
                workers_dispatched=1,
                worker_results_rejected=0,
                evidence_records_written=1,
                deferred_records_written=0,
                provenance_records_written=1,
                findings_written=1,
                started_at=now,
                completed_at=now,
            )

    output = io.StringIO()
    cli = _cli(store, output, orchestrator_factory=FakeOrchestrator)

    assert cli.run(["assess", "--submission", "submission.json"]) == 0
    assert store.query_evidence("asset-cli-001", "M02") is not None
    result = json.loads(output.getvalue())
    assert result["pipeline_summary"]["assets_processed"] == 1
    assert result["asset_ids"] == ["asset-cli-001"]
    assert result["methods_executed"] == ["COMP-W-C2B"]
    assert result["finding_statuses"][0]["detection_status"] == "UNAVAILABLE"


def test_int_cli_002_show_finding_displays_every_field_and_non_claims(
    store: EvidenceStore,
) -> None:
    store.write_finding(_finding("asset-cli-002"))
    expected = store.query_findings("asset-cli-002")
    output = io.StringIO()

    assert _cli(store, output).run(
        ["show-finding", "--asset-id", "asset-cli-002"]
    ) == 0
    assert json.loads(output.getvalue()) == expected
    rendered = output.getvalue()
    assert "UNAVAILABLE" in rendered
    assert '"non_claims"' in rendered
    for prohibited_state in ('"CLEAN"', '"SAFE"', '"HEALTHY"'):
        assert prohibited_state not in rendered


def test_int_cli_003_list_deferred_displays_all_records(
    store: EvidenceStore,
) -> None:
    for index in range(9):
        store.write_deferred_record(
            {
                "schema_version": "deferred-record-v1",
                "asset_id": "asset-cli-003",
                "method_id": f"DEFERRED-M{index + 1:02d}",
                "assessment_status": "DEFERRED_IN_SCOPE",
                "deferral_reason": "MVP bounded-method deferral remains explicit.",
                "finite_battery_non_claim": True,
                "limitations": ["This deferred method was not executed."],
                "non_claims": ["Absence of this method is not evidence of absence."],
            }
        )
    output = io.StringIO()

    assert _cli(store, output).run(["list-deferred"]) == 0
    records = json.loads(output.getvalue())
    assert len(records) == 9
    assert all(record["assessment_status"] == "DEFERRED_IN_SCOPE" for record in records)
    assert all(record["method_id"] for record in records)
    assert all(record["deferral_reason"] for record in records)


def test_int_cli_004_audit_corruption_is_printed_before_events() -> None:
    class FakeStore:
        @staticmethod
        def query_audit_trail(limit=None) -> list[dict]:
            assert limit == 4
            return [{"event_id": 1, "event_type": "PIPELINE_RUN_START"}]

    class CorruptAuditChain:
        @staticmethod
        def verify_chain_integrity() -> ChainVerificationResult:
            return ChainVerificationResult(
                intact=False,
                violations=[{"event_id": 1, "reason": "hash mismatch"}],
            )

    output = io.StringIO()
    cli = _cli(
        FakeStore(),
        output,
        audit_chain_factory=lambda _store: CorruptAuditChain(),
    )

    assert cli.run(["show-audit-trail", "--limit", "4"]) == 0
    rendered = output.getvalue()
    assert "CHAIN_CORRUPT" in rendered
    assert rendered.index("CHAIN_CORRUPT") < rendered.index('"event_id"')


def test_show_evidence_displays_complete_stored_record(store: EvidenceStore) -> None:
    store.write_evidence_record(_evidence("asset-cli-004"))
    expected = store.query_evidence("asset-cli-004", "M02")
    output = io.StringIO()

    assert _cli(store, output).run(
        ["show-evidence", "--asset-id", "asset-cli-004", "--method", "M02"]
    ) == 0
    assert json.loads(output.getvalue()) == expected
    assert '"limitations"' in output.getvalue()
    assert '"non_claims"' in output.getvalue()


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["dashboard"], "dashboard requires TASK-024"),
    ],
)
def test_unavailable_downstream_interfaces_fail_explicitly(
    store: EvidenceStore, arguments: list[str], message: str,
) -> None:
    output = io.StringIO()
    assert _cli(store, output).run(arguments) == 1
    assert output.getvalue().strip() == message


def test_missing_records_fail_closed_with_unavailable(store: EvidenceStore) -> None:
    finding_output = io.StringIO()
    evidence_output = io.StringIO()

    assert _cli(store, finding_output).run(
        ["show-finding", "--asset-id", "missing"]
    ) == 1
    assert finding_output.getvalue().splitlines() == ["Finding not found", "UNAVAILABLE"]
    assert _cli(store, evidence_output).run(
        ["show-evidence", "--asset-id", "missing", "--method", "M02"]
    ) == 1
    assert evidence_output.getvalue().splitlines() == [
        "Evidence not found",
        "UNAVAILABLE",
    ]


def test_cli_source_has_all_commands_and_no_store_mutation_path() -> None:
    source = pathlib.Path("assurance_system/interfaces/cli.py").read_text(
        encoding="utf-8"
    )
    for command in (
        "assess",
        "show-finding",
        "show-evidence",
        "show-audit-trail",
        "export-bundle",
        "list-deferred",
        "dashboard",
    ):
        assert f'"{command}"' in source
    for prohibited in (
        "write_" + "evidence_record",
        "write_" + "finding",
        "write_" + "audit",
        "shell" + "=True",
    ):
        assert prohibited not in source
    assert "import requests" not in source
    assert "import socket" not in source
    assert "import subprocess" not in source
