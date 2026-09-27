# Branch Naming Convention

**Authority:** 11_MVP_IMPLEMENTATION_PLAN_SIH26228.md §13

## Rules

- Branches represent **tasks or workstreams** — not devices, locations, or agents.
- `main` is the stable integration branch. Only receives merges after an integration gate passes.
- All work happens in feature branches.
- Merge via pull request with test evidence.

## Branch Map

| Branch | Tasks | Notes |
|--------|-------|-------|
| `feature/foundation` | TASK-002, TASK-003, TASK-004 | Repository skeleton + types + config |
| `feature/persistence` | TASK-005, TASK-006 | Evidence store + audit chain |
| `feature/worker-base` | TASK-007 | IPC boilerplate |
| `feature/schema` | TASK-008 | Schema validator + JSON schema files |
| `feature/fixtures` | TASK-009 | Full hostile fixture suite — **P0** |
| `feature/c2-data-workers` | TASK-010–013 | All C2 workers |
| `feature/c3-model-workers` | TASK-014–017 | All C3 workers |
| `feature/provenance` | TASK-019 | C4 provenance + signing |
| `feature/reference-manager` | TASK-018 | COMP-REF |
| `feature/capability-declaration` | TASK-020 | COMP-CAP |
| `feature/interpretation` | TASK-021 | C5 rule engine |
| `feature/orchestrator` | TASK-022 | Supervisor pipeline controller |
| `feature/cli` | TASK-023 | CLI entry points |
| `feature/exporter` | TASK-025 | Evidence bundle ZIP export |
| `feature/dashboard` | TASK-024 | Read-only dashboard (Antigravity primary) |
| `feature/integration-tests` | TASK-026 | End-to-end vertical slice + security battery |
| `feature/offline-validation` | TASK-027 | Wheelhouse + zero-egress tests (after PRE-01) |

## Prohibited branch names

Do not use: `office`, `home`, `codex-local`, `antigravity-local`, `my-machine`, or any device/location-based name.

## Merge order (critical path)

```
foundation → persistence → worker-base → schema
                                       ↓
fixtures → c2-data-workers → c3-model-workers
                                       ↓
reference-manager + capability-declaration + provenance → interpretation
                                       ↓
orchestrator → cli + exporter + dashboard
                                       ↓
integration-tests → offline-validation
```
