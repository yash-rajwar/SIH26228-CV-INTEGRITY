"""COMP-CAP: bounded scope declarations and explicit missing-coverage records.

Authority: Architecture §§2.3, 7 AC-09 and Technical Specification §§3.1,
3.15, 20.3; TASK-020 defines ``emit_deferred_records(asset_id)``. The task's
technical §3.17 reference points to fixtures, not a separate COMP-CAP contract.
"""

from __future__ import annotations

import uuid
from typing import Any

from assurance_system.constants import AssessmentStatus, AuditEventType
from assurance_system.exceptions import CapabilityDeclarationError
from assurance_system.supervisor.audit_chain import AuditChainWriter
from assurance_system.supervisor.evidence_store import EvidenceStore
from assurance_system.supervisor.schema_validator import (
    EvidenceSchemaValidator,
    ValidationResult,
)


_SCHEMA_VERSION = "v1.0"  # Frozen by SP-003; not a deployment parameter.
_COMPLETENESS_UNAVAILABLE = "COMPLETENESS_UNAVAILABLE"  # Deferred-table vocabulary.
_T05D_NON_CLAIM = (
    "T05d (clean-label poisoning) is NOT detectable under the current assessment "
    "scope; no detection claim is made for this attack class."
)
_LIMITATIONS = (
    "A scope declaration does not execute an assessment or establish a result.",
    "Host dependencies and per-asset prerequisites must be verified before dispatch.",
    "ONNX runtime verification and identity definition remain blocked by "
    "HOST-CAP-003 and E-2; C3C is not a declared supported capability.",
)
_NON_CLAIMS = (
    "No malware detection claim is made.",
    "No model safety guarantee is established.",
    "Complete integrity assurance is not established.",
    "No probability or confidence of integrity is reported.",
    "Unassessed and deferred coverage does not establish absence of anomalies.",
    _T05D_NON_CLAIM,
)

# These are bounded implemented operations, not claims about every format or
# successful per-asset assessment. C3C is excluded while its runtime is blocked.
# No caller-supplied description or result can expand these scopes.
_SUPPORTED_METHODS = {
    "M01": (
        "All-box YOLO detection and segmentation geometry checks.",
        "COCO runtime validation requires pycocotools (HOST-CAP-001); "
        "YOLO pose and OBB are outside PRE-05 scope.",
        "Geometry checks do not establish label semantic correctness.",
    ),
    "M02": (
        "Streaming SHA-256 exact duplicate grouping.",
        "Only byte-identical files are compared; unreadable files remain errors.",
        "Exact duplicate grouping does not establish intent or near-duplicate coverage.",
    ),
    "M06": (
        "Source HHI, Shannon entropy, counts, and shares.",
        "Contributor identities are untrusted unless independently established.",
        "SYBIL_UNRELIABLE: concentration statistics do not authenticate contributors.",
    ),
    "M15": (
        "Image-file SHA-256 byte identity, hash tier only.",
        "No image decoding or PDQ near-duplicate implementation is included.",
        "Matching image bytes do not establish semantic integrity or visual similarity.",
    ),
    "C3A": (
        "PyTorch single-file artifact-unit resolution and path containment.",
        "Only pytorch-single-file-v1 is frozen; ONNX identity remains blocked by E-2.",
        "Path containment does not establish content properties or causal execution.",
    ),
    "C3B": (
        "SHA-256 identity of an already-resolved PyTorch artifact unit.",
        "No digest is available for an ambiguous unit; ONNX identity is blocked by E-2.",
        "A matching digest does not establish behavior, semantic equivalence, "
        "backdoor absence, or causal execution.",
    ),
    "C3D": (
        "Restricted PyTorch loading with weights_only=True in a worker subprocess.",
        "Requires the verified Torch version; supervisor OOM/timeout integration "
        "remains pending TASK-022.",
        "Successful restricted loading does not establish behavioral properties "
        "or global backdoor absence.",
    ),
}

