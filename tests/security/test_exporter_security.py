"""Security validation for TASK-025 COMP-EXPORT."""

from __future__ import annotations

import ast
import io
import json
import pathlib
import zipfile

import pytest

from assurance_system.export.exporter import EvidenceExportError, EvidenceExporter


FIXED_TIMESTAMP = "2026-09-28T12:00:00.000000Z"
SOURCE_PATH = pathlib.Path("assurance_system/export/exporter.py")


def _source_bundle(findings: list[dict] | None = None) -> bytes:
    documents = {
        "audit.json": [],
        "evidence.json": [],
        "findings.json": findings or [],
        "provenance.json": [],
    }
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w") as archive:
        for name, document in documents.items():
            archive.writestr(name, json.dumps(document, sort_keys=True))
    return target.getvalue()


class _Store:
    def __init__(
        self,
        *,
        findings: list[dict] | None = None,
        deferred: list[dict] | None = None,
    ) -> None:
        self._bundle = _source_bundle(findings)
        self._deferred = deferred or []
        self.read_count = 0

    def export_bundle(self, _asset_id: str) -> bytes:
        self.read_count += 1
        return self._bundle

    def query_deferred(self) -> list[dict]:
        self.read_count += 1
        return self._deferred


def _exporter(store: _Store, allowed: pathlib.Path) -> EvidenceExporter:
    return EvidenceExporter(
        store,
        allowed_output_directory=allowed,
        timestamp_provider=lambda: FIXED_TIMESTAMP,
    )


@pytest.mark.parametrize(
    "output_path",
    ["../escape.zip", "nested/missing/bundle.zip"],
)
def test_path_traversal_and_invalid_locations_fail_before_store_read(
    tmp_path: pathlib.Path, output_path: str,
) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    store = _Store()

    with pytest.raises(EvidenceExportError) as failure:
        _exporter(store, allowed).export_bundle("asset-1", output_path)

    assert failure.value.args[0] in {
        "OUTPUT_PATH_NOT_ALLOWED",
        "INVALID_OUTPUT_PATH",
    }
    assert str(tmp_path) not in str(failure.value)
    assert store.read_count == 0


def test_absolute_path_outside_allowed_directory_is_rejected(
    tmp_path: pathlib.Path,
) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    store = _Store()

    with pytest.raises(EvidenceExportError, match="^OUTPUT_PATH_NOT_ALLOWED$"):
        _exporter(store, allowed).export_bundle(
            "asset-1", tmp_path / "outside.zip"
        )

    assert store.read_count == 0


def test_existing_output_is_never_overwritten(tmp_path: pathlib.Path) -> None:
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    existing = allowed / "protected.zip"
    existing.write_bytes(b"protected-content")
    store = _Store()

    with pytest.raises(EvidenceExportError, match="^OUTPUT_PATH_EXISTS$"):
        _exporter(store, allowed).export_bundle("asset-1", existing)

    assert existing.read_bytes() == b"protected-content"
    assert store.read_count == 0


def test_non_zip_output_is_rejected_with_bounded_error(
    tmp_path: pathlib.Path,
) -> None:
    store = _Store()

    with pytest.raises(EvidenceExportError, match="^OUTPUT_PATH_MUST_BE_ZIP$"):
        _exporter(store, tmp_path).export_bundle("asset-1", "bundle.json")

    assert store.read_count == 0


@pytest.mark.parametrize(
    "field_name",
    [
        "password",
        "access_token",
        "credential",
        "private_key",
        "ASSURANCE_KEY_PATH",
        "ASSURANCE_DB_PATH",
    ],
)
def test_secret_bearing_fields_fail_closed_before_output(
    tmp_path: pathlib.Path, field_name: str,
) -> None:
    output = tmp_path / "secret.zip"
    store = _Store(findings=[{"asset_id": "asset-1", field_name: "sensitive"}])

    with pytest.raises(EvidenceExportError, match="^PROHIBITED_EXPORT_FIELD$"):
        _exporter(store, tmp_path).export_bundle("asset-1", output)

    assert not output.exists()


@pytest.mark.parametrize(
    "field_name",
    [
        "risk_score",
        "confidence_score",
        "trust_score",
        "safety_score",
        "malicious_probability",
        "aggregate_assurance",
    ],
)
def test_prohibited_assurance_fields_fail_closed(
    tmp_path: pathlib.Path, field_name: str,
) -> None:
    output = tmp_path / "prohibited.zip"
    store = _Store(findings=[{"asset_id": "asset-1", field_name: 1}])

    with pytest.raises(EvidenceExportError, match="^PROHIBITED_EXPORT_FIELD$"):
        _exporter(store, tmp_path).export_bundle("asset-1", output)

    assert not output.exists()


def test_generated_bundle_contains_no_secret_or_prohibited_terms(
    tmp_path: pathlib.Path,
) -> None:
    bundle = _exporter(_Store(), tmp_path).export_bundle("asset-1", "clean.zip")
    with zipfile.ZipFile(bundle, "r") as archive:
        content = b"\n".join(archive.read(name) for name in archive.namelist()).lower()

    for prohibited in (
        b"assurance_key_path",
        b"assurance_db_path",
        b"password",
        b"token",
        b"credential",
        b"private_key",
        b"risk_score",
        b"confidence_score",
        b"trust_score",
        b"safety_score",
        b"malicious_probability",
        b"aggregate_assurance",
    ):
        assert prohibited not in content


def test_import_audit_excludes_network_process_dynamic_and_model_loading() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {
        "requests",
        "urllib",
        "socket",
        "http",
        "subprocess",
        "onnx",
        "torch",
        "pickle",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(name.name.split(".")[0] not in forbidden_imports for name in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec", "compile", "__import__"}


def test_exporter_source_has_no_store_or_audit_mutation_path() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    for prohibited in (
        "write_" + "evidence_record",
        "write_" + "finding",
        "write_" + "audit",
        "append_" + "event",
        "shell" + "=True",
    ):
        assert prohibited not in source
