"""Read-only analyst command-line interface for the assurance system."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sqlite3
import sys
from typing import Any, Callable, TextIO

from assurance_system.config.loader import ConfigLoader
from assurance_system.exceptions import AssuranceSystemError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.orchestrator import SupervisorOrchestrator


class AssuranceCLI:
    """Dispatch analyst commands without interpreting or mutating stored records."""

    def __init__(
        self,
        *,
        config_loader: ConfigLoader | None = None,
        evidence_store_factory: Callable[[str], Any] | None = None,
        audit_chain_factory: Callable[[Any], Any] | None = None,
        orchestrator_factory: Callable[..., Any] | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self._config_loader = config_loader or ConfigLoader()
        self._evidence_store_factory = evidence_store_factory or EvidenceStore
        self._audit_chain_factory = audit_chain_factory or AuditChainWriter
        self._orchestrator_factory = orchestrator_factory or SupervisorOrchestrator
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def run(self, argv: list[str] | None = None) -> int:
        """Parse ``argv``, execute one command, and return its process exit code."""

        parser = self._build_parser()
        try:
            arguments = parser.parse_args(argv)
        except SystemExit as exc:
            return int(exc.code)

        try:
            return int(arguments.command_handler(arguments))
        except (
            AssuranceSystemError,
            KeyError,
            OSError,
            sqlite3.Error,
            TypeError,
            ValueError,
        ) as exc:
            print(f"ERROR: {exc}", file=self._stderr)
            return 1

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="assurance-cli",
            description="Offline analyst interface for stored assurance evidence.",
        )
        commands = parser.add_subparsers(dest="command", required=True)

        assess = commands.add_parser("assess", help="run an assessment manifest")
        assess.add_argument("--submission", required=True)
        assess.set_defaults(command_handler=self._assess)

        finding = commands.add_parser("show-finding", help="show stored findings")
        finding.add_argument("--asset-id", required=True)
        finding.set_defaults(command_handler=self._show_finding)

        evidence = commands.add_parser("show-evidence", help="show stored evidence")
        evidence.add_argument("--asset-id", required=True)
        evidence.add_argument("--method", required=True)
        evidence.set_defaults(command_handler=self._show_evidence)

        audit = commands.add_parser("show-audit-trail", help="show the audit chain")
        audit.add_argument("--limit", type=self._positive_integer)
        audit.set_defaults(command_handler=self._show_audit_trail)

        export = commands.add_parser("export-bundle", help="export an evidence bundle")
        export.add_argument("--asset-id", required=True)
        export.add_argument("--output", required=True)
        export.set_defaults(command_handler=self._export_bundle)

        deferred = commands.add_parser(
            "list-deferred", help="show explicit deferred-method records"
        )
        deferred.set_defaults(command_handler=self._list_deferred)

        dashboard = commands.add_parser("dashboard", help="start the analyst dashboard")
        dashboard.add_argument("--port", type=self._positive_integer)
        dashboard.set_defaults(command_handler=self._dashboard)

        return parser

    @staticmethod
    def _positive_integer(value: str) -> int:
        parsed = int(value)
        if parsed <= 0:
            raise argparse.ArgumentTypeError("expected a positive integer")
        return parsed

    def _open_store(self) -> Any:
        config = self._config_loader.load()
        store_path = config["system"]["evidence_store"]["path"]
        return self._evidence_store_factory(store_path)

    def _print_json(self, value: Any) -> None:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            value = dataclasses.asdict(value)
        print(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, default=str),
            file=self._stdout,
        )

    @staticmethod
    def _reported_methods(findings: list[dict[str, Any]]) -> list[str]:
        methods: set[str] = set()
        for finding in findings:
            dependency = finding.get("dependency_declaration")
            co_firing = (
                dependency.get("co_firing_detectors", [])
                if isinstance(dependency, dict)
                else []
            )
            methods.update(
                method for method in co_firing if isinstance(method, str) and method
            )
            if not co_firing:
                method_id = finding.get("method_id")
                if isinstance(method_id, str) and method_id:
                    methods.add(method_id)
        return sorted(methods)

    def _assess(self, arguments: argparse.Namespace) -> int:
        store = self._open_store()
        audit_chain = self._audit_chain_factory(store)
        orchestrator = self._orchestrator_factory(
            store,
            audit_chain,
            config_loader=self._config_loader,
        )

        existing_ids = {
            finding.get("finding_id") for finding in store.query_findings()
        }
        summary = orchestrator.run_pipeline(arguments.submission)
        new_findings = [
            finding
            for finding in store.query_findings()
            if finding.get("finding_id") not in existing_ids
        ]

        output = {
            "asset_ids": sorted(
                {
                    finding["asset_id"]
                    for finding in new_findings
                    if finding.get("asset_id")
                }
            ),
            "finding_statuses": [
                {
                    "asset_id": finding.get("asset_id", "UNAVAILABLE"),
                    "method_id": finding.get("method_id", "UNAVAILABLE"),
                    "detection_status": finding.get(
                        "detection_status", "UNAVAILABLE"
                    ),
                }
                for finding in new_findings
            ],
            "findings": new_findings,
            "methods_executed": self._reported_methods(new_findings),
            "pipeline_summary": (
                dataclasses.asdict(summary)
                if dataclasses.is_dataclass(summary) and not isinstance(summary, type)
                else summary
            ),
        }
        self._print_json(output)
        return 0

    def _show_finding(self, arguments: argparse.Namespace) -> int:
        findings = self._open_store().query_findings(arguments.asset_id)
        if not findings:
            print("Finding not found", file=self._stdout)
            print("UNAVAILABLE", file=self._stdout)
            return 1
        self._print_json(findings)
        return 0

    def _show_evidence(self, arguments: argparse.Namespace) -> int:
        evidence = self._open_store().query_evidence(
            arguments.asset_id, arguments.method
        )
        if evidence is None:
            print("Evidence not found", file=self._stdout)
            print("UNAVAILABLE", file=self._stdout)
            return 1
        self._print_json(evidence)
        return 0

    def _show_audit_trail(self, arguments: argparse.Namespace) -> int:
        store = self._open_store()
        verification = self._audit_chain_factory(store).verify_chain_integrity()
        if not verification.intact:
            print("CHAIN_CORRUPT", file=self._stdout)
        self._print_json(store.query_audit_trail(arguments.limit))
        return 0

    def _export_bundle(self, arguments: argparse.Namespace) -> int:
        try:
            from assurance_system.interfaces.exporter import EvidenceExporter
        except ImportError:
            print("export-bundle requires TASK-025", file=self._stdout)
            return 1

        exporter = EvidenceExporter(self._open_store())
        exporter.export_bundle(arguments.asset_id, arguments.output)
        print(arguments.output, file=self._stdout)
        return 0

    def _list_deferred(self, _arguments: argparse.Namespace) -> int:
        records = self._open_store().query_deferred()
        if not records:
            print(
                "WARNING: no deferred records are available; deferred coverage "
                "status is UNAVAILABLE",
                file=self._stdout,
            )
            return 0
        self._print_json(records)
        return 0

    def _dashboard(self, arguments: argparse.Namespace) -> int:
        try:
            from assurance_system.interfaces.dashboard import Dashboard
        except ImportError:
            print("dashboard requires TASK-024", file=self._stdout)
            return 1

        dashboard = Dashboard(self._open_store())
        if arguments.port is None:
            dashboard.run()
        else:
            dashboard.run(port=arguments.port)
        return 0
