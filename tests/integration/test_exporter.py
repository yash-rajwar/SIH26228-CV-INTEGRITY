"""TASK-025 integration tests for the evidence bundle exporter."""

from __future__ import annotations

import io
import json
import pathlib
import zipfile

import pytest

from assurance_system.export.exporter import EvidenceExporter
from assurance_system.interfaces.cli import AssuranceCLI
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


ASSET_ID = "asset-export-001"
FIXED_TIMESTAMP = "2026-09-28T12:00:00.000000Z"
EXPECTED_FILES = {
    "manifest.json",
    "findings.json",
    "evidence_records.json",
    "audit_trail.json",
    "provenance.json",
    "capabilities.json",
}


def _evidence() -> dict:
    return {
        "schema_version": "worker-output-v1",
        "asset_id": ASSET_ID,
        "method_id": "M02",
        "assessment_status": "UNAVAILABLE",
        "raw_signal": {"duplicate_group_count": 0},
        "access_mode": "UNAVAILABLE",
        "artifact_unit_id": "UNAVAILABLE",
        "coverage_gap_clean_label": True,
        "limitations": ["The method did not produce an assessment result."],
        "non_claims": ["No malicious-intent conclusion is established."],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "assessment_timestamp": "2026-09-28T11:55:00.000000Z",
        "worker_id": "COMP-W-C2B",
        "record_digest": "evidence-digest-001",
        "is_synthetic": False,
    }


def _finding(
    suffix: str,
    detection_status: str,
    interpretation_status: str,
    applicability_status: str,
) -> dict:
    return {
        "finding_id": f"finding-export-{suffix}",
        "schema_version": "finding-v1",
        "asset_id": ASSET_ID,
        "method_id": f"COMP-C5-{suffix}",
        "detection_status": detection_status,
        "interpretation_status": interpretation_status,
        "applicability_status": applicability_status,
        "raw_signal": {"evidence_records": []},
        "reference_health": "UNAVAILABLE",
        "limitations": ["Interpretation is bounded by available evidence."],
        "non_claims": ["No complete-integrity conclusion is established."],
        "dependency_declaration": {
            "co_firing_detectors": [],
            "independence_established": False,
        },
        "coverage_gap_clean_label": True,
        "anomaly_not_malicious_non_claim": False,
        "global_backdoor_absence_not_established": True,
        "pf_002_non_claim": "C4_BINDING_UNAVAILABLE",
        "analyst_disposition_prompt": "UNAVAILABLE_NO_DECISION",
        "is_synthetic": False,
    }


def _populate(store: EvidenceStore) -> None:
    store.write_evidence_record(_evidence())
    store.write_finding(
        _finding("unavailable", "UNAVAILABLE", "UNAVAILABLE", "NOT_ASSESSED")
    )
    store.write_finding(
        _finding(
            "deferred",
            "DEFERRED_IN_SCOPE",
            "DEFERRED",
            "DEFERRED_IN_SCOPE",
        )
    )
    store.write_provenance_record(
        {
            "provenance_id": "provenance-export-001",
            "schema_version": "v1.0",
            "artifact_unit_digest": "artifact-digest-001",
            "evidence_record_digests": ["evidence-digest-001"],
            "signing_key_id": "UNAVAILABLE",
            "signature": None,
            "signature_algorithm": None,
            "sequence_number": 1,
            "replay_nonce": "export-replay-nonce-001",
            "pf_002_non_claim": "digest_match does not establish causal execution",
            "signing_status": "SIGNING_UNAVAILABLE",
            "timestamp": "2026-09-28T11:56:00.000000Z",
        }
    )
    store.write_deferred_record(
        {
            "record_id": "deferred-export-001",
            "schema_version": "v1.0",
            "asset_id": ASSET_ID,
            "method_id": "M03-PDQ",
            "assessment_status": "DEFERRED_IN_SCOPE",
            "deferral_reason": "Near-duplicate analysis remains deferred.",
            "finite_battery_non_claim": False,
            "limitations": ["Near-duplicate relationships were not assessed."],
            "non_claims": ["No near-duplicate absence conclusion is established."],
        }
    )
    AuditChainWriter(store).append_event(
        "EXPORT_TEST_EVENT", {"asset_id": ASSET_ID}
    )


@pytest.fixture
def store(tmp_path: pathlib.Path) -> EvidenceStore:
    evidence_store = EvidenceStore(str(tmp_path / "exporter.sqlite3"))
    _populate(evidence_store)
    try:
        yield evidence_store
    finally:
        evidence_store._conn.close()


def _export(
    store: EvidenceStore, output_directory: pathlib.Path, name: str = "bundle.zip"
) -> pathlib.Path:
    return EvidenceExporter(
        store,
        allowed_output_directory=output_directory,
        timestamp_provider=lambda: FIXED_TIMESTAMP,
    ).export_bundle(ASSET_ID, name)


