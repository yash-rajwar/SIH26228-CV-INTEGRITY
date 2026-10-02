"""Real ONNX C3A -> C3B acceptance for the frozen SP-002 definition."""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import struct

import pytest

from assurance_system.constants import AssessmentStatus, PF_002_NON_CLAIM
from assurance_system.fixtures.hostile import benign, onnx_path_traversal
from assurance_system.supervisor.schema_validator import EvidenceSchemaValidator
from assurance_system.workers import c3a_artifact_unit as c3a, c3b_model_hash as c3b

pytestmark = pytest.mark.skipif(importlib.util.find_spec("onnx") is None,
                              reason="BLOCKED: HOST-CAP-003 — onnx not installed")
_ID = "onnx-main-referenced-external-data-v1"
_SEED = 26228


def _resolve(path, directory):
    return c3a.run_assessment({"schema_version": "worker-input-v1", "task": "C3A_ARTIFACT_UNIT",
        "asset_paths": [str(path)], "format": "ONNX", "asset_directory": str(directory),
        "artifact_unit_definition_id": _ID, "resource_limits": {}, "identity_quality": "UNTRUSTED"})


def _hash(resolution, directory, reference=None):
    # C3A diagnostic partial membership is never authorization to hash it.
    unit = resolution["raw_signal"].get("artifact_unit") if resolution["assessment_status"] == AssessmentStatus.COMPLETED else None
    task = {"schema_version": "worker-input-v1", "task": "C3B_MODEL_HASH", "format": "ONNX",
            "asset_directory": str(directory), "artifact_unit": unit}
    if reference is not None:
        task["reference_digest"] = reference
    return c3b.run_assessment(task)


def _expected(*members):
    # Independent byte-level computation; no production hashing helper reused.
    digests = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in members}
    ordered = sorted(digests)
    return hashlib.sha256("".join(digests[path] for path in ordered).encode("ascii")).hexdigest()


def _assert_contract(result, task_name):
    validation = EvidenceSchemaValidator().validate_worker_output(result, task_name)
    assert validation.valid, validation.reason
    assert result["coverage_gap_clean_label"] is True
    assert result["limitations"] and result["non_claims"]
    assert result["pf_002_non_claim"] == PF_002_NON_CLAIM
    for name in ("hash_match_not_safe", "hash_match_not_semantically_equivalent", "hash_match_not_causal_execution_proof"):
        assert result[name] is True


def _external_model(directory):
    directory.mkdir(exist_ok=True)
    model, data = directory / "model.onnx", directory / "weights.bin"
    # Existing deterministic ONNX fixture writer; complete data includes a tail
    # outside the tensor's declared four-byte slice.
    onnx_path_traversal._write_external_data_model(model, data.name)
    data.write_bytes(struct.pack("<f", 1.0) + b"synthetic-whole-file-tail")
    return model, data


