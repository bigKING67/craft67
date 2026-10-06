# Evidence Graph v2

`contracts/evaluation/evidence-graph.json` is the machine authority for the
source domains used by behavioral evaluation. It separates behavioral input
from performance, native-runtime, and release metadata so unrelated version or
release changes do not force expensive model reruns.

## Causal projection

A domain fingerprint is valid only when the evaluated host can read exactly
that domain. Cross-agent and comparative runners therefore materialize a
task-specific projection of `skills/design-craft/` in a repo-external isolated
workspace. They do not copy the full Skill and then hash a subset.

Each active run records:

- the full canonical Skill tree as forensic provenance;
- the task or case behavior domain;
- the domain fingerprint at the recorded source commit;
- the exact projected tree hash read by the host;
- prompt, output, runner, and contract hashes.

Current-source validation requires the recorded domain fingerprint to match
both the recorded source commit and the current checkout. `VERSION`,
`COMPATIBILITY.json`, and host metadata remain visible as release provenance,
but they are not behavioral dependencies.

## Domain boundaries

- Motion guidance invalidates the motion cross-agent task and Emil cases.
- Visual critique guidance invalidates Taste, production, dashboard, and
  landing-polish evidence according to their explicit bindings.
- Native/adaptive guidance is separate from real native runtime evidence.
- Performance and release domains remain exact artifact/provenance contracts;
  a domain hash never relaxes tag, workflow, benchmark, or device identity.

Old cross-agent score v2-v4/run v2 and comparative run/result v3 artifacts are
read-only history. New active evidence uses cross-agent score v5/run v3 and
comparative run/result v4, produced by the projection runners rather than
transcribed from old full-tree runs.

## Change rules

1. Add or change bindings in `evidence-graph.json`, never in evaluator code.
2. Keep every pattern repository-relative; absolute paths and `..` are rejected.
3. A missing pattern match, unknown parent, cycle, or unbound active task fails
   the repository graph contract.
4. Add a domain dependency only when the file can affect that task's behavior.
5. Rerun only the active evidence whose resolved fingerprint changed, except
   when a runner/schema change requires a one-time new projection baseline.
