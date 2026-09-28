# Execution Checkpoints — Practical Template

Copy this file to `openspec/changes/<change-id>/checkpoints.md` for checkpointed work.

Change: `<change-id>`

## Recovery capsule

Keep this section concise and update it before large write-backs after a blocking review or material decision.

- Current checkpoint: `CP-01`
- State: `PENDING`
- Last accepted design/decision refs: `None`
- Unresolved blocking findings: `None`
- Decisions pending write-back: `None`
- Next action: `<next action>`
- Blockers: `None`
- Independent review: `PENDING | NOT_REQUIRED`
- User gate: `PENDING | NOT_REQUIRED`

---

## State rules

Allowed checkpoint states:

- `PENDING`
- `ACTIVE`
- `REVIEW`
- `BLOCKED`
- `PASSED`

Only primary changes task/checkpoint state. Normal transitions:

- `PENDING → ACTIVE`
- `ACTIVE → REVIEW`
- `REVIEW → PASSED`
- `REVIEW → ACTIVE`
- `ACTIVE/REVIEW → BLOCKED`
- `BLOCKED → ACTIVE`

Task completion, reviewer `PASS`, and user approval are separate inputs; none alone implies checkpoint acceptance.

Only the current `ACTIVE`/`REVIEW` checkpoint is fully elaborated. Future checkpoints remain skeletal until activation.

---

## CP-01 — <current checkpoint name>

State: `PENDING`

### Goal

<What this stage establishes.>

### Entry / barrier

- Entry: <required prior state/evidence>.
- Barrier: <delegated evidence or user/technical fact required before dependent work>.

### Delegation

Decision: `USED | SKIPPED`

Reason: <one short reason>.

Lanes:
- `<role>` — <bounded task>.

### Acceptance

- <observable criterion>.
- <observable criterion>.

### Baseline

State: `PASS | FAIL | NOT_RUN | NOT_APPLICABLE`

Evidence ref: `design.md §<section>` / <short inline result if tiny>.

### Repository verification

- `<command/check>` — `PENDING | PASS | FAIL | NOT_RUN`

### Operational evidence

State: `NOT_REQUIRED | PENDING | PASS | BLOCKED`

Evidence ref: `design.md §<section>` / <short inline result if tiny>.

Known unknowns/blockers:
- None / <item>.

### Independent review

Mode: `FULL | DELTA | CLOSURE | NOT_REQUIRED`

State: `PENDING | PASS | PASS_WITH_NOTES | FAIL | SELF-REVIEW_FALLBACK`

Blocking findings:
- None / `<finding-id>: <short description>`.

Review evidence/ref:
- <short reference; do not paste the full review>.

### User gate

State: `PENDING | APPROVED | NOT_REQUIRED`

Required decision:
- None / <decision>.

### Decision

`PENDING | PASSED | BLOCKED`

Reason/evidence refs:
- <references to `design.md`, tasks, tests, or reviewer findings>.

---

## Future checkpoints

Do not expand these until each checkpoint becomes `ACTIVE`.

| CP | State | Goal | Dependency / gate | References |
|---|---|---|---|---|
| CP-02 | `PENDING` | <one-line goal> | CP-01 `PASSED` | `design.md §...`, `tasks.md ...` |
| CP-03 | `PENDING` | <one-line goal> | CP-02 `PASSED` | `design.md §...`, `tasks.md ...` |
| CP-04 | `PENDING` | <one-line goal> | CP-03 `PASSED`; <user/production gate if known> | `design.md §...` |

Add/remove rows to match the actual change. Do not pre-populate future delegation plans, exact commands, evidence inventories, reviewer notes, residual risks, or rollout procedures.