def test_real_onnx_without_external_data_has_the_independent_combined_digest(tmp_path):
    benign.generate_onnx(str(tmp_path), seed=_SEED)
    model = tmp_path / "valid_minimal.onnx"
    resolution = _resolve(model, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.COMPLETED
    assert resolution["access_mode"] == "BLACK_BOX" and resolution["artifact_unit_id"] == _ID
    assert resolution["raw_signal"]["artifact_unit"] == {"main_file": str(model.resolve()), "external_files": [], "artifact_unit_definition_id": _ID}
    result = _hash(resolution, tmp_path)
    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    expected = _expected(model)
    assert result["raw_signal"]["combined_artifact_unit_digest"] == expected
    assert expected != hashlib.sha256(model.read_bytes()).hexdigest()
    assert _hash(resolution, tmp_path)["raw_signal"] == result["raw_signal"]
    assert result["raw_signal"]["comparison_result"] == "UNAVAILABLE"
    assert _hash(resolution, tmp_path, expected)["raw_signal"]["comparison_result"] == "MATCH"
    assert _hash(resolution, tmp_path, "0" * 64)["raw_signal"]["comparison_result"] == "DIFFERENT"
    _assert_contract(resolution, "C3A_ARTIFACT_UNIT")
    _assert_contract(result, "C3B_MODEL_HASH")


def test_real_onnx_header_in_a_non_onnx_file_is_not_an_approved_unit(tmp_path):
    benign.generate_onnx(str(tmp_path), seed=_SEED)
    model = tmp_path / "valid_minimal.onnx"
    renamed = model.rename(tmp_path / "model.bin")
    resolution = _resolve(renamed, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert "MODEL_FILE_SUFFIX_NOT_ONNX" in str(resolution["raw_signal"])
    result = _hash(resolution, tmp_path)
    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert "combined_artifact_unit_digest" not in result["raw_signal"]
    _assert_contract(resolution, "C3A_ARTIFACT_UNIT")
    _assert_contract(result, "C3B_MODEL_HASH")


def test_real_onnx_with_external_data_hashes_the_complete_unit(tmp_path):
    import onnx
    model, data = _external_model(tmp_path)
    onnx.checker.check_model(str(model))
    resolution = _resolve(model, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.COMPLETED
    assert resolution["raw_signal"]["artifact_unit"]["external_files"] == [str(data.resolve())]
    result = _hash(resolution, tmp_path)
    assert result["assessment_status"] == AssessmentStatus.COMPLETED
    assert result["artifact_unit_id"] == _ID
    assert result["raw_signal"]["combined_artifact_unit_digest"] == _expected(model, data)
    assert set(result["raw_signal"]["per_file_digests"]) == {str(model.resolve()), str(data.resolve())}
    _assert_contract(resolution, "C3A_ARTIFACT_UNIT")
    _assert_contract(result, "C3B_MODEL_HASH")


def test_referenced_external_tail_tamper_changes_only_its_member_digest(tmp_path):
    model, data = _external_model(tmp_path)
    baseline = _hash(_resolve(model, tmp_path), tmp_path)["raw_signal"]
    main_before = model.read_bytes()
    data.write_bytes(data.read_bytes()[:-1] + b"X")
    changed = _hash(_resolve(model, tmp_path), tmp_path)["raw_signal"]
    assert model.read_bytes() == main_before
    assert baseline["per_file_digests"][str(model.resolve())] == changed["per_file_digests"][str(model.resolve())]
    assert baseline["per_file_digests"][str(data.resolve())] != changed["per_file_digests"][str(data.resolve())]
    assert baseline["combined_artifact_unit_digest"] != changed["combined_artifact_unit_digest"]
    assert changed["combined_artifact_unit_digest"] == _expected(model, data)


def test_unreferenced_neighbours_are_excluded_and_do_not_change_identity(tmp_path):
    model, data = _external_model(tmp_path)
    neighbours = [tmp_path / "unrelated.bin", tmp_path / "unreferenced.onnx.data"]
    for path in neighbours:
        path.write_bytes(b"excluded neighbour")
    resolution = _resolve(model, tmp_path)
    baseline = _hash(resolution, tmp_path)["raw_signal"]
    assert resolution["raw_signal"]["artifact_unit"]["external_files"] == [str(data.resolve())]
    for path in neighbours:
        path.write_bytes(b"changed excluded bytes")
    changed = _hash(_resolve(model, tmp_path), tmp_path)["raw_signal"]
    assert changed == baseline


def test_duplicate_canonical_external_references_include_one_file(tmp_path):
    import onnx
    model, data = _external_model(tmp_path)
    proto = onnx.load(str(model), load_external_data=False)
    duplicate = proto.graph.initializer.add()
    duplicate.CopyFrom(proto.graph.initializer[0])
    duplicate.name = "duplicate_reference"
    for item in duplicate.external_data:
        if item.key == "location":
            item.value = "./weights.bin"
    model.write_bytes(proto.SerializeToString())
    resolution = _resolve(model, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.COMPLETED
    assert resolution["raw_signal"]["artifact_unit"]["external_files"] == [str(data.resolve())]
    assert _hash(resolution, tmp_path)["raw_signal"]["combined_artifact_unit_digest"] == _expected(model, data)


@pytest.mark.parametrize("invalid_member", ["missing", "directory", "inconsistent-location"])
def test_incomplete_real_onnx_unit_authorizes_no_digest(tmp_path, invalid_member):
    import onnx
    model, data = _external_model(tmp_path)
    if invalid_member == "inconsistent-location":
        proto = onnx.load(str(model), load_external_data=False)
        item = proto.graph.initializer[0].external_data.add()
        item.key, item.value = "location", "weights.bin"
        model.write_bytes(proto.SerializeToString())
    else:
        data.unlink()
        if invalid_member == "directory":
            data.mkdir()
    resolution = _resolve(model, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    result = _hash(resolution, tmp_path)
    assert result["assessment_status"] == AssessmentStatus.ARTIFACT_UNIT_AMBIGUOUS
    assert "combined_artifact_unit_digest" not in result["raw_signal"]
    assert "per_file_digests" not in result["raw_signal"]
    _assert_contract(result, "C3B_MODEL_HASH")


def test_real_protobuf_recursion_preserves_all_supported_tensor_reference_locations(tmp_path):
    import onnx
    from onnx import TensorProto, helper, external_data_helper
    benign.generate_onnx(str(tmp_path), seed=_SEED)
    model = tmp_path / "valid_minimal.onnx"
    proto = onnx.load(str(model), load_external_data=False)
    locations = []
    def tensor(name):
        location = name + ".bin"
        locations.append(location)
        (tmp_path / location).write_bytes(struct.pack("<f", 1.0))
        value = helper.make_tensor(name, TensorProto.FLOAT, [1], struct.pack("<f", 1.0), raw=True)
        external_data_helper.set_external_data(value, location=location, offset=0, length=4)
        value.data_location = TensorProto.EXTERNAL
        value.ClearField("raw_data")
        return value
    proto.graph.initializer.add().CopyFrom(tensor("initializer"))
    sparse = proto.graph.sparse_initializer.add()
    sparse.values.CopyFrom(tensor("sparse"))
    sparse.indices.CopyFrom(helper.make_tensor("indices", TensorProto.INT64, [1], [0]))
    sparse.dims.append(1)
    proto.graph.node.add().CopyFrom(helper.make_node("Constant", [], ["attr"], value=tensor("attribute")))
    repeated = proto.graph.node.add()
    repeated.op_type, repeated.domain = "SyntheticTraversal", "sih-fixture"
    attribute = repeated.attribute.add()
    attribute.name, attribute.type = "tensors", onnx.AttributeProto.TENSORS
    attribute.tensors.add().CopyFrom(tensor("repeated_a"))
    attribute.tensors.add().CopyFrom(tensor("repeated_b"))
    for attribute_type, name in ((onnx.AttributeProto.GRAPH, "subgraph"), (onnx.AttributeProto.GRAPHS, "repeated_subgraph")):
        attribute = repeated.attribute.add()
        attribute.name, attribute.type = name, attribute_type
        graph = attribute.g if attribute_type == onnx.AttributeProto.GRAPH else attribute.graphs.add()
        graph.name = name
        graph.initializer.add().CopyFrom(tensor(name))
    function = helper.make_function("sih-fixture", "SyntheticFunction", [], ["fn"],
        [helper.make_node("Constant", [], ["fn"], value=tensor("function"))], [helper.make_opsetid("", 17)])
    proto.functions.add().CopyFrom(function)
    # This model covers protobuf membership traversal; custom synthetic nodes
    # do not assert operator-schema validity or execute any model.
    model.write_bytes(proto.SerializeToString())
    resolution = _resolve(model, tmp_path)
    assert resolution["assessment_status"] == AssessmentStatus.COMPLETED
    expected = sorted(str((tmp_path / location).resolve()) for location in locations)
    assert resolution["raw_signal"]["artifact_unit"]["external_files"] == expected
    assert _hash(resolution, tmp_path)["raw_signal"]["combined_artifact_unit_digest"] == _expected(model, *(tmp_path / name for name in locations))
