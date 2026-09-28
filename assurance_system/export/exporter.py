"""Deterministic, read-only evidence bundle packaging for COMP-EXPORT."""

from __future__ import annotations

import datetime
import io
import json
import pathlib
import zipfile
from typing import Any, Callable

from assurance_system.constants import CANONICALIZATION_ALGORITHM_ID
from assurance_system.exceptions import AssuranceSystemError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.workers.base import is_within_directory


_BUNDLE_SCHEMA_VERSION = "v1.0"
_BUNDLE_FORMAT = "SIH26228_EVIDENCE_BUNDLE"
_FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_SOURCE_FILES = frozenset(
    {"audit.json", "evidence.json", "findings.json", "provenance.json"}
)
_BUNDLE_FILES = tuple(
    sorted(
        (
            "manifest.json",
            "findings.json",
            "evidence_records.json",
            "audit_trail.json",
            "provenance.json",
            "capabilities.json",
        )
    )
)
_PROHIBITED_ASSURANCE_FIELDS = frozenset(
    {
        "_".join(("risk", "score")),
        "_".join(("confidence", "score")),
        "_".join(("trust", "score")),
        "_".join(("safety", "score")),
        "_".join(("malicious", "probability")),
        "_".join(("aggregate", "assurance")),
        "_".join(("compromise", "probability")),
    }
)
_PROHIBITED_ENVIRONMENT_NAMES = frozenset(
    {"ASSURANCE_KEY_PATH", "ASSURANCE_DB_PATH"}
)
_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "password",
        "private_key",
        "key_material",
        "access_token",
        "auth_token",
        "bearer_token",
        "api_key",
        "secret",
        "secret_value",
        "credential",
        "credentials",
    }
)


class EvidenceExportError(AssuranceSystemError):
    """Bounded failure raised when a bundle cannot be exported safely."""


