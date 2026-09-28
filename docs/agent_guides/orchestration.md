# Practical Multi-Agent Orchestration Guide

## Goal

Use subagents to make the primary cheaper and more focused, not to maximize analysis depth. The normal target is a small number of bounded lanes whose reports replace broad primary exploration.

## Roles

| Role | Normal model | Purpose |
|---|---|---|
| Primary | Sol High / Astra when user selects it | architecture, synthesis, scope, state, final decisions |
| `scout` | Luna High | bounded repo/history/runtime evidence |
| `researcher` | Luna High | bounded external/version evidence |
| `worker` | Luna High | bounded implementation with settled design |
| `reviewer` | Sol High | independent review when independence is worth its cost |

## Select a mode first

### SIMPLE

Use for local, reversible, low-risk work.

Budget:
- primary only by default;
- 0–1 read-only agent only if it clearly saves more work than it creates;
- no mandatory reviewer/checkpoint machinery.

### STANDARD — default

Use for ordinary features/integrations/cross-module changes.

Budget:
- normally 0–2 subagents;
- prefer one clear scout or `scout + researcher` over many narrow agents;
- one optional reviewer only when cross-layer/regression risk justifies independent review;
- no exhaustive audit unless the request/evidence demands it.

### DEEP

Use for explicit deep/audit requests or inherently high-risk changes: auth/authz, trust boundaries, DB privileges/destructive migration, production security/mutation, concurrency/resource exhaustion, secrets, similarly hard-to-reverse behavior.

Budget:
- use only independent evidence lanes that materially reduce uncertainty; up to the configured cap is allowed, not required;
- one FULL independent review normally expected;
- after blocking fixes, at most one DELTA review is normal;
- third review is exceptional, not automatic;
- a second cross-cutting redesign returns to the operator unless explicitly authorized.

When uncertain, choose the cheaper safe mode.

## Delegation decision

A lane is justified when most of these are true:

- bounded question;
- reasonably independent from other lanes;
- report can replace broad primary reading;
- decision depends on evidence from that lane;
- coordination cost is smaller than primary doing it directly.

A subagent should normally **replace** work the primary would otherwise perform. If the primary must read the same material anyway, skip the agent unless independence itself is the point (reviewer).

## Typical STANDARD patterns

```text
primary + scout
primary + researcher
primary + scout + researcher
primary + two scouts
```

Avoid automatically escalating to four evidence lanes.

## Typical DEEP pattern

```text
minimum central read by primary
        ↓
1–3 useful evidence lanes in parallel
        ↓ barrier
primary targeted follow-up + synthesis
        ↓
one independent FULL review
        ↓
fix blocking findings
        ↓
optional DELTA review
        ↓
operator if another cross-cutting redesign is needed
```

Do not treat this diagram as a mandatory agent count.

## Context discipline

Primary owns central entry points and cross-cutting architecture. Delegate history sweeps, peripheral modules, external docs, production inventory, bounded tests/log analysis when useful.

After delegation:
- wait for the report before broad follow-up;
- consume references and synthesized findings;
- independently verify only decision-critical/conflicting/low-confidence claims;
- do not import raw logs unless needed.

## Barriers

Wait only when a pending lane can change the dependent decision. A blocked/partial lane does not stop unrelated work unless its missing evidence is decision-critical.

## OpenSpec/state discipline

Use strict artifact ownership and progressive checkpoints. Keep a compact Recovery capsule only for complex/checkpointed work. Future checkpoints stay skeletal.

## Baseline

STANDARD/DEEP implementation-affecting changes should establish a focused baseline when practical. Delegate it if a safe non-mutating command is a natural scout task. SIMPLE may rely on focused post-change verification when pre-change evidence adds little value.

## Remote reconnaissance

Resolve target binding before connection. With proven binding, read-only inventory is permitted without extra approval unless the user explicitly forbids connection/reconnaissance. "Do not change/deploy/modify production" is a mutation prohibition, not a read-only prohibition.

Never use an SSH/cloud/container target merely because it appears in local configuration.

## Review economy

Reviewer is not a universal second primary.

- STANDARD reviewer: focused on requirements, regressions, failure paths, and risks relevant to the task; normally one pass.
- DEEP reviewer: broad first pass at the depth requested/justified by the task; one DELTA follow-up after blocking fixes is normal.
- Do not repeatedly re-review unchanged material.
- If DELTA reveals another cross-cutting architectural choice, return it to the operator instead of continuing an autonomous review loop.

## User decisions

Do not interrupt for reversible local choices. Ask for decisions that materially change behavior, public contract, architecture/dependency, security/trust posture, destructive data/runtime action, deployment topology, scope, or a second cross-cutting redesign.

Batch related blocking decisions when possible.
