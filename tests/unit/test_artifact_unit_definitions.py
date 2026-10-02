"""Trusted SP-002 definition records and submission-ID enforcement."""
from __future__ import annotations

import pathlib

import pytest

from assurance_system.exceptions import IngestError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator
from assurance_system.workers.c3a_artifact_unit import (
    ONNX_ARTIFACT_UNIT_DEFINITION_ID,
    PYTORCH_ARTIFACT_UNIT_DEFINITION_ID,
)

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_ONNX_ID = "onnx-main-referenced-external-data-v1"
_PYTORCH_ID = "pytorch-single-file-v1"


def test_published_artifact_definitions_match_the_active_worker_contract():
    assert ONNX_ARTIFACT_UNIT_DEFINITION_ID == _ONNX_ID
    assert PYTORCH_ARTIFACT_UNIT_DEFINITION_ID == _PYTORCH_ID
    for filename, identifier in (("onnx_artifact_unit_spec.md", _ONNX_ID),
                                  ("pytorch_artifact_unit_spec.md", _PYTORCH_ID)):
        record = (_ROOT / "artifact_unit_defs" / filename).read_text(encoding="utf-8")
        assert f"Specification ID: `{identifier}`" in record
    onnx_record = (_ROOT / "artifact_unit_defs/onnx_artifact_unit_spec.md").read_text(encoding="utf-8")
    assert "Decision date: 2026-10-05" in onnx_record
    assert "E-2 / SP-002-ONNX" in onnx_record


@pytest.fixture
def subject(tmp_path):
    store = EvidenceStore(str(tmp_path / "definitions.sqlite3"))
    try:
        yield SupervisorOrchestrator(store, AuditChainWriter(store))
    finally:
        store._conn.close()


def _manifest(tmp_path, format_name, supplied_id=None):
    path = tmp_path / ("model.onnx" if format_name == "ONNX" else "model.pt")
    path.write_bytes(b"manifest validation must not parse this asset")
    asset = {"asset_id": "definition-contract", "asset_paths": [str(path)],
             "format": format_name, "is_synthetic": True}
    if supplied_id is not None:
        asset["artifact_unit_definition_id"] = supplied_id
    return {"schema_version": "submission-manifest-v1",
            "asset_directory": str(tmp_path), "assets": [asset]}


@pytest.mark.parametrize("format_name,approved_id", [("ONNX", _ONNX_ID), ("PYTORCH", _PYTORCH_ID)])
@pytest.mark.parametrize("supplied", [False, True])
def test_manifest_normalization_uses_the_approved_format_definition(subject, tmp_path, format_name, approved_id, supplied):
    manifest = _manifest(tmp_path, format_name, approved_id if supplied else None)
    normalized = subject._validate_manifest(manifest)
    assert normalized["assets"][0]["artifact_unit_definition_id"] == approved_id
    assert ("artifact_unit_definition_id" in manifest["assets"][0]) is supplied


@pytest.mark.parametrize("format_name,supplied_id", [
    ("ONNX", _PYTORCH_ID), ("ONNX", "UNAVAILABLE"), ("ONNX", "submitter-chosen-id"),
    ("PYTORCH", _ONNX_ID), ("PYTORCH", "UNAVAILABLE"),
])
def test_manifest_rejects_an_unapproved_or_wrong_format_definition(subject, tmp_path, format_name, supplied_id):
    with pytest.raises(IngestError, match="does not match the approved definition"):
        subject._validate_manifest(_manifest(tmp_path, format_name, supplied_id))
