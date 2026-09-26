from assurance_system.exceptions import (
    ArtifactUnitAmbiguousError,
    AssuranceSystemError,
    AuditWriteError,
    CapabilityDeclarationError,
    ChainCorruptError,
    ConfigError,
    IngestError,
    PathContainmentError,
    PipelineError,
    ReferenceHealthError,
    ReplayAttemptError,
    SchemaViolationError,
    SequenceGapError,
    SigningKeyUnavailableError,
    StorageWriteError,
    WorkerCrashError,
    WorkerTimeoutError,
)


def test_all_exceptions_importable():
    assert AssuranceSystemError.__name__ == "AssuranceSystemError"


def test_exception_hierarchy():
    subclasses = [
        PipelineError,
        SchemaViolationError,
        StorageWriteError,
        AuditWriteError,
        SigningKeyUnavailableError,
        WorkerTimeoutError,
        WorkerCrashError,
        PathContainmentError,
        ArtifactUnitAmbiguousError,
        ChainCorruptError,
        ReferenceHealthError,
        ReplayAttemptError,
        SequenceGapError,
        CapabilityDeclarationError,
        ConfigError,
        IngestError,
    ]
    for cls in subclasses:
        assert issubclass(cls, AssuranceSystemError), (
            f"{cls.__name__} must inherit from AssuranceSystemError"
        )


def test_audit_write_error_is_distinct():
    assert not issubclass(AuditWriteError, StorageWriteError)
    assert not issubclass(StorageWriteError, AuditWriteError)


def test_exceptions_are_exceptions():
    for cls in [AssuranceSystemError, PipelineError, AuditWriteError]:
        assert isinstance(cls("test"), Exception)
