# THIS FILE IS A HOSTILE FIXTURE — FOR TESTING ONLY — DO NOT LOAD IN PRODUCTION
"""Seed-pinned PyTorch safe-load and resource-control fixtures."""

from collections.abc import Iterator
import os
import pathlib
import pickle
import pickletools
import random
import struct
import zipfile

from assurance_system.config.loader import ConfigLoader


HOSTILE_FIXTURE_WARNING = (
    "# THIS FILE IS A HOSTILE FIXTURE — FOR TESTING ONLY — DO NOT LOAD IN PRODUCTION"
)
_FIXED_ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
_STREAM_CHUNK_BYTES = 1024 * 1024
_ZIP_COMPRESSION_LEVEL = 1


class _HostilePayload:
    """Serialize an unsafe global without executing it during generation."""

    def __init__(self, seed: int):
        self.seed = seed

    def __reduce__(self):
        command = f"echo HOSTILE_FIXTURE_{self.seed}_MUST_NOT_EXECUTE"
        return os.system, (command,)


def _load_torch():
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("BLOCKED: torch not installed") from exc
    return torch


def _manifest(
    fixture_id: str, seed: int, path: pathlib.Path, expected_result: dict
) -> dict:
    return {
        "fixture_id": fixture_id,
        "seed": seed,
        "is_synthetic": True,
        "path": str(path),
        "expected_result": expected_result,
    }


