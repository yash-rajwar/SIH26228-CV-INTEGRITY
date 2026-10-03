"""Gate-5: repeatable synthetic demo through the real CLI, with loopback only.

Working artifacts stay in build/demo; assessments append to the existing
configured supervisor store. No database, audit history or asset is deleted.
Run from the repository root with its approved Python environment.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid
import zipfile


SEED = 26228
LOOPBACK = "127.0.0.1"
# Demo-process/readiness watchdogs, not worker assessment thresholds.
COMMAND_TIMEOUT_SECONDS = 600
READINESS_TIMEOUT_SECONDS = 30
HTTP_TIMEOUT_SECONDS = 5
POLL_SECONDS = 0.2
STOP_TIMEOUT_SECONDS = 10
BUNDLE_DOCUMENTS = {
    "manifest.json", "findings.json", "evidence_records.json",
    "provenance.json", "audit_trail.json", "capabilities.json",
}
PROHIBITED_FIELDS = {
    "risk_score", "aggregate_assurance", "compromise_probability",
    "overall_assurance_score", "confidence_score", "trust_score",
    "safety_score", "malicious_probability",
}
# Inspect the trusted configuration/registry without emitting declarations,
# accessing keys or writing to the store. The production registry is authority.
PREFLIGHT_CODE = """
import json, pathlib
import onnx, torch, pycocotools, yaml
from assurance_system.config.loader import ConfigLoader
from assurance_system.supervisor.capability_declaration import _DEFERRED_METHODS
c = ConfigLoader().load()
print(json.dumps({
    'evidence_store': str(pathlib.Path(c['system']['evidence_store']['path']).resolve()),
    'worker_temp': str(pathlib.Path(c['system']['worker_temp_dir_base']).resolve()),
    'expected_coverage': {s[0]: s[1] for s in _DEFERRED_METHODS},
}))
"""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def bounded_fields(value):
    if isinstance(value, dict):
        require(PROHIBITED_FIELDS.isdisjoint(value), "Prohibited output field")
        for nested in value.values():
            bounded_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            bounded_fields(nested)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute(root, directory, name, arguments):
    """Every subprocess uses this same interpreter and shell-free argument lists."""
    completed = subprocess.run(
        [sys.executable, *arguments], cwd=root, stdin=subprocess.DEVNULL,
        capture_output=True, timeout=COMMAND_TIMEOUT_SECONDS,
    )
    (directory / f"{name}.stdout.txt").write_bytes(completed.stdout)
    (directory / f"{name}.stderr.txt").write_bytes(completed.stderr)
    write_json(directory / f"{name}.command.json", {
        "argv": [sys.executable, *arguments], "exit_code": completed.returncode,
    })
    require(completed.returncode == 0, f"{name} failed: see saved stdout/stderr")
    return completed.stdout.decode("utf-8")


def cli(root, directory, name, *arguments):
    return execute(root, directory, name, ["cli.py", *arguments])


def submission(directory, asset_id, fixture_directory, path, format_name):
    asset = {"asset_id": asset_id, "asset_paths": [str(path.resolve())],
             "format": format_name, "is_synthetic": True}
    if format_name == "COCO":
        asset["contributor_metadata"] = [{"contributor_id": "synthetic-source-1"}]
    manifest = directory / f"{asset_id}.json"
    write_json(manifest, {
        "schema_version": "submission-manifest-v1",
        "asset_directory": str(fixture_directory.resolve()), "assets": [asset],
    })
    return manifest


def http_get(port, path):
    # Direct HTTPConnection bypasses environment HTTP proxies; only IPv4 loopback.
    connection = http.client.HTTPConnection(LOOPBACK, port, timeout=HTTP_TIMEOUT_SECONDS)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        require(response.status == 200, f"Dashboard {path}: HTTP {response.status}")
        return response.read().decode("utf-8")
    finally:
        connection.close()


def dashboard_snapshot(process, port):
    deadline = time.monotonic() + READINESS_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        require(process.poll() is None, "Dashboard exited before readiness")
        try:
            page = http_get(port, "/")
            snapshot = json.loads(http_get(port, "/api/dashboard"))
            return page, snapshot
        except (OSError, http.client.HTTPException):
            time.sleep(POLL_SECONDS)
    raise RuntimeError("Dashboard readiness timeout")


def check_scenario(snapshot, asset_id, unavailable=False):
    findings = [r for r in snapshot["findings"] if r["asset_id"] == asset_id]
    evidence = [r for r in snapshot["evidence"] if r["asset_id"] == asset_id]
    require(findings and evidence, "Missing persisted demo finding/evidence")
    require(all(r["is_synthetic"] == 1 for r in findings + evidence),
            "Synthetic label lost")
    require(all(r["coverage_gap_clean_label"] == 1 and r["limitations"]
                and r["non_claims"] for r in findings + evidence), "Non-claims lost")
    if unavailable:
        require(all(r["detection_status"] == "UNAVAILABLE" and
                    r["analyst_disposition_prompt"] == "UNAVAILABLE_NO_DECISION"
                    for r in findings), "VS-007 unavailable finding contract differs")
        require(any(r["assessment_status"] in {"ASSESSMENT_ERROR", "UNAVAILABLE"}
                    for r in evidence), "Missing unavailable evidence")
    else:
        geometry = [r for r in evidence if r["method_id"] == "M01"]
        require(len(geometry) == 1 and geometry[0]["assessment_status"] == "COMPLETED"
                and geometry[0]["raw_signal"]["violation_count"] == 0,
                "Benign COCO geometry did not complete")
    bounded_fields([findings, evidence])
    return {"asset_id": asset_id, "findings": findings, "evidence": evidence}


def run_demo(root, directory, report, serve):
    authority = json.loads(execute(root, directory, "preflight", ["-c", PREFLIGHT_CODE]))
    require(Path(authority["evidence_store"]).is_file(), "Configured deployment DB missing")
    require(Path(authority["worker_temp"]).is_dir(), "Configured worker temp missing")
    report["evidence_store"] = authority["evidence_store"]
    baseline_audit = json.loads(cli(root, directory, "audit-baseline", "show-audit-trail"))
    expected = authority["expected_coverage"]
    a_id, b_id = "demo-coco-" + report["run_id"], "demo-unavailable-" + report["run_id"]
    fixture = directory / "benign-coco"
    execute(root, directory, "fixture-generator", [
        "-m", "assurance_system.fixtures.generator", "benign-coco",
        "--output", str(fixture), "--seed", str(SEED),
    ])
    generated = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))
    require(generated["is_synthetic"] is True and generated["seed"] == SEED
            and generated["expected_result"]["violation_count"] == 0,
            "Unexpected approved fixture manifest")
    a_manifest = submission(directory, a_id, fixture, fixture / "valid_coco.json", "COCO")
    a_assess = json.loads(cli(root, directory, "assess-a", "assess", "--submission", str(a_manifest)))
    missing = directory / "missing-model"
    missing.mkdir()
    require(not (missing / "missing.pt").exists(), "Missing model unexpectedly exists")
    b_manifest = submission(directory, b_id, missing, missing / "missing.pt", "PYTORCH")
    b_assess = json.loads(cli(root, directory, "assess-b", "assess", "--submission", str(b_manifest)))
    for result in (a_assess, b_assess):
        require(result["pipeline_summary"]["evidence_records_written"] > 0
                and result["pipeline_summary"]["findings_written"] == 1,
                "Assessment did not persist evidence/finding")
        bounded_fields(result)
    a_findings = json.loads(cli(root, directory, "finding-a", "show-finding", "--asset-id", a_id))
    b_findings = json.loads(cli(root, directory, "finding-b", "show-finding", "--asset-id", b_id))
    require(all(r["detection_status"] == "UNAVAILABLE" for r in b_findings),
            "CLI did not preserve literal UNAVAILABLE")
    records = json.loads(cli(root, directory, "deferred", "list-deferred"))
    coverage = [r for r in records if r["asset_id"] == b_id]
    require(len(coverage) == len(expected) and
            {r["method_id"]: r["assessment_status"] for r in coverage} == expected,
            "CLI coverage differs from production capability registry")
    report["coverage"] = {"expected": expected, "records": coverage}
    audit_before = json.loads(cli(root, directory, "audit-before", "show-audit-trail"))
    audit_after = json.loads(cli(root, directory, "audit-after", "show-audit-trail"))
    require(audit_before and audit_before == audit_after, "Audit display changed history")
    require(audit_after[:len(baseline_audit)] == baseline_audit, "Historical audit changed")
    new_events = audit_after[len(baseline_audit):]
    require(all(sum(e["event_type"] == event for e in new_events) >= 2 for event in
                ("PIPELINE_RUN_COMPLETE", "FINDING_WRITTEN", "EVIDENCE_RECORD_WRITTEN")),
            "Missing pipeline audit events")
    report["new_audit_events"] = len(new_events)
    bundle = directory / "unavailable-evidence.zip"
    cli(root, directory, "export", "export-bundle", "--asset-id", b_id, "--output", str(bundle))
    with zipfile.ZipFile(bundle) as archive:
        require(archive.testzip() is None and len(archive.namelist()) == len(BUNDLE_DOCUMENTS)
                and set(archive.namelist()) == BUNDLE_DOCUMENTS, "Invalid six-document ZIP")
        documents = {name: json.loads(archive.read(name)) for name in archive.namelist()}
    require(documents["findings.json"] == b_findings, "Export changed unavailable finding")
    require(documents["capabilities.json"]["deferred_records"] == coverage,
            "Export lost coverage")
    require(documents["evidence_records.json"] and all(r["is_synthetic"] == 1 for r in
            documents["findings.json"] + documents["evidence_records.json"]),
            "Export lost synthetic labels")
    # VS-007 has no completed C3B digest, hence no C4 binding. An empty
    # provenance document is valid; neither this demo nor export invents one.
    require(isinstance(documents["provenance.json"], list)
            and documents["audit_trail.json"]["events"], "Invalid provenance/audit documents")
    bounded_fields(documents)
    report["bundle"] = {"path": str(bundle), "documents": sorted(documents), "valid": True}
    with socket.socket() as listener:
        listener.bind((LOOPBACK, 0))
        port = listener.getsockname()[1]
    process = None
    with (directory / "dashboard.stdout.txt").open("wb") as out, \
         (directory / "dashboard.stderr.txt").open("wb") as err:
        try:
            process = subprocess.Popen(
                [sys.executable, "cli.py", "dashboard", "--port", str(port)], cwd=root,
                stdin=subprocess.DEVNULL, stdout=out, stderr=err,
            )
            page, snapshot = dashboard_snapshot(process, port)
            (directory / "dashboard.html").write_text(page, encoding="utf-8")
            write_json(directory / "dashboard.json", snapshot)
            require(a_id in snapshot["assets"] and b_id in snapshot["assets"],
                    "Dashboard lacks demo assets")
            report["scenario_a"] = check_scenario(snapshot, a_id)
            report["scenario_b"] = check_scenario(snapshot, b_id, unavailable=True)
            require(report["scenario_a"]["findings"] == a_findings, "CLI/dashboard differ")
            require(report["scenario_b"]["findings"] == b_findings, "CLI/dashboard differ")
            require("UNAVAILABLE" in page and "DEFERRED_IN_SCOPE" in page
                    and "SIGNING_UNAVAILABLE" in page, "Missing literal dashboard states")
            hashes = {r["record_digest"] for r in report["scenario_b"]["evidence"]}
            bound_provenance = [p for p in snapshot["provenance"]
                                if hashes.intersection(p["evidence_record_digests"])]
            require(not bound_provenance and all(r["pf_002_non_claim"] == "C4_BINDING_UNAVAILABLE"
                    for r in b_findings), "Missing-model provenance contract differs")
            require(all(p["signing_status"] == "SIGNING_UNAVAILABLE"
                    and p["signature"] is None for p in snapshot["provenance"]),
                    "Stored provenance signing contract differs")
            require(snapshot["chain"]["status"] in {"CHAIN INTACT", "CHAIN_CORRUPT"},
                    "Dashboard chain status missing")
            require([r for r in snapshot["deferred"] if r["asset_id"] == b_id] == coverage,
                    "Dashboard lost coverage")
            refreshed = json.loads(http_get(port, "/api/dashboard"))
            for key in ("findings", "evidence", "deferred", "provenance", "audit", "chain"):
                require(snapshot[key] == refreshed[key], "Dashboard refresh changed records")
            require(snapshot["audit"] == audit_after, "Read/export path mutated audit history")
            bounded_fields(snapshot)
            report["dashboard"] = {"url": f"http://{LOOPBACK}:{port}", "http_status": 200,
                                   "read_only": True, "chain": snapshot["chain"],
                                   "signing_notice_visible": True,
                                   "stored_signing_statuses": sorted({p["signing_status"]
                                                               for p in snapshot["provenance"]}),
                                   "scenario_b_binding": "C4_BINDING_UNAVAILABLE"}
            if serve:
                print(f"Dashboard: http://{LOOPBACK}:{port}\nPress Ctrl+C to stop.", flush=True)
                try:
                    while process.poll() is None:
                        time.sleep(POLL_SECONDS)
                except KeyboardInterrupt:
                    pass
                else:
                    raise RuntimeError("Presentation dashboard exited unexpectedly")
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=STOP_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=STOP_TIMEOUT_SECONDS)
                report["dashboard_stopped"] = process.poll() is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="leave verified dashboard up until Ctrl+C")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root or not (root / "cli.py").is_file():
        print("Run from the repository root.", file=sys.stderr)
        return 1
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex
    directory = root / "build" / "demo" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    report = {"run_id": run_id, "seed": SEED, "is_synthetic": True,
              "directory": str(directory), "python": sys.executable, "status": "FAIL"}
    try:
        run_demo(root, directory, report, args.serve)
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["sha256"] = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(directory.rglob("*")) if p.is_file()}
    write_json(directory / "result.json", report)
    print(json.dumps({"status": report["status"], "result": str(directory / "result.json"),
                      "error": report.get("error")}, sort_keys=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
