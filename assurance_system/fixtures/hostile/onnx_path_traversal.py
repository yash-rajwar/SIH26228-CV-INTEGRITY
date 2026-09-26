"""Seed-pinned ONNX external-data path fixtures (FIX-004 through FIX-006)."""

import pathlib
import random
import struct


_ONNX_BLOCKER = "BLOCKED: onnx package not installed"


def _load_onnx():
    try:
        import onnx
        from onnx import TensorProto, external_data_helper, helper
    except ImportError as exc:
        raise RuntimeError(_ONNX_BLOCKER) from exc
    return onnx, TensorProto, external_data_helper, helper


def _write_external_data_model(path: pathlib.Path, location: str) -> None:
    onnx, tensor_proto, external_data_helper, helper = _load_onnx()
    initializer = helper.make_tensor(
        name="synthetic_weight",
        data_type=tensor_proto.FLOAT,
        dims=[1],
        vals=struct.pack("<f", 1.0),
        raw=True,
    )
    external_data_helper.set_external_data(
        initializer,
        location=location,
        offset=0,
        length=4,
    )
    initializer.data_location = tensor_proto.EXTERNAL
    initializer.ClearField("raw_data")
    output_info = helper.make_tensor_value_info(
        "output", tensor_proto.FLOAT, [1]
    )
    graph = helper.make_graph(
        [helper.make_node("Identity", ["synthetic_weight"], ["output"])],
        "synthetic-external-data-graph",
        [],
        [output_info],
        [initializer],
    )
    model = helper.make_model(graph, producer_name="sih26228-synthetic-fixture")
    path.write_bytes(model.SerializeToString())
    # Parse from memory to verify protobuf validity without following the hostile path.
    onnx.load_model_from_string(path.read_bytes())


def _generate_one(
    output_dir: str,
    seed: int,
    *,
    fixture_id: str,
    filename: str,
    location: str,
    violation_reason: str,
) -> dict:
    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _write_external_data_model(output / filename, location)
    return {
        "fixture_id": fixture_id,
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "assessment_status": "ONNX_PATH_CONTAINMENT_VIOLATION",
            "violation_reason": violation_reason,
        },
    }


def generate_absolute_path(output_dir: str, seed: int) -> dict:
    return _generate_one(
        output_dir,
        seed,
        fixture_id="FIX-004",
        filename="absolute_external_data.onnx",
        location="/synthetic/outside/weights.bin",
        violation_reason="ABSOLUTE_PATH",
    )


def generate_traversal_path(output_dir: str, seed: int) -> dict:
    return _generate_one(
        output_dir,
        seed,
        fixture_id="FIX-005",
        filename="traversal_external_data.onnx",
        location="../../../synthetic/outside/weights.bin",
        violation_reason="TRAVERSAL_PATTERN",
    )


def generate_symlink_escape(output_dir: str, seed: int) -> dict:
    manifest = _generate_one(
        output_dir,
        seed,
        fixture_id="FIX-006",
        filename="symlink_external_data.onnx",
        location="external.bin",
        violation_reason="SYMLINK_ESCAPE",
    )
    manifest["expected_result"]["test_setup"] = (
        "Create external.bin as a symlink to a target outside the fixture directory."
    )
    return manifest


def generate(output_dir: str, seed: int) -> dict:
    """Generate the complete ONNX path-containment family for the CLI."""

    random.seed(seed)
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    fixtures = [
        generate_absolute_path(str(output), seed),
        generate_traversal_path(str(output), seed),
        generate_symlink_escape(str(output), seed),
    ]
    return {
        "fixture_id": "FIX-004",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {
            "fixture_family": [item["fixture_id"] for item in fixtures],
            "assessment_status": "ONNX_PATH_CONTAINMENT_VIOLATION",
        },
    }
