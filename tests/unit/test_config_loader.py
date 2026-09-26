import pathlib

import pytest

from assurance_system.config.loader import ConfigLoader, ResourceLimits
from assurance_system.exceptions import ConfigError


CONFIG_DIR = (
    pathlib.Path(__file__).parent.parent.parent / "assurance_system" / "config"
)


def test_load_valid_config():
    loader = ConfigLoader(config_dir=CONFIG_DIR)
    config = loader.load()
    assert set(config) == {"system", "resource_limits", "supported_formats"}
    assert config["system"]["schema_version"] == "v1.0"
    assert config["system"]["schema_active_version_id"] == "worker-output-v1"
    assert config["system"]["signing"]["algorithm"] == "HMAC-SHA256"


def test_missing_required_key_raises_config_error(tmp_path):
    _write_complete_config_set(tmp_path)
    (tmp_path / "system_config.yaml").write_text(
        "evidence_store:\n  path: /tmp/x.db\n", encoding="utf-8"
    )
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigError, match="schema_version"):
        loader.load()


def test_invalid_yaml_raises_config_error(tmp_path):
    _write_complete_config_set(tmp_path)
    (tmp_path / "system_config.yaml").write_text(
        ": invalid: yaml: content: :\n", encoding="utf-8"
    )
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigError, match="Failed to parse"):
        loader.load()


def test_resource_limits_accessible_per_worker():
    loader = ConfigLoader(config_dir=CONFIG_DIR)
    default_limits = loader.get_resource_limits("default")
    assert default_limits == ResourceLimits(120, 2048, 64)

    safe_load_limits = loader.get_resource_limits("C3D_SAFE_LOAD")
    assert safe_load_limits == ResourceLimits(60, 4096, 32)


def test_unknown_worker_uses_default_limits():
    loader = ConfigLoader(config_dir=CONFIG_DIR)
    assert loader.get_resource_limits("UNKNOWN_WORKER") == ResourceLimits(
        120, 2048, 64
    )


def test_supported_formats_match_pre05_decision():
    supported = ConfigLoader(config_dir=CONFIG_DIR).load()["supported_formats"]
    assert supported == {
        "coco_in_scope": True,
        "onnx_in_scope": True,
        "yolo_task_variants": ["YOLO_DETECTION", "YOLO_SEG"],
        "pytorch_in_scope": True,
    }


def test_missing_config_file_raises_config_error(tmp_path):
    _write_complete_config_set(tmp_path)
    (tmp_path / "resource_limits.yaml").unlink()
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigError, match="not found"):
        loader.load()


def test_invalid_resource_limit_type_raises_config_error(tmp_path):
    _write_complete_config_set(tmp_path)
    (tmp_path / "resource_limits.yaml").write_text(
        "resource_limits:\n"
        "  default:\n"
        "    timeout_seconds: invalid\n"
        "    memory_limit_mb: 512\n"
        "    max_file_descriptors: 16\n",
        encoding="utf-8",
    )
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigError, match="timeout_seconds"):
        loader.load()


def _write_complete_config_set(config_dir):
    (config_dir / "system_config.yaml").write_text(
        "schema_version: v1.0\n"
        "schema_active_version_id: worker-output-v1\n"
        "evidence_store:\n  path: /tmp/x.db\n"
        "audit_trail:\n  path: /tmp/a.db\n"
        "signing:\n"
        "  key_path: /tmp/k.bin\n"
        "  public_key_path: /tmp/k.pub\n"
        "  sequence_state_path: /tmp/s.json\n"
        "  algorithm: HMAC-SHA256\n"
        "supported_formats_config: config/supported_formats.yaml\n"
        "artifact_unit_defs_dir: artifact_unit_defs/\n"
        "supervisor_version_id: 0.1.0-mvp\n"
        "worker_temp_dir_base: /tmp/workers\n"
        "coco_annotation_file_max_size_bytes: 2147483648\n",
        encoding="utf-8",
    )
    (config_dir / "resource_limits.yaml").write_text(
        "resource_limits:\n"
        "  default:\n"
        "    timeout_seconds: 10\n"
        "    memory_limit_mb: 512\n"
        "    max_file_descriptors: 16\n",
        encoding="utf-8",
    )
    (config_dir / "supported_formats.yaml").write_text(
        "coco_in_scope: true\n"
        "onnx_in_scope: true\n"
        "yolo_task_variants: [YOLO_DETECTION]\n"
        "pytorch_in_scope: true\n",
        encoding="utf-8",
    )
