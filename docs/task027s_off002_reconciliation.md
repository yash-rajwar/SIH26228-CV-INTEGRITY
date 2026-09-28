# TASK-027-S OFF-002 Evidence Reconciliation

Generated: 2026-09-28T23:10:44.8695039+05:30

## Run

Evidence directory:

C:\ProgramData\SIH26228-Off002\evidence\task027s-run-20260928-224909

Result file:

C:\ProgramData\SIH26228-Off002\evidence\task027s-run-20260928-224909\TASK-027-Q-final-result.json

## OFF-002 Acceptance Result

Acceptance window:

2026-09-28T17:19:58.2002931Z through 2026-09-28T17:19:59.5909248Z

Acceptance physical-NIC Tx packets:

0

Acceptance physical-NIC Tx bytes:

0

Assessment exit code:

0

Asset ID:

off-002-valid-coco

### Acceptance determination

The recorded OFF-002 acceptance window contains zero non-loopback physical-NIC
Tx packets and zero Tx bytes, and the assessment command exited with code 0.

Pre-isolation and isolation-transition traffic are recorded separately as
readiness/environment evidence and are not included in the OFF-002 acceptance
window.

## Recovery Result

Original recovery marker status:

FAIL

Adapter status recorded by recovery:

Up

Recovery binding mismatches recorded:

0

Firewall rule removed:

True

PktMon stopped:

True

Recovery errors:

binding:ms_netbios:No matching MSFT_NetAdapterBindingSettingData objects found by CIM query for instances of the ROOT/StandardCimv2/MSFT_NetAdapterBindingSettingData class on the  CIM server: SELECT * FROM MSFT_NetAdapterBindingSettingData  WHERE ((Name LIKE 'Ethernet0 3')) AND ((ComponentID LIKE 'ms[_]netbios')). Verify query parameters and retry.
binding:ms_netbt:No matching MSFT_NetAdapterBindingSettingData objects found by CIM query for instances of the ROOT/StandardCimv2/MSFT_NetAdapterBindingSettingData class on the  CIM server: SELECT * FROM MSFT_NetAdapterBindingSettingData  WHERE ((Name LIKE 'Ethernet0 3')) AND ((ComponentID LIKE 'ms[_]netbt')). Verify query parameters and retry.

## Independent Final-State Verification

Ethernet0 3:

Up

Current binding mismatches against the saved pre-run snapshot:

0

Temporary firewall rule:

ABSENT

Recovery task:

ABSENT

PktMon:

Packet Monitor is not running.

## ms_netbios / ms_netbt Reconciliation

Saved pre-run state:

ms_netbios = True

ms_netbt = True

Current state:

ms_netbios = True

ms_netbt = True

Both bindings therefore match their recorded pre-run state.

## Evidence Interpretation

The raw TASK-027-S result and recovery marker are preserved unchanged.

The runner's overall FAIL status resulted from transient recovery-command
errors for ms_netbios and ms_netbt. The later independent complete binding
comparison reports zero mismatches, and the adapter, firewall, recovery-task,
and PktMon final states are restored.

Therefore this reconciliation does not rewrite the original FAIL evidence.

It records separately that:

1. The OFF-002 acceptance window recorded zero physical-NIC Tx bytes.
2. The assessment command exited successfully.
3. Final host recovery state matches the saved pre-run state.
4. The recovery marker contains transient ms_netbios/ms_netbt query errors.
5. No network rerun was performed.

## Raw Evidence Preservation

No raw evidence file was modified by this reconciliation.

## Scope

This reconciliation does not modify:

- Ethernet0 3
- adapter bindings
- Windows Firewall policy
- PktMon state
- recovery task state
- production code