class EvidenceExporter:
    """Package approved store records without creating or modifying evidence."""

    def __init__(
        self,
        evidence_store: EvidenceStore,
        *,
        allowed_output_directory: str | pathlib.Path | None = None,
        timestamp_provider: Callable[[], str] | None = None,
    ) -> None:
        self._store = evidence_store
        self._allowed_output_directory = pathlib.Path(
            allowed_output_directory
            if allowed_output_directory is not None
            else pathlib.Path.cwd()
        )
        self._timestamp_provider = timestamp_provider or self._utc_timestamp

    @staticmethod
    def _utc_timestamp() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _canonical_json(value: Any) -> bytes:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    @staticmethod
    def _validate_asset_id(asset_id: str) -> None:
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise EvidenceExportError("INVALID_ASSET_ID")

    def _validated_output_path(self, output_path: str | pathlib.Path) -> pathlib.Path:
        if not isinstance(output_path, (str, pathlib.Path)):
            raise EvidenceExportError("INVALID_OUTPUT_PATH")
        try:
            allowed_directory = self._allowed_output_directory.resolve(strict=True)
        except OSError:
            raise EvidenceExportError("OUTPUT_DIRECTORY_UNAVAILABLE") from None
        if not allowed_directory.is_dir():
            raise EvidenceExportError("OUTPUT_DIRECTORY_UNAVAILABLE")

        candidate = pathlib.Path(output_path)
        if not candidate.is_absolute():
            candidate = allowed_directory / candidate
        try:
            candidate = candidate.resolve(strict=False)
            parent = candidate.parent.resolve(strict=True)
        except OSError:
            raise EvidenceExportError("INVALID_OUTPUT_PATH") from None

        if (
            parent != candidate.parent
            or not is_within_directory(str(candidate), str(allowed_directory))
        ):
            raise EvidenceExportError("OUTPUT_PATH_NOT_ALLOWED")
        if candidate.suffix.lower() != ".zip":
            raise EvidenceExportError("OUTPUT_PATH_MUST_BE_ZIP")
        if candidate.exists():
            raise EvidenceExportError("OUTPUT_PATH_EXISTS")
        return candidate

    @classmethod
    def _find_prohibited_field(cls, value: Any) -> str | None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_text = str(key)
                normalized = key_text.casefold()
                if (
                    key_text in _PROHIBITED_ENVIRONMENT_NAMES
                    or normalized in _PROHIBITED_ASSURANCE_FIELDS
                    or normalized in _SENSITIVE_FIELD_NAMES
                ):
                    return key_text
                found = cls._find_prohibited_field(nested)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for nested in value:
                found = cls._find_prohibited_field(nested)
                if found is not None:
                    return found
        elif isinstance(value, str) and value in _PROHIBITED_ENVIRONMENT_NAMES:
            return value
        return None

    def _read_store_export(self, asset_id: str) -> dict[str, Any]:
        source_bytes = self._store.export_bundle(asset_id)
        if not isinstance(source_bytes, bytes):
            raise EvidenceExportError("STORE_EXPORT_INVALID")
        try:
            with zipfile.ZipFile(io.BytesIO(source_bytes), mode="r") as source:
                names = source.namelist()
                if len(names) != len(set(names)) or set(names) != _SOURCE_FILES:
                    raise EvidenceExportError("STORE_EXPORT_INVALID")
                documents = {
                    name: json.loads(source.read(name).decode("utf-8"))
                    for name in sorted(_SOURCE_FILES)
                }
        except EvidenceExportError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile):
            raise EvidenceExportError("STORE_EXPORT_INVALID") from None

        if not all(isinstance(document, list) for document in documents.values()):
            raise EvidenceExportError("STORE_EXPORT_INVALID")
        return documents

    @staticmethod
    def _audit_verification(events: list[dict[str, Any]]) -> dict[str, Any]:
        violations: list[dict[str, Any]] = []
        expected_event_id = 1
        expected_predecessor = AuditChainWriter.GENESIS_HASH

        for event in events:
            if not isinstance(event, dict):
                violations.append(
                    {"event_id": "UNAVAILABLE", "violation_type": "MALFORMED_EVENT"}
                )
                continue
            event_id = event.get("event_id")
            if not isinstance(event_id, int):
                violations.append(
                    {"event_id": "UNAVAILABLE", "violation_type": "MALFORMED_EVENT"}
                )
                continue
            if event_id != expected_event_id:
                violations.append(
                    {"event_id": event_id, "violation_type": "SEQUENCE_GAP"}
                )
            if event.get("previous_event_digest") != expected_predecessor:
                violations.append(
                    {
                        "event_id": event_id,
                        "violation_type": "PREVIOUS_EVENT_DIGEST_MISMATCH",
                    }
                )
            try:
                persisted = AuditChainWriter._persisted_event_record(event)
                recomputed = AuditChainWriter._event_hash(persisted)
            except (KeyError, TypeError, ValueError):
                violations.append(
                    {"event_id": event_id, "violation_type": "MALFORMED_EVENT"}
                )
            else:
                if event.get("chain_link_hash") != recomputed:
                    violations.append(
                        {
                            "event_id": event_id,
                            "violation_type": "CHAIN_LINK_HASH_MISMATCH",
                        }
                    )
            chain_link_hash = event.get("chain_link_hash")
            if isinstance(chain_link_hash, str) and chain_link_hash:
                expected_predecessor = chain_link_hash
            expected_event_id = event_id + 1

        result: dict[str, Any] = {
            "intact": not violations,
            "scope": "EXPORTED_EVENT_CHAIN",
            "violations": violations,
        }
        if violations:
            result["result"] = "CHAIN_CORRUPT"
        return result

    def _bundle_documents(self, asset_id: str) -> dict[str, Any]:
        source = self._read_store_export(asset_id)
        deferred_records = self._store.query_deferred()
        if not isinstance(deferred_records, list):
            raise EvidenceExportError("STORE_EXPORT_INVALID")
        capabilities = [
            record
            for record in deferred_records
            if isinstance(record, dict) and record.get("asset_id") == asset_id
        ]
        audit_events = source["audit.json"]
        creation_timestamp = self._timestamp_provider()
        if not isinstance(creation_timestamp, str) or not creation_timestamp.strip():
            raise EvidenceExportError("INVALID_CREATION_TIMESTAMP")

        documents: dict[str, Any] = {
            "audit_trail.json": {
                "chain_verification": self._audit_verification(audit_events),
                "events": audit_events,
            },
            "capabilities.json": {
                "asset_id": asset_id,
                "deferred_records": capabilities,
            },
            "evidence_records.json": source["evidence.json"],
            "findings.json": source["findings.json"],
            "manifest.json": {
                "asset_id": asset_id,
                "bundle_format": _BUNDLE_FORMAT,
                "contents": list(_BUNDLE_FILES),
                "creation_timestamp": creation_timestamp,
                "json_canonicalization": CANONICALIZATION_ALGORITHM_ID,
                "schema_version": _BUNDLE_SCHEMA_VERSION,
            },
            "provenance.json": source["provenance.json"],
        }
        if set(documents) != set(_BUNDLE_FILES):
            raise EvidenceExportError("BUNDLE_CONTENT_INVALID")
        prohibited = self._find_prohibited_field(documents)
        if prohibited is not None:
            raise EvidenceExportError("PROHIBITED_EXPORT_FIELD")
        return documents

    @classmethod
    def _build_zip(cls, documents: dict[str, Any]) -> bytes:
        target = io.BytesIO()
        with zipfile.ZipFile(target, mode="w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(documents):
                info = zipfile.ZipInfo(filename=name, date_time=_FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 0
                info.external_attr = 0
                info.flag_bits = 0
                archive.writestr(info, cls._canonical_json(documents[name]))
        return target.getvalue()

    @staticmethod
    def _write_new_file(output_path: pathlib.Path, bundle: bytes) -> None:
        created = False
        try:
            with output_path.open("xb") as output_file:
                created = True
                output_file.write(bundle)
        except FileExistsError:
            raise EvidenceExportError("OUTPUT_PATH_EXISTS") from None
        except OSError:
            cleanup_failed = False
            if created:
                try:
                    output_path.unlink(missing_ok=True)
                except OSError:
                    cleanup_failed = True
            if cleanup_failed:
                raise EvidenceExportError("EVIDENCE_EXPORT_CLEANUP_FAILED") from None
            raise EvidenceExportError("EVIDENCE_EXPORT_FAILED") from None

    def export_bundle(
        self, asset_id: str, output_path: str | pathlib.Path
    ) -> pathlib.Path:
        """Create the approved six-document ZIP and return its contained path."""

        self._validate_asset_id(asset_id)
        target = self._validated_output_path(output_path)
        try:
            documents = self._bundle_documents(asset_id)
            bundle = self._build_zip(documents)
            self._write_new_file(target, bundle)
        except EvidenceExportError:
            raise
        except Exception:
            raise EvidenceExportError("EVIDENCE_EXPORT_FAILED") from None
        return target
