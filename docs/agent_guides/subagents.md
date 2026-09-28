# Practical Subagents Guide

## Core rule

Use the fewest agents that materially reduce primary context, uncertainty, or wall-clock time. Reports must be short enough that consuming them is cheaper than repeating the investigation.

## Roles

### scout
Read-only repository/history/runtime evidence. Does not choose architecture or edit files.

### researcher
Read-only authoritative external/version evidence. Returns exact provenance for material findings.

### worker
Bounded implementation after design is settled. Stops on a new architecture/dependency/public-contract/destructive decision.

### reviewer
Independent read-only review. Depth is specified by parent as STANDARD-FOCUSED, DEEP-FULL, or DEEP-DELTA.

## Assignment contract

Include only:
- ROLE / MODE when relevant;
- GOAL;
- bounded SCOPE;
- OUT OF SCOPE;
- key INPUTS/references;
- evidence/verification needed;
- STOP CONDITIONS;
- requested OUTPUT.

For remote work, parent supplies the proven target/binding evidence. Scout must not discover a target by probing aliases.

## Report budgets

Prefer references over narrative.

- scout/researcher: usually <= 400 words;
- worker: usually <= 500 words;
- STANDARD reviewer: usually <= 500 words;
- DEEP FULL reviewer: usually <= 800 words;
- DEEP DELTA reviewer: usually <= 450 words.

Exceed only for blocking/conflicting evidence.

## Report shapes

Scout:
```text
STATUS: DONE | PARTIAL | BLOCKED
FINDINGS
EVIDENCE
UNKNOWNS/RISKS
```

Researcher:
```text
STATUS: DONE | PARTIAL | BLOCKED
FINDINGS
SOURCES
VERSION/CONFLICT NOTES
IMPLICATIONS
```

Worker:
```text
STATUS: DONE | PARTIAL | BLOCKED
CHANGES
VERIFICATION
DECISIONS/RISKS/BLOCKERS
```

Reviewer:
```text
STATUS: PASS | PASS_WITH_NOTES | FAIL
MODE: STANDARD-FOCUSED | DEEP-FULL | DEEP-DELTA
FINDINGS
EVIDENCE
MISSING VERIFICATION
RECOMMENDATION: PASS | RETURN_TO_IMPLEMENTATION | RETURN_TO_USER_DECISION
```
