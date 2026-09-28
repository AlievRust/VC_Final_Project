# Debug Playbook

Use this guide for logs, errors, failing tests, broken behavior, or screenshots.

## Debug process

1. Identify the symptom.
2. Locate the failure path.
3. Read relevant logs/code/config.
4. Form one or more hypotheses.
5. Prefer the smallest safe fix.
6. Verify with the narrowest command.
7. Update OpenSpec if behavior changes.

## Delegation for unclear failures

For a simple local bug, the primary orchestrator may investigate directly.

For a cross-layer or version-dependent failure:

1. delegate repository/runtime tracing to `scout`;
2. delegate official documentation or version checks to `researcher`, when needed;
3. wait at the evidence barrier;
4. let the orchestrator choose the hypothesis and fix boundary;
5. delegate one bounded fix to `worker`;
6. use `reviewer` when security, data, deployment, or regression risk is meaningful.

Do not start the dependent fix before required scout/researcher evidence returns.

## Do not

- rewrite large modules for a narrow bug;
- change architecture during debugging;
- add broad exception handling to hide errors;
- remove validation without understanding why it fails;
- silence logs instead of fixing the cause;
- claim the issue is fixed without verification.

## Good debugging response

Include:
- likely cause;
- evidence;
- files inspected;
- proposed fix;
- verification command;
- risk/limitation.

## If logs contain secrets

Mask:
- tokens;
- passwords;
- API keys;
- cookies;
- private URLs with credentials;
- connection strings.

## If root cause is uncertain

Say so.

Use wording like:
- “Most likely cause...”
- “Evidence points to...”
- “I would verify by running...”

Do not present guesses as facts.

If evidence invalidates the current design or expected runtime behavior, stop the affected
fix and return the decision to the primary orchestrator.