# Architecture-specific unavailable states are retained. T05d uses the existing
# deferred-table envelope, with PERMANENT_NON_CLAIM persisted in reason and text;
# it is never represented as a future detection capability or a new status.
_DEFERRED_METHODS = (
    ("M07", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Behavioral model consistency battery is deferred; a reference and an "
     "isolated target-host worker have not been established.",
     "A finite behavioral battery cannot establish universal backdoor absence.", True),
    ("M03-PDQ", AssessmentStatus.DEFERRED_IN_SCOPE,
     "PDQ near-duplicate detection is deferred pending native build and calibration.",
     "Near-duplicate relationships have not been assessed.", False),
    ("M04", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Statistical drift detection is deferred; calibration and reference are unavailable.",
     "Statistical drift has not been assessed.", False),
    ("M05", AssessmentStatus.DEFERRED_IN_SCOPE,
     "OOD detection is deferred; calibration and reference are unavailable.",
     "Out-of-distribution behavior has not been assessed.", False),
    ("M11", AssessmentStatus.REFERENCE_UNAVAILABLE,
     "Reference-relative comparison is unavailable under the MVP capability scope.",
     "No reference-relative comparison result is established.", False),
    ("TORCHSCRIPT", AssessmentStatus.DEFERRED_IN_SCOPE,
     "TorchScript ingestion is deferred; an isolated worker is not demonstrated.",
     "TorchScript artifacts have not been assessed.", False),
    ("SAFETENSORS", AssessmentStatus.DEFERRED_IN_SCOPE,
     "SafeTensors plus JSON configuration is deferred; RC-014 mapping is absent.",
     "SafeTensors artifacts have not been assessed.", False),
    ("TAIL_COMPLETENESS", _COMPLETENESS_UNAVAILABLE,
     "External tail completeness witness is outside the MVP scope.",
     "Local audit-chain integrity does not establish tail completeness.", False),
    ("SYBIL_IDENTITY", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Sybil-resistant contributor identity authentication lacks an external mechanism.",
     "SYBIL_UNRELIABLE: contributor identity authenticity is not established.", False),
    ("T05d", AssessmentStatus.DEFERRED_IN_SCOPE,
     "PERMANENT_NON_CLAIM: T05d detection is a permanent coverage gap, "
     "not a future deferred capability.", _T05D_NON_CLAIM, False),
    ("ACTIVATION_SPACE", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Activation-space analysis remains a post-MVP research candidate.",
     "Activation-space behavior has not been assessed.", False),
    ("NEURAL_CLEANSE", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Neural Cleanse remains a post-MVP research candidate.",
     "No Neural Cleanse detection claim is made.", False),
    ("B3D", AssessmentStatus.DEFERRED_IN_SCOPE,
     "B3D remains a post-MVP research candidate.",
     "No B3D detection claim is made.", False),
    ("ABS", AssessmentStatus.DEFERRED_IN_SCOPE,
     "ABS remains a post-MVP research candidate.",
     "No ABS detection claim is made.", False),
    ("AC", AssessmentStatus.DEFERRED_IN_SCOPE,
     "Activation Clustering remains a post-MVP research candidate.",
     "No Activation Clustering detection claim is made.", False),
)
_DEFERRED_FIELDS = frozenset({
    "record_id", "schema_version", "asset_id", "method_id", "assessment_status",
    "deferral_reason", "finite_battery_non_claim", "limitations", "non_claims",
})
_DECLARATION_FIELDS = frozenset({
    "schema_version", "asset_id", "assessment_status", "supported_capabilities",
    "deferred_records", "limitations", "non_claims",
})


