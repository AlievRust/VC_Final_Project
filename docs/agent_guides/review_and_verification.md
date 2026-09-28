# Practical Review and Verification Guide

## Principle

Review depth must match the requested/risk-justified scope. Independent review increases confidence; it is not proof and should not automatically expand the task into an exhaustive audit.

## SIMPLE

Usually no independent reviewer. Primary performs focused tests/checks and final diff review.

## STANDARD

Independent reviewer is optional. Use it for meaningful cross-layer/regression/failure risk or when the user requests it.

A STANDARD review is normally one focused pass covering:
- stated requirements and OpenSpec consistency;
- likely regressions;
- error/failure paths relevant to the change;
- data/security/operational risks directly implicated by the change;
- missing verification.

Do not broaden a STANDARD review into a full security audit without evidence or instruction.

## DEEP

One `FULL` review is normally expected before accepting the high-risk checkpoint.

FULL should examine the risks actually relevant to the request: correctness, requirements, security/trust boundaries, data integrity, concurrency/resource behavior, deployment/rollback, and verification. If the prompt explicitly asks for adversarial/DoS analysis, perform it; otherwise do not invent an unrelated audit program.

After blocking fixes, use one `DELTA` review covering:
- prior blocking findings;
- changed sections/files;
- side effects introduced by the fix;
- concise cross-cutting sanity checks around the affected path.

A third reviewer run is exceptional. Use it only for explicit high-assurance work or when primary cannot safely verify a bounded remaining fix. If DELTA requires another cross-cutting redesign, return the decision to the user.

## Severity

- `CRITICAL` — blocks acceptance.
- `MAJOR` — likely defect/regression/security issue/unmet requirement; blocks acceptance.
- `MINOR` — real but normally non-blocking.
- `NOTE` — observation.

## Observable contract check

When implementation changes a machine-observable signal, search for relevant downstream consumers before acceptance.

Typical signals:

* HTTP statuses and headers;
* audit/log/event names;
* API or DB status values;
* error/exit codes;
* file or manifest markers.

Check only the active spec and relevant repository references. Report semantic conflicts or ambiguous reuse of the same signal.

This is a targeted consistency check, not a whole-system audit.

## Verification

Never claim a check passed unless it ran. Use the narrowest relevant project commands. Record skipped checks and residual risk.

For STANDARD/DEEP implementation-affecting work, preserve a focused pre-change baseline when practical. Pre-existing failures are starting-state evidence, not permission for unrelated repairs.

For production/deployment/security/DB work, distinguish repository evidence from runtime evidence and from planned operational gates.

## Review loop brake

After FULL → fix → DELTA:
- local remaining defect: primary may fix and verify directly;
- new cross-cutting `CRITICAL/MAJOR`: return the architectural choice to the user unless autonomous redesign loops were explicitly requested.

## Final acceptance

Primary, not reviewer, accepts tasks/checkpoints. Reviewer PASS does not imply user approval or production readiness.
