"""Trusted supervisor orchestration for the offline assurance pipeline.

The supervisor controls worker subprocesses and persistence. It never opens
submitted assets or runs worker analysis in-process.
"""

from __future__ import annotations

import copy
import dataclasses
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from typing import Any

from assurance_system.config.loader import ConfigLoader, ResourceLimits
from assurance_system.constants import (
    AccessMode,
    AssessmentStatus,
    AuditEventType,
    IdentityQuality,
    ReferenceHealth,
)
from assurance_system.exceptions import (
    AuditWriteError,
    IngestError,
    PipelineError,
    SchemaViolationError,
)
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.capability_declaration import CapabilityDeclaration
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.interpretation import C5InterpretationEngine
from assurance_system.supervisor.provenance import ProvenanceBuilder
from assurance_system.supervisor.reference_manager import ReferenceManager
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers.base import is_within_directory


_MANIFEST_FORMATS = frozenset(
    {
        "COCO",
        "YOLO_DETECTION",
        "YOLO_SEG",
        "YOLO_POSE",
        "YOLO_OBB",
        "ONNX",
        "PYTORCH",
        "TORCHSCRIPT",
    }
)
_DATA_FORMATS = frozenset(
    {"COCO", "YOLO_DETECTION", "YOLO_SEG", "YOLO_POSE", "YOLO_OBB"}
)
_MODEL_FORMATS = frozenset({"ONNX", "PYTORCH", "TORCHSCRIPT"})
_SUPERVISOR_FIELDS = frozenset(
    {"record_id", "asset_id", "record_digest", "is_synthetic", "created_at"}
)
_PROHIBITED_INPUT_FIELDS = frozenset({"key_path", "db_path"})
_PROHIBITED_INPUT_FRAGMENTS = ("password", "secret", "credential")
_WORKER_INPUT_SCHEMA = "worker-input-v1"


@dataclasses.dataclass(frozen=True)
class PipelineRunSummary:
    """Operational counts for one successfully completed pipeline run."""

    run_id: str
    assets_processed: int
    workers_dispatched: int
    worker_results_rejected: int
    evidence_records_written: int
    deferred_records_written: int
    provenance_records_written: int
    findings_written: int
    started_at: str
    completed_at: str


@dataclasses.dataclass(frozen=True)
class _WorkerSpec:
    task_name: str
    worker_id: str
    method_id: str
    module_name: str


@dataclasses.dataclass
class _PendingWorker:
    process: subprocess.Popen
    task_spec: dict[str, Any]
    resource_limits: ResourceLimits
    temp_directory: pathlib.Path
    result_path: pathlib.Path


@dataclasses.dataclass
class _RunCounters:
    workers_dispatched: int = 0
    worker_results_rejected: int = 0
    evidence_records_written: int = 0
    deferred_records_written: int = 0
    provenance_records_written: int = 0
    findings_written: int = 0


_C2_WORKERS = (
    _WorkerSpec(
        "C2A_STRUCTURAL",
        "COMP-W-C2A",
        "M01",
        "assurance_system.workers.c2a_structural",
    ),
    _WorkerSpec(
        "C2B_EXACT_HASH",
        "COMP-W-C2B",
        "M02",
        "assurance_system.workers.c2b_exact_hash",
    ),
    _WorkerSpec(
        "C2C_CONCENTRATION",
        "COMP-W-C2C",
        "M06",
        "assurance_system.workers.c2c_concentration",
    ),
    _WorkerSpec(
        "C2D_IMAGE_HASH",
        "COMP-W-C2D",
        "M15",
        "assurance_system.workers.c2d_image_hash",
    ),
)
_C3A = _WorkerSpec(
    "C3A_ARTIFACT_UNIT",
    "COMP-W-C3A",
    "C3A",
    "assurance_system.workers.c3a_artifact_unit",
)
_C3B = _WorkerSpec(
    "C3B_MODEL_HASH",
    "COMP-W-C3B",
    "C3B",
    "assurance_system.workers.c3b_model_hash",
)
_C3C = _WorkerSpec(
    "C3C_ONNX_STRUCTURAL",
    "COMP-W-C3C",
    "C3C",
    "assurance_system.workers.c3c_onnx_structural",
)
_C3D = _WorkerSpec(
    "C3D_SAFE_LOAD",
    "COMP-W-C3D",
    "C3D",
    "assurance_system.workers.c3d_safe_load",
)
_WORKER_BY_TASK = {
    spec.task_name: spec for spec in (*_C2_WORKERS, _C3A, _C3B, _C3C, _C3D)
}
_WORKER_BY_METHOD = {spec.method_id: spec for spec in _WORKER_BY_TASK.values()}