class CapabilityDeclaration:
    """Supervisor component with a closed method registry and no artifact parsing."""

    def __init__(self, evidence_store: EvidenceStore, audit_chain: AuditChainWriter):
        self._store = evidence_store
        self._audit = audit_chain
        self._schema = EvidenceSchemaValidator()

    @staticmethod
    def _validate_asset_id(asset_id: str) -> None:
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise CapabilityDeclarationError("asset_id must be a non-empty string")

    @staticmethod
    def _supported_record(method_id: str) -> dict[str, Any]:
        description, limitation, non_claim = _SUPPORTED_METHODS[method_id]
        return {
            "method_id": method_id,
            "assessment_status": AssessmentStatus.UNAVAILABLE,
            "limitations": [description, limitation, *_LIMITATIONS],
            "non_claims": [non_claim, *_NON_CLAIMS],
        }

    @staticmethod
    def _deferred_record(asset_id: str, spec: tuple) -> dict[str, Any]:
        method_id, status, reason, non_claim, finite = spec
        return {
            "record_id": str(uuid.uuid4()),
            "schema_version": _SCHEMA_VERSION,
            "asset_id": asset_id,
            "method_id": method_id,
            "assessment_status": status,
            "deferral_reason": reason,
            "finite_battery_non_claim": finite,
            "limitations": [reason],
            "non_claims": [non_claim, *_NON_CLAIMS],
        }

    def validate_deferred_record(self, record: dict) -> ValidationResult:
        """Gate the existing deferred schema and immutable coverage semantics."""

        if not isinstance(record, dict) or set(record) != _DEFERRED_FIELDS:
            return ValidationResult(False, "invalid deferred record fields")
        if self._schema._recursive_prohibited_scan(record):
            return ValidationResult(False, "prohibited field present")
        try:
            self._validate_asset_id(record["asset_id"])
            identifier = uuid.UUID(record["record_id"])
            if identifier.version != 4:
                return ValidationResult(False, "record_id must be UUID4")
            spec = next(
                (item for item in _DEFERRED_METHODS if item[0] == record["method_id"]),
                None,
            )
            if spec is None:
                return ValidationResult(False, "unsupported deferred method")
            if type(record["finite_battery_non_claim"]) is not bool:
                return ValidationResult(False, "finite_battery_non_claim must be boolean")
            if (
                record["schema_version"] != _SCHEMA_VERSION
                or record["assessment_status"] != spec[1]
                or record["deferral_reason"] != spec[2]
                or record["limitations"] != [spec[2]]
                or record["non_claims"] != [spec[3], *_NON_CLAIMS]
                or record["finite_battery_non_claim"] is not spec[4]
            ):
                return ValidationResult(False, "deferred scope or non-claims changed")
        except (CapabilityDeclarationError, ValueError, TypeError, AttributeError):
            return ValidationResult(False, "invalid deferred record value")
        return ValidationResult(True)

    def validate_declaration(self, declaration: dict) -> ValidationResult:
        """Reject extra fields, unknown methods, promoted results, or removed gaps."""

        if not isinstance(declaration, dict) or set(declaration) != _DECLARATION_FIELDS:
            return ValidationResult(False, "invalid declaration fields")
        if self._schema._recursive_prohibited_scan(declaration):
            return ValidationResult(False, "prohibited field present")
        try:
            self._validate_asset_id(declaration["asset_id"])
            if (
                declaration["schema_version"] != _SCHEMA_VERSION
                or declaration["assessment_status"] != AssessmentStatus.UNAVAILABLE
                or declaration["limitations"] != list(_LIMITATIONS)
                or declaration["non_claims"] != list(_NON_CLAIMS)
            ):
                return ValidationResult(False, "declaration scope or non-claims changed")
            supported = declaration["supported_capabilities"]
            if not isinstance(supported, list):
                return ValidationResult(False, "supported_capabilities must be a list")
            seen: set[str] = set()
            for entry in supported:
                if not isinstance(entry, dict):
                    return ValidationResult(False, "invalid supported capability")
                method_id = entry.get("method_id")
                if (
                    not isinstance(method_id, str)
                    or method_id not in _SUPPORTED_METHODS
                    or method_id in seen
                ):
                    return ValidationResult(False, "unsupported or changed capability")
                description, limitation, non_claim = _SUPPORTED_METHODS[method_id]
                if entry != {
                    "method_id": method_id,
                    "assessment_status": AssessmentStatus.UNAVAILABLE,
                    "limitations": [description, limitation, *_LIMITATIONS],
                    "non_claims": [non_claim, *_NON_CLAIMS],
                }:
                    return ValidationResult(False, "supported scope or non-claims changed")
                seen.add(method_id)
            deferred = declaration["deferred_records"]
            if not isinstance(deferred, list) or len(deferred) != len(_DEFERRED_METHODS):
                return ValidationResult(False, "mandatory coverage gaps missing")
            deferred_ids: set[str] = set()
            record_ids: set[str] = set()
            for record in deferred:
                result = self.validate_deferred_record(record)
                if not result.valid:
                    return result
                if (
                    record["asset_id"] != declaration["asset_id"]
                    or record["method_id"] in deferred_ids
                    or record["record_id"] in record_ids
                ):
                    return ValidationResult(False, "invalid coverage gap binding")
                deferred_ids.add(record["method_id"])
                record_ids.add(record["record_id"])
        except (CapabilityDeclarationError, ValueError, TypeError):
            return ValidationResult(False, "invalid declaration value")
        return ValidationResult(True)

    def declare_capabilities(
        self, asset_id: str, supported_capabilities: list[str] | None = None
    ) -> dict[str, Any]:
        """Audit a scope declaration; the default advertises no supported methods."""

        self._validate_asset_id(asset_id)
        requested = [] if supported_capabilities is None else supported_capabilities
        if not isinstance(requested, list) or any(
            not isinstance(method_id, str) or method_id not in _SUPPORTED_METHODS
            for method_id in requested
        ):
            raise CapabilityDeclarationError("unsupported capability request")
        if len(requested) != len(set(requested)):
            raise CapabilityDeclarationError("duplicate capability request")
        declaration = {
            "schema_version": _SCHEMA_VERSION,
            "asset_id": asset_id,
            "assessment_status": AssessmentStatus.UNAVAILABLE,
            "supported_capabilities": [
                self._supported_record(method_id) for method_id in sorted(requested)
            ],
            "deferred_records": [
                self._deferred_record(asset_id, spec) for spec in _DEFERRED_METHODS
            ],
            "limitations": list(_LIMITATIONS),
            "non_claims": list(_NON_CLAIMS),
        }
        result = self.validate_declaration(declaration)
        if not result.valid:
            raise CapabilityDeclarationError(result.reason)
        self._audit.append_event(
            AuditEventType.CAPABILITY_DECLARATION_EMITTED, declaration
        )
        return declaration

    def emit_deferred_records(self, asset_id: str) -> list[dict[str, Any]]:
        """Persist every required coverage gap, then audit each emitted record.

        Store and audit methods retain their existing commit boundaries. A write
        failure propagates without returning success; earlier committed rows are
        retained, so this API does not claim batch-level atomicity.
        """

        self._validate_asset_id(asset_id)
        records = [self._deferred_record(asset_id, spec) for spec in _DEFERRED_METHODS]
        # Validate the entire batch before any record can enter the store.
        for record in records:
            result = self.validate_deferred_record(record)
            if not result.valid:
                raise CapabilityDeclarationError(result.reason)
        if (
            {record["method_id"] for record in records}
            != {spec[0] for spec in _DEFERRED_METHODS}
            or len({record["record_id"] for record in records}) != len(records)
            or any(record["asset_id"] != asset_id for record in records)
        ):
            raise CapabilityDeclarationError("invalid coverage gap binding")
        for record in records:
            self._store.write_deferred_record(record)
            self._audit.append_event(AuditEventType.DEFERRED_IN_SCOPE_EMITTED, record)
        return records
