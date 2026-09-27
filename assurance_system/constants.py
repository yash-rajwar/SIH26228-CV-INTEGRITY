"""
Project-wide state vocabulary constants.
Authority: §10 §3.2 (10_TECHNICAL_SPECIFICATION_SIH26228.md)
           §09 §16.1 state machine (09_ARCHITECTURE_SPECIFICATION_SIH26228.md)

STUB — not yet implemented.
Implementation task: TASK-003.

IMPORTANT: The strings CLEAN, SAFE, HEALTHY must NOT appear as positive
assurance states anywhere in this file or any other project file.
Grep enforcement: grep -r 'CLEAN\|SAFE\|HEALTHY' assurance_system/ → 0 positive state matches.
"""


class AssessmentStatus:
    APPLICABLE                    = "APPLICABLE"
    COMPLETED                     = "COMPLETED"
    ASSESSMENT_ERROR              = "ASSESSMENT_ERROR"
    UNAVAILABLE                   = "UNAVAILABLE"
    UNSUPPORTED                   = "UNSUPPORTED"
    DEFERRED_IN_SCOPE             = "DEFERRED_IN_SCOPE"
    ARTIFACT_UNIT_AMBIGUOUS       = "ARTIFACT_UNIT_AMBIGUOUS"
    SCHEMA_VIOLATION              = "SCHEMA_VIOLATION"
    LOAD_BLOCKED                  = "LOAD_BLOCKED"
    LOAD_SUCCESS                  = "LOAD_SUCCESS"
    LOAD_ERROR                    = "LOAD_ERROR"
    ONNX_PATH_CONTAINMENT_VIOLATION = "ONNX_PATH_CONTAINMENT_VIOLATION"
    REFERENCE_UNAVAILABLE         = "REFERENCE_UNAVAILABLE"
    SIGNING_UNAVAILABLE           = "SIGNING_UNAVAILABLE"
    NO_ANOMALY_DETECTED           = "NO_ANOMALY_DETECTED"
    ANOMALY_DETECTED              = "ANOMALY_DETECTED"


class AnalystDisposition:
    ACCEPT                        = "ACCEPT"
    ACCEPT_WITH_CONTEXT           = "ACCEPT_WITH_CONTEXT"
    ESCALATE                      = "ESCALATE"
    CONTAIN_HOLD                  = "CONTAIN_HOLD"
    OVERRIDE                      = "OVERRIDE"
    UNAVAILABLE_NO_DECISION       = "UNAVAILABLE_NO_DECISION"


class IdentityQuality:
    TRUSTED                       = "TRUSTED"
    UNTRUSTED                     = "UNTRUSTED"


class ReferenceHealth:
    HEALTH_VERIFIED               = "HEALTH_VERIFIED"
    HEALTH_UNVERIFIED             = "HEALTH_UNVERIFIED"
    CONTAMINATION_SUSPECTED       = "CONTAMINATION_SUSPECTED"
    STALE_SUSPECTED               = "STALE_SUSPECTED"
    UNAVAILABLE                   = "UNAVAILABLE"


# Non-claim field name constants
NON_CLAIM_T05D                    = "does_not_detect_clean_label_poisoning_T05d"
NON_CLAIM_PF002                   = "does_not_prove_model_executed_assessed_inferences_PF002"
NON_CLAIM_GLOBAL_BACKDOOR         = "does_not_claim_global_backdoor_absence"
NON_CLAIM_HASH_MATCH_SAFE         = "hash_match_does_not_imply_safe_or_semantically_equivalent"
NON_CLAIM_ANOMALY_PROVEN_ATTACK   = "anomaly_detected_does_not_prove_malicious_attack"

# Trusted clock availability flag
TRUSTED_CLOCK_UNAVAILABLE         = "TRUSTED_CLOCK_UNAVAILABLE"
