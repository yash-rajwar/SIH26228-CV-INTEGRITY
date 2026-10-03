"""G5-DEMO-001..008: actual subprocess demo, no mocked acceptance pipeline."""

import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "demo.py"


@pytest.fixture(scope="module")
def demo():
    completed = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT,
                               capture_output=True, text=True, timeout=900)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads(completed.stdout)
    result = json.loads(Path(summary["result"]).read_text(encoding="utf-8"))
    return result


def test_g5_demo_001_python_stdlib_bounded():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(n.name.split(".")[0] in sys.stdlib_module_names for n in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module.split(".")[0] in sys.stdlib_module_names | {"__future__"}


def test_g5_demo_002_actual_automated_execution(demo):
    assert demo["status"] == "PASS"
    assert demo["python"] == sys.executable
    assert demo["is_synthetic"] is True
    assert demo["seed"] == 26228
    assert demo["dashboard_stopped"] is True


def test_g5_demo_003_coco_completed_evidence(demo):
    scenario = demo["scenario_a"]
    assert scenario["findings"] and len(scenario["evidence"]) == 4
    assert all(r["is_synthetic"] == 1 for r in scenario["findings"] + scenario["evidence"])
    m01 = next(r for r in scenario["evidence"] if r["method_id"] == "M01")
    assert m01["assessment_status"] == "COMPLETED"
    assert m01["raw_signal"]["violation_count"] == 0


def test_g5_demo_004_unavailable_preserved(demo):
    finding = demo["scenario_b"]["findings"][0]
    assert finding["detection_status"] == "UNAVAILABLE"
    assert finding["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
    assert not (Path(demo["directory"]) / "missing-model" / "missing.pt").exists()


def test_g5_demo_005_cli_coverage_matches_authority(demo):
    records = json.loads((Path(demo["directory"]) / "deferred.stdout.txt").read_text(encoding="utf-8"))
    actual = {r["method_id"]: r["assessment_status"] for r in records
              if r["asset_id"] == demo["scenario_b"]["asset_id"]}
    assert actual == demo["coverage"]["expected"]
    assert "DEFERRED_IN_SCOPE" in actual.values()


def test_g5_demo_006_export_zip_actual_data(demo):
    with zipfile.ZipFile(demo["bundle"]["path"]) as archive:
        assert archive.testzip() is None
        assert sorted(archive.namelist()) == demo["bundle"]["documents"]
        assert len(archive.namelist()) == 6
        assert json.loads(archive.read("findings.json")) == demo["scenario_b"]["findings"]
        assert json.loads(archive.read("capabilities.json"))["deferred_records"] == demo["coverage"]["records"]


def test_g5_demo_007_real_loopback_dashboard(demo):
    assert demo["dashboard"]["http_status"] == 200
    assert demo["dashboard"]["url"].startswith("http://127.0.0.1:")
    assert demo["dashboard"]["read_only"] is True
    assert demo["dashboard"]["signing_notice_visible"] is True
    assert set(demo["dashboard"]["stored_signing_statuses"]) <= {"SIGNING_UNAVAILABLE"}
    assert demo["dashboard"]["scenario_b_binding"] == "C4_BINDING_UNAVAILABLE"
    snapshot = json.loads((Path(demo["directory"]) / "dashboard.json").read_text(encoding="utf-8"))
    assert {demo["scenario_a"]["asset_id"], demo["scenario_b"]["asset_id"]} <= set(snapshot["assets"])


def test_g5_demo_008_no_external_network_or_shell():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "shell=True" not in source
    assert all(url.startswith(("http://127.0.0.1", "http://{LOOPBACK}"))
               for url in re.findall(r"https?://[^\s\"']+", source))
    assert 'LOOPBACK = "127.0.0.1"' in source
    assert "HTTPConnection(LOOPBACK" in source
    assert "listener.bind((LOOPBACK, 0))" in source
    assert not any(word in source for word in ("urlopen", "pip install", "Disable-NetAdapter"))
