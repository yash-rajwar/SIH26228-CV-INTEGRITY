"""Synthetic benign controls for ONNX and COCO fixture families."""

import pathlib
import random

from assurance_system.fixtures.hostile import coco_geometry


def _load_onnx():
    try:
        import onnx
        from onnx import TensorProto, helper
    except ImportError as exc:
        raise RuntimeError("BLOCKED: onnx package not installed") from exc
    return onnx, TensorProto, helper


def generate_onnx(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    onnx, tensor_proto, helper = _load_onnx()
    output = pathlib.Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    input_info = helper.make_tensor_value_info("input", tensor_proto.FLOAT, [1])
    output_info = helper.make_tensor_value_info("output", tensor_proto.FLOAT, [1])
    graph = helper.make_graph(
        [helper.make_node("Identity", ["input"], ["output"])],
        "synthetic-benign-graph",
        [input_info],
        [output_info],
    )
    model = helper.make_model(graph, producer_name="sih26228-synthetic-fixture")
    model_path = output / "valid_minimal.onnx"
    model_path.write_bytes(model.SerializeToString())
    onnx.checker.check_model(onnx.load_model_from_string(model_path.read_bytes()))
    return {
        "fixture_id": "FIX-016",
        "seed": seed,
        "is_synthetic": True,
        "expected_result": {"expected_assessment_status": "STRUCTURAL_VALID"},
    }


def generate_coco(output_dir: str, seed: int) -> dict:
    random.seed(seed)
    return coco_geometry.generate_valid(output_dir, seed)
