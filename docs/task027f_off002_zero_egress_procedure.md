# OFF-002 Purpose

This document defines the evidence procedure required to evaluate OFF-002. It
does not execute OFF-002 and does not assert that the system operated with zero
egress.

OFF-002 is the target-host requirement that a **full pipeline run monitored for
its entire execution window shows exactly zero bytes leaving the host**. This
is stronger than local-only package resolution, a successful `--no-index`
installation, or the absence of a DNS lookup.

# Authoritative Contract

The authoritative requirements are:

- `10_TECHNICAL_SPECIFICATION_SIH26228.md` section 12.2: monitor network
  traffic during imports and observe zero bytes egress.
- `10_TECHNICAL_SPECIFICATION_SIH26228.md` section 17.4: OFF-002 is a full
  pipeline run under a network monitor with zero bytes egress.
- `11_MVP_IMPLEMENTATION_PLAN_SIH26228.md`, TASK-027: the full pipeline run
  must show zero bytes egress under network monitoring.
- `09_ARCHITECTURE_SPECIFICATION_SIH26228.md` section 19.4: target-host
  network isolation is confirmed by monitoring.
- `tests/offline/test_offline_validation.py`: the executable contract remains
  a skipped placeholder and is not evidence that OFF-002 passed.

The following conditions are distinct:

1. No package download occurred.
2. No network request was attempted.
3. No traffic left the host through any non-loopback interface.
4. The validation environment was isolated from external networks.

OFF-002 requires condition 3 to be observed during the complete pipeline
window. The architecture additionally requires the target-host isolation
boundary to be confirmed by that monitoring. Conditions 1 and 2 alone do not
satisfy the contract.

Qualifying evidence is a lossless, reviewable NIC-layer capture and counter
record that covers every active non-loopback interface for the OFF-002
acceptance window: immediately before `cli.py assess` starts until that command
and its required pipeline cleanup have completed. Isolation-transition traffic
is retained in a separate readiness capture and is not OFF-002 acceptance
evidence. It must be accompanied by the command
transcript, UTC timestamps, interface/address/route/DNS/proxy/firewall
inventories, converted packet output, and SHA-256 hashes.

The following do not qualify by themselves: `pip --no-index`, local wheel
hashes, a successful offline install or import, no observed DNS, an
application log, packet counters without a capture, a capture begun after
preparation, a TCP-only or IPv4-only filter, or the mere availability of
PktMon.

# Target Environment

The inspected target is Windows 10 Pro build 22631, AMD64, with repository-
local CPython 3.13.12. The inspection on 2026-09-28 found:

| Item | Observed state |
|---|---|
| Active NIC | `Ethernet0 3`, interface index 15, Intel 82574L, up |
| Host IPv4 | `192.168.10.212/24` |
| IPv4 default route | `0.0.0.0/0` via `192.168.10.1` |
| IPv6 | Loopback only; no global address or default route |
| Connection profile | Public; IPv4 reports Internet connectivity |
| DNS | `192.168.10.1`, `8.8.8.8`; legacy loopback IPv6 entries also reported |
| WinHTTP proxy | Direct access, no proxy |
| User proxy | Disabled; no PAC URL |
| Proxy environment variables | None |
| Windows Firewall | Domain, Private, and Public profiles enabled; effective policy `BlockInbound,AllowOutbound`; allowed/dropped connection logging enabled |

No network, firewall, proxy, DNS, or security configuration was changed.

# Network Boundary

The evidence boundary is every active non-loopback network adapter reported by
both `Get-NetAdapter -IncludeHidden` and `pktmon list --all --include-hidden`.
Every transmitted frame at that boundary counts as egress, including IPv4,
IPv6, ARP, multicast, broadcast, DNS, proxy traffic, and same-subnet traffic.
There are no exemptions for Windows services, remote administration, security
software, or traffic believed to be unrelated to the validation.

Loopback-only traffic (`127.0.0.0/8` and `::1`) does not leave the host and is
reported separately. A same-subnet destination is not loopback and therefore
counts as egress. Destination classification must use the captured source and
destination addresses plus the pre-capture interface and route inventory; DNS
names are not used to decide whether a packet left the host.

