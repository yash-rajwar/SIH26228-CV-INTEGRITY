"""Project exception hierarchy for SIH 2026 PS 26228.

Authority: ``docs/TECHNICAL_SPECIFICATION.md`` §3.18.
"""


class AssuranceSystemError(Exception):
    pass


class PipelineError(AssuranceSystemError):
    pass


class SchemaViolationError(AssuranceSystemError):
    pass


class StorageWriteError(AssuranceSystemError):
    pass


class AuditWriteError(AssuranceSystemError):
    pass


class SigningKeyUnavailableError(AssuranceSystemError):
    pass


class WorkerTimeoutError(AssuranceSystemError):
    pass


class WorkerCrashError(AssuranceSystemError):
    pass


class PathContainmentError(AssuranceSystemError):
    pass


class ArtifactUnitAmbiguousError(AssuranceSystemError):
    pass


class ChainCorruptError(AssuranceSystemError):
    pass


class ReferenceHealthError(AssuranceSystemError):
    pass


class ReplayAttemptError(AssuranceSystemError):
    pass


class SequenceGapError(AssuranceSystemError):
    pass


class CapabilityDeclarationError(AssuranceSystemError):
    pass


# Required by TASK-004 and TASK-022. These extend the §3.18 hierarchy without
# changing its inheritance or failure semantics.
class ConfigError(AssuranceSystemError):
    pass


class IngestError(AssuranceSystemError):
    pass