def generate_hostile_pickle(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "hostile_pickle.pt"
    payload = {
        "warning": HOSTILE_FIXTURE_WARNING,
        "payload": _HostilePayload(seed),
        "is_synthetic": True,
    }
    path.write_bytes(pickle.dumps(payload, protocol=2))
    return _manifest(
        "FIX-001",
        seed,
        path,
        {
            "assessment_status": "LOAD_BLOCKED",
            "expected_fallback_attempted": False,
            "expected_exception": "UnpicklingError or equivalent",
        },
    )


def _pickle_integer_operations(data: bytes) -> Iterator[tuple[int, int, int]]:
    widths = {"BININT1": 2, "BININT2": 3, "BININT": 5}
    for opcode, argument, position in pickletools.genops(data):
        if opcode.name in widths:
            yield position, widths[opcode.name], int(argument)


def _patch_tensor_element_count(data: bytes, element_count: int) -> bytes:
    integers = list(_pickle_integer_operations(data))
    if len(integers) < 4 or [item[2] for item in integers[:4]] != [1, 0, 1, 1]:
        raise RuntimeError("Unexpected PyTorch tensor pickle layout")
    encoded_count = b"J" + struct.pack("<i", element_count)
    # Patch in descending byte-position order so the first edit cannot move the second.
    for position, width, _ in (integers[2], integers[0]):
        data = data[:position] + encoded_count + data[position + width :]
    return data


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    return info


def _write_zero_storage(record, declared_bytes: int) -> None:
    chunk = b"\0" * _STREAM_CHUNK_BYTES
    remaining = declared_bytes
    while remaining:
        write_size = min(remaining, len(chunk))
        record.write(chunk[:write_size])
        remaining -= write_size


def generate_oom_trigger(
    output_dir: str, seed: int, *, memory_limit_mb: int | None = None
) -> dict:
    """Build a compact archive whose load allocation exceeds the C3D cap.

    The optional limit override exists only so unit tests can validate the archive
    with a bounded allocation. Production fixture generation reads the named C3D
    limit from configuration. The production-size artifact must be loaded only by
    the isolated, resource-limited worker path.
    """

    random.seed(seed)
    torch = _load_torch()
    if memory_limit_mb is None:
        memory_limit_mb = ConfigLoader().get_resource_limits(
            "C3D_SAFE_LOAD"
        ).memory_limit_mb
    if isinstance(memory_limit_mb, bool) or not isinstance(memory_limit_mb, int):
        raise ValueError("memory_limit_mb must be an integer")
    if memory_limit_mb <= 0:
        raise ValueError("memory_limit_mb must be positive")

    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "oom_trigger.pt"
    template_path = output / "_oom_template.pt"
    element_size = torch.empty((), dtype=torch.float32).element_size()
    memory_limit_bytes = memory_limit_mb * 1024 * 1024
    element_count = memory_limit_bytes // element_size + 1
    declared_bytes = element_count * element_size

    try:
        torch.save(torch.zeros(1, dtype=torch.float32), template_path)
        with zipfile.ZipFile(template_path, "r") as template:
            names = template.namelist()
            data_pickle_name = next(
                name for name in names if name.endswith("/data.pkl")
            )
            storage_name = next(name for name in names if name.endswith("/data/0"))
            records = {
                name: template.read(name) for name in names if name != storage_name
            }
        records[data_pickle_name] = _patch_tensor_element_count(
            records[data_pickle_name], element_count
        )

        original_prefix = data_pickle_name.split("/", maxsplit=1)[0]
        normalized_records = {
            "oom_trigger/" + name.split("/", maxsplit=1)[1]: value
            for name, value in records.items()
        }
        normalized_storage_name = storage_name.replace(
            original_prefix + "/", "oom_trigger/", 1
        )
        with zipfile.ZipFile(
            path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=_ZIP_COMPRESSION_LEVEL,
            allowZip64=True,
        ) as archive:
            for name in sorted(normalized_records):
                archive.writestr(
                    _zip_info(name),
                    normalized_records[name],
                    compresslevel=_ZIP_COMPRESSION_LEVEL,
                )
            with archive.open(
                _zip_info(normalized_storage_name), "w", force_zip64=True
            ) as storage_record:
                _write_zero_storage(storage_record, declared_bytes)
    finally:
        template_path.unlink(missing_ok=True)

    return _manifest(
        "FIX-002",
        seed,
        path,
        {
            "assessment_status": "LOAD_ERROR",
            "expected_behavior": "memory limit trigger; supervisor continues",
            "configured_memory_limit_mb": memory_limit_mb,
            "declared_shape": [element_count],
            "declared_storage_bytes": declared_bytes,
            "isolated_load_required": True,
        },
    )


def generate_hang_trigger(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "hang_trigger.py"
    path.write_text(
        "# THIS FILE IS A HOSTILE FIXTURE — FOR TESTING ONLY — DO NOT LOAD IN PRODUCTION\n"
        "import time\n"
        "while True:\n"
        "    time.sleep(1)\n",
        encoding="utf-8",
    )
    return _manifest(
        "FIX-003",
        seed,
        path,
        {
            "assessment_status": "ASSESSMENT_ERROR",
            "expected_behavior": "worker timeout; supervisor continues",
            "trigger_type": "INFINITE_SLEEP_LOOP",
        },
    )


def generate_benign_pytorch(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    torch = _load_torch()
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "benign_pytorch.pt"
    torch.save({"weight": torch.zeros(3, 3)}, path)
    return _manifest(
        "FIX-015",
        seed,
        path,
        {
            "expected_assessment_status": "LOAD_SUCCESS",
            "expected_fallback_attempted": False,
        },
    )


def generate(output_dir: str, seed: int) -> dict:
    """Generate the bounded Part B family except the OOM artifact.

    FIX-002 is intentionally generated through ``generate_oom_trigger`` so a
    caller must make an explicit resource-fixture choice.
    """

    random.seed(seed)
    output = pathlib.Path(output_dir)
    hostile = generate_hostile_pickle(str(output / "fix001"), seed)
    hang = generate_hang_trigger(str(output / "fix003"), seed)
    benign = generate_benign_pytorch(str(output / "fix015"), seed)
    return {
        "fixture_id": "FIX-001",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "fixture_family": [
                hostile["fixture_id"],
                "FIX-002_EXPLICIT_RESOURCE_GENERATION",
                hang["fixture_id"],
                benign["fixture_id"],
            ]
        },
    }
