"""TASK-024 HTTP/data acceptance; real store, real inspection, ephemeral loopback.

The synchronous HTTP server and its SQLite connection share their own thread.
Every store write method and trusted verifier is forbidden after seeding.
"""

from contextlib import contextmanager
import hashlib
import inspect
import io
import json
from queue import Queue
import re
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from assurance_system.interfaces.dashboard import Dashboard, _CSS, _JS, _page
from assurance_system.interfaces.cli import AssuranceCLI
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore


HOSTILE = '</script><script>alert("x")</script><img src=x onerror=alert(1)>'


def seed(store, *, corrupt=False):
    store.write_evidence_record({
        "record_id": "evidence-dashboard-001", "schema_version": "v1.0",
        "asset_id": "asset-dashboard-001", "method_id": "M01",
        "worker_id": "COMP-W-C2A", "assessment_status": "UNAVAILABLE",
        "raw_signal": {"hostile": HOSTILE}, "access_mode": "UNAVAILABLE",
        "artifact_unit_id": "UNAVAILABLE", "record_digest": "e" * 64,
        "coverage_gap_clean_label": True, "limitations": [HOSTILE],
        "non_claims": ["No complete integrity conclusion is established."],
        "dependency_declaration": {"independence_established": False},
        "assessment_timestamp": "2026-10-02T12:00:00Z", "is_synthetic": True,
    })
    store.write_finding({
        "finding_id": "finding-dashboard-001", "schema_version": "v1.0",
        "asset_id": "asset-dashboard-001", "method_id": "M01",
        "detection_status": "UNAVAILABLE", "interpretation_status": "UNAVAILABLE",
        "applicability_status": "NOT_ASSESSED", "reference_health": "UNAVAILABLE",
        "limitations": ["Reference path unavailable."], "non_claims": [HOSTILE],
        "dependency_declaration": {"co_firing_detectors": ["M01"], "independence_established": False},
        "coverage_gap_clean_label": True, "is_synthetic": True,
    })
    store.write_deferred_record({
        "schema_version": "v1.0", "asset_id": "asset-dashboard-001",
        "method_id": "M03-PDQ", "assessment_status": "DEFERRED_IN_SCOPE",
        "deferral_reason": "Near-duplicate method is deferred.",
        "limitations": ["Method not executed."], "non_claims": ["Deferral is not a finding."],
    })
    store.write_provenance_record({
        "provenance_id": "provenance-dashboard-001", "schema_version": "v1.0",
        "artifact_unit_digest": "a" * 64, "evidence_record_digests": ["e" * 64],
        "signing_key_id": "UNAVAILABLE", "sequence_number": 1,
        "replay_nonce": "nonce-dashboard-001", "pf_002_non_claim": "digest_match ≠ causal_execution_proof",
        "signing_status": "SIGNING_UNAVAILABLE", "timestamp": "2026-10-02T12:00:00Z",
    })
    audit = AuditChainWriter(store)
    audit.append_event("PIPELINE_RUN_START", {})
    audit.append_event("PIPELINE_RUN_COMPLETE", {})
    if corrupt:
        with store._conn:
            store._conn.execute("UPDATE audit_events SET payload_digest='tampered' WHERE event_id=1")


@contextmanager
def serving(*, corrupt=False, empty=False, unavailable=False):
    ready = Queue()
    failures = []

    def target():
        store = EvidenceStore(":memory:")
        try:
            if not empty:
                seed(store, corrupt=corrupt)
            before = store._conn.total_changes
            def forbidden(*args, **kwargs):
                raise AssertionError("Analyst interface attempted a mutation")
            for name in dir(store):
                if name.startswith("write_"):
                    setattr(store, name, forbidden)
            audit = AuditChainWriter(store)
            audit.append_event = forbidden
            audit.verify_chain_integrity = forbidden
            if unavailable:
                store.query_all_evidence = lambda: (_ for _ in ()).throw(ValueError("unavailable"))
            dashboard = Dashboard(store, audit_chain_factory=lambda _: audit)
            with dashboard._make_server(port=0) as server:
                ready.put(server)
                server.serve_forever(poll_interval=0.01)
            assert store._conn.total_changes == before
        except BaseException as exc:
            failures.append(exc)
            if ready.empty():
                ready.put(None)
        finally:
            store._conn.close()

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    server = ready.get(timeout=10)
    assert server is not None, failures
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=10)
        assert not thread.is_alive()
        assert not failures, failures


