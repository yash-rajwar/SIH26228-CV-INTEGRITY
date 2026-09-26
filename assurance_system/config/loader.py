"""Fail-closed loader for the assurance system's YAML configuration."""

from dataclasses import dataclass
import pathlib
from typing import Any

from assurance_system.exceptions import ConfigError


@dataclass(frozen=True)
class ResourceLimits:
    """Per-worker limits loaded from ``resource_limits.yaml``."""

    timeout_seconds: int
    memory_limit_mb: int
    max_file_descriptors: int


class ConfigLoader:
    """Read and validate the complete configuration set without defaults."""

    REQUIRED_SYSTEM_KEYS = (
        "schema_version",
        "schema_active_version_id",
        "evidence_store",
        "audit_trail",
        "signing",
        "supported_formats_config",
        "artifact_unit_defs_dir",
        "supervisor_version_id",
        "worker_temp_dir_base",
        "coco_annotation_file_max_size_bytes",
    )
    REQUIRED_EVIDENCE_STORE_KEYS = ("path",)
    REQUIRED_AUDIT_TRAIL_KEYS = ("path",)
    REQUIRED_SIGNING_KEYS = (
        "key_path",
        "public_key_path",
        "sequence_state_path",
        "algorithm",
    )
    REQUIRED_LIMIT_KEYS = (
        "timeout_seconds",
        "memory_limit_mb",
        "max_file_descriptors",
    )

    def __init__(self, config_dir: str | pathlib.Path | None = None):
        if config_dir is None:
            config_dir = pathlib.Path(__file__).parent
        self._config_dir = pathlib.Path(config_dir)

    def load(self) -> dict[str, dict[str, Any]]:
        """Load all configuration files or raise :class:`ConfigError`."""

        system_cfg = self._load_yaml("system_config.yaml")
        self._validate_required_keys(
            system_cfg, self.REQUIRED_SYSTEM_KEYS, "system_config.yaml"
        )
        self._validate_mapping(system_cfg["evidence_store"], "evidence_store")
        self._validate_required_keys(
            system_cfg["evidence_store"],
            self.REQUIRED_EVIDENCE_STORE_KEYS,
            "system_config.yaml:evidence_store",
        )
        self._validate_mapping(system_cfg["audit_trail"], "audit_trail")
        self._validate_required_keys(
            system_cfg["audit_trail"],
            self.REQUIRED_AUDIT_TRAIL_KEYS,
            "system_config.yaml:audit_trail",
        )
        self._validate_mapping(system_cfg["signing"], "signing")
        self._validate_required_keys(
            system_cfg["signing"],
            self.REQUIRED_SIGNING_KEYS,
            "system_config.yaml:signing",
        )
        self._validate_system_types(system_cfg)

        resource_cfg = self._load_yaml("resource_limits.yaml")
        self._validate_resource_limits(resource_cfg)

        supported_cfg = self._load_yaml("supported_formats.yaml")
        self._validate_supported_formats(supported_cfg)

        return {
            "system": system_cfg,
            "resource_limits": resource_cfg,
            "supported_formats": supported_cfg,
        }

    def get_resource_limits(self, worker_type: str = "default") -> ResourceLimits:
        """Return limits for ``worker_type``, falling back to ``default``."""

        config = self.load()
        resource_limits = config["resource_limits"]["resource_limits"]
        limits = resource_limits.get(worker_type, resource_limits["default"])
        return ResourceLimits(
            timeout_seconds=limits["timeout_seconds"],
            memory_limit_mb=limits["memory_limit_mb"],
            max_file_descriptors=limits["max_file_descriptors"],
        )

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = self._config_dir / filename
        if not path.is_file():
            raise ConfigError(f"Config file not found: {path}")

        try:
            import yaml
        except ImportError as exc:
            raise ConfigError(
                "PyYAML not available. Ensure it is pre-staged in wheelhouse/ "
                "and installed."
            ) from exc

        try:
            with path.open("r", encoding="utf-8") as config_file:
                data = yaml.safe_load(config_file)
        except Exception as exc:
            raise ConfigError(f"Failed to parse {filename}: {exc}") from exc

        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigError(
                f"{filename}: expected a YAML mapping, got {type(data).__name__}"
            )
        return data

    @staticmethod
    def _validate_required_keys(
        mapping: dict[str, Any], keys: tuple[str, ...], context: str
    ) -> None:
        for key in keys:
            if key not in mapping:
                raise ConfigError(
                    f"Required configuration key '{key}' missing from {context}"
                )

    @staticmethod
    def _validate_mapping(value: Any, context: str) -> None:
        if not isinstance(value, dict):
            raise ConfigError(f"{context}: expected a YAML mapping")

    @staticmethod
    def _require_nonempty_string(value: Any, context: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"{context}: expected a non-empty string")

    def _validate_system_types(self, config: dict[str, Any]) -> None:
        string_keys = (
            "schema_version",
            "schema_active_version_id",
            "supported_formats_config",
            "artifact_unit_defs_dir",
            "supervisor_version_id",
            "worker_temp_dir_base",
        )
        for key in string_keys:
            self._require_nonempty_string(config[key], f"system_config.yaml:{key}")

        self._require_nonempty_string(
            config["evidence_store"]["path"],
            "system_config.yaml:evidence_store:path",
        )
        self._require_nonempty_string(
            config["audit_trail"]["path"],
            "system_config.yaml:audit_trail:path",
        )
        for key in self.REQUIRED_SIGNING_KEYS:
            self._require_nonempty_string(
                config["signing"][key], f"system_config.yaml:signing:{key}"
            )

        size_limit = config["coco_annotation_file_max_size_bytes"]
        if isinstance(size_limit, bool) or not isinstance(size_limit, int):
            raise ConfigError(
                "system_config.yaml:coco_annotation_file_max_size_bytes: "
                "expected an integer"
            )
        if size_limit <= 0:
            raise ConfigError(
                "system_config.yaml:coco_annotation_file_max_size_bytes: "
                "expected a positive integer"
            )

    def _validate_resource_limits(self, config: dict[str, Any]) -> None:
        limits_by_worker = config.get("resource_limits")
        self._validate_mapping(limits_by_worker, "resource_limits.yaml:resource_limits")
        if "default" not in limits_by_worker:
            raise ConfigError(
                "Required configuration key 'default' missing from "
                "resource_limits.yaml:resource_limits"
            )

        for worker_type, limits in limits_by_worker.items():
            context = f"resource_limits.yaml:resource_limits:{worker_type}"
            self._validate_mapping(limits, context)
            self._validate_required_keys(limits, self.REQUIRED_LIMIT_KEYS, context)
            for key in self.REQUIRED_LIMIT_KEYS:
                value = limits[key]
                if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                    raise ConfigError(f"{context}:{key}: expected a positive integer")

    def _validate_supported_formats(self, config: dict[str, Any]) -> None:
        required = (
            "coco_in_scope",
            "onnx_in_scope",
            "yolo_task_variants",
            "pytorch_in_scope",
        )
        self._validate_required_keys(config, required, "supported_formats.yaml")
        if not isinstance(config["coco_in_scope"], bool):
            raise ConfigError("supported_formats.yaml:coco_in_scope: expected boolean")
        if not isinstance(config["onnx_in_scope"], bool):
            raise ConfigError("supported_formats.yaml:onnx_in_scope: expected boolean")
        if not isinstance(config["pytorch_in_scope"], bool):
            raise ConfigError("supported_formats.yaml:pytorch_in_scope: expected boolean")
        variants = config["yolo_task_variants"]
        if not isinstance(variants, list) or not all(
            isinstance(variant, str) and variant for variant in variants
        ):
            raise ConfigError(
                "supported_formats.yaml:yolo_task_variants: "
                "expected a list of non-empty strings"
            )
