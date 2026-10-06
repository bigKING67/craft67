# Repair and security

## Repair loop

Limit automated repair to three attempts. Each attempt records:

1. failed gate and evidence;
2. root-cause hypothesis;
3. smallest targeted change;
4. new source or asset hash;
5. the same evidence rerun;
6. `improved`, `regressed`, or `unchanged`.

At the first failed hard gate, stop every downstream stage and do not describe
the candidate, handoff, or delivery as complete. Within the existing task
authorization, a repair may make only the smallest causal change needed to
address the failure. Rerun the failed evidence and every receipt invalidated by
that changed candidate before proceeding. Do not restart modeling or change
cameras merely to hide a failing comparison, widen the task, or substitute
unaffected evidence for the failed gate. After three unsuccessful attempts,
report the concrete blocker and remaining `FAIL`, `BLOCKED`, or `UNVERIFIED`
gates.

## Safety

- Arbitrary Blender Python executes with the current user's permissions. Run
  only reviewed local scripts within the declared task boundary.
- Do not enable unknown Blender add-ons or open untrusted files with embedded
  execution behavior.
- Do not download third-party models or textures without confirmed license and
  manifest attribution.
- Do not upload private assets to external services by default.
- Use a clean browser67-managed profile, not a personal logged-in profile.
- Never record credentials, cookies, tokens, raw personal browser data, or
  private model contents in evidence reports.
- Missing tools degrade results to `UNVERIFIED`; they do not expand authority.