def request(server, path="/", method="GET", headers=None):
    req = Request(f"http://127.0.0.1:{server.server_port}{path}", method=method, headers=headers or {})
    try:
        response = urlopen(req, timeout=5)
    except HTTPError as exc:
        response = exc
    with response:
        return response.status, response.headers, response.read()


def snapshot(server):
    status, _, body = request(server, "/api/dashboard")
    assert status == 200
    return json.loads(body)


def test_int_dash_001_loopback_server_returns_html():
    with serving() as server:
        code, headers, body = request(server)
        assert code == 200
        assert "text/html" in headers["Content-Type"]
        assert b"CV Integrity" in body
        assert server.server_address[0] == "127.0.0.1"


def test_int_dash_002_unavailable_finding_visible():
    with serving() as server:
        data = snapshot(server)
        assert data["findings"][0]["detection_status"] == "UNAVAILABLE"
        assert data["findings"][0]["applicability_status"] == "NOT_ASSESSED"
        assert "detection_status" in _JS and "textContent" in _JS


def test_int_dash_003_zero_external_assets():
    page = _page()
    for token in ("http://", "https://", "cdn", "fonts.googleapis", "cdnjs", "jsdelivr", "unpkg", "localStorage", "sessionStorage"):
        assert token not in page
    assert "fetch('/api/dashboard'" in _JS
    assert not re.search(r'<(?:script|link|img)[^>]+(?:src|href)=', page)


def test_int_dash_004_deferred_visible():
    with serving() as server:
        assert snapshot(server)["deferred"][0]["assessment_status"] == "DEFERRED_IN_SCOPE"
        assert "Coverage explicitly not assessed" in _page()


def test_int_dash_005_corruption_visible_history_unchanged():
    with serving(corrupt=True) as server:
        before = snapshot(server)
        after = snapshot(server)
        assert before["chain"]["status"] == "CHAIN_CORRUPT"
        assert before["chain"]["violations"]
        assert before["audit"] == after["audit"]
        assert len(after["audit"]) == 2
        assert after["audit"][0]["payload_digest"] == "tampered"


def test_int_dash_006_signing_unavailable_visible():
    with serving() as server:
        record = snapshot(server)["provenance"][0]
        assert record["signing_status"] == "SIGNING_UNAVAILABLE"
        assert record["signature"] is None
        assert "badge(r.signing_status)" in _JS


def test_int_dash_007_render_refresh_zero_mutations():
    with serving(corrupt=True) as server:
        assert request(server)[0] == 200
        first = snapshot(server)
        second = snapshot(server)
        for key in ("findings", "evidence", "provenance", "deferred", "audit", "counts", "chain"):
            assert second[key] == first[key]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CONNECT", "BREW"])
def test_int_dash_008_mutation_verbs_return_405(method):
    with serving() as server:
        status, headers, _ = request(server, "/api/dashboard", method)
        assert status == 405
        assert headers["Allow"] == "GET, HEAD"


def test_int_dash_009_default_bind_is_loopback():
    assert inspect.signature(Dashboard.run).parameters["host"].default == "127.0.0.1"
    with pytest.raises(ValueError, match="loopback"):
        Dashboard(object())._make_server("0.0.0.0", 0)


def test_int_dash_010_hostile_text_never_embedded_in_html():
    with serving() as server:
        data = snapshot(server)
        assert data["evidence"][0]["raw_signal"]["hostile"] == HOSTILE
        assert HOSTILE.encode() not in request(server)[2]
    for sink in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
        assert sink not in _JS
    assert "e.textContent=String(text)" in _JS


