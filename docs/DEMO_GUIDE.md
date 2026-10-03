# SIH26228 synthetic MVP demo

## Preconditions

Run from the repository root on the frozen, provisioned Windows AMD64 target:
Windows 10 Pro owner record, build 22631, CPython 3.13.12, 16 GB RAM. Do not
replace that owner decision with Python's Windows-11 branding. Use the approved
adjacent `.venv-torch-test` environment with the already staged dependencies.
The configured supervisor evidence-store and worker temporary directories must
already exist, with the accepted Windows restricted-worker deployment and
supervisor privileges. The script does not install, provision ACLs, read keys,
alter networking or reset stores. Close other assessment writers during demo
acceptance so read-only snapshot comparisons are meaningful.

The real CLI uses `config/system_config.yaml` through ConfigLoader. On this
validated deployment `/var/assurance/evidence-store/evidence.db` resolves to
`C:\var\assurance\evidence-store\evidence.db`, and worker temporaries to
`C:\tmp\assurance-workers`. Each demo appends synthetic records to that
configured store. It does not relocate it or isolate it with an invented
configuration override. Working files, logs, reports and the exported ZIP stay
under ignored `build/demo/<unique-run-id>/`; never commit those artifacts.

## One-command automated acceptance

```powershell
& 'C:\Users\master\Desktop\SIH26228-CV-INTEGRITY.venv-torch-test\Scripts\python.exe' scripts/demo.py
```

The script uses its own `sys.executable` for the fixture generator and every
real CLI subprocess. It creates unique asset/run IDs, generates the approved
benign COCO fixture at seed **26228**, and runs two synthetic assessments.
Scenario A completes COCO geometry and statistics evidence. Scenario B declares
a contained but nonexistent PyTorch model; no hostile model is executed.
It reads findings, complete coverage and audit history, exports the unavailable
asset, validates all six ZIP documents, then starts and probes the actual
loopback dashboard. Its default cleanup reaps that child. Exit 0 means every
mandatory demo check passed; failures exit nonzero and retain diagnostics.
Infrastructure watchdogs in the demo are named constants, not new worker
resource/assessment limits; workers continue using the configuration contract.

No user input or network service is required. Only `127.0.0.1` HTTP is used,
directly without proxy discovery. This run does **not** disconnect the network
or re-execute OFF-002: accepted TASK-027 evidence remains the separate monitored
zero-egress proof for the frozen host. The demo is not a new packet-capture claim.

## Presentation mode

```powershell
& 'C:\Users\master\Desktop\SIH26228-CV-INTEGRITY.venv-torch-test\Scripts\python.exe' scripts/demo.py --serve
```

After the same checks, the script prints `Dashboard: http://127.0.0.1:<port>`.
Open that URL manually in a local browser. It does not launch a browser or
require browser automation. Use the printed `demo-coco-...` and
`demo-unavailable-...` IDs from the run's `result.json`/submission files for
filtering. Historical synthetic observations remain in the store; refresh
does not delete, rewrite or conceal them. Script/API acceptance is automated;
prior visual QA remains static/CSS review, not a browser-rendered inspection.

## Suggested 3–5 minute walkthrough

1. **Overview / Observed Pipeline State (30 seconds):** point out evidence counts
   and recorded states. The stepper is persisted observation, not live telemetry
   or assurance confidence. Missing ingestion telemetry is UNAVAILABLE.
2. **Completed COCO (45 seconds):** filter by this run's COCO asset. M01 checks
   every generated annotation; zero fixture geometry violations is a bounded
   structural result. C2C reports statistics, not authenticated identity.
3. **Explicit UNAVAILABLE (45 seconds):** select the missing-model asset.
   Finding detection is UNAVAILABLE with UNAVAILABLE_NO_DECISION; upstream
   ambiguity/error is retained. It is not an absence-of-anomalies conclusion.
4. **Findings / Evidence Explorer (45 seconds):** inspect raw signals, worker
   methods, limitations, non-claims and coverage_gap_clean_label. Matching bytes
   are identity only; independent detector evidence is not established by default.
5. **Coverage & Deferred (30 seconds):** show every stored method and its reason.
   DEFERRED_IN_SCOPE, REFERENCE_UNAVAILABLE and COMPLETENESS_UNAVAILABLE remain
   distinct. T05d is a permanent non-claim, not promised future detection.
6. **Audit Timeline (30 seconds):** show full ordered history and chain status.
   Intact local links do not establish external tail completeness. Corruption
   visibility is proved in isolated tests, never by damaging this store. Where
   payload identifiers were not persisted, record-to-audit correlation is unavailable.
7. **Provenance / Export (30 seconds):** display SIGNING_UNAVAILABLE where stored.
   A missing model cannot produce a completed C3B digest or C4 binding;
   C4_BINDING_UNAVAILABLE and an empty provenance array are truthful. The UI's
   signing notice is not a fabricated provenance record. Existing provenance
   exported from the store is historical context, not automatically this asset's
   binding. Open the ZIP's six JSON documents and show preserved UNAVAILABLE,
   synthetic labels, reasons and non-claims.

## What not to claim

Do not claim malware detection, model safety, every-attack coverage, complete
integrity assurance, behavioral equivalence, causal execution proof, verified
reference health when unavailable, or signatures when signing is unavailable.
Anomaly is not proof of an attack. Preserve PF-002: digest match is not causal
execution proof. Successful restricted loading does not establish backdoor
absence. Unavailable and deferred coverage never become positive assurance.
The unsigned provenance shell is the approved MVP behavior; PRE-08 remains
PARTIAL. Historical HOST-CAP-003 procedural re-entry is still pending despite
actual ONNX runtime capability PASS. No post-MVP implementation is implied.

## Stop and inspect outputs

Press **Ctrl+C** in the presentation terminal. The script terminates/reaps the
dashboard child in `finally`, retaining all records and working files. Default
automated mode stops it without interaction. Do not close the terminal forcibly
if you want normal cleanup and the final marker.

The export is `build/demo/<run-id>/unavailable-evidence.zip`, containing:
`manifest.json`, `findings.json`, `evidence_records.json`, `provenance.json`,
`audit_trail.json`, and `capabilities.json`. `result.json` records verification,
actual asset IDs and SHA-256 hashes of working artifacts; per-command stdout,
stderr and exit-code records are beside it. Unique metadata changes between
runs, while the seed-pinned COCO fixture content stays deterministic. A failure
does not authorize changing assessment semantics, retrying OFF-002, or removing
earlier evidence.