The current session is connected through the target adapter. An autonomous
SYSTEM runner must arm independent recovery, record transition traffic,
establish the approved firewall/binding isolation, verify the isolated state,
and only then start the acceptance capture. Remote-administration and other
traffic observed before that acceptance start is readiness/environment traffic,
not OFF-002 evidence. Firewall and endpoint-security controls must remain
enabled except for the narrowly scoped temporary outbound isolation rule.

# PktMon Capability

`pktmon.exe` is available. Its help exposes NIC/all-component capture,
unfiltered IPv4/IPv6/ARP packet collection, counters, ETL output, and
conversion to text and PCAPNG. `pktmon list` identifies the active physical
NIC as component 1. The ETL header from the dry run reports provider version
22631; the tool does not expose a separate semantic version in its help.

PktMon can technically observe transmitted frames on the relevant NIC and can
produce independently inspectable ETL, text, and PCAPNG files. With no packet
filters, NIC capture covers IPv4, IPv6, ARP, and other layer-2 traffic. The
current host has no routable IPv6 path, but IPv6 remains inside the capture
boundary and must not be filtered out in a future run.

PktMon's documented filters are MAC, VLAN, ethertype, transport protocol, IP,
port, heartbeat, and encapsulation. They do not include a PID/process filter.
The dry-run text records direction, component, frame size, addresses, and
ports, but no reliable process identity. PktMon therefore cannot attribute
concurrent background traffic to the validation process. It is sufficient for
a strict host-wide zero-transmit assertion only when the execution boundary is
isolated or quiescent.

# Capture Procedure

The commands below define the candidate capture mechanism. They are to be run
only under a separate OFF-002 execution authorization and from an elevated
PowerShell session. `$EvidenceRoot` must point to a secured directory outside
the Git worktree. `$RepoRoot` is the repository root and `$Python` is the
approved repository-local interpreter.

Before capture, the operator must freeze the exact full-pipeline command list
in `validation-commands.txt`, record its SHA-256, and confirm that no command
uses a package index or network URL. For OFF-002 the frozen command is exactly
`python cli.py assess --submission tests/fixtures/valid_coco_submission.json`.
OFF-001, OFF-003, and OFF-004 are separate tests and are not executed inside
the OFF-002 acceptance window.

```powershell
$ErrorActionPreference = 'Stop'
$RepoRoot = (Get-Location).Path
$Python = (Resolve-Path '.\.venv-torch-test\Scripts\python.exe').Path
$EvidenceRoot = '<approved-secured-evidence-directory>'
$TransitionEtl = Join-Path $EvidenceRoot 'transition-pktmon.etl'
$AcceptanceEtl = Join-Path $EvidenceRoot 'off002-acceptance-pktmon.etl'

if ((Test-Path $EvidenceRoot) -and (Get-ChildItem $EvidenceRoot -Force)) {
    throw 'Evidence directory must be new or empty.'
}
New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
[DateTime]::UtcNow.ToString('o') | Set-Content (Join-Path $EvidenceRoot 'capture-start-requested-utc.txt')
Get-ComputerInfo | Out-File (Join-Path $EvidenceRoot 'computer-info.txt')
Get-NetAdapter -IncludeHidden | Format-List * | Out-File (Join-Path $EvidenceRoot 'adapters.txt')
Get-NetIPAddress | Format-List * | Out-File (Join-Path $EvidenceRoot 'addresses.txt')
Get-NetRoute -AddressFamily IPv4,IPv6 | Format-List * | Out-File (Join-Path $EvidenceRoot 'routes.txt')
Get-DnsClientServerAddress | Format-List * | Out-File (Join-Path $EvidenceRoot 'dns.txt')
Get-NetConnectionProfile | Format-List * | Out-File (Join-Path $EvidenceRoot 'profiles.txt')
Get-NetFirewallProfile | Format-List * | Out-File (Join-Path $EvidenceRoot 'firewall.txt')
netsh winhttp show proxy | Out-File (Join-Path $EvidenceRoot 'winhttp-proxy.txt')
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' |
    Select-Object ProxyEnable,ProxyServer,AutoConfigURL |
    Format-List | Out-File (Join-Path $EvidenceRoot 'user-proxy.txt')
Get-ChildItem Env: | Where-Object Name -Match '^(HTTP|HTTPS|ALL|NO)_PROXY$' |
    Format-List | Out-File (Join-Path $EvidenceRoot 'proxy-environment.txt')
pktmon list --all --include-hidden --json | Out-File (Join-Path $EvidenceRoot 'pktmon-components.json')

if ((pktmon status | Out-String) -notmatch 'not running') {
    throw 'PktMon already active; preserve that evidence and stop for review.'
}
Arm-And-Verify-SystemRecovery
Snapshot-AllAdapterBindings
Create-DisabledTemporaryFirewallRule

# Transition/readiness capture. Preserve it, but never use it to decide OFF-002.
pktmon reset
pktmon start --capture --comp nics --type all --pkt-size 128 `
    --file-name $TransitionEtl --file-size 128 --log-mode multi-file
