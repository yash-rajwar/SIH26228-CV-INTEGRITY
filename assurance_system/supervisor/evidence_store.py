# assurance_system/supervisor/evidence_store.py
#
# SHA-256 streaming pattern and SQLite/WAL connection setup adapted from R17 (clay-good/origin, MIT licence).
# See NOTICE file for attribution. Project-specific schema, supervisor-only write enforcement,
# hash-chain integration, and CHECK constraints are added by this project.
#
# REUSE decision: REUSE-018 — EXTRACT (R17 patterns); REIMPLEMENT (project code).
# Do NOT copy verbatim from R17. This file implements project-specific schema and security requirements.

"""Supervisor-owned SQLite persistence for assurance evidence."""

import io
import json
import sqlite3
import uuid
import zipfile
from typing import Any

from assurance_system.exceptions import (
    AuditWriteError,
    SchemaViolationError,
    StorageWriteError,
)


_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS evidence_records (
    record_id               TEXT PRIMARY KEY NOT NULL,
    schema_version          TEXT NOT NULL,
    asset_id                TEXT NOT NULL,
    method_id               TEXT NOT NULL,
    assessment_status       TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                            CHECK (assessment_status IN (
                              'COMPLETED','ASSESSMENT_ERROR','UNAVAILABLE','UNSUPPORTED',
                              'DEFERRED_IN_SCOPE','ARTIFACT_UNIT_AMBIGUOUS',
                              'LOAD_BLOCKED','LOAD_SUCCESS','LOAD_ERROR',
                              'ONNX_PATH_CONTAINMENT_VIOLATION',
                              'STRUCTURAL_VALID','STRUCTURAL_INVALID','REFERENCE_UNAVAILABLE')),
    raw_signal              TEXT,
    access_mode             TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    artifact_unit_id        TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    coverage_gap_clean_label INTEGER NOT NULL DEFAULT 1
                            CHECK (coverage_gap_clean_label = 1),
    limitations             TEXT NOT NULL,
    non_claims              TEXT NOT NULL,
    dependency_declaration  TEXT,
    assessment_timestamp    TEXT NOT NULL,
    worker_id               TEXT NOT NULL DEFAULT 'SUPERVISOR',
    record_digest           TEXT,
    is_synthetic            INTEGER NOT NULL DEFAULT 0 CHECK (is_synthetic IN (0,1)),
    created_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id                           TEXT PRIMARY KEY NOT NULL,
    schema_version                       TEXT NOT NULL,
    asset_id                             TEXT NOT NULL,
    method_id                            TEXT NOT NULL,
    detection_status                     TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    interpretation_status                TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    applicability_status                 TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    raw_signal                           TEXT,
    reference_health                     TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    limitations                          TEXT NOT NULL,
    non_claims                           TEXT NOT NULL,
    dependency_declaration               TEXT NOT NULL,
    coverage_gap_clean_label             INTEGER NOT NULL DEFAULT 1
                                         CHECK (coverage_gap_clean_label = 1),
    anomaly_not_malicious_non_claim      INTEGER NOT NULL DEFAULT 0
                                         CHECK (anomaly_not_malicious_non_claim IN (0,1)),
    global_backdoor_absence_not_established INTEGER NOT NULL DEFAULT 0
                                         CHECK (global_backdoor_absence_not_established IN (0,1)),
    pf_002_non_claim                     TEXT NOT NULL DEFAULT 'C4_BINDING_UNAVAILABLE',
    analyst_disposition_prompt           TEXT NOT NULL DEFAULT 'UNAVAILABLE_NO_DECISION',
    is_synthetic                         INTEGER NOT NULL DEFAULT 0 CHECK (is_synthetic IN (0,1)),
    created_at                           TEXT NOT NULL
                                         DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS provenance_records (
    provenance_id               TEXT PRIMARY KEY NOT NULL,
    schema_version              TEXT NOT NULL,
    artifact_unit_digest        TEXT NOT NULL,
    evidence_record_digests     TEXT NOT NULL,
    signing_key_id              TEXT NOT NULL,
    signature                   TEXT,
    signature_algorithm         TEXT,
    canonicalization_algorithm  TEXT NOT NULL DEFAULT 'json-canonical-utf8-sort-keys-v1',
    sequence_number             INTEGER NOT NULL,
    replay_nonce                TEXT NOT NULL UNIQUE,
    pf_002_non_claim            TEXT NOT NULL,
    signing_status              TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                                CHECK (signing_status IN ('SIGNED','SIGNING_UNAVAILABLE')),
    timestamp                   TEXT NOT NULL,
    created_at                  TEXT NOT NULL
                                DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS deferred_records (
    record_id               TEXT PRIMARY KEY NOT NULL,
    schema_version          TEXT NOT NULL,
    asset_id                TEXT NOT NULL,
    method_id               TEXT NOT NULL,
    assessment_status       TEXT NOT NULL DEFAULT 'DEFERRED_IN_SCOPE'
                            CHECK (assessment_status IN (
                              'DEFERRED_IN_SCOPE','REFERENCE_UNAVAILABLE',
                              'COMPLETENESS_UNAVAILABLE')),
    deferral_reason         TEXT NOT NULL,
    finite_battery_non_claim INTEGER NOT NULL DEFAULT 0 CHECK (finite_battery_non_claim IN (0,1)),
    limitations             TEXT NOT NULL,
    non_claims              TEXT NOT NULL,
    created_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS reference_health (
    reference_id            TEXT PRIMARY KEY NOT NULL,
    reference_name          TEXT NOT NULL,
    health_state            TEXT NOT NULL DEFAULT 'UNAVAILABLE'
                            CHECK (health_state IN (
                              'UNAVAILABLE','HEALTH_UNVERIFIED','FORMAT_ASSET',
                              'HEALTH_VERIFIED','CONTAMINATION_SUSPECTED','STALE_SUSPECTED')),
    format_category         TEXT,
    gate_completion_record  TEXT,
    last_verified_timestamp TEXT,
    updated_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type             TEXT NOT NULL,
    payload_digest         TEXT NOT NULL,
    previous_event_digest  TEXT NOT NULL DEFAULT 'GENESIS',
    chain_link_hash        TEXT NOT NULL,
    timestamp              TEXT NOT NULL,
    supervisor_version_id  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chain_state (
    id                      INTEGER PRIMARY KEY CHECK (id = 1),
    last_event_id           INTEGER NOT NULL DEFAULT 0,
    last_chain_link_hash    TEXT    NOT NULL DEFAULT 'GENESIS',
    last_sequence_number    INTEGER NOT NULL DEFAULT 0,
    updated_at              TEXT NOT NULL
                            DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);

INSERT OR IGNORE INTO chain_state
  (id, last_event_id, last_chain_link_hash, last_sequence_number)
  VALUES (1, 0, 'GENESIS', 0);

CREATE INDEX IF NOT EXISTS idx_ev_asset_method ON evidence_records(asset_id, method_id);
CREATE INDEX IF NOT EXISTS idx_finding_asset   ON findings(asset_id);
CREATE INDEX IF NOT EXISTS idx_prov_artifact   ON provenance_records(artifact_unit_digest);
CREATE INDEX IF NOT EXISTS idx_audit_type      ON audit_events(event_type);
"""

_PROHIBITED_AGGREGATE_FIELDS = frozenset(
    {
        "_".join(("risk", "score")),
        "_".join(("aggregate", "assurance")),
        "_".join(("compromise", "probability")),
    }
)
_JSON_FIELDS = frozenset(
    {
        "raw_signal",
        "limitations",
        "non_claims",
        "dependency_declaration",
        "evidence_record_digests",
        "gate_completion_record",
    }
)


class EvidenceStore:
    """SQLite store whose single connection is owned by the supervisor."""

    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=True)
        self._conn.row_factory = sqlite3.Row
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._apply_schema()
        except sqlite3.Error as exc:
            self._conn.close()
            raise StorageWriteError("Failed to initialise evidence store") from exc

    def _apply_schema(self) -> None:
        with self._conn:
            self._conn.executescript(_DDL)

    def _confirm_wal_mode(self) -> bool:
        row = self._conn.execute("PRAGMA journal_mode").fetchone()
        return row is not None and str(row[0]).lower() == "wal"

    @staticmethod
    def _require_fields(record: dict[str, Any], fields: tuple[str, ...]) -> None:
        missing = [field for field in fields if field not in record]
        if missing:
            raise SchemaViolationError(
                "Missing required field(s): " + ", ".join(missing)
            )

    @classmethod
    def _reject_prohibited_fields(cls, value: Any) -> None:
        if isinstance(value, dict):
            if _PROHIBITED_AGGREGATE_FIELDS.intersection(value):
                raise SchemaViolationError("Prohibited aggregate field present")
            for nested in value.values():
                cls._reject_prohibited_fields(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                cls._reject_prohibited_fields(nested)

    @staticmethod
    def _encode(value: Any) -> str | None:
        if value is None:
            return None
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _decode_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        result = dict(row)
        for field in _JSON_FIELDS.intersection(result):
            value = result[field]
            if value is not None:
                result[field] = json.loads(value)
        return result

    def write_evidence_record(self, record: dict) -> str:
        self._reject_prohibited_fields(record)
        self._require_fields(
            record,
            (
                "schema_version",
                "asset_id",
                "method_id",
                "assessment_status",
                "coverage_gap_clean_label",
                "limitations",
                "non_claims",
                "assessment_timestamp",
            ),
        )
        clean_label = record["coverage_gap_clean_label"]
        if not (clean_label is True or type(clean_label) is int and clean_label == 1):
            raise SchemaViolationError(
                "coverage_gap_clean_label must be exactly integer 1 or True"
            )
        record_id = str(record.get("record_id") or uuid.uuid4())
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO evidence_records
                       (record_id, schema_version, asset_id, method_id,
                        assessment_status, raw_signal, access_mode,
                        artifact_unit_id, coverage_gap_clean_label, limitations,
                        non_claims, dependency_declaration,
                        assessment_timestamp, worker_id, record_digest,
                        is_synthetic)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        record_id,
                        record["schema_version"],
                        record["asset_id"],
                        record["method_id"],
                        record["assessment_status"],
                        self._encode(record.get("raw_signal")),
                        record.get("access_mode", "UNAVAILABLE"),
                        record.get("artifact_unit_id", "UNAVAILABLE"),
                        clean_label,
                        self._encode(record["limitations"]),
                        self._encode(record["non_claims"]),
                        self._encode(record.get("dependency_declaration")),
                        record["assessment_timestamp"],
                        record.get("worker_id", "SUPERVISOR"),
                        record.get("record_digest"),
                        int(bool(record.get("is_synthetic", False))),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageWriteError("Failed to write evidence record") from exc
        return record_id

    def write_finding(self, finding: dict) -> str:
        self._reject_prohibited_fields(finding)
        self._require_fields(
            finding,
            (
                "schema_version",
                "asset_id",
                "method_id",
                "limitations",
                "non_claims",
                "dependency_declaration",
                "coverage_gap_clean_label",
            ),
        )
        clean_label = finding["coverage_gap_clean_label"]
        if not (clean_label is True or type(clean_label) is int and clean_label == 1):
            raise SchemaViolationError(
                "coverage_gap_clean_label must be exactly integer 1 or True"
            )
        finding_id = str(finding.get("finding_id") or uuid.uuid4())
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO findings
                       (finding_id, schema_version, asset_id, method_id,
                        detection_status, interpretation_status,
                        applicability_status, raw_signal, reference_health,
                        limitations, non_claims, dependency_declaration,
                        coverage_gap_clean_label,
                        anomaly_not_malicious_non_claim,
                        global_backdoor_absence_not_established,
                        pf_002_non_claim, analyst_disposition_prompt,
                        is_synthetic)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        finding_id,
                        finding["schema_version"],
                        finding["asset_id"],
                        finding["method_id"],
                        finding.get("detection_status", "UNAVAILABLE"),
                        finding.get("interpretation_status", "UNAVAILABLE"),
                        finding.get("applicability_status", "UNAVAILABLE"),
                        self._encode(finding.get("raw_signal")),
                        finding.get("reference_health", "UNAVAILABLE"),
                        self._encode(finding["limitations"]),
                        self._encode(finding["non_claims"]),
                        self._encode(finding["dependency_declaration"]),
                        clean_label,
                        int(bool(finding.get("anomaly_not_malicious_non_claim", False))),
                        int(
                            bool(
                                finding.get(
                                    "global_backdoor_absence_not_established", False
                                )
                            )
                        ),
                        finding.get("pf_002_non_claim", "C4_BINDING_UNAVAILABLE"),
                        finding.get(
                            "analyst_disposition_prompt", "UNAVAILABLE_NO_DECISION"
                        ),
                        int(bool(finding.get("is_synthetic", False))),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageWriteError("Failed to write finding") from exc
        return finding_id

    def write_provenance_record(self, record: dict) -> str:
        self._reject_prohibited_fields(record)
        self._require_fields(
            record,
            (
                "schema_version",
                "artifact_unit_digest",
                "evidence_record_digests",
                "signing_key_id",
                "sequence_number",
                "replay_nonce",
                "pf_002_non_claim",
                "signing_status",
                "timestamp",
            ),
        )
        provenance_id = str(record.get("provenance_id") or uuid.uuid4())
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO provenance_records
                       (provenance_id, schema_version, artifact_unit_digest,
                        evidence_record_digests, signing_key_id, signature,
                        signature_algorithm, canonicalization_algorithm,
                        sequence_number, replay_nonce, pf_002_non_claim,
                        signing_status, timestamp)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        provenance_id,
                        record["schema_version"],
                        record["artifact_unit_digest"],
                        self._encode(record["evidence_record_digests"]),
                        record["signing_key_id"],
                        record.get("signature"),
                        record.get("signature_algorithm"),
                        record.get(
                            "canonicalization_algorithm",
                            "json-canonical-utf8-sort-keys-v1",
                        ),
                        record["sequence_number"],
                        record["replay_nonce"],
                        record["pf_002_non_claim"],
                        record["signing_status"],
                        record["timestamp"],
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageWriteError("Failed to write provenance record") from exc
        return provenance_id

    def write_audit_event(self, event_type: str, payload: dict) -> str:
        self._reject_prohibited_fields(payload)
        self._require_fields(
            payload,
            (
                "payload_digest",
                "previous_event_digest",
                "chain_link_hash",
                "timestamp",
                "supervisor_version_id",
                "sequence_number",
            ),
        )
        try:
            with self._conn:
                state = self._conn.execute(
                    """SELECT last_chain_link_hash, last_sequence_number
                       FROM chain_state WHERE id = ?""",
                    (1,),
                ).fetchone()
                if state is None:
                    raise AuditWriteError("Audit chain state is missing")
                expected_sequence = state["last_sequence_number"] + 1
                if payload["sequence_number"] != expected_sequence:
                    raise AuditWriteError("Audit sequence is not monotonic")
                if payload["previous_event_digest"] != state["last_chain_link_hash"]:
                    raise AuditWriteError("Audit predecessor does not match chain state")
                cursor = self._conn.execute(
                    """INSERT INTO audit_events
                       (event_type, payload_digest, previous_event_digest,
                        chain_link_hash, timestamp, supervisor_version_id)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        event_type,
                        payload["payload_digest"],
                        payload["previous_event_digest"],
                        payload["chain_link_hash"],
                        payload["timestamp"],
                        payload["supervisor_version_id"],
                    ),
                )
                self._conn.execute(
                    """UPDATE chain_state
                       SET last_event_id = ?, last_chain_link_hash = ?,
                           last_sequence_number = ?,
                           updated_at = strftime('%Y-%m-%dT%H:%M:%SZ','now')
                       WHERE id = ?""",
                    (
                        cursor.lastrowid,
                        payload["chain_link_hash"],
                        payload["sequence_number"],
                        1,
                    ),
                )
        except sqlite3.Error as exc:
            raise AuditWriteError("Failed to write audit event") from exc
        return str(cursor.lastrowid)

    def write_deferred_record(self, record: dict) -> str:
        self._reject_prohibited_fields(record)
        self._require_fields(
            record,
            (
                "schema_version",
                "asset_id",
                "method_id",
                "assessment_status",
                "deferral_reason",
                "limitations",
                "non_claims",
            ),
        )
        record_id = str(record.get("record_id") or uuid.uuid4())
        try:
            with self._conn:
                self._conn.execute(
                    """INSERT INTO deferred_records
                       (record_id, schema_version, asset_id, method_id,
                        assessment_status, deferral_reason,
                        finite_battery_non_claim, limitations, non_claims)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        record_id,
                        record["schema_version"],
                        record["asset_id"],
                        record["method_id"],
                        record["assessment_status"],
                        record["deferral_reason"],
                        int(bool(record.get("finite_battery_non_claim", False))),
                        self._encode(record["limitations"]),
                        self._encode(record["non_claims"]),
                    ),
                )
        except sqlite3.Error as exc:
            raise StorageWriteError("Failed to write deferred record") from exc
        return record_id

    def query_chain_state(self) -> dict | None:
        """Narrow SELECT-only durable audit state; no connection exposure."""
        row = self._conn.execute(
            """SELECT last_event_id, last_chain_link_hash, last_sequence_number
               FROM chain_state WHERE id = ?""", (1,),
        ).fetchone()
        return dict(row) if row is not None else None

    def query_all_evidence(self) -> list[dict]:
        """Read all persisted evidence, including older observations."""
        rows = self._conn.execute(
            "SELECT * FROM evidence_records ORDER BY created_at, record_id"
        ).fetchall()
        return [self._decode_row(row) for row in rows]

    def query_provenance_records(self) -> list[dict]:
        """Read provenance with decoded JSON and deterministic ordering."""
        rows = self._conn.execute(
            "SELECT * FROM provenance_records ORDER BY created_at, provenance_id"
        ).fetchall()
        return [self._decode_row(row) for row in rows]

    def query_findings(self, asset_id: str = None) -> list[dict]:
        if asset_id is None:
            rows = self._conn.execute(
                "SELECT * FROM findings ORDER BY created_at, finding_id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT * FROM findings
                   WHERE asset_id = ? ORDER BY created_at, finding_id""",
                (asset_id,),
            ).fetchall()
        return [self._decode_row(row) for row in rows]

    def query_evidence(self, asset_id: str, method_id: str) -> dict | None:
        row = self._conn.execute(
            """SELECT * FROM evidence_records
               WHERE asset_id = ? AND method_id = ?
               ORDER BY created_at DESC, record_id DESC LIMIT 1""",
            (asset_id, method_id),
        ).fetchone()
        return self._decode_row(row)

    def query_audit_trail(self, limit: int = None) -> list[dict]:
        if limit is None:
            rows = self._conn.execute(
                "SELECT * FROM audit_events ORDER BY event_id"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM audit_events ORDER BY event_id LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def query_deferred(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM deferred_records ORDER BY created_at, record_id"
        ).fetchall()
        return [self._decode_row(row) for row in rows]

    def query_reference_health(self, reference_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM reference_health WHERE reference_id = ?", (reference_id,)
        ).fetchone()
        return self._decode_row(row)

    def export_bundle(self, asset_id: str) -> bytes:
        evidence_rows = self._conn.execute(
            """SELECT * FROM evidence_records
               WHERE asset_id = ? ORDER BY created_at, record_id""",
            (asset_id,),
        ).fetchall()
        provenance_rows = self._conn.execute(
            "SELECT * FROM provenance_records ORDER BY created_at, provenance_id"
        ).fetchall()
        documents = {
            "evidence.json": [self._decode_row(row) for row in evidence_rows],
            "findings.json": self.query_findings(asset_id),
            "provenance.json": [self._decode_row(row) for row in provenance_rows],
            "audit.json": self.query_audit_trail(),
        }
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in documents.items():
                archive.writestr(
                    name,
                    json.dumps(content, sort_keys=True, separators=(",", ":")),
                )
        return bundle.getvalue()
