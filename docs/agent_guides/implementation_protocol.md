# Implementation Protocol Guide

Use this guide for multi-step implementation tasks.

## Ownership

The primary orchestrator owns the task lifecycle in `tasks.md`.

The orchestrator may implement a task directly or delegate a bounded implementation to `worker`. A worker changes code and returns evidence, but does not mark the OpenSpec task complete.

## Before editing

The orchestrator confirms:

- current task from `tasks.md`;
- expected behavior;
- what must remain unchanged;
- allowed write scope;
- likely files to touch;
- success criteria;
- verification commands;
- whether the task depends on pending scout/researcher results.

Check:

- `git status`;
- active OpenSpec change;
- relevant source files;
- relevant tests;
- existing project style.

If delegated findings are prerequisites, wait at the barrier before implementation.

## Per-task flow

1. Orchestrator selects the next task and marks it `[~]`.
2. Orchestrator defines a bounded implementation contract.
3. Orchestrator implements directly or delegates to one worker.
4. Worker makes the smallest necessary change and runs focused verification.
5. Worker returns changed files, decisions, command results, risks, and blockers.
6. Orchestrator inspects the actual diff and verification evidence.
7. Reviewer performs the review mode required by checkpoint policy (`FULL` first; later `DELTA`/`CLOSURE` as appropriate).
8. After a blocking reviewer verdict or material design decision, update the Recovery capsule before large write-backs.
9. Findings are fixed, accepted explicitly, escalated, or returned to the user when the review-loop brake is triggered.
10. Orchestrator alone marks the task `[x]`.

Task completion does not by itself pass a checkpoint.

## One-writer rule

Default to one write-capable worker at a time.

Parallel writers are allowed only when the orchestrator records why all of the following are true:

- file scopes do not overlap;
- public behavior scopes do not overlap;
- shared schemas/config/contracts are not touched;
- verification can be performed independently;
- merge order cannot invalidate either result.

If these conditions are not obvious, serialize the work.

## Change discipline

One task should produce one logical change.

Avoid:

- unrelated refactors;
- broad rewrites;
- formatting-only noise;
- speculative abstractions;
- casual dependency updates;
- changing public behavior without OpenSpec.

## Simplicity rule

Prefer:

- small functions;
- explicit names;
- existing patterns;
- boring reliable code.

Avoid:

- new framework layers for one feature;
- factories/builders unless needed;
- premature plugins;
- unnecessary config toggles;
- “future-proofing” without spec.

## If design mismatch appears

If implementation reveals that `design.md` is wrong, incomplete, unsafe, or contradictory:

1. stop affected implementation;
2. report the evidence and affected scope;
3. return control to the orchestrator;
4. update `design.md` and `tasks.md` only after a design decision;
5. resume only when the contract and acceptance criteria are clear.