Enable-TemporaryIsolation
Wait-For-IsolationStability
Assert-AdapterUpRuleActiveAndBindingsDisabled
pktmon stop
Convert-And-HashTransitionEvidence

# The OFF-002 acceptance boundary starts only after isolation is stable.
pktmon reset
pktmon start --capture --comp nics --type all --pkt-size 128 `
    --file-name $AcceptanceEtl --file-size 512 --log-mode multi-file
$AcceptanceStart = Get-Date

try {
    & $Python cli.py assess --submission tests/fixtures/valid_coco_submission.json `
        1> (Join-Path $EvidenceRoot 'off002-assess.stdout.txt') `
        2> (Join-Path $EvidenceRoot 'off002-assess.stderr.txt')
    $AssessExit = $LASTEXITCODE
    # Returning from assess is the pipeline-cleanup completion point.
    $AcceptanceEnd = Get-Date
}
finally {
    pktmon counters --json | Out-File (Join-Path $EvidenceRoot 'acceptance-counters.json')
    pktmon stop | Out-File (Join-Path $EvidenceRoot 'acceptance-stop.txt')
}

Convert-And-HashAcceptanceEvidence
Measure-OnlyTrafficBetween $AcceptanceStart $AcceptanceEnd
Restore-ExactPreRunState

$Etls = Get-ChildItem $EvidenceRoot -Filter 'off002-pktmon*.etl' | Sort-Object Name
if (-not $Etls) { throw 'PktMon produced no ETL evidence.' }
foreach ($File in $Etls) {
    $Stem = [System.IO.Path]::GetFileNameWithoutExtension($File.Name)
    pktmon etl2txt $File.FullName --out (Join-Path $EvidenceRoot ($Stem + '.txt')) --timestamp-only --brief
    pktmon etl2pcap $File.FullName --out (Join-Path $EvidenceRoot ($Stem + '.pcapng'))
}
Get-FileHash -Algorithm SHA256 (Join-Path $EvidenceRoot '*') |
    Sort-Object Path | Format-Table -AutoSize |
    Out-File (Join-Path $EvidenceRoot 'sha256.txt')
```

The command transcript must record exit codes and UTC start/end markers. A
failed command does not permit a zero-egress PASS; it produces a blocked or
failed validation package for review. The monitor must always be stopped in
the `finally` block, and its “events lost”/conversion statistics must be
retained. Multi-file logging is mandatory so a long run cannot silently
overwrite early traffic; every emitted ETL segment must be converted, hashed,
and reviewed.

# Filtering Procedure

No packet filter is permitted for acceptance capture. The procedure executes
`pktmon filter remove`, resets counters, and captures `--comp nics --type all`.
This avoids excluding IPv6, UDP, ICMP, ARP, multicast, proxy, encapsulated, or
unexpected traffic. A 128-byte snapshot retains link/network/transport headers
and endpoint data while limiting incidental payload collection; PktMon's
`OriginalSize` and counters retain the actual frame byte count.

Post-capture classification is allowed only to apply the contract boundary and
separate loopback. Traffic outside the recorded acceptance timestamps and
loopback-only traffic are excluded. Every `Direction Tx` record inside the
acceptance interval on a monitored non-loopback NIC counts
toward egress, regardless of destination, owner, protocol, port, or apparent
purpose.

# Zero-Egress Acceptance Criteria

OFF-002 may pass only if all of the following are true:

1. The execution was separately authorized and used the frozen command
   manifest on the approved target host.
2. Isolation was established and verified before the acceptance capture.
3. The acceptance capture was active immediately before `cli.py assess` and
   ended only after that command and its required cleanup completed.
4. Every active non-loopback NIC was included, with no packet filters.
5. The ETL reports zero lost events and converts successfully to text and
   PCAPNG.
