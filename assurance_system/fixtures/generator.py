"""Seed-pinned CLI for synthetic hostile and benign fixture families."""

import argparse
import json
import pathlib
import sys

from assurance_system.fixtures.hostile import (
    archive_bomb,
    benign,
    coco_geometry,
    exact_duplicate,
    onnx_path_traversal,
    schema_violation,
    sybil_corpus,
    unavailable_injector,
    yolo_geometry,
)


_GENERATORS = {
    "onnx-path-traversal": onnx_path_traversal.generate,
    "archive-bomb": archive_bomb.generate,
    "coco-geometry": coco_geometry.generate,
    "yolo-detection": yolo_geometry.generate,
    "exact-duplicate": exact_duplicate.generate,
    "sybil-corpus": sybil_corpus.generate,
    "unavailable-injector": unavailable_injector.generate,
    "schema-violation": schema_violation.generate,
    "benign-onnx": benign.generate_onnx,
    "benign-coco": benign.generate_coco,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture_type", choices=sorted(_GENERATORS))
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args(argv)

    output_dir = pathlib.Path(args.output)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest = _GENERATORS[args.fixture_type](str(output_dir), args.seed)
        if manifest.get("is_synthetic") is not True:
            raise ValueError("fixture manifest must declare is_synthetic=true")
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return 0
    except Exception as exc:
        print(f"Fixture generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