def _documents(bundle_path: pathlib.Path) -> tuple[list[str], dict[str, object]]:
    with zipfile.ZipFile(bundle_path, "r") as archive:
        names = archive.namelist()
        return names, {
            name: json.loads(archive.read(name).decode("utf-8")) for name in names
        }


def test_bundle_contains_exact_six_files_and_manifest_metadata(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    bundle_path = _export(store, tmp_path)
    names, documents = _documents(bundle_path)

    assert names == sorted(EXPECTED_FILES)
    assert set(names) == EXPECTED_FILES
    manifest = documents["manifest.json"]
    assert manifest["asset_id"] == ASSET_ID
    assert manifest["schema_version"] == "v1.0"
    assert manifest["creation_timestamp"] == FIXED_TIMESTAMP
    assert manifest["bundle_format"] == "SIH26228_EVIDENCE_BUNDLE"
    assert manifest["contents"] == sorted(EXPECTED_FILES)
    rendered = json.dumps(manifest, sort_keys=True)
    assert str(tmp_path) not in rendered
    assert "AppData" not in rendered
    assert "Temp" not in rendered


def test_findings_evidence_provenance_and_capabilities_are_preserved(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    _, documents = _documents(_export(store, tmp_path))

    findings = documents["findings.json"]
    assert {finding["detection_status"] for finding in findings} == {
        "UNAVAILABLE",
        "DEFERRED_IN_SCOPE",
    }
    assert {finding["applicability_status"] for finding in findings} == {
        "NOT_ASSESSED",
        "DEFERRED_IN_SCOPE",
    }
    assert all(finding["limitations"] for finding in findings)
    assert all(finding["non_claims"] for finding in findings)

    evidence = documents["evidence_records.json"]
    assert len(evidence) == 1
    assert evidence[0]["asset_id"] == ASSET_ID
    assert evidence[0]["assessment_status"] == "UNAVAILABLE"
    assert evidence[0]["limitations"] == _evidence()["limitations"]
    assert evidence[0]["non_claims"] == _evidence()["non_claims"]

    provenance = documents["provenance.json"]
    assert len(provenance) == 1
    assert provenance[0]["provenance_id"] == "provenance-export-001"
    assert provenance[0]["signing_status"] == "SIGNING_UNAVAILABLE"
    assert provenance[0]["signature"] is None

    capabilities = documents["capabilities.json"]
    assert capabilities["asset_id"] == ASSET_ID
    assert len(capabilities["deferred_records"]) == 1
    assert (
        capabilities["deferred_records"][0]["assessment_status"]
        == "DEFERRED_IN_SCOPE"
    )


def test_audit_records_and_verification_are_exported(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    _, documents = _documents(_export(store, tmp_path))
    audit_document = documents["audit_trail.json"]

    assert len(audit_document["events"]) == 1
    assert audit_document["events"][0]["event_type"] == "EXPORT_TEST_EVENT"
    assert audit_document["chain_verification"] == {
        "intact": True,
        "scope": "EXPORTED_EVENT_CHAIN",
        "violations": [],
    }


def test_corruption_is_visible_without_mutating_audit_trail(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    with store._conn:
        store._conn.execute(
            "UPDATE audit_events SET chain_link_hash = ? WHERE event_id = ?",
            ("tampered-chain-link", 1),
        )
    before_events = store.query_audit_trail()

    _, documents = _documents(_export(store, tmp_path))

    verification = documents["audit_trail.json"]["chain_verification"]
    assert verification["intact"] is False
    assert verification["result"] == "CHAIN_CORRUPT"
    assert verification["violations"]
    assert store.query_audit_trail() == before_events


def test_export_does_not_modify_evidence_store(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    before = list(store._conn.iterdump())

    _export(store, tmp_path)

    assert list(store._conn.iterdump()) == before


def test_identical_data_and_timestamp_produce_identical_zip_bytes(
    store: EvidenceStore, tmp_path: pathlib.Path,
) -> None:
    first = _export(store, tmp_path, "first.zip")
    second = _export(store, tmp_path, "second.zip")

    assert first.read_bytes() == second.read_bytes()
    with zipfile.ZipFile(first, "r") as archive:
        assert archive.namelist() == sorted(EXPECTED_FILES)
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())


class _CLIConfig:
    @staticmethod
    def load() -> dict:
        return {"system": {"evidence_store": {"path": "unused.sqlite3"}}}


def test_cli_export_command_delegates_to_evidence_exporter(
    store: EvidenceStore,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    output = io.StringIO()
    cli = AssuranceCLI(
        config_loader=_CLIConfig(),
        evidence_store_factory=lambda _path: store,
        stdout=output,
        stderr=output,
    )

    result = cli.run(
        ["export-bundle", "--asset-id", ASSET_ID, "--output", "cli-bundle.zip"]
    )

    assert result == 0
    assert output.getvalue().strip() == "cli-bundle.zip"
    assert (tmp_path / "cli-bundle.zip").is_file()
