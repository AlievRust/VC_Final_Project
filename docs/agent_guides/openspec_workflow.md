# OpenSpec Workflow Guide — Practical Orchestrator

Use this guide for new features, behavior/architecture/config/data/deployment changes, or unclear tasks.

## Purpose

OpenSpec prevents spec drift. It should be durable enough to recover intent and decisions, but it should not duplicate the same material across several files or fully pre-author future stages before they become active.

## Change folder

Use:

- `openspec/changes/<number-change-id>/proposal.md`
- `openspec/changes/<number-change-id>/design.md`
- `openspec/changes/<number-change-id>/tasks.md`
- `openspec/changes/<number-change-id>/checkpoints.md` when meaningful gated stages exist

Change id: `NNNN-short-kebab-slug`.

## Artifact ownership

### `proposal.md` — WHY / WHAT

Keep compact:

- problem;
- goal;
- scope / out of scope;
- user-visible behavior;
- top-level risks;
- top-level acceptance.

Do not copy technical design, detailed test matrix, runtime inventory, or rollout commands here.

### `design.md` — HOW / EVIDENCE

This is the durable technical source of truth:

- current and target behavior;
- affected modules/interfaces;
- architecture and failure/security semantics;
- data/API/config/DB/deployment implications;
- pre-change baseline evidence;
- material repository/runtime facts that affect design;
- external contracts/provenance;
- decision register for meaningful trade-offs;
- verification strategy and residual risks.

Prefer concise tables/contracts where they reduce repeated prose.

### `tasks.md` — EXECUTION

Only executable checklist items and their state.

Example:

- [ ] Add limiter admission primitive
- [ ] Update login route ordering
- [ ] Add concurrency tests
- [ ] Update deployment config

Do not restate design contracts, evidence inventories, or checkpoint acceptance prose.

### `checkpoints.md` — STATE / GATES

Only:

- Recovery capsule;
- current checkpoint state/barrier/delegation;
- short acceptance summary;
- baseline/verification/review/user-gate status;
- blockers;
- evidence/decision references;
- skeletal future checkpoints.

Do not duplicate `design.md` evidence or `tasks.md` checklists.

## Progressive elaboration

Fully elaborate only the current `ACTIVE`/`REVIEW` checkpoint.

Future `PENDING` checkpoints should contain only:

- id/name;
- one-line goal;
- dependency;
- known user/production gate;
- references to relevant design/tasks.

Expand the next checkpoint when it becomes active. Do not front-load exact commands, delegation plans, evidence, review notes, rollout steps, or residual risks for stages that have not started.

## Recovery capsule

For complex/checkpointed changes, maintain the short Recovery capsule defined in `orchestration.md` / `checkpoints_template.md`.

After a blocking reviewer verdict or material design decision, update the capsule before large write-back. It should let a compacted/restarted session know which older design is no longer authoritative and what action is next.

## Decision register

Use for non-trivial architectural/security/deployment/data/failure-semantics choices that a later session could plausibly reinterpret.

```text
D-01 <title>
Chosen: <decision>
Alternative: <rejected option>
Reason/evidence: <why>
Revisit if: <condition>
```

Do not register every local coding choice.

## External contracts and provenance

For material official/vendor/upstream facts, preserve in `design.md`:

- source title/owner;
- exact URL/location;
- applicable version/date/range;
- verified finding;
- dependent design/verification constraint.

Do not rely on transient subagent conversation as the only provenance.

## Pre-change baseline

Before implementing behavior-affecting work, run the narrowest useful existing baseline unless unavailable/disproportionately expensive. Record once in `design.md`: command/check, `PASS|FAIL|NOT_RUN|NOT_APPLICABLE`, concise result, pre-existing failures, and residual risk if skipped.

Checkpoint should reference that record.

## When OpenSpec is required

Create/update OpenSpec for:

- feature/user-flow/API changes;
- DB schema/data contract changes;
- config/logging/validation changes;
- deployment/import-export changes;
- security/auth changes;
- meaningful architecture changes.

May be skipped for tiny typo/docs-only changes, investigation without code changes, or behavior-neutral internal refactors.

## Checkpointed changes

Use `checkpoints.md` for meaningful gates involving security/auth, DB permissions/migrations, deployment/rollback, data integrity, external contracts, destructive operations, cross-module refactors, or long multi-stage work.

Use `docs/agent_guides/checkpoints_template.md`.

Task state and checkpoint state are distinct. Only primary moves either.

Before crossing a checkpoint barrier confirm acceptance, required verification/operational evidence, review, user gate, blockers, and OpenSpec consistency.

## Archive completed changes

After all required tasks are `[x]`, required checkpoints are `PASSED`, and verification is recorded, move the full change directory to:

`openspec/changes/archive/YYYY-MM-DD-<change-id>/`

Incomplete/blocked changes stay active. Fix internal links after move; historical command references tied to old commits may remain as historical evidence.