6. For every monitored NIC, the acceptance interval reports `Tx Packets = 0`
   and `Tx Bytes = 0` after loopback exclusion.
7. The converted text and PCAPNG contain no transmitted frame during the
   acceptance interval at the
   non-loopback boundary. Any ARP, DNS, same-subnet, broadcast, multicast,
   IPv4, or IPv6 transmit is a nonzero-egress result.
8. The frozen `cli.py assess` command completes successfully and its transcript
   is present.
9. Environment, command, capture, conversion, decision, and SHA-256 evidence
   is complete and independently reviewable.
10. There is no unexplained acceptance-window capture gap, counter reset,
    logging rollover, or security-control change.

Traffic in the separately timestamped isolation-transition capture is
readiness/environment evidence only. It is not added to the OFF-002 acceptance
total and cannot by itself produce an OFF-002 failure.

Any non-loopback transmitted packet in the acceptance interval produces
**FAIL**, not a discretionary ignore.
Missing, lossy, late, truncated, inconsistent, or unauditable evidence
produces **BLOCKED**, not PASS.

# Background Traffic Handling

Background traffic inside the acceptance window is not subtracted. PktMon does
not provide reliable process attribution, so every non-loopback physical-NIC
transmission in that window fails OFF-002 regardless of apparent owner.

RDP, HTTPS, LLDP, or other traffic observed before isolation is complete is
recorded as transition/readiness evidence. It does not fail OFF-002. The
autonomous runner must prevent that traffic from continuing into the acceptance
window through the approved adapter-scoped firewall and binding isolation.

# DNS/Proxy Handling

DNS is captured, not ignored. A DNS request is egress even when it fails and
even when no package download follows. Absence of DNS does not prove absence
of direct-IP, proxy, UDP, ICMP, IPv6, or other traffic.

The current host has no configured WinHTTP, user, PAC, or environment proxy,
but each authorized run must capture those settings before monitoring starts.
Any proxy setting change during the window blocks acceptance. Proxy traffic is
ordinary transmitted traffic and counts toward the zero-byte total.

# Evidence Artifacts

The final evidence package must contain:

1. Raw PktMon ETL capture.
2. Converted text and PCAPNG output.
3. PktMon counters, start/stop output, component inventory, and conversion
   statistics including lost-event/drop counts.
4. Host, adapter, address, route, connection-profile, DNS, proxy, and firewall
   inventories.
5. Frozen validation command manifest and its SHA-256.
6. Complete command transcript with exit codes and UTC timestamps.
7. Pipeline output and environment-cleanup evidence.
8. A machine-generated classification summary enumerating every transmitted
   record and byte count inside the acceptance interval, with loopback reported
   separately; zero non-loopback rows is required for PASS.
9. SHA-256 hashes for every evidence file, calculated after capture and
   conversion.
10. A signed-off `PASS`, `FAIL`, or `BLOCKED` decision that cites the exact
    acceptance criteria above.

Raw captures may contain network metadata and must remain in an access-
controlled evidence location outside Git. They must not be committed without
separate repository-policy approval.

# Reproducibility

Another authorized operator can reproduce the mechanism using the PowerShell
sequence above, the repository-local interpreter, the committed wheelhouse
verifier, and the committed vertical-slice test. The operator must not begin
until the deployment owner provides the approved isolated/local-console
boundary and the final task authorization freezes the command manifest.

The evidence is mechanically reviewable: PktMon counters provide the total,
the text/PCAPNG files expose every captured frame, and hashes bind all files.
No “watch the screen” decision is part of the acceptance rule.

# False Positive Analysis

A false FAIL can result if transition/readiness traffic is incorrectly counted
inside the OFF-002 acceptance interval. The separate transition capture and
recorded acceptance start/end timestamps prevent that error. Windows services,
RDP, security software, DNS, ARP, DHCP, multicast, another session, or any
unrelated application transmitting after acceptance starts still cause a valid
OFF-002 failure; those packets are not subtracted.

Loopback traffic can also be mistaken for egress if captures from non-NIC
components are mixed into the decision. Capturing NIC components only and
retaining the adapter/component inventory prevents that mistake without
excluding any packet capable of leaving the host.

# False Negative Analysis