class _SchemaGatedStore:
    """Validate C4 records before delegating their supervisor-owned write."""

    def __init__(self, store: EvidenceStore, validator: EvidenceSchemaValidator):
        self._store = store
        self._validator = validator

    def __getattr__(self, name: str) -> Any:
        return getattr(self._store, name)

    def write_provenance_record(self, record: dict) -> str:
        result = self._validator.validate_provenance_record(record)
        if not result.valid:
            raise SchemaViolationError(
                result.reason or "provenance record rejected by schema gate"
            )
        return self._store.write_provenance_record(record)


class SupervisorOrchestrator:
    """Coordinate untrusted workers and trusted supervisor components."""

    def __init__(
        self,
        evidence_store: EvidenceStore,
        audit_chain: AuditChainWriter,
        *,
        schema_validator: EvidenceSchemaValidator | None = None,
        config_loader: ConfigLoader | None = None,
        worker_temp_dir_base: str | os.PathLike[str] | None = None,
        python_executable: str | None = None,
    ) -> None:
        self._store = evidence_store
        self._audit = audit_chain
        self._schema = schema_validator or EvidenceSchemaValidator()
        self._config = config_loader or ConfigLoader()
        self._reference_manager = ReferenceManager(evidence_store, audit_chain)
        self._capabilities = CapabilityDeclaration(evidence_store, audit_chain)
        self._interpretation = C5InterpretationEngine(self._schema)
        gated_store = _SchemaGatedStore(evidence_store, self._schema)
        self._provenance = ProvenanceBuilder(gated_store, audit_chain)
        self._worker_temp_dir_base = (
            pathlib.Path(worker_temp_dir_base)
            if worker_temp_dir_base is not None
            else None
        )
        self._python_executable = python_executable or sys.executable
        self._asset_synthetic: dict[str, bool] = {}
        self._accepted_records: dict[str, dict[str, Any]] = {}
        self._pipeline_active = False

    @staticmethod
    def _timestamp() -> str:
        return (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _canonical_bytes(value: dict[str, Any]) -> bytes:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    @classmethod
    def _contains_prohibited_input(cls, value: Any) -> bool:
        if isinstance(value, dict):
            for key, nested in value.items():
                normalized = str(key).casefold()
                if normalized in _PROHIBITED_INPUT_FIELDS or any(
                    fragment in normalized
                    for fragment in _PROHIBITED_INPUT_FRAGMENTS
                ):
                    return True
                if cls._contains_prohibited_input(nested):
                    return True
        elif isinstance(value, (list, tuple)):
            return any(cls._contains_prohibited_input(item) for item in value)
        return False

    @staticmethod
    def _required_text(value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise IngestError(f"{field_name} must be a non-empty string")
        return value

    def _load_manifest(self, manifest_path: str) -> dict[str, Any]:
        path_text = self._required_text(manifest_path, "manifest_path")
        path = pathlib.Path(path_text)
        try:
            serialized = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise IngestError("submission manifest could not be read") from exc

        try:
            if path.suffix.casefold() in {".yaml", ".yml"}:
                import yaml

                manifest = yaml.safe_load(serialized)
            else:
                manifest = json.loads(serialized)
        except Exception as exc:
            raise IngestError("submission manifest could not be parsed") from exc
        return self._validate_manifest(manifest)

    def _validate_manifest(self, manifest: Any) -> dict[str, Any]:
        if not isinstance(manifest, dict):
            raise IngestError("submission manifest must be an object")
        if self._contains_prohibited_input(manifest):
            raise IngestError("submission manifest contains a prohibited field")
        self._required_text(manifest.get("schema_version"), "schema_version")

        asset_directory = os.path.realpath(
            self._required_text(manifest.get("asset_directory"), "asset_directory")
        )
        if not os.path.isabs(asset_directory) or not os.path.isdir(asset_directory):
            raise IngestError("asset_directory must be an existing absolute directory")

        assets = manifest.get("assets")
        if not isinstance(assets, list) or not assets:
            raise IngestError("assets must be a non-empty list")

        normalized_assets: list[dict[str, Any]] = []
        asset_ids: set[str] = set()
        for asset in assets:
            if not isinstance(asset, dict):
                raise IngestError("each asset entry must be an object")
            asset_id = self._required_text(asset.get("asset_id"), "asset_id")
            if asset_id in asset_ids:
                raise IngestError("asset_id values must be unique")
            asset_ids.add(asset_id)

            format_name = self._required_text(asset.get("format"), "format").upper()
            if format_name not in _MANIFEST_FORMATS:
                raise IngestError("asset format is outside the frozen vocabulary")

            entry_directory = os.path.realpath(
                asset.get("asset_directory", asset_directory)
            )
            if not (
                os.path.isabs(entry_directory)
                and os.path.isdir(entry_directory)
                and is_within_directory(entry_directory, asset_directory)
            ):
                raise IngestError("asset entry directory is not contained")

            paths = asset.get("asset_paths")
            if not isinstance(paths, list) or not paths:
                raise IngestError("asset_paths must be a non-empty list")
            normalized_paths: list[str] = []
            for submitted_path in paths:
                submitted_path = self._required_text(
                    submitted_path, "asset_paths entry"
                )
                if not os.path.isabs(submitted_path):
                    raise IngestError("asset paths must be absolute")
                normalized_path = os.path.realpath(submitted_path)
                if not is_within_directory(normalized_path, entry_directory):
                    raise IngestError("asset path is not contained")
                normalized_paths.append(normalized_path)
            if format_name in _MODEL_FORMATS and len(normalized_paths) != 1:
                raise IngestError("model asset entries require exactly one path")

            artifact_definition = (
                "pytorch-single-file-v1"
                if format_name == "PYTORCH"
                else "UNAVAILABLE"
            )
            supplied_definition = asset.get("artifact_unit_definition_id")
            if (
                supplied_definition is not None
                and supplied_definition != artifact_definition
            ):
                raise IngestError(
                    "artifact_unit_definition_id does not match the approved definition"
                )
            identity_quality = asset.get(
                "identity_quality", IdentityQuality.UNTRUSTED
            )
            if identity_quality not in {
                IdentityQuality.UNTRUSTED,
                IdentityQuality.UNAVAILABLE,
            }:
                raise IngestError(
                    "manifest identity_quality cannot establish trusted identity"
                )
            contributor_metadata = asset.get("contributor_metadata", [])
            if not isinstance(contributor_metadata, list) or any(
                not isinstance(item, dict) for item in contributor_metadata
            ):
                raise IngestError("contributor_metadata must be a list of objects")
            reference_digest = asset.get("reference_digest")
            if reference_digest is not None:
                raise IngestError(
                    "reference_digest must come from the supervisor reference path"
                )
            reference_id = asset.get("reference_id")
            if reference_id is not None:
                self._required_text(reference_id, "reference_id")
            is_synthetic = asset.get("is_synthetic", False)
            if type(is_synthetic) is not bool:
                raise IngestError("is_synthetic must be boolean")

            normalized = dict(asset)
            normalized.update(
                {
                    "asset_id": asset_id,
                    "asset_directory": entry_directory,
                    "asset_paths": normalized_paths,
                    "format": format_name,
                    "artifact_unit_definition_id": artifact_definition,
                    "identity_quality": identity_quality,
                    "contributor_metadata": copy.deepcopy(contributor_metadata),
                    "reference_digest": reference_digest,
                    "reference_id": reference_id,
                    "is_synthetic": is_synthetic,
                }
            )
            normalized_assets.append(normalized)

        validated = dict(manifest)
        validated["asset_directory"] = asset_directory
        validated["assets"] = normalized_assets
        return validated

    def _resource_limits(self, task_name: str) -> ResourceLimits:
        limits = self._config.get_resource_limits(task_name)
        values = (
            limits.timeout_seconds,
            limits.memory_limit_mb,
            limits.max_file_descriptors,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            raise PipelineError("worker resource limits are missing or invalid")
        return limits

    @staticmethod
    def _resource_contract(limits: ResourceLimits) -> dict[str, int]:
        return {
            "timeout_s": limits.timeout_seconds,
            "memory_mb": limits.memory_limit_mb,
            "max_fds": limits.max_file_descriptors,
        }

    def _task_spec(
        self,
        worker: _WorkerSpec,
        asset: dict[str, Any],
        *,
        artifact_unit: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], ResourceLimits]:
        limits = self._resource_limits(worker.task_name)
        task = {
            "schema_version": _WORKER_INPUT_SCHEMA,
            "task": worker.task_name,
            "asset_paths": list(asset["asset_paths"]),
            "format": asset["format"],
            "asset_directory": asset["asset_directory"],
            "artifact_unit_definition_id": asset["artifact_unit_definition_id"],
            "resource_limits": self._resource_contract(limits),
            "identity_quality": asset["identity_quality"],
        }
        if asset.get("task_variant") is not None:
            task["task_variant"] = asset["task_variant"]
        if asset.get("reference_digest") is not None:
            task["reference_digest"] = asset["reference_digest"]
        if asset.get("contributor_metadata"):
            task["contributor_metadata"] = copy.deepcopy(
                asset["contributor_metadata"]
            )
        if worker is _C3B:
            task["artifact_unit"] = copy.deepcopy(artifact_unit)
            if isinstance(artifact_unit, dict):
                definition_id = artifact_unit.get("artifact_unit_definition_id")
                if isinstance(definition_id, str) and definition_id:
                    task["artifact_unit_definition_id"] = definition_id
        return task, limits

    def _clean_worker_environment(self, temp_directory: pathlib.Path) -> dict[str, str]:
        allowed = {
            "PATH",
            "PATHEXT",
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "LANG",
            "LC_ALL",
            "TZ",
        }
        clean_env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in allowed
        }
        package_root = str(pathlib.Path(__file__).resolve().parents[2])
        clean_env.update(
            {
                "PYTHONPATH": package_root,
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONIOENCODING": "utf-8",
                "TEMP": str(temp_directory),
                "TMP": str(temp_directory),
            }
        )
        clean_env.pop("ASSURANCE_KEY_PATH", None)
        clean_env.pop("ASSURANCE_DB_PATH", None)
        return clean_env

    def _start_worker(
        self,
        worker_module: str,
        task_spec: dict[str, Any],
        resource_limits: ResourceLimits,
    ) -> _PendingWorker | dict[str, Any]:
        temp_directory: pathlib.Path | None = None
        try:
            if self._contains_prohibited_input(task_spec):
                raise ValueError("worker task contains a prohibited field")
            worker = _WORKER_BY_TASK.get(str(task_spec.get("task")))
            if worker is None or worker.module_name != worker_module:
                raise ValueError("worker module does not match the approved task")
            limit_values = (
                resource_limits.timeout_seconds,
                resource_limits.memory_limit_mb,
                resource_limits.max_file_descriptors,
            )
            if any(
                type(value) is not int or value <= 0 for value in limit_values
            ):
                raise ValueError("worker resource limits are missing or invalid")
            temp_directory = pathlib.Path(
                tempfile.mkdtemp(
                    prefix="assurance-worker-",
                    dir=(
                        str(self._worker_temp_dir_base)
                        if self._worker_temp_dir_base is not None
                        else None
                    ),
                )
            )
            task_path = temp_directory / "task.json"
            result_path = temp_directory / "result.json"
            task_path.write_text(
                json.dumps(task_spec, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            try:
                task_path.chmod(0o600)
            except OSError:
                pass

            self._audit.append_event(
                AuditEventType.WORKER_DISPATCHED,
                {
                    "worker_id": task_spec.get("task", "UNAVAILABLE"),
                    "worker_module": worker_module,
                    "resource_limits": self._resource_contract(resource_limits),
                },
            )
            command = [
                self._python_executable,
                "-m",
                worker_module,
                "--task-file",
                str(task_path),
                "--result-file",
                str(result_path),
            ]
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                close_fds=True,
                cwd=str(temp_directory),
                env=self._clean_worker_environment(temp_directory),
            )
            return _PendingWorker(
                process=process,
                task_spec=task_spec,
                resource_limits=resource_limits,
                temp_directory=temp_directory,
                result_path=result_path,
            )
        except AuditWriteError:
            if temp_directory is not None:
                shutil.rmtree(temp_directory, ignore_errors=True)
            raise
        except Exception as exc:
            if temp_directory is not None:
                shutil.rmtree(temp_directory, ignore_errors=True)
            return self._build_assessment_error(
                task_spec, "SPAWN_ERROR", type(exc).__name__
            )

    def _collect_worker(self, pending: _PendingWorker) -> dict[str, Any]:
        try:
            try:
                pending.process.communicate(
                    timeout=pending.resource_limits.timeout_seconds
                )
            except subprocess.TimeoutExpired:
                pending.process.kill()
                pending.process.wait()
                return self._build_assessment_error(
                    pending.task_spec,
                    "TIMEOUT",
                    "worker exceeded its configured wall-clock limit",
                )

            if pending.process.returncode != 0:
                return self._build_assessment_error(
                    pending.task_spec,
                    "NONZERO_EXIT",
                    "worker process exited unsuccessfully",
                )
            if not pending.result_path.is_file():
                return self._build_assessment_error(
                    pending.task_spec,
                    "NO_RESULT_FILE",
                    "worker did not produce its named result file",
                )
            try:
                result_metadata = pending.result_path.lstat()
            except OSError as exc:
                return self._build_assessment_error(
                    pending.task_spec,
                    "INVALID_RESULT",
                    type(exc).__name__,
                )
            if (
                not stat.S_ISREG(result_metadata.st_mode)
                or pending.result_path.is_symlink()
                or not is_within_directory(
                    str(pending.result_path), str(pending.temp_directory)
                )
            ):
                return self._build_assessment_error(
                    pending.task_spec,
                    "INVALID_RESULT_FILE_TYPE",
                    "worker result was not a contained regular file",
                )
            try:
                raw_result = json.loads(
                    pending.result_path.read_text(encoding="utf-8")
                )
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                return self._build_assessment_error(
                    pending.task_spec,
                    "INVALID_RESULT",
                    type(exc).__name__,
                )
            if not isinstance(raw_result, dict):
                return self._build_assessment_error(
                    pending.task_spec,
                    "INVALID_RESULT",
                    "worker result was not an object",
                )
            return raw_result
        except Exception as exc:
            return self._build_assessment_error(
                pending.task_spec, "COLLECTION_ERROR", type(exc).__name__
            )
        finally:
            self._cleanup_pending_worker(pending)

    @staticmethod
    def _cleanup_pending_worker(pending: _PendingWorker) -> None:
        try:
            if pending.process.poll() is None:
                pending.process.kill()
                pending.process.wait()
        finally:
            shutil.rmtree(pending.temp_directory, ignore_errors=True)

    def _dispatch_worker(
        self,
        worker_module: str,
        task_spec: dict,
        resource_limits: ResourceLimits,
    ) -> dict:
        """Run one worker through named-file IPC and clean every temp resource."""

        pending = self._start_worker(worker_module, task_spec, resource_limits)
        if isinstance(pending, dict):
            return pending
        return self._collect_worker(pending)

    def _dispatch_batch(
        self,
        requests: list[tuple[_WorkerSpec, dict[str, Any], ResourceLimits]],
    ) -> list[dict[str, Any]]:
        """Spawn every requested worker before collecting any worker result."""

        started: list[_PendingWorker | dict[str, Any]] = []
        try:
            for worker, task_spec, limits in requests:
                started.append(
                    self._start_worker(worker.module_name, task_spec, limits)
                )
        except Exception:
            for pending in started:
                if isinstance(pending, _PendingWorker):
                    self._cleanup_pending_worker(pending)
            raise

        results: list[dict[str, Any]] = []
        for pending in started:
            if isinstance(pending, dict):
                results.append(pending)
            else:
                results.append(self._collect_worker(pending))
        return results

    def _build_assessment_error(
        self, task_spec: dict, reason: str, detail: str = ""
    ) -> dict:
        """Build a fail-closed result without exposing exception text or paths."""

        del detail
        task_name = task_spec.get("task") if isinstance(task_spec, dict) else None
        worker = _WORKER_BY_TASK.get(str(task_name))
        worker_id = worker.worker_id if worker is not None else "COMP-W-UNKNOWN"
        return {
            "schema_version": "worker-output-v1",
            "worker_id": worker_id,
            "assessment_status": AssessmentStatus.ASSESSMENT_ERROR,
            "raw_signal": {"failure_reason": str(reason)},
            "access_mode": AccessMode.UNAVAILABLE,
            "artifact_unit_id": "UNAVAILABLE",
            "coverage_gap_clean_label": True,
            "limitations": ["Worker assessment did not complete."],
            "non_claims": [
                "No positive assurance conclusion is available from this failed assessment."
            ],
            "dependency_declaration": {
                "co_firing_detectors": [],
                "independence_established": False,
            },
            "assessment_timestamp": self._timestamp(),
            "error_detail": str(reason),
        }

    def _worker_validation_reason(
        self, raw_result: dict, method_id: str
    ) -> str | None:
        worker = _WORKER_BY_METHOD.get(method_id)
        if worker is None:
            return "unknown method identifier"
        if any(field in raw_result for field in _SUPERVISOR_FIELDS):
            return "worker supplied a supervisor-owned field"
        if raw_result.get("worker_id") != worker.worker_id:
            return "worker identity does not match dispatched method"
        validation = self._schema.validate_worker_output(
            raw_result, worker.task_name
        )
        return None if validation.valid else validation.reason or "schema rejection"

    def _audit_worker_rejection(
        self, asset_id: str, method_id: str, reason: str
    ) -> None:
        self._audit.append_event(
            AuditEventType.WORKER_RESULT_REJECTED_SCHEMA_VIOLATION,
            {
                "asset_id": asset_id,
                "method_id": method_id,
                "reason": reason,
            },
        )

    def _accept_worker_result(
        self, raw_result: dict, asset_id: str, method_id: str
    ) -> str:
        """Validate, identify, digest, persist, and audit one worker result."""

        reason = self._worker_validation_reason(raw_result, method_id)
        if reason is not None:
            self._audit_worker_rejection(asset_id, method_id, reason)
            raise SchemaViolationError(reason)

        record = copy.deepcopy(raw_result)
        record.update(
            {
                "record_id": str(uuid.uuid4()),
                "asset_id": asset_id,
                "method_id": method_id,
                "is_synthetic": self._asset_synthetic.get(asset_id, False),
            }
        )
        record["record_digest"] = hashlib.sha256(
            self._canonical_bytes(record)
        ).hexdigest()
        record_id = self._store.write_evidence_record(record)
        self._accepted_records[record_id] = record
        event_payload = {
            "record_id": record_id,
            "asset_id": asset_id,
            "method_id": method_id,
            "worker_id": record["worker_id"],
            "assessment_status": record["assessment_status"],
            "record_digest": record["record_digest"],
        }
        self._audit.append_event(AuditEventType.WORKER_RESULT_ACCEPTED, event_payload)
        self._audit.append_event(AuditEventType.EVIDENCE_RECORD_WRITTEN, event_payload)
        return record_id

    def _process_results(
        self,
        asset_id: str,
        items: list[tuple[_WorkerSpec, dict[str, Any], dict[str, Any]]],
        counters: _RunCounters,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Prevalidate the complete batch before writing any valid result."""

        validation_reasons = [
            self._worker_validation_reason(result, worker.method_id)
            for worker, _task, result in items
        ]
        evidence_for_c5: list[dict[str, Any]] = []
        accepted: list[dict[str, Any]] = []

        for (worker, task, result), reason in zip(
            items, validation_reasons, strict=True
        ):
            if reason is not None:
                self._audit_worker_rejection(asset_id, worker.method_id, reason)
                counters.worker_results_rejected += 1
                evidence_for_c5.append(
                    self._build_assessment_error(task, "SCHEMA_VIOLATION")
                )
                continue
            record_id = self._accept_worker_result(
                result, asset_id, worker.method_id
            )
            record = self._accepted_records[record_id]
            accepted.append(record)
            evidence_for_c5.append(record)
            counters.evidence_records_written += 1
        return evidence_for_c5, accepted

    def _run_c2(
        self, asset: dict[str, Any], counters: _RunCounters
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        requests: list[tuple[_WorkerSpec, dict[str, Any], ResourceLimits]] = []
        for worker in _C2_WORKERS:
            task, limits = self._task_spec(worker, asset)
            requests.append((worker, task, limits))
        results = self._dispatch_batch(requests)
        counters.workers_dispatched += len(requests)
        items = [
            (worker, task, result)
            for (worker, task, _limits), result in zip(
                requests, results, strict=True
            )
        ]
        return self._process_results(asset["asset_id"], items, counters)

    def _run_one_worker(
        self,
        worker: _WorkerSpec,
        asset: dict[str, Any],
        counters: _RunCounters,
        *,
        artifact_unit: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        task, limits = self._task_spec(
            worker, asset, artifact_unit=artifact_unit
        )
        result = self._dispatch_worker(worker.module_name, task, limits)
        counters.workers_dispatched += 1
        for_c5, accepted = self._process_results(
            asset["asset_id"], [(worker, task, result)], counters
        )
        return for_c5[0], accepted[0] if accepted else None

    def _run_c3(
        self, asset: dict[str, Any], counters: _RunCounters
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        evidence_for_c5: list[dict[str, Any]] = []
        accepted: list[dict[str, Any]] = []

        c3a_for_c5, c3a_record = self._run_one_worker(_C3A, asset, counters)
        evidence_for_c5.append(c3a_for_c5)
        if c3a_record is not None:
            accepted.append(c3a_record)
        if (
            c3a_for_c5.get("assessment_status")
            == AssessmentStatus.ONNX_PATH_CONTAINMENT_VIOLATION
        ):
            return evidence_for_c5, accepted

        c3a_signal = c3a_for_c5.get("raw_signal")
        artifact_unit = (
            c3a_signal.get("artifact_unit")
            if isinstance(c3a_signal, dict)
            else None
        )
        c3b_for_c5, c3b_record = self._run_one_worker(
            _C3B, asset, counters, artifact_unit=artifact_unit
        )
        evidence_for_c5.append(c3b_for_c5)
        if c3b_record is not None:
            accepted.append(c3b_record)

        tail_workers: list[_WorkerSpec] = []
        if asset["format"] == "ONNX":
            tail_workers.append(_C3C)
        elif asset["format"] == "PYTORCH":
            tail_workers.append(_C3D)
        if tail_workers:
            requests: list[
                tuple[_WorkerSpec, dict[str, Any], ResourceLimits]
            ] = []
            for worker in tail_workers:
                task, limits = self._task_spec(
                    worker, asset, artifact_unit=artifact_unit
                )
                requests.append((worker, task, limits))
            results = self._dispatch_batch(requests)
            counters.workers_dispatched += len(requests)
            items = [
                (worker, task, result)
                for (worker, task, _limits), result in zip(
                    requests, results, strict=True
                )
            ]
            tail_for_c5, tail_accepted = self._process_results(
                asset["asset_id"], items, counters
            )
            evidence_for_c5.extend(tail_for_c5)
            accepted.extend(tail_accepted)
        return evidence_for_c5, accepted

    def _emit_deferred_in_scope_records(self, asset_id: str) -> list[dict]:
        return self._capabilities.emit_deferred_records(asset_id)

    @staticmethod
    def _supported_capabilities(format_name: str) -> list[str]:
        if format_name in _DATA_FORMATS:
            return ["M01", "M02", "M06", "M15"]
        if format_name == "PYTORCH":
            return ["C3A", "C3B", "C3D"]
        if format_name == "ONNX":
            return ["C3A", "C3B"]
        return []

    def _build_provenance(
        self, evidence_records: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        c3b_record = next(
            (
                record
                for record in evidence_records
                if record.get("worker_id") == _C3B.worker_id
            ),
            None,
        )
        if (
            c3b_record is None
            or c3b_record.get("assessment_status") != AssessmentStatus.COMPLETED
        ):
            return None
        raw_signal = c3b_record.get("raw_signal")
        digest = (
            raw_signal.get("combined_artifact_unit_digest")
            if isinstance(raw_signal, dict)
            else None
        )
        if not isinstance(digest, str) or not digest:
            raise PipelineError("completed C3B record omitted its artifact digest")
        evidence_digests = [
            record["record_digest"]
            for record in evidence_records
            if isinstance(record.get("record_digest"), str)
            and record["record_digest"]
        ]
        if len(evidence_digests) != len(evidence_records):
            raise PipelineError("accepted evidence record omitted its digest")
        return self._provenance.build_and_sign(digest, evidence_digests)

    def _persist_finding(self, finding: dict[str, Any]) -> str:
        validation = self._schema.validate_finding(finding)
        if not validation.valid:
            raise SchemaViolationError(
                validation.reason or "finding rejected by schema gate"
            )
        finding_id = self._store.write_finding(finding)
        self._audit.append_event(
            AuditEventType.FINDING_WRITTEN,
            {
                "finding_id": finding_id,
                "asset_id": finding["asset_id"],
                "method_id": finding["method_id"],
                "detection_status": finding["detection_status"],
            },
        )
        return finding_id

    def _reference_health(self, asset: dict[str, Any]) -> str:
        reference_id = asset.get("reference_id")
        if not isinstance(reference_id, str) or not reference_id:
            return ReferenceHealth.UNAVAILABLE
        return self._reference_manager.get_reference_health(reference_id)

    @staticmethod
    def _access_mode(evidence_records: list[dict[str, Any]]) -> str:
        for record in evidence_records:
            value = record.get("access_mode")
            if isinstance(value, str) and value != AccessMode.UNAVAILABLE:
                return value
        return AccessMode.UNAVAILABLE

    def run_pipeline(self, manifest_path: str) -> PipelineRunSummary:
        """Run the complete fail-closed pipeline for a validated manifest."""

        if self._pipeline_active:
            raise PipelineError("a pipeline run is already active")
        self._pipeline_active = True
        self._asset_synthetic.clear()
        self._accepted_records.clear()
        counters = _RunCounters()
        run_id = str(uuid.uuid4())
        started_at = self._timestamp()

        try:
            self._audit.append_event(
                AuditEventType.PIPELINE_RUN_START,
                {"run_id": run_id, "started_at": started_at},
            )
            manifest = self._load_manifest(manifest_path)
            for asset in manifest["assets"]:
                asset_id = asset["asset_id"]
                self._asset_synthetic[asset_id] = asset["is_synthetic"]
                self._capabilities.declare_capabilities(
                    asset_id,
                    self._supported_capabilities(asset["format"]),
                )
                deferred = self._emit_deferred_in_scope_records(asset_id)
                counters.deferred_records_written += len(deferred)

                if asset["format"] in _DATA_FORMATS:
                    evidence_for_c5, accepted = self._run_c2(asset, counters)
                else:
                    evidence_for_c5, accepted = self._run_c3(asset, counters)

                c4_binding = self._build_provenance(accepted)
                if c4_binding is not None:
                    counters.provenance_records_written += 1
                finding = self._interpretation.produce_finding(
                    asset_id=asset_id,
                    method_id="COMP-C5",
                    evidence_records=evidence_for_c5,
                    c4_binding=c4_binding,
                    reference_health=self._reference_health(asset),
                    access_mode=self._access_mode(evidence_for_c5),
                )
                self._persist_finding(finding)
                counters.findings_written += 1

            completed_at = self._timestamp()
            summary = PipelineRunSummary(
                run_id=run_id,
                assets_processed=len(manifest["assets"]),
                workers_dispatched=counters.workers_dispatched,
                worker_results_rejected=counters.worker_results_rejected,
                evidence_records_written=counters.evidence_records_written,
                deferred_records_written=counters.deferred_records_written,
                provenance_records_written=counters.provenance_records_written,
                findings_written=counters.findings_written,
                started_at=started_at,
                completed_at=completed_at,
            )
            self._audit.append_event(
                AuditEventType.PIPELINE_RUN_COMPLETE,
                dataclasses.asdict(summary),
            )
            return summary
        except AuditWriteError:
            raise
        except Exception as exc:
            self._audit.append_event(
                AuditEventType.PIPELINE_RUN_ERROR,
                {
                    "run_id": run_id,
                    "started_at": started_at,
                    "failed_component": type(exc).__name__,
                },
            )
            if isinstance(exc, PipelineError):
                raise
            raise PipelineError("pipeline run failed closed") from exc
        finally:
            self._pipeline_active = False
            self._asset_synthetic.clear()
            self._accepted_records.clear()