@pytest.mark.parametrize("port", [None, 8765])
def test_int_dash_011_cli_delegates_dashboard(monkeypatch, port):
    import assurance_system.interfaces.dashboard as module
    calls = []
    sentinel = object()
    class FakeDashboard:
        def __init__(self, store, *, audit_chain_factory):
            assert store is sentinel
            assert audit_chain_factory is AuditChainWriter
        def run(self, **kwargs):
            calls.append(kwargs)
    monkeypatch.setattr(module, "Dashboard", FakeDashboard)
    class Loader:
        def load(self):
            return {"system": {"evidence_store": {"path": "test-only"}}}
    cli = AssuranceCLI(config_loader=Loader(), evidence_store_factory=lambda _: sentinel, stdout=io.StringIO())
    args = ["dashboard"] + (["--port", str(port)] if port else [])
    assert cli.run(args) == 0
    assert calls == ([{"port": port}] if port else [{}])


def test_int_dash_012_responsive_accessible_layout():
    assert "max-width:950px" in _CSS and "max-width:650px" in _CSS
    assert "prefers-reduced-motion" in _CSS and ":focus-visible" in _CSS
    page = _page()
    assert '<nav aria-label="Primary">' in page
    assert '<main class="main">' in page
    assert 'scope="col"' in page


def test_int_dash_013_no_score_ui_or_positive_assurance():
    page = _page()
    for token in ("risk_score", "aggregate_assurance", "compromise_probability", "confidence_score", "threat_score", "overall_assurance_score", '"SAFE"', '"CLEAN"', '"HEALTHY"'):
        assert token not in page
    assert "radial" not in page and "gauge" not in page


def test_int_dash_014_all_primary_sections_and_composition():
    page = _page()
    for name in ("overview", "findings", "evidence", "audit", "coverage", "provenance"):
        assert f'data-view="{name}"' in page
        assert f'id="view-{name}"' in page
    for marker in ("Observed Pipeline State", "Assessment State Overview", "master-detail", "timeline", "brandmark", "coverage-grid", "finding-detail", "evidence-detail"):
        assert marker in page
    assert page.count("<svg") >= 7


def test_int_dash_015_explicit_non_mutating_inspection():
    source = inspect.getsource(Dashboard)
    assert ".inspect_chain_integrity()" in source
    assert "verify_chain_integrity(" not in source
    assert "._conn" not in source
    assert "write_" not in source


def test_empty_store_is_explicit_not_fabricated_success():
    with serving(empty=True) as server:
        data = snapshot(server)
        assert data["assets"] == []
        assert all(count == 0 for count in data["counts"].values())
        assert data["chain"]["intact"] is True  # Empty event chain + GENESIS, not asset assurance.
        assert data["assessment_states"] == {}


def test_response_headers_csp_hashes_head_and_failure():
    import base64
    with serving() as server:
        status, headers, body = request(server)
        assert status == 200
        for name, expected in (("X-Content-Type-Options", "nosniff"), ("Referrer-Policy", "no-referrer"), ("X-Frame-Options", "DENY"), ("Cache-Control", "no-store")):
            assert headers[name] == expected
        csp = headers["Content-Security-Policy"]
        for content in (_CSS, _JS):
            digest = base64.b64encode(hashlib.sha256(content.encode()).digest()).decode()
            assert "'sha256-" + digest + "'" in csp
        assert "unsafe-inline" not in csp and "https:" not in csp
        assert request(server, method="HEAD")[2] == b""
        assert request(server, "/missing")[0] == 404
        assert request(server, headers={"Host": "foreign.invalid"})[0] == 403
    with serving(unavailable=True) as server:
        status, _, body = request(server, "/api/dashboard")
        assert status == 503 and b"UNAVAILABLE" in body


def test_readiness_pipeline_never_infers_live_telemetry():
    assert "RUNNING" not in _JS and "PENDING" not in _JS
    assert "'Ingestion','UNAVAILABLE'" in _JS
    assert "digests.has(d)" in _JS  # C4 correlation only by stored evidence digest.
    assert "not live execution telemetry" in _page()


def test_snapshot_query_count_is_bounded():
    class Store:
        calls = []
        def __getattr__(self, name):
            assert name.startswith("query_")
            def read():
                self.calls.append(name)
                return []
            return read
    class Audit:
        def inspect_chain_integrity(self):
            from assurance_system.supervisor.audit_chain import ChainVerificationResult
            return ChainVerificationResult(True)
    store = Store()
    Dashboard(store, audit_chain_factory=lambda _: Audit()).snapshot()
    assert len(store.calls) == 5