A false PASS could result from starting late, stopping early, monitoring the
wrong adapter, filtering by protocol/address/port, ignoring IPv6 or
same-subnet traffic, omitted multi-file ETL segments, capture loss, counter resets, treating
`--no-index` as network evidence, deleting unexpected records, or classifying
background traffic away. The procedure mitigates these risks with pre-start
inventory, all-NIC/no-filter capture, a `finally` stop, loss checks, strict
zero-Tx counters, independent text/PCAPNG review, and fail-closed handling of
any evidence gap.

PktMon's lack of process attribution remains a limitation. It does not cause a
false PASS under the strict host-wide zero-transmit rule, but it prevents a
defensible application-specific decision on the currently connected host.

# Dry-Run Result

A bounded procedure dry run was performed on 2026-09-28. It was not an
OFF-002 run and deliberately generated two harmless ICMP events: one to the
local-subnet gateway and one to remote IPv4 address `1.1.1.1`.

- Capture started and stopped successfully on the physical NIC with no
  filters.
- The counter snapshot recorded 44 transmitted packets / 12,755 bytes and 60
  received packets / 8,148 bytes.
- PktMon reported no lost ETL events; ETL conversion produced 106 packet
  appearances with zero reported packet drops.
- Text and PCAPNG conversions succeeded.
- The converted text contained both controlled packets and distinguished
  their endpoints/directions.
- It also contained continuous unrelated RDP and HTTPS transmissions to
  same-subnet and public destinations, without process identifiers.
- UTC transcript markers correlated with local-time ETL records.

The four raw dry-run files remain outside the repository in a temporary,
access-controlled operator location under
`%LOCALAPPDATA%\Temp\sih26228-task027f-f90c45835efc4e86b220f72e3a68c43a`.
They are procedure-capability evidence only and must not be reused as OFF-002
evidence.

| Dry-run artifact | SHA-256 |
|---|---|
| `pktmon-dry-run.etl` | `fd04a432e23a2499697e08331731058344b6a2bee916795afba369001d8eb938` |
| `pktmon-dry-run.txt` | `b11a2d10d3a153b49af92a64c9cd08d74c428d936f74eecc4e9e26285b50b442` |
| `pktmon-dry-run.pcapng` | `d1cc1283abe54ffd26dff00420573746e424f8a77977694c2458f75f7e62dc8f` |
| `dry-run-transcript.txt` | `dda4d0248a94f3ca86b98e063071891ef3a8c1fa80fddb072a00e54b6d7547ac` |

## TASK-027-S contract-alignment dry run

The contract-aligned SYSTEM runner completed a non-isolating dry run on
2026-09-28. It changed no adapter binding, created no firewall rule, started no
PktMon capture, and did not execute OFF-002. It confirmed the acceptance start
and end definitions, the five approved binding changes, the exact recovery
snapshot, and the frozen `cli.py assess` command. The dry-run evidence is held
outside Git under
`C:\ProgramData\SIH26228-Off002\evidence\task027q-dry-run-20260928-224314`.

The updated recovery task was also demand-run against the unchanged state. It
returned success, changed zero bindings, confirmed the adapter `Up`, confirmed
the temporary rule absent, and confirmed PktMon stopped.

# Limitations

- PktMon does not provide the process attribution required to separate
  validation traffic from concurrent background traffic.
- The connected session emits remote-administration traffic before isolation.
  The autonomous runner must disconnect that session through the approved
  controls before starting the acceptance window.
- The host has no active external IPv6 route. The unfiltered capture includes
  IPv6 if present, but the dry run did not generate an external IPv6 probe.
- PktMon availability and successful conversion do not prove isolation.
- The final OFF-002 run requires separate execution authorization and evidence
  review; the command and acceptance boundary are frozen by this procedure.

# Final Readiness Decision

**NOT READY**

PktMon is technically capable of producing full-NIC, IPv4/IPv6-inclusive,
auditable packet evidence, and the capture/conversion mechanism works.
The contract-aligned autonomous runner has not yet executed an OFF-002
acceptance window. The earlier TASK-027-R observation of 118 pre-isolation Tx
packets is classified as readiness/environment traffic and is not OFF-002
acceptance evidence. OFF-002 therefore remains `BLOCKED / NOT EXECUTED`; no
zero-egress or offline capability claim is made until an authorized acceptance
run completes and its acceptance-only evidence is reviewed.
