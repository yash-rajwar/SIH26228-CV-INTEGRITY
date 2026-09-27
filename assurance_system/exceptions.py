"""
Project exception hierarchy.
Authority: §10 §3.18 (10_TECHNICAL_SPECIFICATION_SIH26228.md)

STUB — not yet implemented.
Implementation task: TASK-003.
"""

# --- Base ---

class AssuranceSystemError(Exception):
    """Base class for all project exceptions."""


# --- Component-level ---

class ConfigError(AssuranceSystemError):
    """Configuration loading or validation failure."""

class IngestError(AssuranceSystemError):
    """Manifest or asset ingestion failure."""

class WorkerError(AssuranceSystemError):
    """Worker subprocess failure (generic)."""

class WorkerTimeoutError(WorkerError):
    """Worker exceeded resource_limits.timeout_seconds."""

class WorkerCrashError(WorkerError):
    """Worker exited with non-zero status."""

class SchemaViolationError(AssuranceSystemError):
    """Evidence record failed schema validation — record must NOT be persisted."""

class AuditWriteError(AssuranceSystemError):
    """Audit chain write failure — MUST NOT be silently swallowed (fail-closed)."""

class PipelineError(AssuranceSystemError):
    """Unrecoverable supervisor pipeline error."""

class SigningError(AssuranceSystemError):
    """Provenance signing failure (SIGNING_UNAVAILABLE state emitted upstream)."""

class EvidenceStoreError(AssuranceSystemError):
    """Evidence store read/write failure."""

class ReferenceManagerError(AssuranceSystemError):
    """Reference health state machine error."""
